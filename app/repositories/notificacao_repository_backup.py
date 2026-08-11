from datetime import date

from app.extensions import db
from app.models.notificacao import Notificacao


class NotificacaoRepository:
    @staticmethod
    def listar():
        return (
            Notificacao.query
            .order_by(
                Notificacao.data_agendada_disparo.asc(),
                Notificacao.id.asc(),
            )
            .all()
        )

    @staticmethod
    def buscar_por_id(notificacao_id: int):
        return db.session.get(
            Notificacao,
            notificacao_id,
        )

    @staticmethod
    def buscar_por_ordem(ordem_servico_id: int):
        return (
            Notificacao.query
            .filter(
                Notificacao.ordem_servico_id
                == ordem_servico_id
            )
            .first()
        )

    @staticmethod
    def buscar_pendentes_para_disparo(
        data_limite: date,
    ):
        return (
            Notificacao.query
            .filter(
                Notificacao.status == "PENDENTE",
                Notificacao.data_agendada_disparo
                <= data_limite,
            )
            .order_by(
                Notificacao.data_agendada_disparo.asc(),
                Notificacao.id.asc(),
            )
            .all()
        )

    @staticmethod
    def adicionar(notificacao: Notificacao):
        db.session.add(notificacao)
        db.session.flush()

        return notificacao

    @staticmethod
    def salvar(notificacao: Notificacao):
        try:
            NotificacaoRepository.adicionar(
                notificacao
            )

            db.session.commit()

            return notificacao

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