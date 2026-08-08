from alembic import op
import sqlalchemy as sa


revision = "114ebb60b393"
down_revision = "6949b1dab7e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notificacoes",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "cliente_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "ordem_servico_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "data_agendada_disparo",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "mensagem",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "tentativas",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "data_envio",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "erro",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clientes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["ordem_servico_id"],
            ["ordens_servico.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table(
        "notificacoes",
        schema=None,
    ) as batch_op:
        batch_op.create_index(
            batch_op.f(
                "ix_notificacoes_cliente_id"
            ),
            ["cliente_id"],
            unique=False,
        )

        batch_op.create_index(
            batch_op.f(
                "ix_notificacoes_data_agendada_disparo"
            ),
            ["data_agendada_disparo"],
            unique=False,
        )

        batch_op.create_index(
            batch_op.f(
                "ix_notificacoes_ordem_servico_id"
            ),
            ["ordem_servico_id"],
            unique=True,
        )

        batch_op.create_index(
            batch_op.f(
                "ix_notificacoes_status"
            ),
            ["status"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table(
        "notificacoes",
        schema=None,
    ) as batch_op:
        batch_op.drop_index(
            batch_op.f(
                "ix_notificacoes_status"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_notificacoes_ordem_servico_id"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_notificacoes_data_agendada_disparo"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_notificacoes_cliente_id"
            )
        )

    op.drop_table("notificacoes")