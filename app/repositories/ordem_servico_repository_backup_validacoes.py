from datetime import date

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
    def buscar_por_id(
        ordem_id: int,
    ):
        return db.session.get(
            OrdemServico,
            ordem_id,
        )

    @staticmethod
    def buscar_historico_por_placa(
        placa: str,
    ):
        placa_normalizada = (
            placa.strip().upper()
        )

        return (
            OrdemServico.query
            .filter(
                OrdemServico.placa
                == placa_normalizada
            )
            .order_by(
                OrdemServico.data_servico.asc(),
                OrdemServico.id.asc(),
            )
            .all()
        )

    @staticmethod
    def buscar_historico_ate_data(
        placa: str,
        data_limite: date,
        ordem_id_ignorar: int | None = None,
    ):
        placa_normalizada = (
            placa.strip().upper()
        )

        consulta = (
            OrdemServico.query
            .filter(
                OrdemServico.placa
                == placa_normalizada,
                OrdemServico.data_servico
                <= data_limite,
            )
        )

        if ordem_id_ignorar is not None:
            consulta = consulta.filter(
                OrdemServico.id
                != ordem_id_ignorar
            )

        return (
            consulta
            .order_by(
                OrdemServico.data_servico.asc(),
                OrdemServico.id.asc(),
            )
            .all()
        )

    @staticmethod
    def adicionar(
        ordem: OrdemServico,
    ):
        db.session.add(
            ordem
        )

        db.session.flush()

        return ordem

    @staticmethod
    def remover(
        ordem: OrdemServico,
    ):
        if ordem.notificacao is not None:
            db.session.delete(
                ordem.notificacao
            )

        db.session.delete(
            ordem
        )

        db.session.flush()

    @staticmethod
    def flush():
        db.session.flush()

    @staticmethod
    def salvar(
        ordem: OrdemServico,
    ):
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
    def excluir(
        ordem: OrdemServico,
    ):
        try:
            OrdemServicoRepository.remover(
                ordem
            )

            db.session.commit()

        except Exception:
            db.session.rollback()
            raise