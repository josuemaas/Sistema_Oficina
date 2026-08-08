from alembic import op
import sqlalchemy as sa


revision = "6949b1dab7e5"
down_revision = "f76c6607a347"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "clientes",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "cpf_cnpj",
                sa.String(length=18),
                nullable=True,
            )
        )

        batch_op.create_index(
            batch_op.f("ix_clientes_cpf_cnpj"),
            ["cpf_cnpj"],
            unique=True,
        )

        batch_op.create_index(
            batch_op.f("ix_clientes_nome"),
            ["nome"],
            unique=False,
        )

        batch_op.create_index(
            batch_op.f("ix_clientes_telefone"),
            ["telefone"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table(
        "clientes",
        schema=None,
    ) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_clientes_telefone")
        )

        batch_op.drop_index(
            batch_op.f("ix_clientes_nome")
        )

        batch_op.drop_index(
            batch_op.f("ix_clientes_cpf_cnpj")
        )

        batch_op.drop_column("cpf_cnpj")