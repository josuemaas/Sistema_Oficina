import pytest
from bs4 import BeautifulSoup

from app import create_app
from app.extensions import db
from config import Config


ROTAS_PRINCIPAIS = [
    ("/", "Visão geral"),
    ("/painel/clientes", "Clientes"),
    ("/painel/clientes/novo", "Novo cliente"),
    ("/painel/ordens", "Ordens de Serviço"),
    ("/painel/ordens/nova", "Nova Ordem de Serviço"),
    ("/painel/notificacoes", "Notificações"),
]


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


@pytest.mark.parametrize(
    ("rota", "titulo_rotina"),
    ROTAS_PRINCIPAIS,
)
def test_rotas_principais_sem_barra_superior(
    client,
    rota,
    titulo_rotina,
):
    resposta = client.get(rota)

    assert resposta.status_code == 200

    pagina = BeautifulSoup(
        resposta.data,
        "html.parser",
    )

    texto = pagina.get_text(" ", strip=True)
    titulos = [
        titulo.get_text(" ", strip=True)
        for titulo in pagina.find_all("h1")
    ]

    assert pagina.select_one(".app-topbar") is None
    assert "Gestão de oficina" not in texto
    assert (
        "Central de clientes, ordens e serviços"
        not in texto
    )
    assert titulo_rotina in titulos

    botoes_menu = pagina.select("#sidebarToggle")

    assert len(botoes_menu) == 1

    botao_menu = botoes_menu[0]

    assert botao_menu.get("type") == "button"
    assert "sidebar-toggle" in botao_menu.get(
        "class",
        [],
    )
    assert botao_menu.get("aria-label") == (
        "Abrir ou fechar menu"
    )
    assert botao_menu.get("aria-controls") == (
        "appSidebar"
    )
    assert botao_menu.get("aria-expanded") == "false"
    assert pagina.select_one("#appSidebar") is not None
