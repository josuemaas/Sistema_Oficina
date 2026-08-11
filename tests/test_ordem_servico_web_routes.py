from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup

from app import create_app
from app.routes import ordem_servico_web_routes
from app.routes.ordem_servico_web_routes import (
    filtrar_ordens,
)
from app.services.cliente_service import ClienteService
from app.services.ordem_servico_service import (
    OrdemServicoService,
)
from config import Config


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(
        Config,
        "SQLALCHEMY_DATABASE_URI",
        "sqlite://",
    )

    app = create_app()
    app.config["TESTING"] = True

    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def ordem():
    return SimpleNamespace(
        id=42,
        cliente=SimpleNamespace(
            nome="Maria da Silva",
            telefone="47991977977",
        ),
        marca="Volkswagen",
        modelo="Gol",
        placa="ABC1D23",
        ano=2020,
        data_servico=date(2026, 8, 10),
        quilometragem=85000,
        descricao_servico="Troca de óleo",
        tipo_oleo="5W30",
        quantidade_litros=4.5,
        filtro_oleo=True,
        filtro_ar=True,
        filtro_combustivel=True,
        observacoes="Verificar os freios",
        proxima_troca_km=95000,
        proxima_troca_data=date(2027, 2, 10),
    )


def test_filtrar_ordens_pelo_campo_selecionado():
    ordens = [
        SimpleNamespace(
            cliente=SimpleNamespace(
                nome="Maria da Silva",
                telefone="47991977977",
            ),
            placa="ABC1D23",
            marca="Volkswagen",
            modelo="Gol",
        ),
        SimpleNamespace(
            cliente=SimpleNamespace(
                nome="João Souza",
                telefone="(47) 98888-2222",
            ),
            placa="DEF4G56",
            marca="Honda",
            modelo="Civic",
        ),
    ]

    assert filtrar_ordens(
        ordens,
        "maria",
        "cliente",
    ) == [ordens[0]]
    assert filtrar_ordens(
        ordens,
        "(47) 99197-7977",
        "telefone",
    ) == [ordens[0]]
    assert filtrar_ordens(
        ordens,
        "4799197797712345",
        "telefone",
    ) == [ordens[0]]
    assert filtrar_ordens(
        ordens,
        "abc-1d23",
        "placa",
    ) == [ordens[0]]
    assert filtrar_ordens(
        ordens,
        "abc-1d23XYZ",
        "placa",
    ) == [ordens[0]]
    assert filtrar_ordens(
        ordens,
        "VOLKS",
        "marca",
    ) == [ordens[0]]
    assert filtrar_ordens(
        ordens,
        "cIvIc",
        "modelo",
    ) == [ordens[1]]
    assert filtrar_ordens(
        ordens,
        "gol",
        "cliente",
    ) == []
    assert filtrar_ordens(
        ordens,
        "joão",
        "tipo-invalido",
    ) == [ordens[1]]
    assert filtrar_ordens(
        ordens,
        "---",
        "telefone",
    ) == []
    assert filtrar_ordens(
        ordens,
        "---",
        "placa",
    ) == []
    assert filtrar_ordens(
        ordens,
        "",
        "cliente",
    ) == ordens


