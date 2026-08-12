from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import pytest
from bs4 import BeautifulSoup

from app import create_app
from app.extensions import db
from app.integrations.evolution_api import EvolutionAPI
from app.models.cliente import Cliente
from app.models.notificacao import Notificacao
from app.models.ordem_servico import OrdemServico
from config import Config


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(
        Config,
        "SQLALCHEMY_DATABASE_URI",
        "sqlite://",
    )

    chamadas_evolution = []

    def impedir_envio(*args, **kwargs):
        chamadas_evolution.append((args, kwargs))
        raise AssertionError(
            "A consulta de notificações não pode enviar mensagens."
        )

    monkeypatch.setattr(
        EvolutionAPI,
        "enviar_texto",
        staticmethod(impedir_envio),
    )

    aplicacao = create_app()
    aplicacao.config["TESTING"] = True

    with aplicacao.app_context():
        db.create_all()

    yield aplicacao

    with aplicacao.app_context():
        db.session.remove()
        db.drop_all()

    assert chamadas_evolution == []


@pytest.fixture
def client(app):
    return app.test_client()


def hoje_local():
    return datetime.now(FUSO_BRASIL).date()


def instante_local(
    data_local: date,
    hora: int = 12,
):
    return datetime.combine(
        data_local,
        time(hour=hora),
        tzinfo=FUSO_BRASIL,
    ).astimezone(timezone.utc)


def criar_ordem(
    nome: str,
    telefone: str,
    placa: str,
    data_atendimento: date,
    proxima_troca_data: date,
    proxima_troca_km: int = 95000,
    quilometragem: int = 85000,
):
    cliente = Cliente(
        nome=nome,
        telefone=telefone,
        recebe_notificacao=True,
        ativo=True,
    )

    db.session.add(cliente)
    db.session.flush()

    ordem = OrdemServico(
        cliente_id=cliente.id,
        placa=placa,
        marca="Volkswagen",
        modelo="Gol",
        data_servico=data_atendimento,
        quilometragem=quilometragem,
        descricao_servico="Troca de óleo",
        proxima_troca_km=proxima_troca_km,
        proxima_troca_data=proxima_troca_data,
    )

    db.session.add(ordem)
    db.session.flush()

    return cliente, ordem


def criar_notificacao(
    nome: str,
    telefone: str,
    placa: str,
    data_agendada: date,
    status: str = "PENDENTE",
    tentativas: int = 0,
    data_envio: datetime | None = None,
    erro: str | None = None,
    data_atendimento: date | None = None,
    proxima_troca_data: date | None = None,
    proxima_troca_km: int = 95000,
    quilometragem: int = 85000,
):
    data_atendimento = (
        data_atendimento
        or data_agendada - timedelta(days=90)
    )

    proxima_troca_data = (
        proxima_troca_data
        or data_agendada + timedelta(days=7)
    )

    cliente, ordem = criar_ordem(
        nome=nome,
        telefone=telefone,
        placa=placa,
        data_atendimento=data_atendimento,
        proxima_troca_data=proxima_troca_data,
        proxima_troca_km=proxima_troca_km,
        quilometragem=quilometragem,
    )

    notificacao = Notificacao(
        cliente_id=cliente.id,
        ordem_servico_id=ordem.id,
        data_agendada_disparo=data_agendada,
        status=status,
        mensagem=f"Mensagem para {nome}",
        tentativas=tentativas,
        data_envio=data_envio,
        erro=erro,
    )

    db.session.add(notificacao)
    db.session.flush()

    return notificacao


def analisar(resposta):
    assert resposta.status_code == 200

    return BeautifulSoup(
        resposta.data,
        "html.parser",
    )


def texto(elemento):
    return " ".join(
        elemento.get_text(
            " ",
            strip=True,
        ).split()
    )


def linhas_notificacoes(pagina):
    return pagina.select(
        "tr[data-notificacao-row]"
    )


def nomes_listados(pagina):
    return [
        texto(linha)
        for linha in linhas_notificacoes(pagina)
    ]


