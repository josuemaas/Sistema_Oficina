from datetime import date

from app.extensions import db
from app.models.notificacao import Notificacao
from app.models.ordem_servico import OrdemServico


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
    def buscar_por_id(
        notificacao_id: int,
    ):
        return db.session.get(
            Notificacao,
            notificacao_id,
        )

    @staticmethod
    def buscar_por_ordem(
        ordem_servico_id: int,
    ):
        return (
            Notificacao.query
            .filter(
                Notificacao.ordem_servico_id
                == ordem_servico_id
            )
            .first()
        )

    @staticmethod
    def buscar_ativas_por_placa(
        placa: str,
        ordem_servico_id_ignorar: int | None = None,
    ):
        consulta = (
            Notificacao.query
            .join(
                OrdemServico,
                Notificacao.ordem_servico_id
                == OrdemServico.id,
            )
            .filter(
                OrdemServico.placa
                == placa.strip().upper(),
                Notificacao.status.in_(
                    [
                        "PENDENTE",
                        "FALHA",
                    ]
                ),
            )
        )

        if ordem_servico_id_ignorar is not None:
            consulta = consulta.filter(
                Notificacao.ordem_servico_id
                != ordem_servico_id_ignorar
            )

        return (
            consulta
            .order_by(
                Notificacao.id.asc()
            )
            .all()
        )

    @staticmethod
    def cancelar_ativas_por_placa(
        placa: str,
        ordem_servico_id_ignorar: int | None = None,
    ):
        notificacoes = (
            NotificacaoRepository
            .buscar_ativas_por_placa(
                placa,
                ordem_servico_id_ignorar,
            )
        )

        for notificacao in notificacoes:
            notificacao.status = "CANCELADO"
            notificacao.erro = None

        return len(notificacoes)

    @staticmethod
    def buscar_pendentes_para_disparo(
        data_limite: date,
    ):
        return (
            Notificacao.query
            .filter(
                Notificacao.status
                == "PENDENTE",
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
    def adicionar(
        notificacao: Notificacao,
    ):
        db.session.add(
            notificacao
        )

        db.session.flush()

        return notificacao

    @staticmethod
    def salvar(
        notificacao: Notificacao,
    ):
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