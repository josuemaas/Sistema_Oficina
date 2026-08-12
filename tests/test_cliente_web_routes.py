from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from bs4 import BeautifulSoup

from app import create_app
from app.extensions import db
from app.models.cliente import Cliente
from app.routes.cliente_web_routes import filtrar_clientes, filtrar_situacao_clientes
from app.services.cliente_service import ClienteService
from config import Config


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    aplicacao = create_app()
    aplicacao.config["TESTING"] = True

    with aplicacao.app_context():
        db.create_all()

    yield aplicacao

    with aplicacao.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def criar_clientes_listagem(quantidade, prefixo="Cliente", inicio=1, ativo=True):
    return [
        SimpleNamespace(
            id=numero,
            nome=f"{prefixo} {numero:02d}",
            cpf_cnpj=None,
            telefone=f"479{numero:08d}",
            ativo=ativo,
            recebe_notificacao=False,
        )
        for numero in range(inicio, inicio + quantidade)
    ]


def analisar(resposta):
    assert resposta.status_code == 200
    return BeautifulSoup(resposta.data, "html.parser")


def texto(elemento):
    return " ".join(elemento.get_text(" ", strip=True).split())


def test_filtrar_clientes_pelo_campo_selecionado():
    clientes = [
        SimpleNamespace(
            nome="Maria da Silva",
            cpf_cnpj="111.222.333-44",
            telefone="(47) 99999-1111",
        ),
        SimpleNamespace(
            nome="João Souza",
            cpf_cnpj=None,
            telefone="(47) 98888-2222",
        ),
    ]

    assert filtrar_clientes(clientes, "maria", "nome") == [clientes[0]]
    assert filtrar_clientes(clientes, "111.222.333-44", "cpf") == [clientes[0]]
    assert filtrar_clientes(clientes, "98888-2222", "telefone") == [clientes[1]]
    assert filtrar_clientes(clientes, "maria", "tipo-invalido") == [clientes[0]]


def test_filtrar_clientes_por_situacao():
    clientes = [
        SimpleNamespace(nome="Cliente ativo", ativo=True),
        SimpleNamespace(nome="Cliente desativado", ativo=False),
    ]

    assert filtrar_situacao_clientes(clientes, "todas") == clientes
    assert filtrar_situacao_clientes(clientes, "ativo") == [clientes[0]]
    assert filtrar_situacao_clientes(clientes, "desativado") == [clientes[1]]