def test_listagem_usa_notificacoes_reais_e_renderiza_estrutura(
    app,
    client,
):
    hoje = hoje_local()

    with app.app_context():
        criar_ordem(
            nome="Somente ordem",
            telefone="47999990000",
            placa="SEM1F23",
            data_atendimento=(
                hoje - timedelta(days=30)
            ),
            proxima_troca_data=(
                hoje + timedelta(days=90)
            ),
        )

        notificacao = criar_notificacao(
            nome="Cliente na fila",
            telefone="47991977977",
            placa="ABC1D23",
            data_agendada=(
                hoje + timedelta(days=3)
            ),
        )

        notificacao_id = notificacao.id

        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/notificacoes"
        )
    )

    conteudo = texto(pagina)

    assert "Notificações" in [
        texto(titulo)
        for titulo in pagina.find_all("h1")
    ]

    assert (
        "Acompanhe os avisos programados e enviados aos clientes."
        in conteudo
    )

    assert "Cliente na fila" in conteudo
    assert "Somente ordem" not in conteudo

    assert len(
        pagina.select(
            ".page-section > .panel"
        )
    ) == 1

    botao_visualizar = pagina.find(
        id="acaoVisualizarNotificacao"
    )

    assert botao_visualizar is not None
    assert botao_visualizar.has_attr(
        "disabled"
    )

    assert "button-small" in (
        botao_visualizar.get(
            "class",
            [],
        )
    )

    assert (
        texto(botao_visualizar)
        == "Visualizar"
    )

    selecoes = pagina.select(
        "input[data-notificacao-selection]"
    )

    assert len(selecoes) == 1
    assert selecoes[0]["type"] == "checkbox"

    assert (
        selecoes[0][
            "data-url-visualizar"
        ].endswith(
            f"/{notificacao_id}/visualizar"
        )
    )

    assert (
        pagina.find(
            "select",
            id="fila",
        )
        is None
    )

    assert (
        pagina.find(
            "input",
            id="data_inicial",
        )
        is None
    )

    assert (
        pagina.find(
            "input",
            id="data_final",
        )
        is None
    )

    situacao = pagina.find(
        "select",
        id="situacao",
    )

    assert situacao is not None

    assert [
        opcao["value"]
        for opcao
        in situacao.find_all("option")
    ] == [
        "todas",
        "PENDENTE",
        "ENVIADO",
        "FALHA",
    ]

    assert [
        opcao.get_text(strip=True)
        for opcao
        in situacao.find_all("option")
    ] == [
        "Todas",
        "Pendentes",
        "Enviadas",
        "Falhas",
    ]

    tipo_pesquisa = pagina.find(
        "select",
        id="tipo_pesquisa",
    )

    assert tipo_pesquisa is not None

    assert [
        opcao["value"]
        for opcao
        in tipo_pesquisa.find_all("option")
    ] == [
        "cliente",
        "telefone",
        "placa",
    ]

    formulario = pagina.find(
        "form",
        class_="page-search",
    )

    assert formulario is not None

    botao_consultar = formulario.find(
        "button",
        attrs={
            "type": "submit",
        },
    )

    assert (
        "Consultar"
        in texto(botao_consultar)
    )

    limpar = formulario.find(
        "a",
        string=lambda valor: (
            valor
            and valor.strip()
            == "Limpar"
        ),
    )

    assert limpar is not None

    assert (
        urlparse(
            limpar["href"]
        ).path
        == "/painel/notificacoes"
    )

    assert (
        urlparse(
            limpar["href"]
        ).query
        == ""
    )

    tabela = pagina.find(
        "table",
        class_="system-table",
    )

    assert tabela is not None

    assert [
        texto(cabecalho)
        for cabecalho
        in tabela.find_all("th")
    ] == [
        "Selecionar",
        "Cliente",
        "Telefone",
        "Placa",
        "Próxima troca prevista",
        "Data programada para envio",
        "Envio",
        "Situação",
        "Tentativas",
    ]

    assert (
        texto(
            pagina.find(
                class_="table-footer-information"
            )
        )
        == "1 registro"
    )

    menu_notificacoes = pagina.find(
        "a",
        href="/painel/notificacoes",
        class_="sidebar-navigation-link",
    )

    assert menu_notificacoes is not None

    assert (
        "is-active"
        in menu_notificacoes.get(
            "class",
            [],
        )
    )

    assert (
        menu_notificacoes.get(
            "aria-current"
        )
        == "page"
    )


