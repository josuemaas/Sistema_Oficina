"""Removendo cadastro de veiculos

Revision ID: f76c6607a347
Revises: 8804f13da7c8
Create Date: 2026-08-03 20:11:14.885141
"""

from alembic import op
import sqlalchemy as sa


# Identificadores da migration.
revision = "f76c6607a347"
down_revision = "8804f13da7c8"
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove a dependência das ordens com a tabela de veículos
    e exclui definitivamente a tabela veiculos.
    """

    with op.batch_alter_table(
        "ordens_servico",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "cliente_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.alter_column(
            "placa",
            existing_type=sa.String(length=10),
            nullable=False,
        )

        batch_op.alter_column(
            "marca",
            existing_type=sa.String(length=50),
            nullable=False,
        )

        batch_op.alter_column(
            "modelo",
            existing_type=sa.String(length=80),
            nullable=False,
        )

        batch_op.alter_column(
            "proxima_troca_data",
            existing_type=sa.Date(),
            nullable=False,
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_ordens_servico_veiculo_id"
            )
        )

        batch_op.drop_constraint(
            batch_op.f(
                "ordens_servico_veiculo_id_fkey"
            ),
            type_="foreignkey",
        )

        batch_op.drop_column(
            "veiculo_id"
        )

    # Remove definitivamente a tabela de veículos.
    op.drop_table(
        "veiculos"
    )


def downgrade():
    """
    Recria a tabela de veículos e restaura a coluna
    veiculo_id nas ordens caso a migration seja revertida.
    """

    op.create_table(
        "veiculos",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "cliente_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "placa",
            sa.String(length=10),
            nullable=False,
        ),
        sa.Column(
            "marca",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "modelo",
            sa.String(length=80),
            nullable=False,
        ),
        sa.Column(
            "ano",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "quilometragem_atual",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "observacoes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "ativo",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clientes.id"],
        ),
        sa.UniqueConstraint(
            "placa",
        ),
    )

    op.create_index(
        "ix_veiculos_cliente_id",
        "veiculos",
        ["cliente_id"],
        unique=False,
    )

    op.create_index(
        "ix_veiculos_placa",
        "veiculos",
        ["placa"],
        unique=True,
    )

    with op.batch_alter_table(
        "ordens_servico",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "veiculo_id",
                sa.Integer(),
                nullable=True,
            )
        )

        batch_op.create_foreign_key(
            "ordens_servico_veiculo_id_fkey",
            "veiculos",
            ["veiculo_id"],
            ["id"],
        )

        batch_op.create_index(
            "ix_ordens_servico_veiculo_id",
            ["veiculo_id"],
            unique=False,
        )

        batch_op.alter_column(
            "proxima_troca_data",
            existing_type=sa.Date(),
            nullable=True,
        )

        batch_op.alter_column(
            "modelo",
            existing_type=sa.String(length=80),
            nullable=True,
        )

        batch_op.alter_column(
            "marca",
            existing_type=sa.String(length=50),
            nullable=True,
        )

        batch_op.alter_column(
            "placa",
            existing_type=sa.String(length=10),
            nullable=True,
        )

        batch_op.alter_column(
            "cliente_id",
            existing_type=sa.Integer(),
            nullable=True,
        )