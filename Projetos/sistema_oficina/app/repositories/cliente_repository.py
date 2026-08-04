from app.extensions import db
from app.models.cliente import Cliente


class ClienteRepository:
    """
    Responsável pelo acesso aos dados dos clientes.
    """

    @staticmethod
    def listar():
        """
        Retorna todos os clientes cadastrados,
        ordenados pelo nome.
        """

        return (
            Cliente.query
            .order_by(Cliente.nome.asc())
            .all()
        )

    @staticmethod
    def buscar_por_id(cliente_id: int):
        """
        Busca um cliente pelo identificador.
        """

        return db.session.get(
            Cliente,
            cliente_id,
        )

    @staticmethod
    def salvar(cliente: Cliente):
        """
        Salva um novo cliente no banco de dados.
        """

        try:
            db.session.add(cliente)
            db.session.commit()

            return cliente

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def atualizar():
        """
        Confirma no banco as alterações realizadas
        em um cliente existente.
        """

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def excluir(cliente: Cliente):
        """
        Realiza a exclusão lógica do cliente,
        mantendo seu histórico no banco.
        """

        try:
            cliente.ativo = False
            db.session.commit()

            return cliente

        except Exception:
            db.session.rollback()
            raise