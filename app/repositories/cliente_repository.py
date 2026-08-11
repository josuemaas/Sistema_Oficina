from sqlalchemy import func, or_

from app.extensions import db
from app.models.cliente import Cliente


class ClienteRepository:
    @staticmethod
    def listar():
        return (
            Cliente.query
            .order_by(Cliente.nome.asc())
            .all()
        )

    @staticmethod
    def listar_ativos():
        return (
            Cliente.query
            .filter(Cliente.ativo.is_(True))
            .order_by(Cliente.nome.asc())
            .all()
        )

    @staticmethod
    def buscar_por_id(cliente_id: int):
        return db.session.get(
            Cliente,
            cliente_id,
        )

    @staticmethod
    def buscar_ativos(termo: str, limite: int = 20):
        termo = (termo or "").strip()

        consulta = Cliente.query.filter(
            Cliente.ativo.is_(True)
        )

        if termo:
            padrao = f"%{termo}%"

            consulta = consulta.filter(
                or_(
                    Cliente.nome.ilike(padrao),
                    Cliente.cpf_cnpj.ilike(padrao),
                    Cliente.telefone.ilike(padrao),
                )
            )

        return (
            consulta
            .order_by(Cliente.nome.asc())
            .limit(limite)
            .all()
        )

    @staticmethod
    def buscar_por_cpf_cnpj(cpf_cnpj: str):
        cpf_cnpj = (cpf_cnpj or "").strip()

        if not cpf_cnpj:
            return None

        cpf_cnpj_normalizado = "".join(
            caractere
            for caractere in cpf_cnpj
            if caractere.isdigit()
        )

        if not cpf_cnpj_normalizado:
            return (
                Cliente.query
                .filter(
                    Cliente.cpf_cnpj
                    == cpf_cnpj
                )
                .first()
            )

        valor_normalizado = Cliente.cpf_cnpj

        for caractere in (
            ".",
            "-",
            "/",
            " ",
        ):
            valor_normalizado = func.replace(
                valor_normalizado,
                caractere,
                "",
            )

        return (
            Cliente.query
            .filter(
                valor_normalizado
                == cpf_cnpj_normalizado
            )
            .first()
        )

    @staticmethod
    def salvar(cliente: Cliente):
        try:
            db.session.add(cliente)
            db.session.commit()

            return cliente

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def atualizar():
        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def excluir(cliente: Cliente):
        try:
            cliente.ativo = False
            db.session.commit()

            return cliente

        except Exception:
            db.session.rollback()
            raise