def test_listagem_renderiza_filtros_acoes_e_selecao(app, client):
    with app.app_context():
        db.session.add_all(
            [
                Cliente(
                    nome="Maria da Silva",
                    cpf_cnpj="11122233344",
                    telefone="47999991111",
                ),
                Cliente(
                    nome="João Souza",
                    cpf_cnpj="55566677788",
                    telefone="47988882222",
                ),
            ]
        )
        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/clientes",
            query_string={
                "tipo_pesquisa": "cpf",
                "pesquisa": "111.222.333-44",
            },
        )
    )

    situacao = pagina.find("select", id="situacao")
    tipo_pesquisa = pagina.find("select", id="tipo_pesquisa")
    campo_pesquisa = pagina.find("input", id="pesquisa")
    formulario = tipo_pesquisa.find_parent("form", class_="page-search")

    assert [opcao["value"] for opcao in situacao.find_all("option")] == [
        "todas",
        "ativo",
        "desativado",
    ]

    assert [opcao.get_text(strip=True) for opcao in situacao.find_all("option")] == [
        "Todas",
        "Ativos",
        "Desativados",
    ]

    assert situacao.find("option", selected=True)["value"] == "todas"

    assert [opcao["value"] for opcao in tipo_pesquisa.find_all("option")] == [
        "nome",
        "cpf",
        "telefone",
    ]

    assert tipo_pesquisa.find("option", selected=True)["value"] == "cpf"

    assert texto(
        formulario.find(
            "label",
            attrs={"for": "situacao"},
        )
    ) == "Situação"

    assert texto(
        formulario.find(
            "label",
            attrs={"for": "tipo_pesquisa"},
        )
    ) == "Pesquisar por"

    assert tipo_pesquisa.has_attr("data-client-search-type")
    assert campo_pesquisa.has_attr("data-client-search-term")

    botao_consultar = formulario.find(
        "button",
        attrs={"type": "submit"},
    )

    botao_limpar = formulario.find(
        "a",
        string=lambda valor: valor and valor.strip() == "Limpar",
    )

    assert "Consultar" in texto(botao_consultar)
    assert botao_limpar is not None

    botao_alterar = pagina.find(id="acaoAlterarCliente")
    botao_visualizar = pagina.find(id="acaoVisualizarCliente")
    botao_situacao = pagina.find(id="acaoSituacaoCliente")

    assert botao_alterar.has_attr("disabled")
    assert botao_visualizar.has_attr("disabled")
    assert botao_situacao.has_attr("disabled")
    assert texto(botao_situacao) == "Desativar"
    assert pagina.find(id="acaoSelecionarCliente") is None

    tabela = pagina.find(
        "table",
        class_="system-table",
    )

    assert [texto(cabecalho) for cabecalho in tabela.find_all("th")] == [
        "Selecionar",
        "Código",
        "Nome/Razão Social",
        "CPF",
        "Telefone",
        "Situação",
    ]

    assert "Maria da Silva" in texto(tabela)
    assert "João Souza" not in texto(tabela)

    selecoes = tabela.select(
        "input[data-cliente-selection]"
    )

    assert len(selecoes) == 1
    assert selecoes[0]["data-cliente-ativo"] == "true"
    assert selecoes[0].has_attr("data-url-situacao")

    assert texto(
        pagina.find(
            class_="table-footer-information"
        )
    ) == "1 registro"


def test_listagem_filtra_por_situacao(app, client):
    with app.app_context():
        db.session.add_all(
            [
                Cliente(
                    nome="Cliente ativo",
                    telefone="47999991111",
                    ativo=True,
                ),
                Cliente(
                    nome="Cliente desativado",
                    telefone="47988882222",
                    ativo=False,
                ),
            ]
        )
        db.session.commit()

    pagina_ativos = analisar(
        client.get(
            "/painel/clientes",
            query_string={
                "situacao": "ativo",
            },
        )
    )

    assert "Cliente ativo" in texto(pagina_ativos)
    assert "Cliente desativado" not in texto(pagina_ativos)

    pagina_desativados = analisar(
        client.get(
            "/painel/clientes",
            query_string={
                "situacao": "desativado",
            },
        )
    )

    assert "Cliente desativado" in texto(pagina_desativados)
    assert "Cliente ativo" not in texto(pagina_desativados)
    assert "Desativado" in texto(pagina_desativados)


def test_situacao_e_pesquisa_funcionam_em_conjunto(app, client):
    with app.app_context():
        db.session.add_all(
            [
                Cliente(
                    nome="Maria Ativa",
                    telefone="47999991111",
                    ativo=True,
                ),
                Cliente(
                    nome="Maria Desativada",
                    telefone="47988882222",
                    ativo=False,
                ),
                Cliente(
                    nome="João Ativo",
                    telefone="47977773333",
                    ativo=True,
                ),
            ]
        )
        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/clientes",
            query_string={
                "situacao": "desativado",
                "tipo_pesquisa": "nome",
                "pesquisa": "Maria",
            },
        )
    )

    conteudo = texto(pagina)

    assert "Maria Desativada" in conteudo
    assert "Maria Ativa" not in conteudo
    assert "João Ativo" not in conteudo


