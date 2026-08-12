from datetime import date, datetime

from sqlalchemy import case, func

from app.extensions import db
from app.models.cliente import Cliente
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
    def consultar(
        fila: str,
        situacao: str,
        data_inicial: date | None,
        data_final: date | None,
        tipo_pesquisa: str,
        pesquisa: str,
        data_referencia: date,
    ):
        consulta = Notificacao.query

        if fila == "hoje":
            consulta = consulta.filter(
                Notificacao.data_agendada_disparo
                == data_referencia
            )

        elif fila == "proximas":
            consulta = consulta.filter(
                Notificacao.status == "PENDENTE",
                Notificacao.data_agendada_disparo
                > data_referencia,
            )

        if situacao != "todas":
            consulta = consulta.filter(
                Notificacao.status == situacao
            )

        if data_inicial is not None:
            consulta = consulta.filter(
                Notificacao.data_agendada_disparo
                >= data_inicial
            )

        if data_final is not None:
            consulta = consulta.filter(
                Notificacao.data_agendada_disparo
                <= data_final
            )

        if pesquisa:
            if tipo_pesquisa == "telefone":
                telefone = Cliente.telefone

                for caractere in (
                    "(",
                    ")",
                    "-",
                    " ",
                    "+",
                ):
                    telefone = func.replace(
                        telefone,
                        caractere,
                        "",
                    )

                consulta = (
                    consulta
                    .join(
                        Cliente,
                        Notificacao.cliente_id
                        == Cliente.id,
                    )
                    .filter(
                        telefone.contains(pesquisa)
                    )
                )

            elif tipo_pesquisa == "placa":
                placa = OrdemServico.placa

                for caractere in (
                    "-",
                    " ",
                ):
                    placa = func.replace(
                        placa,
                        caractere,
                        "",
                    )

                consulta = (
                    consulta
                    .join(
                        OrdemServico,
                        Notificacao.ordem_servico_id
                        == OrdemServico.id,
                    )
                    .filter(
                        placa.ilike(
                            f"%{pesquisa}%"
                        )
                    )
                )

            else:
                consulta = (
                    consulta
                    .join(
                        Cliente,
                        Notificacao.cliente_id
                        == Cliente.id,
                    )
                    .filter(
                        Cliente.nome.ilike(
                            f"%{pesquisa}%"
                        )
                    )
                )

        prioridade_status = case(
            (Notificacao.status == "PENDENTE", 0),
            (Notificacao.status == "FALHA", 1),
            (Notificacao.status == "ENVIADO", 2),
            else_=3,
        )

        return (
            consulta
            .order_by(
                prioridade_status.asc(),
                Notificacao.data_agendada_disparo.asc(),
                Notificacao.id.asc(),
            )
            .all()
        )

    @staticmethod
    def obter_indicadores(
        data_referencia: date,
        inicio_dia_utc: datetime,
        fim_dia_utc: datetime,
    ):
        pendentes = (
            Notificacao.query
            .filter(
                Notificacao.status == "PENDENTE"
            )
            .count()
        )

        para_hoje = (
            Notificacao.query
            .filter(
                Notificacao.status == "PENDENTE",
                Notificacao.data_agendada_disparo
                == data_referencia,
            )
            .count()
        )

        falhas = (
            Notificacao.query
            .filter(
                Notificacao.status == "FALHA"
            )
            .count()
        )

        enviadas_hoje = (
            Notificacao.query
            .filter(
                Notificacao.status == "ENVIADO",
                Notificacao.data_envio
                >= inicio_dia_utc,
                Notificacao.data_envio
                < fim_dia_utc,
            )
            .count()
        )

        return {
            "pendentes": pendentes,
            "para_hoje": para_hoje,
            "falhas": falhas,
            "enviadas_hoje": enviadas_hoje,
        }

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
            .join(
                Cliente,
                Notificacao.cliente_id
                == Cliente.id,
            )
            .filter(
                Notificacao.status == "PENDENTE",
                Notificacao.data_agendada_disparo
                <= data_limite,
                Cliente.ativo.is_(True),
                Cliente.recebe_notificacao.is_(True),
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