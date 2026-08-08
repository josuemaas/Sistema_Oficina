import pytest
from flask import Flask

from app.controllers.ordem_servico_controller import OrdemServicoController


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


def test_cadastrar_retorna_400_quando_dados_estao_invalidos(app):
    with app.test_request_context(
        "/ordens",
        method="POST",
        json={"cliente_id": 1},
    ):
        response, status_code = OrdemServicoController.cadastrar()

    assert status_code == 400
    assert "mensagem" in response
