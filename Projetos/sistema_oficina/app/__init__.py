from flask import Flask
from sqlalchemy import text

from app.extensions import db, migrate
from app.routes import (
    cliente_bp,
    cliente_web_bp,
    dashboard_web_bp,
    notificacao_web_bp,
    ordem_servico_bp,
    ordem_servico_web_bp,
)
from config import Config

import app.models


def create_app() -> Flask:
    """
    Cria e configura a aplicação Flask.
    """

    app = Flask(__name__)

    # Carrega as configurações da aplicação.
    app.config.from_object(Config)

    # Inicializa o banco de dados e as migrações.
    db.init_app(app)
    migrate.init_app(app, db)

    # Registra as rotas da API.
    app.register_blueprint(cliente_bp)
    app.register_blueprint(ordem_servico_bp)

    # Registra as rotas da interface web.
    app.register_blueprint(dashboard_web_bp)
    app.register_blueprint(cliente_web_bp)
    app.register_blueprint(ordem_servico_web_bp)
    app.register_blueprint(notificacao_web_bp)

    @app.get("/saude/banco")
    def verificar_banco():
        """
        Testa a conexão entre o Flask
        e o PostgreSQL.
        """

        try:
            resultado = db.session.execute(
                text("SELECT 1")
            ).scalar()

            return {
                "banco": "conectado",
                "resultado_teste": resultado,
                "status": "online",
            }

        except Exception as erro:
            print(
                f"Erro ao conectar ao banco: {erro}"
            )

            return {
                "banco": "desconectado",
                "mensagem": (
                    "Não foi possível acessar o PostgreSQL."
                ),
                "status": "erro",
            }, 500

    return app