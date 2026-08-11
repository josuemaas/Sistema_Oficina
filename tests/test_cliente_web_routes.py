from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from bs4 import BeautifulSoup

from app import create_app
from app.extensions import db
from app.models.cliente import Cliente
from app.routes.cliente_web_routes import (
    filtrar_clientes,
)
from app.services.cliente_service import ClienteService
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

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


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

    assert filtrar_clientes(
        clientes,
        "maria",
        "nome",
    ) == [clientes[0]]

    assert filtrar_clientes(
        clientes,
        "111.222.333-44",
        "cpf",
    ) == [clientes[0]]

    assert filtrar_clientes(
        clientes,
        "98888-2222",
        "telefone",
    ) == [clientes[1]]

    assert filtrar_clientes(
        clientes,
        "maria",
        "tipo-invalido",
    ) == [clientes[0]]


def test_listagem_renderiza_filtros_acoes_e_selecao(
    app,
    client,
):
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

    resposta = client.get(
        "/painel/clientes",
        query_string={
            "tipo_pesquisa": "cpf",
            "pesquisa": "111.222.333-44",
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

    assert tipo_pesquisa.has_attr(
        "data-client-search-type"
    )
    assert campo_pesquisa.has_attr(
        "data-client-search-term"
    )

    botao_consultar = pagina.find(
        "button",
        attrs={
            "type": "submit",
        },
    )

    assert "Consultar" in botao_consultar.get_text()

    botao_alterar = pagina.find(
        id="acaoAlterarCliente",
    )

    botao_visualizar = pagina.find(
        id="acaoVisualizarCliente",
    )

    assert botao_alterar.has_attr("disabled")
    assert botao_visualizar.has_attr("disabled")
    assert pagina.find(
        id="acaoSelecionarCliente",
    ) is None
    assert pagina.find(
        id="acaoSelecionarCliente",
    ) is None
    assert "button-small" in botao_alterar.get(
        "class",
        [],
    )
    assert "button-small" in botao_visualizar.get(
        "class",
        [],
    )
    assert botao_alterar.find_parent(
        class_="panel-header",
    ) is not None
    assert pagina.find(
        class_="page-actions-bar",
    ) is None

    acao_incluir = pagina.find(
        "a",
        string=lambda texto: (
            texto
            and "Incluir" in texto
        ),
    )

    assert "button-primary" in acao_incluir.get(
        "class",
        [],
    )
    assert "button-small" in acao_incluir.get(
        "class",
        [],
    )

    tabela = pagina.find(
        "table",
        class_="system-table",
    )

    cabecalhos = [
        cabecalho.get_text(
            " ",
            strip=True,
        )
        for cabecalho in tabela.find_all("th")
    ]

    assert cabecalhos == [
        "Selecionar",
        "Código",
        "Nome/Razão Social",
        "CPF",
        "Telefone",
        "Situação",
    ]

    assert "Maria da Silva" in tabela.get_text()
    assert "João Souza" not in tabela.get_text()
    assert tabela.find("a") is None
    assert len(
        tabela.select(
            "input[data-cliente-selection]"
        )
    ) == 1


def test_modo_selecionar_preserva_fluxo_de_ordem(
    app,
    client,
):
    with app.app_context():
        db.session.add_all(
            [
                Cliente(
                    nome="Cliente ativo",
                    telefone="47999991111",
                ),
                Cliente(
                    nome="Cliente inativo",
                    telefone="47988882222",
                    ativo=False,
                ),
            ]
        )
        db.session.commit()

    resposta = client.get(
        "/painel/clientes",
        query_string={
            "modo": "selecionar",
            "ordem_id": 42,
            "pesquisa": "Cliente",
        },
    )

    pagina = BeautifulSoup(
        resposta.data,
        "html.parser",
    )

    botao_selecionar = pagina.find(
        id="acaoSelecionarCliente",
    )

    assert botao_selecionar.has_attr("disabled")
    assert "button-small" in botao_selecionar.get(
        "class",
        [],
    )
    assert pagina.find(
        id="acaoAlterarCliente",
    ) is None
    assert pagina.find(
        id="acaoVisualizarCliente",
    ) is None
    acao_incluir = pagina.find(
        "a",
        string=lambda texto: (
            texto
            and "Incluir" in texto
        ),
    )

    assert "button-primary" in acao_incluir.get(
        "class",
        [],
    )
    assert "button-small" in acao_incluir.get(
        "class",
        [],
    )

    parametros_incluir = parse_qs(
        urlparse(
            acao_incluir["href"]
        ).query
    )

    assert parametros_incluir == {
        "modo": ["selecionar"],
        "ordem_id": ["42"],
    }

    formulario_pesquisa = pagina.find(
        "form",
        class_="page-search",
    )

    assert formulario_pesquisa.find(
        "input",
        attrs={
            "name": "modo",
            "value": "selecionar",
        },
    ) is not None

    acao_limpar = pagina.find(
        "a",
        string=lambda texto: (
            texto
            and texto.strip() == "Limpar"
        ),
    )
    parametros_limpar = parse_qs(
        urlparse(
            acao_limpar["href"]
        ).query
    )

    assert parametros_limpar == {
        "modo": ["selecionar"],
        "ordem_id": ["42"],
    }
    assert formulario_pesquisa.find(
        "input",
        attrs={
            "name": "ordem_id",
            "value": "42",
        },
    ) is not None

    acao_retornar = pagina.find(
        "a",
        string=lambda texto: (
            texto
            and texto.strip() == "Retornar"
        ),
    )

    assert acao_retornar["href"].endswith(
        "/painel/ordens/42/editar"
    )

    selecoes = pagina.select(
        "input[data-cliente-selection]"
    )

    assert len(selecoes) == 2
    assert not selecoes[0].has_attr("disabled")
    url_selecao = urlparse(
        selecoes[0]["data-url-selecionar"]
    )

    assert url_selecao.path.endswith(
        "/painel/ordens/42/editar"
    )
    assert "cliente_id" in parse_qs(
        url_selecao.query
    )
    assert selecoes[1].has_attr("disabled")


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
        db.session.add(cliente)
        db.session.commit()
        cliente_id = cliente.id

    resposta_nova_ordem = client.get(
        "/painel/ordens/nova"
    )

    assert resposta_nova_ordem.status_code == 200

    pagina_nova_ordem = BeautifulSoup(
        resposta_nova_ordem.data,
        "html.parser",
    )

    campo_cliente = pagina_nova_ordem.find(
        "input",
        id="cliente_nome",
    )
    lupa_cliente = pagina_nova_ordem.find(
        "a",
        id="abrirBuscaCliente",
    )
    consulta_clientes_url = campo_cliente[
        "data-client-selection-url"
    ]

    assert campo_cliente["value"] == ""
    assert lupa_cliente["href"] == consulta_clientes_url
    assert pagina_nova_ordem.find(
        id="modalCliente",
    ) is None
    assert pagina_nova_ordem.find(
        "script",
        src=lambda origem: (
            origem
            and origem.endswith("/js/ordens.js")
        ),
    ) is not None
    assert parse_qs(
        urlparse(
            consulta_clientes_url
        ).query
    ) == {
        "modo": ["selecionar"],
    }

    resposta_consulta = client.get(
        "/painel/clientes",
        query_string={
            "modo": "selecionar",
            "tipo_pesquisa": "nome",
            "pesquisa": "Maria",
        },
    )

    assert resposta_consulta.status_code == 200

    pagina_consulta = BeautifulSoup(
        resposta_consulta.data,
        "html.parser",
    )
    selecoes = pagina_consulta.select(
        "input[data-cliente-selection]"
    )

    assert len(selecoes) == 1
    assert "Maria da Silva" in pagina_consulta.get_text()
    assert pagina_consulta.find(
        id="acaoSelecionarCliente",
    ).has_attr("disabled")

    resposta_retorno = client.get(
        selecoes[0]["data-url-selecionar"]
    )

    assert resposta_retorno.status_code == 200

    pagina_retorno = BeautifulSoup(
        resposta_retorno.data,
        "html.parser",
    )

    assert pagina_retorno.find(
        "input",
        id="cliente_id",
    )["value"] == str(cliente_id)
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

        assert cliente.cpf_cnpj == "11122233344"
        assert cliente.telefone == "47999991111"


def test_cadastro_preserva_contexto_de_selecao_da_ordem(
    app,
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
        resposta.headers["Location"]
    )

    assert destino.path.endswith(
        "/painel/clientes"
    )
    assert parse_qs(destino.query) == {
        "modo": ["selecionar"],
        "ordem_id": ["42"],
    }

    resposta_listagem = client.get(
        resposta.headers["Location"]
    )

    assert resposta_listagem.status_code == 200

    pagina = BeautifulSoup(
        resposta_listagem.data,
        "html.parser",
    )

    assert "Novo cliente" in pagina.get_text()
    assert pagina.find(
        id="acaoSelecionarCliente",
    ) is not None

    with app.app_context():
        cliente = Cliente.query.one()

        assert cliente.telefone == "47999991111"


def test_formulario_configura_mascaras_e_limites(
    client,
):
    resposta = client.get(
        "/painel/clientes/novo"
    )

    pagina = BeautifulSoup(
        resposta.data,
        "html.parser",
    )

    campo_cpf = pagina.find(
        "input",
        id="cpf_cnpj",
    )

    campo_telefone = pagina.find(
        "input",
        id="telefone",
    )

    assert campo_cpf["maxlength"] == "14"
    assert campo_cpf["inputmode"] == "numeric"
    assert campo_cpf[
        "data-mask-input"
    ] == "cpf"

    assert campo_telefone["maxlength"] == "15"
    assert campo_telefone["inputmode"] == "numeric"
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
        db.session.add(cliente)
        db.session.commit()
        cliente_id = cliente.id

    resposta = client.get(
        f"/painel/clientes/{cliente_id}/detalhes"
    )

    assert resposta.status_code == 200

    pagina = BeautifulSoup(
        resposta.data,
        "html.parser",
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
        db.session.add(cliente)
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

        assert cliente.nome == "Maria da Silva"
        assert cliente.cpf_cnpj == "11122233344"
        assert cliente.telefone == "47988882222"


def test_inativacao_continua_logica(
    app,
    client,
):
    with app.app_context():
        cliente = Cliente(
            nome="Maria da Silva",
            telefone="47999991111",
        )
        db.session.add(cliente)
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

        assert cliente.ativo is False