@pytest.mark.parametrize(
    "quantidade",
    [
        0,
        10,
    ],
)
def test_clientes_uma_pagina_oculta_controles_e_exibe_total(
    client,
    monkeypatch,
    quantidade,
):
    clientes = criar_clientes_listagem(
        quantidade
    )

    monkeypatch.setattr(
        ClienteService,
        "listar_clientes",
        lambda: clientes,
    )

    pagina = analisar(
        client.get(
            "/painel/clientes"
        )
    )

    assert len(
        pagina.select(
            "input[data-cliente-selection]"
        )
    ) == quantidade

    assert pagina.find(
        class_="table-pagination"
    ) is None

    assert pagina.find(
        class_="pagination-jump"
    ) is None

    assert texto(
        pagina.find(
            class_="table-footer-information"
        )
    ) == f"{quantidade} registros"

    if quantidade == 0:
        assert "Nenhum resultado" in texto(
            pagina
        )


def test_clientes_paginacao_filtra_preserva_parametros_e_navegacao(
    client,
    monkeypatch,
):
    clientes = criar_clientes_listagem(
        25,
        prefixo="Grupo Alfa",
    )

    clientes += criar_clientes_listagem(
        4,
        prefixo="Grupo Beta",
        inicio=101,
    )

    monkeypatch.setattr(
        ClienteService,
        "listar_clientes",
        lambda: clientes,
    )

    pagina = analisar(
        client.get(
            "/painel/clientes",
            query_string={
                "situacao": "todas",
                "tipo_pesquisa": "nome",
                "pesquisa": "Grupo Alfa",
                "pagina": 2,
            },
        )
    )

    tabela = pagina.find(
        "table",
        class_="system-table",
    )

    selecoes = tabela.select(
        "input[data-cliente-selection]"
    )

    assert len(selecoes) == 10

    assert [
        selecao.find_parent(
            "tr"
        ).find_all(
            "td"
        )[1].get_text(
            strip=True
        )
        for selecao in selecoes
    ] == [
        str(numero)
        for numero in range(
            11,
            21,
        )
    ]

    assert "Grupo Beta" not in texto(
        tabela
    )

    navegacao = pagina.find(
        class_="table-pagination"
    )

    assert navegacao.find(
        class_="is-active"
    ).get_text(
        strip=True
    ) == "2"

    anterior = navegacao.find(
        "a",
        attrs={
            "aria-label": "Página anterior",
        },
    )

    proxima = navegacao.find(
        "a",
        attrs={
            "aria-label": "Próxima página",
        },
    )

    esperado_anterior = {
        "pagina": ["1"],
        "situacao": ["todas"],
        "tipo_pesquisa": ["nome"],
        "pesquisa": ["Grupo Alfa"],
    }

    esperado_proxima = {
        "pagina": ["3"],
        "situacao": ["todas"],
        "tipo_pesquisa": ["nome"],
        "pesquisa": ["Grupo Alfa"],
    }

    assert parse_qs(
        urlparse(
            anterior["href"]
        ).query
    ) == esperado_anterior

    assert parse_qs(
        urlparse(
            proxima["href"]
        ).query
    ) == esperado_proxima

    for link in navegacao.find_all(
        "a"
    ):
        parametros = parse_qs(
            urlparse(
                link["href"]
            ).query
        )

        assert parametros[
            "situacao"
        ] == ["todas"]

        assert parametros[
            "tipo_pesquisa"
        ] == ["nome"]

        assert parametros[
            "pesquisa"
        ] == ["Grupo Alfa"]

    formulario_pagina = pagina.find(
        "form",
        class_="pagination-jump",
    )

    campos = {
        campo["name"]: campo.get(
            "value",
            "",
        )
        for campo in formulario_pagina.find_all(
            "input"
        )
    }

    assert campos == {
        "situacao": "todas",
        "tipo_pesquisa": "nome",
        "pesquisa": "Grupo Alfa",
        "pagina": "2",
    }

    assert texto(
        pagina.find(
            class_="table-footer-information"
        )
    ) == "25 registros"