def test_inclusao_renderiza_formulario_unico_simplificado(
    client,
    monkeypatch,
):
    class DataFixa(date):
        @classmethod
        def today(cls):
            return cls(2026, 8, 10)

    cliente = SimpleNamespace(
        id=7,
        nome="Maria da Silva",
        telefone="47991977977",
        ativo=True,
    )

    monkeypatch.setattr(
        ordem_servico_web_routes,
        "date",
        DataFixa,
    )
    monkeypatch.setattr(
        ClienteService,
        "buscar_por_id",
        lambda cliente_id: (
            cliente
            if cliente_id == cliente.id
            else None
        ),
    )

    resposta = client.get(
        "/painel/ordens/nova",
        query_string={
            "cliente_id": 7,
        },
    )

    assert resposta.status_code == 200

    pagina = BeautifulSoup(
        resposta.data,
        "html.parser",
    )
    formulario = pagina.find(
        "form",
        id="formOrdemServico",
    )

    assert len(
        formulario.select(".panel")
    ) == 1
    assert formulario.find(
        "input",
        id="cliente_id",
    )["value"] == "7"
    assert formulario.find(
        "input",
        id="cliente_nome",
    )["value"] == "Maria da Silva"
    assert formulario.find(
        "a",
        id="abrirBuscaCliente",
    ) is not None
    assert formulario.find(
        id="clienteSelecionadoInfo",
    ) is None

    placa = formulario.find(
        "input",
        id="placa",
    )

    assert placa["maxlength"] == "7"
    assert placa.has_attr(
        "data-order-plate-input"
    )
    assert placa["autocapitalize"] == "characters"
    assert formulario.find(
        "input",
        id="quilometragem",
    ) is not None

    data_servico = formulario.find(
        "input",
        id="data_servico",
    )

    assert data_servico["value"] == "2026-08-10"
    assert data_servico.has_attr("readonly")
    assert not data_servico.has_attr("name")

    grupo_servicos = formulario.find(
        attrs={
            "role": "group",
            "aria-label": "Serviços realizados",
        },
    )

    assert "flex-column" in grupo_servicos["class"]
    assert [
        campo["name"]
        for campo in grupo_servicos.find_all(
            "input",
            attrs={
                "type": "checkbox",
            },
        )
    ] == [
        "troca_oleo",
        "filtro_ar",
        "filtro_combustivel",
    ]
    assert [
        " ".join(
            rotulo.get_text(
                " ",
                strip=True,
            ).split()
        )
        for rotulo in grupo_servicos.find_all("label")
    ] == [
        "Troca de óleo",
        "Filtro de ar",
        "Filtro de gasolina",
    ]
    assert formulario.find(
        "textarea",
        id="observacoes",
    ) is not None

    for campo_removido in (
        "marca",
        "modelo",
        "ano",
        "descricao_servico",
        "tipo_oleo",
        "quantidade_litros",
        "proxima_troca_km",
    ):
        assert formulario.find(
            id=campo_removido
        ) is None

    botoes_salvar = formulario.find_all(
        "button",
        attrs={
            "type": "submit",
        },
    )

    assert len(botoes_salvar) == 1
    assert " ".join(
        botoes_salvar[0].get_text().split()
    ) == (
        "Salvar Ordem de Serviço / "
        "Agendar Notificação"
    )


def test_script_ordens_limita_digitacao_e_colagem_da_placa():
    caminho_script = (
        Path(__file__).parents[1]
        / "app"
        / "static"
        / "js"
        / "ordens.js"
    )
    script = caminho_script.read_text(
        encoding="utf-8"
    )

    assert '"[data-order-plate-input]"' in script
    assert '.replace(/[^a-zA-Z0-9]/g, "")' in script
    assert ".toUpperCase()" in script
    assert ".slice(0, 7)" in script
    assert '"input"' in script
    assert '"paste"' in script


