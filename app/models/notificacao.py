from datetime import datetime, timezone

from app.extensions import db


class Notificacao(db.Model):
    __tablename__ = "notificacoes"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=False,
        index=True,
    )

    ordem_servico_id = db.Column(
        db.Integer,
        db.ForeignKey("ordens_servico.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    data_agendada_disparo = db.Column(
        db.Date,
        nullable=False,
        index=True,
    )

    status = db.Column(
        db.String(20),
        default="PENDENTE",
        nullable=False,
        index=True,
    )

    mensagem = db.Column(
        db.Text,
        nullable=False,
    )

    tentativas = db.Column(
        db.Integer,
        default=0,
        nullable=False,
    )

    data_envio = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    erro = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    cliente = db.relationship(
        "Cliente",
        backref=db.backref(
            "notificacoes",
            lazy=True,
        ),
        lazy="joined",
    )

    ordem_servico = db.relationship(
        "OrdemServico",
        backref=db.backref(
            "notificacao",
            uselist=False,
            lazy=True,
        ),
        lazy="joined",
    )