def test_resumo_colorido_nao_e_exibido(
    app,
    client,
):
    hoje = hoje_local()

    with app.app_context():
        criar_notificacao(
            "Pendente",
            "47990000001",
            "PEN0001",
            hoje + timedelta(days=2),
        )

        criar_notificacao(
            "Falha",
            "47990000002",
            "FAL0001",
            hoje,
            status="FALHA",
            tentativas=1,
            erro="Erro",
        )

        criar_notificacao(
            "Enviada",
            "47990000003",
            "ENV0001",
            hoje - timedelta(days=1),
            status="ENVIADO",
            tentativas=1,
            data_envio=instante_local(
                hoje
            ),
        )

        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/notificacoes"
        )
    )

    assert (
        pagina.find(
            class_="summary-grid"
        )
        is None
    )

    assert (
        texto(
            pagina.find(
                class_="table-footer-information"
            )
        )
        == "3 registros"
    )


@pytest.mark.parametrize(
    (
        "situacao",
        "nome_esperado",
    ),
    [
        (
            "PENDENTE",
            "Registro pendente",
        ),
        (
            "ENVIADO",
            "Registro enviado",
        ),
        (
            "FALHA",
            "Registro com falha",
        ),
    ],
)
def test_filtro_de_situacao_exibe_opcoes_da_tela(
    app,
    client,
    situacao,
    nome_esperado,
):
    hoje = hoje_local()

    with app.app_context():
        criar_notificacao(
            "Registro pendente",
            "47990000201",
            "SIT0201",
            hoje + timedelta(days=1),
            status="PENDENTE",
        )

        criar_notificacao(
            "Registro enviado",
            "47990000202",
            "SIT0202",
            hoje - timedelta(days=1),
            status="ENVIADO",
            tentativas=1,
            data_envio=instante_local(
                hoje
            ),
        )

        criar_notificacao(
            "Registro com falha",
            "47990000203",
            "SIT0203",
            hoje - timedelta(days=1),
            status="FALHA",
            tentativas=1,
            erro="Erro",
        )

        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/notificacoes",
            query_string={
                "situacao": situacao,
            },
        )
    )

    linhas = nomes_listados(
        pagina
    )

    assert len(linhas) == 1
    assert nome_esperado in linhas[0]

    selecionada = pagina.find(
        "select",
        id="situacao",
    ).find(
        "option",
        selected=True,
    )

    assert selecionada is not None

    assert (
        selecionada["value"]
        == situacao
    )


def test_cancelada_aparece_em_todas_sem_opcao_especifica(
    app,
    client,
):
    hoje = hoje_local()

    with app.app_context():
        criar_notificacao(
            "Registro cancelado",
            "47990000204",
            "SIT0204",
            hoje - timedelta(days=2),
            status="CANCELADO",
        )

        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/notificacoes"
        )
    )

    assert (
        "Registro cancelado"
        in texto(pagina)
    )

    assert (
        "Cancelada"
        in texto(pagina)
    )

    situacao = pagina.find(
        "select",
        id="situacao",
    )

    assert (
        "CANCELADO"
        not in [
            opcao["value"]
            for opcao
            in situacao.find_all(
                "option"
            )
        ]
    )


@pytest.mark.parametrize(
    (
        "tipo_pesquisa",
        "pesquisa",
        "pesquisa_normalizada",
        "nome_esperado",
    ),
    [
        (
            "cliente",
            "maria silva",
            "maria silva",
            "Maria Silva",
        ),
        (
            "telefone",
            "(47) 99197-7002",
            "47991977002",
            "João Souza",
        ),
        (
            "placa",
            "abc-1d23!xyz",
            "ABC1D23",
            "Carlos Lima",
        ),
    ],
)
def test_pesquisa_cliente_telefone_e_placa_normaliza_termo(
    app,
    client,
    tipo_pesquisa,
    pesquisa,
    pesquisa_normalizada,
    nome_esperado,
):
    hoje = hoje_local()

    with app.app_context():
        criar_notificacao(
            "Maria Silva",
            "47991977001",
            "DEF2E34",
            hoje + timedelta(days=1),
        )

        criar_notificacao(
            "João Souza",
            "47991977002",
            "GHI3F45",
            hoje + timedelta(days=2),
        )

        criar_notificacao(
            "Carlos Lima",
            "47991977003",
            "ABC1D23",
            hoje + timedelta(days=3),
        )

        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/notificacoes",
            query_string={
                "tipo_pesquisa": tipo_pesquisa,
                "pesquisa": pesquisa,
            },
        )
    )

    linhas = nomes_listados(
        pagina
    )

    assert len(linhas) == 1

    assert (
        nome_esperado
        in linhas[0]
    )

    assert (
        pagina.find(
            "input",
            id="pesquisa",
        )["value"]
        == pesquisa_normalizada
    )