def test_listagem_renderiza_acoes_compactas_e_selecao(
    client,
    monkeypatch,
    ordem,
):
    monkeypatch.setattr(
        OrdemServicoService,
        "listar_ordens",
        lambda: [ordem],
    )

    resposta = client.get(
        "/painel/ordens",
        query_string={
            "tipo_pesquisa": "placa",
            "pesquisa": "abc1d23",
        },
    )

    assert resposta.status_code == 200

    pagina = BeautifulSoup(
        resposta.data,
        "html.parser",
    )

    tipo_pesquisa = pagina.find(
        "select",
        id="tipo_pesquisa",
    )

    campo_pesquisa = pagina.find(
        "input",
        id="pesquisa",
    )

    assert [
        opcao["value"]
        for opcao in tipo_pesquisa.find_all("option")
    ] == [
        "cliente",
        "telefone",
        "placa",
        "marca",
        "modelo",
    ]
    assert tipo_pesquisa.find(
        "option",
        selected=True,
    )["value"] == "placa"
    assert tipo_pesquisa.has_attr(
        "data-order-search-type"
    )
    assert campo_pesquisa["value"] == "abc1d23"
    assert campo_pesquisa.has_attr(
        "data-order-search-term"
    )

    consultar = pagina.find(
        "button",
        attrs={
            "type": "submit",
        },
    )

    assert "Consultar" in consultar.get_text()
    assert "button-primary" in consultar["class"]

    limpar = pagina.find(
        "a",
        string=lambda texto: (
            texto
            and texto.strip() == "Limpar"
        ),
    )

    assert limpar["href"].endswith(
        "/painel/ordens"
    )

    titulo_listagem = pagina.find(
        "h2",
        string=lambda texto: (
            texto
            and "Ordens cadastradas" in texto
        ),
    )

    cabecalho = titulo_listagem.find_parent(
        class_="panel-header"
    )

    assert cabecalho.find(
        attrs={
            "role": "toolbar",
        },
    ) is not None
    contador = cabecalho.find(
        class_="badge-neutral",
    )

    assert " ".join(
        contador.get_text().split()
    ) == "1 registro"

    incluir = cabecalho.find(
        "a",
        string=lambda texto: (
            texto
            and "Incluir" in texto
        ),
    )

    alterar = cabecalho.find(
        id="acaoAlterarOrdem"
    )
    visualizar = cabecalho.find(
        id="acaoVisualizarOrdem"
    )
    excluir = cabecalho.find(
        id="acaoExcluirOrdem"
    )

    assert incluir["href"].endswith(
        "/painel/ordens/nova"
    )
    assert "button-primary" in incluir["class"]
    assert "button-small" in incluir["class"]

    for botao in (
        alterar,
        visualizar,
    ):
        assert botao.has_attr("disabled")
        assert "button-secondary" in botao["class"]
        assert "button-small" in botao["class"]

    assert excluir.has_attr("disabled")
    assert "button-danger" in excluir["class"]
    assert "button-small" in excluir["class"]

    tabela = pagina.find(
        "table",
        class_="system-table",
    )

    cabecalhos = [
        item.get_text(
            " ",
            strip=True,
        )
        for item in tabela.find_all("th")
    ]

    assert cabecalhos == [
        "Selecionar",
        "ID",
        "Veículo",
        "Data",
        "Quilometragem",
        "Serviço",
        "Próxima troca",
    ]

    selecao = tabela.find(
        "input",
        attrs={
            "data-ordem-selection": "",
        },
    )

    assert selecao[
        "data-url-alterar"
    ].endswith("/42/editar")
    assert selecao[
        "data-url-visualizar"
    ].endswith("/42/detalhes")
    assert selecao[
        "data-url-excluir"
    ].endswith("/42/excluir")

    linha = selecao.find_parent("tr")

    assert linha.find("a") is None
    assert linha.find("button") is None
    assert linha.find("form") is None
    assert "Ações" not in cabecalhos
    assert "+ Nova ordem" not in pagina.get_text()

    form_excluir = pagina.find(
        "form",
        id="formExcluirOrdem",
    )

    assert form_excluir["method"] == "post"
    assert not form_excluir.has_attr("action")

    script_ordens = pagina.find(
        "script",
        src=lambda origem: (
            origem
            and origem.endswith("/js/ordens.js")
        ),
    )

    assert script_ordens is not None


def test_visualizacao_exibe_dados_sem_edicao(
    client,
    monkeypatch,
    ordem,
):
    monkeypatch.setattr(
        OrdemServicoService,
        "buscar_por_id",
        lambda ordem_id: (
            ordem
            if ordem_id == ordem.id
            else None
        ),
    )

    resposta = client.get(
        "/painel/ordens/42/detalhes"
    )

    assert resposta.status_code == 200

    pagina = BeautifulSoup(
        resposta.data,
        "html.parser",
    )

    conteudo = pagina.get_text(
        " ",
        strip=True,
    )

    for valor in (
        "Ordem de Serviço #42",
        "Maria da Silva",
        "(47) 99197-7977",
        "Volkswagen",
        "Gol",
        "ABC1D23",
        "10/08/2026",
        "85.000 km",
        "Troca de óleo",
        "5W30",
        "Verificar os freios",
        "95.000 km",
        "10/02/2027",
    ):
        assert valor in conteudo

    assert pagina.find("form") is None
    assert pagina.find("input") is None
    assert pagina.find("textarea") is None
    assert pagina.find("select") is None

    voltar = pagina.find(
        "a",
        string=lambda texto: (
            texto
            and texto.strip() == "Voltar"
        ),
    )

    assert voltar["href"].endswith(
        "/painel/ordens"
    )
    assert "button-small" in voltar["class"]