def test_clientes_paginacao_trata_paginas_invalidas(
    client,
    monkeypatch,
):
    clientes = criar_clientes_listagem(
        25
    )

    monkeypatch.setattr(
        ClienteService,
        "listar_clientes",
        lambda: clientes,
    )

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
        pagina_solicitada,
        pagina_esperada,
        quantidade,
    ) in casos:
        pagina = analisar(
            client.get(
                "/painel/clientes",
                query_string={
                    "pagina": pagina_solicitada,
                },
            )
        )

        assert (
            pagina.find(
                class_="table-pagination"
            )
            .find(
                class_="is-active"
            )
            .get_text(
                strip=True
            )
            == pagina_esperada
        )

        assert pagina.find(
            "input",
            attrs={
                "name": "pagina",
            },
        )["value"] == pagina_esperada

        assert len(
            pagina.select(
                "input[data-cliente-selection]"
            )
        ) == quantidade


def test_clientes_paginacao_preserva_modo_selecionar(
    client,
    monkeypatch,
):
    clientes = criar_clientes_listagem(
        12,
        prefixo="Selecionável",
    )

    monkeypatch.setattr(
        ClienteService,
        "listar_clientes",
        lambda: clientes,
    )

    pagina = analisar(
        client.get(
            "/painel/clientes",
            query_string={
                "modo": "selecionar",
                "ordem_id": 42,
                "situacao": "todas",
                "tipo_pesquisa": "nome",
                "pesquisa": "Selecionável",
                "pagina": 2,
            },
        )
    )

    navegacao = pagina.find(
        class_="table-pagination"
    )

    assert len(
        pagina.select(
            "input[data-cliente-selection]"
        )
    ) == 2

    assert pagina.find(
        id="acaoSelecionarCliente",
    ).has_attr(
        "disabled"
    )

    for link in navegacao.find_all(
        "a"
    ):
        parametros = parse_qs(
            urlparse(
                link["href"]
            ).query
        )

        assert parametros[
            "modo"
        ] == ["selecionar"]

        assert parametros[
            "ordem_id"
        ] == ["42"]

        assert parametros[
            "situacao"
        ] == ["todas"]

        assert parametros[
            "tipo_pesquisa"
        ] == ["nome"]

        assert parametros[
            "pesquisa"
        ] == ["Selecionável"]

    formulario_pagina = pagina.find(
        "form",
        class_="pagination-jump",
    )

    campos = {
        campo["name"]: campo.get(
            "value",
            "",
        )
        for campo in formulario_pagina.find_all(
            "input"
        )
    }

    assert campos == {
        "situacao": "todas",
        "tipo_pesquisa": "nome",
        "pesquisa": "Selecionável",
        "modo": "selecionar",
        "ordem_id": "42",
        "pagina": "2",
    }


def test_modo_selecionar_preserva_fluxo_e_bloqueia_desativado(
    app,
    client,
):
    with app.app_context():
        db.session.add_all(
            [
                Cliente(
                    nome="Cliente ativo",
                    telefone="47999991111",
                    ativo=True,
                ),
                Cliente(
                    nome="Cliente desativado",
                    telefone="47988882222",
                    ativo=False,
                ),
            ]
        )
        db.session.commit()

    pagina = analisar(
        client.get(
            "/painel/clientes",
            query_string={
                "modo": "selecionar",
                "ordem_id": 42,
                "pesquisa": "Cliente",
            },
        )
    )

    assert pagina.find(
        id="acaoAlterarCliente"
    ) is None

    assert pagina.find(
        id="acaoVisualizarCliente"
    ) is None

    assert pagina.find(
        id="acaoSituacaoCliente"
    ) is None

    assert pagina.find(
        id="acaoSelecionarCliente"
    ).has_attr(
        "disabled"
    )

    selecoes = pagina.select(
        "input[data-cliente-selection]"
    )

    assert len(
        selecoes
    ) == 2

    selecao_ativa = next(
        selecao
        for selecao in selecoes
        if selecao[
            "data-cliente-ativo"
        ] == "true"
    )

    selecao_desativada = next(
        selecao
        for selecao in selecoes
        if selecao[
            "data-cliente-ativo"
        ] == "false"
    )

    assert not selecao_ativa.has_attr(
        "disabled"
    )

    assert selecao_desativada.has_attr(
        "disabled"
    )

    retorno = pagina.find(
        "a",
        string=lambda valor: (
            valor
            and valor.strip() == "Retornar"
        ),
    )

    assert retorno[
        "href"
    ].endswith(
        "/painel/ordens/42/editar"
    )