def test_situacao_e_pesquisa_funcionam_em_conjunto(
    app,
    client,
):
    hoje = hoje_local()

    with app.app_context():
        criar_notificacao(
            "Josué Pendente",
            "47990000401",
            "COM0401",
            hoje + timedelta(days=3),
            status="PENDENTE",
        )

        criar_notificacao(
            "Josué Enviado",
            "47990000402",
            "COM0402",
            hoje + timedelta(days=3),
            status="ENVIADO",
            tentativas=1,
            data_envio=instante_local(
                hoje
            ),
        )

        criar_notificacao(
            "Outro Pendente",
            "47990000403",
            "COM0403",
            hoje + timedelta(days=4),
            status="PENDENTE",
        )

        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/notificacoes",
            query_string={
                "situacao": "PENDENTE",
                "tipo_pesquisa": "cliente",
                "pesquisa": "Josué",
            },
        )
    )

    linhas = nomes_listados(
        pagina
    )

    assert len(linhas) == 1

    assert (
        "Josué Pendente"
        in linhas[0]
    )

    assert (
        "Josué Enviado"
        not in linhas[0]
    )


def test_paginacao_limita_preserva_filtros_e_oferece_navegacao(
    app,
    client,
):
    hoje = hoje_local()

    with app.app_context():
        for numero in range(
            1,
            26,
        ):
            criar_notificacao(
                nome=(
                    f"Grupo Alfa "
                    f"{numero:02d}"
                ),
                telefone=(
                    f"4798{numero:07d}"
                ),
                placa=(
                    f"A{numero:06d}"
                ),
                data_agendada=(
                    hoje
                    + timedelta(
                        days=numero
                    )
                ),
                status="PENDENTE",
            )

        db.session.commit()

    filtros = {
        "situacao": "PENDENTE",
        "tipo_pesquisa": "cliente",
        "pesquisa": "Grupo Alfa",
        "pagina": "2",
    }

    pagina = analisar(
        client.get(
            "/painel/notificacoes",
            query_string=filtros,
        )
    )

    linhas = nomes_listados(
        pagina
    )

    assert len(linhas) == 10

    assert (
        "Grupo Alfa 11"
        in linhas[0]
    )

    assert (
        "Grupo Alfa 20"
        in linhas[-1]
    )

    navegacao = pagina.find(
        class_="table-pagination"
    )

    assert navegacao is not None

    assert (
        navegacao.find(
            class_="is-active"
        ).get_text(
            strip=True
        )
        == "2"
    )

    assert (
        navegacao.find(
            "a",
            attrs={
                "aria-label":
                "Página anterior",
            },
        )
        is not None
    )

    assert (
        navegacao.find(
            "a",
            attrs={
                "aria-label":
                "Próxima página",
            },
        )
        is not None
    )

    filtros_sem_pagina = {
        chave: [valor]
        for chave, valor
        in filtros.items()
        if chave != "pagina"
    }

    for link in navegacao.find_all(
        "a"
    ):
        parametros = parse_qs(
            urlparse(
                link["href"]
            ).query
        )

        for chave, valor in (
            filtros_sem_pagina.items()
        ):
            assert (
                parametros[chave]
                == valor
            )

        assert (
            "fila"
            not in parametros
        )

        assert (
            "data_inicial"
            not in parametros
        )

        assert (
            "data_final"
            not in parametros
        )

    formulario_pagina = pagina.find(
        "form",
        class_="pagination-jump",
    )

    assert (
        formulario_pagina
        is not None
    )

    campo_pagina = (
        formulario_pagina.find(
            "input",
            attrs={
                "name": "pagina",
            },
        )
    )

    assert (
        campo_pagina["type"]
        == "number"
    )

    assert (
        campo_pagina["value"]
        == "2"
    )

    assert (
        campo_pagina["min"]
        == "1"
    )

    assert (
        campo_pagina["max"]
        == "3"
    )

    campos_ocultos = {
        campo["name"]:
        campo.get(
            "value",
            "",
        )
        for campo
        in formulario_pagina.find_all(
            "input",
            attrs={
                "type": "hidden",
            },
        )
    }

    assert campos_ocultos == {
        "situacao": "PENDENTE",
        "tipo_pesquisa": "cliente",
        "pesquisa": "Grupo Alfa",
    }

    assert (
        texto(
            pagina.find(
                class_="table-footer-information"
            )
        )
        == "25 registros"
    )


