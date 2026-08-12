import logging

from flask import Flask
from sqlalchemy import text

from app.extensions import db, migrate
from app.routes import (
    cliente_bp,
    cliente_web_bp,
    dashboard_web_bp,
    notificacao_web_bp,
    ordem_servico_web_bp,
)
from config import Config

import app.models

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(cliente_bp)

    app.register_blueprint(dashboard_web_bp)
    app.register_blueprint(cliente_web_bp)
    app.register_blueprint(ordem_servico_web_bp)
    app.register_blueprint(notificacao_web_bp)

    @app.get("/saude/banco")
    def verificar_banco():
        try:
            resultado = db.session.execute(text("SELECT 1")).scalar()

            return {
                "banco": "conectado",
                "resultado_teste": resultado,
                "status": "online",
            }
        except Exception:
            logger.exception("Falha ao conectar ao banco")

            return {
                "banco": "desconectado",
                "mensagem": "Não foi possível acessar o PostgreSQL.",
                "status": "erro",
            }, 500

    return app