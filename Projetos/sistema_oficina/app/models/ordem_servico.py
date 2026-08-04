from datetime import date, datetime, timezone

from app.extensions import db


class OrdemServico(db.Model):
    """
    Representa uma manutenção ou troca de óleo
    realizada para um cliente da oficina.
    """

    __tablename__ = "ordens_servico"

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

    placa = db.Column(
        db.String(10),
        nullable=False,
        index=True,
    )

    marca = db.Column(
        db.String(50),
        nullable=False,
    )

    modelo = db.Column(
        db.String(80),
        nullable=False,
    )

    ano = db.Column(
        db.Integer,
        nullable=True,
    )

    data_servico = db.Column(
        db.Date,
        default=date.today,
        nullable=False,
    )

    quilometragem = db.Column(
        db.Integer,
        nullable=False,
    )

    descricao_servico = db.Column(
        db.String(150),
        nullable=False,
    )

    tipo_oleo = db.Column(
        db.String(100),
        nullable=True,
    )

    quantidade_litros = db.Column(
        db.Numeric(5, 2),
        nullable=True,
    )

    filtro_oleo = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    filtro_ar = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    filtro_combustivel = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    proxima_troca_km = db.Column(
        db.Integer,
        nullable=True,
    )

    proxima_troca_data = db.Column(
        db.Date,
        nullable=False,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    cliente = db.relationship(
        "Cliente",
        backref=db.backref(
            "ordens_servico",
            lazy=True,
        ),
        lazy="joined",
    )