def test_paginacao_trata_paginas_invalidas(
    app,
    client,
):
    hoje = hoje_local()

    with app.app_context():
        for numero in range(
            1,
            26,
        ):
            criar_notificacao(
                nome=(
                    f"Página "
                    f"{numero:02d}"
                ),
                telefone=(
                    f"4797{numero:07d}"
                ),
                placa=(
                    f"P{numero:06d}"
                ),
                data_agendada=(
                    hoje
                    + timedelta(
                        days=numero
                    )
                ),
            )

        db.session.commit()

    casos = (
        (
            "0",
            "1",
            10,
        ),
        (
            "-3",
            "1",
            10,
        ),
        (
            "texto",
            "1",
            10,
        ),
        (
            "999",
            "3",
            5,
        ),
    )

    for (
        solicitada,
        esperada,
        quantidade,
    ) in casos:
        pagina = analisar(
            client.get(
                "/painel/notificacoes",
                query_string={
                    "pagina":
                    solicitada,
                },
            )
        )

        assert (
            pagina.find(
                class_="table-pagination"
            ).find(
                class_="is-active"
            ).get_text(
                strip=True
            )
            == esperada
        )

        assert (
            pagina.find(
                "input",
                attrs={
                    "name":
                    "pagina",
                },
            )["value"]
            == esperada
        )

        assert (
            len(
                linhas_notificacoes(
                    pagina
                )
            )
            == quantidade
        )


def test_envio_amigavel_e_identificacao_de_atraso(
    app,
    client,
):
    hoje = hoje_local()

    with app.app_context():
        criar_notificacao(
            "Atrasada dois dias",
            "47990000501",
            "ATR0501",
            hoje - timedelta(days=2),
        )

        criar_notificacao(
            "Envio hoje",
            "47990000502",
            "ATR0502",
            hoje,
        )

        criar_notificacao(
            "Envio amanhã",
            "47990000503",
            "ATR0503",
            hoje + timedelta(days=1),
        )

        criar_notificacao(
            "Envio em três dias",
            "47990000504",
            "ATR0504",
            hoje + timedelta(days=3),
        )

        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/notificacoes"
        )
    )

    conteudo = texto(
        pagina
    )

    assert (
        "Atrasada há 2 dias"
        in conteudo
    )

    assert (
        "Hoje"
        in conteudo
    )

    assert (
        "Amanhã"
        in conteudo
    )

    assert (
        "Em 3 dias"
        in conteudo
    )

    linha_atrasada = next(
        linha
        for linha
        in linhas_notificacoes(
            pagina
        )
        if (
            "Atrasada dois dias"
            in texto(linha)
        )
    )

    assert (
        "Pendente"
        in texto(
            linha_atrasada
        )
    )

    assert (
        "Atrasada"
        in texto(
            linha_atrasada
        )
    )


def test_sem_resultados_exibe_mensagem_simples(
    client,
):
    pagina = analisar(
        client.get(
            "/painel/notificacoes",
            query_string={
                "tipo_pesquisa":
                "cliente",
                "pesquisa":
                "Cliente inexistente",
            },
        )
    )

    conteudo = texto(
        pagina
    )

    assert (
        "Nenhum resultado"
        in conteudo
    )

    assert (
        "Ajuste os filtros para consultar outros registros"
        not in conteudo
    )


def test_detalhes_exibe_dados_existentes_sem_edicao(
    app,
    client,
):
    hoje = hoje_local()

    data_atendimento = (
        hoje - timedelta(
            days=90
        )
    )

    proxima_data = (
        hoje + timedelta(
            days=7
        )
    )

    with app.app_context():
        notificacao = criar_notificacao(
            nome="Maria da Silva",
            telefone="47991977977",
            placa="ABC1D23",
            data_agendada=hoje,
            status="FALHA",
            tentativas=3,
            erro="Tempo limite excedido",
            data_atendimento=(
                data_atendimento
            ),
            proxima_troca_data=(
                proxima_data
            ),
            proxima_troca_km=95000,
            quilometragem=85000,
        )

        notificacao_id = (
            notificacao.id
        )

        ordem_id = (
            notificacao
            .ordem_servico_id
        )

        db.session.commit()

    pagina = analisar(
        client.get(
            (
                "/painel/notificacoes/"
                f"{notificacao_id}"
                "/visualizar"
            )
        )
    )

    conteudo = texto(
        pagina
    )

    for valor in (
        "Maria da Silva",
        "47991977977",
        "ABC1D23",
        f"#{ordem_id}",
        data_atendimento.strftime(
            "%d/%m/%Y"
        ),
        "85.000 km",
        "95.000 km",
        proxima_data.strftime(
            "%d/%m/%Y"
        ),
        hoje.strftime(
            "%d/%m/%Y"
        ),
        "Falha",
        "3",
        "Tempo limite excedido",
    ):
        assert (
            valor
            in conteudo
        )

    assert (
        pagina.find("form")
        is None
    )

    assert (
        pagina.find("input")
        is None
    )

    assert (
        pagina.find("textarea")
        is None
    )

    assert (
        pagina.find("select")
        is None
    )

    assert (
        "Tentar novamente"
        not in conteudo
    )

    voltar = pagina.find(
        "a",
        string=lambda valor: (
            valor
            and valor.strip()
            == "Voltar"
        ),
    )

    assert voltar is not None

    assert (
        urlparse(
            voltar["href"]
        ).path
        == "/painel/notificacoes"
    )

    assert (
        "button-small"
        in voltar.get(
            "class",
            [],
        )
    )

    with app.app_context():
        registro = db.session.get(
            Notificacao,
            notificacao_id,
        )

        assert (
            registro.status
            == "FALHA"
        )

        assert (
            registro.tentativas
            == 3
        )

        assert (
            registro.erro
            == "Tempo limite excedido"
        )

        assert (
            registro.data_envio
            is None
        )


