from datetime import datetime, timezone

from app.extensions import db


class Cliente(db.Model):
    """
    Representa um cliente cadastrado na oficina.
    """

    __tablename__ = "clientes"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    nome = db.Column(
        db.String(150),
        nullable=False,
    )

    telefone = db.Column(
        db.String(20),
        nullable=False,
    )

    email = db.Column(
        db.String(150),
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    recebe_notificacao = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    ativo = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )