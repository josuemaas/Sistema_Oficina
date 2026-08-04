from app.extensions import db
from app.models.ordem_servico import OrdemServico


class OrdemServicoRepository:
    """
    Responsável pelas operações de banco de dados
    relacionadas às ordens de serviço.
    """

    @staticmethod
    def listar():
        """
        Retorna todas as ordens de serviço.
        """
        return OrdemServico.query.order_by(
            OrdemServico.data_servico.desc()
        ).all()

    @staticmethod
    def buscar_por_id(ordem_id: int):
        """
        Busca uma ordem de serviço pelo ID.
        """
        return db.session.get(OrdemServico, ordem_id)

    @staticmethod
    def salvar(ordem: OrdemServico):
        """
        Salva uma nova ordem de serviço.
        """
        db.session.add(ordem)
        db.session.commit()

        return ordem

    @staticmethod
    def atualizar():
        """
        Confirma as alterações realizadas em uma ordem.
        """
        db.session.commit()

    @staticmethod
    def excluir(ordem: OrdemServico):
        """
        Exclui uma ordem de serviço do banco.
        """
        db.session.delete(ordem)
        db.session.commit()