def test_fluxo_nova_ordem_seleciona_cliente_e_retorna_preenchido(
    app,
    client,
):
    with app.app_context():
        cliente = Cliente(
            nome="Maria da Silva",
            cpf_cnpj="09544566789",
            telefone="47991977977",
        )

        db.session.add(
            cliente
        )

        db.session.commit()

        cliente_id = cliente.id

    pagina_nova_ordem = analisar(
        client.get(
            "/painel/ordens/nova"
        )
    )

    campo_cliente = pagina_nova_ordem.find(
        "input",
        id="cliente_nome",
    )

    consulta_clientes_url = campo_cliente[
        "data-client-selection-url"
    ]

    assert parse_qs(
        urlparse(
            consulta_clientes_url
        ).query
    ) == {
        "modo": ["selecionar"]
    }

    pagina_consulta = analisar(
        client.get(
            "/painel/clientes",
            query_string={
                "modo": "selecionar",
                "tipo_pesquisa": "nome",
                "pesquisa": "Maria",
            },
        )
    )

    selecoes = pagina_consulta.select(
        "input[data-cliente-selection]"
    )

    assert len(
        selecoes
    ) == 1

    pagina_retorno = analisar(
        client.get(
            selecoes[0][
                "data-url-selecionar"
            ]
        )
    )

    assert pagina_retorno.find(
        "input",
        id="cliente_id",
    )["value"] == str(
        cliente_id
    )

    assert pagina_retorno.find(
        "input",
        id="cliente_nome",
    )["value"] == "Maria da Silva"


def test_cadastro_normaliza_cpf_e_telefone(
    app,
    client,
):
    resposta = client.post(
        "/painel/clientes/novo",
        data={
            "nome": "Maria da Silva",
            "cpf_cnpj": "111.222.333-44",
            "telefone": "(47) 99999-1111",
            "email": "maria@example.com",
        },
    )

    assert resposta.status_code == 302

    with app.app_context():
        cliente = Cliente.query.one()

        assert cliente.cpf_cnpj == (
            "11122233344"
        )

        assert cliente.telefone == (
            "47999991111"
        )


def test_cadastro_preserva_contexto_de_selecao_da_ordem(
    client,
):
    resposta = client.post(
        "/painel/clientes/novo",
        query_string={
            "modo": "selecionar",
            "ordem_id": 42,
        },
        data={
            "nome": "Novo cliente",
            "telefone": "(47) 99999-1111",
        },
    )

    assert resposta.status_code == 302

    destino = urlparse(
        resposta.headers[
            "Location"
        ]
    )

    assert destino.path.endswith(
        "/painel/clientes"
    )

    assert parse_qs(
        destino.query
    ) == {
        "modo": ["selecionar"],
        "ordem_id": ["42"],
    }


def test_formulario_configura_mascaras_e_limites(
    client,
):
    pagina = analisar(
        client.get(
            "/painel/clientes/novo"
        )
    )

    campo_cpf = pagina.find(
        "input",
        id="cpf_cnpj",
    )

    campo_telefone = pagina.find(
        "input",
        id="telefone",
    )

    assert campo_cpf[
        "maxlength"
    ] == "14"

    assert campo_cpf[
        "inputmode"
    ] == "numeric"

    assert campo_cpf[
        "data-mask-input"
    ] == "cpf"

    assert campo_telefone[
        "maxlength"
    ] == "15"

    assert campo_telefone[
        "inputmode"
    ] == "numeric"

    assert campo_telefone[
        "data-mask-input"
    ] == "telefone-local"