def test_detalhes_exibe_data_de_envio_quando_existente(
    app,
    client,
):
    hoje = hoje_local()

    data_envio = instante_local(
        hoje,
        hora=14,
    )

    with app.app_context():
        notificacao = criar_notificacao(
            nome="Cliente enviado",
            telefone="47990000601",
            placa="ENV0601",
            data_agendada=hoje,
            status="ENVIADO",
            tentativas=1,
            data_envio=data_envio,
        )

        notificacao_id = (
            notificacao.id
        )

        db.session.commit()

    pagina = analisar(
        client.get(
            (
                "/painel/notificacoes/"
                f"{notificacao_id}"
                "/visualizar"
            )
        )
    )

    conteudo = texto(
        pagina
    )

    assert (
        "Enviada"
        in conteudo
    )

    assert (
        hoje.strftime(
            "%d/%m/%Y"
        )
        in conteudo
    )

    assert (
        "14:00"
        in conteudo
    )


def test_detalhes_inexistente_redireciona_para_listagem(
    client,
):
    resposta = client.get(
        (
            "/painel/notificacoes/"
            "999/visualizar"
        )
    )

    assert (
        resposta.status_code
        == 302
    )

    assert (
        urlparse(
            resposta.headers[
                "Location"
            ]
        ).path
        == "/painel/notificacoes"
    )


def test_dashboard_exibe_pendentes_reais_e_aponta_para_notificacoes(
    app,
    client,
):
    hoje = hoje_local()

    with app.app_context():
        criar_notificacao(
            "Pendente um",
            "47990000701",
            "DSH0701",
            hoje + timedelta(days=1),
        )

        criar_notificacao(
            "Pendente dois",
            "47990000702",
            "DSH0702",
            hoje + timedelta(days=2),
        )

        criar_notificacao(
            "Já enviada",
            "47990000703",
            "DSH0703",
            hoje - timedelta(days=1),
            status="ENVIADO",
            tentativas=1,
            data_envio=instante_local(
                hoje
            ),
        )

        db.session.commit()

    pagina = analisar(
        client.get("/")
    )

    cartao = next(
        elemento
        for elemento
        in pagina.select(
            ".summary-card"
        )
        if (
            "Notificações"
            in texto(elemento)
        )
    )

    assert (
        "Notificações pendentes"
        in texto(cartao)
    )

    assert (
        cartao.find(
            class_="summary-value"
        ).get_text(
            strip=True
        )
        == "2"
    )

    assert (
        urlparse(
            cartao.find(
                "a"
            )["href"]
        ).path
        == "/painel/notificacoes"
    )


def test_javascript_limita_mascaras_e_mantem_selecao_unica():
    caminho = (
        Path(__file__).parents[1]
        / "app"
        / "static"
        / "js"
        / "notificacoes.js"
    )

    codigo = caminho.read_text(
        encoding="utf-8"
    )

    assert (
        ".slice(0, 11)"
        in codigo
    )

    assert (
        ".slice(0, 7)"
        in codigo
    )

    assert (
        "selecao.checked = false"
        in codigo
    )

    assert (
        "acaoVisualizar.disabled = !notificacaoSelecionada"
        in codigo
    )