def test_visualizacao_inexistente_redireciona(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        OrdemServicoService,
        "buscar_por_id",
        lambda ordem_id: None,
    )

    resposta = client.get(
        "/painel/ordens/999/detalhes"
    )

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith(
        "/painel/ordens"
    )


def test_edicao_preserva_ordem_ao_selecionar_cliente(
    client,
    monkeypatch,
    ordem,
):
    cliente_atual = SimpleNamespace(
        id=10,
        nome="Cliente atual",
        telefone="47988882222",
        ativo=True,
    )
    cliente_escolhido = SimpleNamespace(
        id=99,
        nome="Cliente escolhido",
        telefone="47991977977",
        ativo=True,
    )
    ordem.cliente = cliente_atual

    monkeypatch.setattr(
        OrdemServicoService,
        "buscar_por_id",
        lambda ordem_id: ordem,
    )
    monkeypatch.setattr(
        ClienteService,
        "buscar_por_id",
        lambda cliente_id: (
            cliente_escolhido
            if cliente_id == cliente_escolhido.id
            else None
        ),
    )

    resposta_edicao = client.get(
        "/painel/ordens/42/editar"
    )

    assert resposta_edicao.status_code == 200

    pagina_edicao = BeautifulSoup(
        resposta_edicao.data,
        "html.parser",
    )
    campo_cliente = pagina_edicao.find(
        "input",
        id="cliente_nome",
    )
    formulario_edicao = pagina_edicao.find(
        "form",
        id="formOrdemServico",
    )

    assert campo_cliente["value"] == "Cliente atual"
    assert (
        "modo=selecionar"
        in campo_cliente["data-client-selection-url"]
    )
    assert (
        "ordem_id=42"
        in campo_cliente["data-client-selection-url"]
    )
    assert pagina_edicao.find(
        id="modalCliente",
    ) is None
    assert formulario_edicao.find(
        "input",
        id="marca",
    )["value"] == "Volkswagen"
    assert formulario_edicao.find(
        "input",
        id="modelo",
    )["value"] == "Gol"
    assert formulario_edicao.find(
        "input",
        id="ano",
    )["value"] == "2020"
    assert formulario_edicao.find(
        "input",
        id="data_servico",
    )["name"] == "data_servico"
    assert formulario_edicao.find(
        "input",
        id="descricao_servico",
    )["value"] == ordem.descricao_servico
    assert formulario_edicao.find(
        "input",
        id="tipo_oleo",
    )["value"] == "5W30"
    assert formulario_edicao.find(
        "input",
        id="quantidade_litros",
    )["value"] == "4.5"

    resposta_retorno = client.get(
        "/painel/ordens/42/editar",
        query_string={
            "cliente_id": 99,
        },
    )

    assert resposta_retorno.status_code == 200

    pagina_retorno = BeautifulSoup(
        resposta_retorno.data,
        "html.parser",
    )

    assert pagina_retorno.find(
        "input",
        id="cliente_id",
    )["value"] == "99"
    assert pagina_retorno.find(
        "input",
        id="cliente_nome",
    )["value"] == "Cliente escolhido"