def test_visualizacao_exibe_cpf_e_telefone_mascaraveis(
    app,
    client,
):
    with app.app_context():
        cliente = Cliente(
            nome="Maria da Silva",
            cpf_cnpj="11122233344",
            telefone="47999991111",
        )

        db.session.add(
            cliente
        )

        db.session.commit()

        cliente_id = cliente.id

    pagina = analisar(
        client.get(
            f"/painel/clientes/{cliente_id}/detalhes"
        )
    )

    assert pagina.find(
        attrs={
            "data-mask-text": "cpf-cnpj",
        },
    ) is not None

    assert pagina.find(
        attrs={
            "data-mask-text": "telefone",
        },
    ) is not None


def test_cpf_duplicado_considera_valor_mascarado(
    app,
):
    with app.app_context():
        db.session.add(
            Cliente(
                nome="Maria da Silva",
                cpf_cnpj="111.222.333-44",
                telefone="47999991111",
            )
        )

        db.session.commit()

        with pytest.raises(
            ValueError,
            match="CPF/CNPJ",
        ):
            ClienteService.cadastrar_cliente(
                {
                    "nome": "Outra pessoa",
                    "cpf_cnpj": "11122233344",
                    "telefone": "47988882222",
                }
            )


def test_edicao_preserva_fluxo_e_normaliza_campos(
    app,
    client,
):
    with app.app_context():
        cliente = Cliente(
            nome="Maria",
            cpf_cnpj="111.222.333-44",
            telefone="47999991111",
        )

        db.session.add(
            cliente
        )

        db.session.commit()

        cliente_id = cliente.id

    resposta = client.post(
        f"/painel/clientes/{cliente_id}/editar",
        data={
            "nome": "Maria da Silva",
            "cpf_cnpj": "111.222.333-44",
            "telefone": "(47) 98888-2222",
            "email": "maria@example.com",
        },
    )

    assert resposta.status_code == 302

    with app.app_context():
        cliente = db.session.get(
            Cliente,
            cliente_id,
        )

        assert cliente.nome == (
            "Maria da Silva"
        )

        assert cliente.cpf_cnpj == (
            "11122233344"
        )

        assert cliente.telefone == (
            "47988882222"
        )


def test_alterar_situacao_desativa_e_reativa_cliente(
    app,
    client,
):
    with app.app_context():
        cliente = Cliente(
            nome="Maria da Silva",
            telefone="47999991111",
            ativo=True,
        )

        db.session.add(
            cliente
        )

        db.session.commit()

        cliente_id = cliente.id

    resposta_desativar = client.post(
        f"/painel/clientes/{cliente_id}/situacao",
        data={
            "situacao": "todas",
            "tipo_pesquisa": "nome",
            "pesquisa": "Maria",
            "pagina": "1",
        },
    )

    assert (
        resposta_desativar.status_code
        == 302
    )

    destino = urlparse(
        resposta_desativar.headers[
            "Location"
        ]
    )

    assert destino.path == (
        "/painel/clientes"
    )

    assert parse_qs(
        destino.query
    ) == {
        "situacao": ["todas"],
        "tipo_pesquisa": ["nome"],
        "pesquisa": ["Maria"],
        "pagina": ["1"],
    }

    with app.app_context():
        cliente = db.session.get(
            Cliente,
            cliente_id,
        )

        assert cliente.ativo is False

    resposta_ativar = client.post(
        f"/painel/clientes/{cliente_id}/situacao"
    )

    assert (
        resposta_ativar.status_code
        == 302
    )

    with app.app_context():
        cliente = db.session.get(
            Cliente,
            cliente_id,
        )

        assert cliente.ativo is True


def test_inativacao_legada_continua_logica(
    app,
    client,
):
    with app.app_context():
        cliente = Cliente(
            nome="Maria da Silva",
            telefone="47999991111",
        )

        db.session.add(
            cliente
        )

        db.session.commit()

        cliente_id = cliente.id

    resposta = client.post(
        f"/painel/clientes/{cliente_id}/excluir"
    )

    assert resposta.status_code == 302

    with app.app_context():
        cliente = db.session.get(
            Cliente,
            cliente_id,
        )

        assert cliente is not None
        assert cliente.ativo is False