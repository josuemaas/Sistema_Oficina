from app.extensions import db
from app.models.ordem_servico import OrdemServico


class OrdemServicoRepository:
    @staticmethod
    def listar():
        return (
            OrdemServico.query
            .order_by(
                OrdemServico.data_servico.desc(),
                OrdemServico.id.desc(),
            )
            .all()
        )

    @staticmethod
    def buscar_por_id(ordem_id: int):
        return db.session.get(
            OrdemServico,
            ordem_id,
        )

    @staticmethod
    def adicionar(ordem: OrdemServico):
        db.session.add(ordem)
        db.session.flush()

        return ordem

    @staticmethod
    def salvar(ordem: OrdemServico):
        try:
            OrdemServicoRepository.adicionar(
                ordem
            )

            db.session.commit()

            return ordem

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def confirmar():
        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def desfazer():
        db.session.rollback()

    @staticmethod
    def atualizar():
        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def excluir(ordem: OrdemServico):
        try:
            if ordem.notificacao is not None:
                db.session.delete(
                    ordem.notificacao
                )

            db.session.delete(
                ordem
            )

            db.session.commit()

        except Exception:
            db.session.rollback()
            raise