def test_cadastro_ordem_monta_payload_simplificado(
    client,
    monkeypatch,
):
    class DataFixa(date):
        @classmethod
        def today(cls):
            return cls(2026, 8, 10)

    cliente = SimpleNamespace(
        id=7,
        nome="Maria da Silva",
        telefone="47991977977",
        ativo=True,
    )
    dados_recebidos = []

    monkeypatch.setattr(
        ordem_servico_web_routes,
        "date",
        DataFixa,
    )
    monkeypatch.setattr(
        ClienteService,
        "buscar_por_id",
        lambda cliente_id: (
            cliente
            if cliente_id == cliente.id
            else None
        ),
    )
    monkeypatch.setattr(
        OrdemServicoService,
        "listar_ordens",
        lambda: [],
    )
    monkeypatch.setattr(
        OrdemServicoService,
        "cadastrar_ordem",
        lambda dados: dados_recebidos.append(dados),
    )

    resposta = client.post(
        "/painel/ordens/nova",
        data={
            "cliente_id": "7",
            "placa": "a-bc1d23XYZ!",
            "quilometragem": "85000",
            "data_servico": "1999-01-01",
            "troca_oleo": "on",
            "filtro_ar": "on",
            "filtro_combustivel": "on",
            "observacoes": "  Verificar os freios  ",
        },
    )

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith(
        "/painel/ordens"
    )
    assert dados_recebidos == [
        {
            "cliente_id": 7,
            "placa": "ABC1D23",
            "marca": "Não informada",
            "modelo": "Não informado",
            "ano": None,
            "quilometragem": 85000,
            "data_servico": date(2026, 8, 10),
            "descricao_servico": (
                "Troca de óleo, Filtro de ar, "
                "Filtro de gasolina"
            ),
            "tipo_oleo": None,
            "quantidade_litros": None,
            "filtro_oleo": False,
            "filtro_ar": True,
            "filtro_combustivel": True,
            "observacoes": "Verificar os freios",
        }
    ]


def test_cadastro_ordem_preserva_placa_do_historico(
    client,
    monkeypatch,
):
    cliente = SimpleNamespace(
        id=7,
        nome="Maria da Silva",
        telefone="47991977977",
        ativo=True,
    )
    dados_recebidos = []

    monkeypatch.setattr(
        ClienteService,
        "buscar_por_id",
        lambda cliente_id: (
            cliente
            if cliente_id == cliente.id
            else None
        ),
    )
    monkeypatch.setattr(
        OrdemServicoService,
        "listar_ordens",
        lambda: [
            SimpleNamespace(
                placa="ABC-1234"
            )
        ],
    )
    monkeypatch.setattr(
        OrdemServicoService,
        "cadastrar_ordem",
        lambda dados: dados_recebidos.append(dados),
    )

    resposta = client.post(
        "/painel/ordens/nova",
        data={
            "cliente_id": "7",
            "placa": "abc1234",
            "quilometragem": "85000",
            "troca_oleo": "on",
        },
    )

    assert resposta.status_code == 302
    assert dados_recebidos[0]["placa"] == "ABC-1234"


def test_cadastro_ordem_exige_servico_realizado(
    client,
    monkeypatch,
):
    cliente = SimpleNamespace(
        id=7,
        nome="Maria da Silva",
        telefone="47991977977",
        ativo=True,
    )
    dados_recebidos = []

    monkeypatch.setattr(
        ClienteService,
        "buscar_por_id",
        lambda cliente_id: (
            cliente
            if cliente_id == cliente.id
            else None
        ),
    )
    monkeypatch.setattr(
        OrdemServicoService,
        "cadastrar_ordem",
        lambda dados: dados_recebidos.append(dados),
    )

    resposta = client.post(
        "/painel/ordens/nova",
        data={
            "cliente_id": "7",
            "placa": "ABC1D23",
            "quilometragem": "85000",
        },
    )

    assert resposta.status_code == 200
    assert (
        "Selecione ao menos um serviço realizado."
        in resposta.get_data(as_text=True)
    )
    assert dados_recebidos == []


def test_exclusao_permanece_post(
    client,
    monkeypatch,
):
    ordens_excluidas = []

    def excluir_ordem(ordem_id):
        ordens_excluidas.append(ordem_id)
        return True

    monkeypatch.setattr(
        OrdemServicoService,
        "excluir_ordem",
        excluir_ordem,
    )

    resposta = client.post(
        "/painel/ordens/42/excluir"
    )

    assert resposta.status_code == 302
    assert ordens_excluidas == [42]

    resposta_get = client.get(
        "/painel/ordens/42/excluir"
    )

    assert resposta_get.status_code == 405
