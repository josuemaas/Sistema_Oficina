from datetime import date

from app.models.cliente import Cliente
from app.models.notificacao import Notificacao
from app.models.ordem_servico import OrdemServico


class DashboardService:
    """
    Responsável por reunir os dados exibidos
    no painel principal do sistema.
    """

    @staticmethod
    def obter_resumo():
        """
        Retorna os totais principais do sistema.
        """

        total_clientes = (
            Cliente.query
            .filter_by(ativo=True)
            .count()
        )

        total_ordens = (
            OrdemServico.query
            .count()
        )

        proximas_trocas = (
            OrdemServico.query
            .filter(
                OrdemServico.proxima_troca_data.isnot(
                    None
                ),
                OrdemServico.proxima_troca_data
                >= date.today(),
            )
            .count()
        )

        notificacoes_pendentes = (
            Notificacao.query
            .filter(
                Notificacao.status == "PENDENTE"
            )
            .count()
        )

        return {
            "total_clientes": total_clientes,
            "total_ordens": total_ordens,
            "proximas_trocas": proximas_trocas,
            "notificacoes_pendentes": (
                notificacoes_pendentes
            ),
        }

    @staticmethod
    def listar_ultimas_ordens(
        limite: int = 5,
    ):
        """
        Retorna as ordens de serviço mais recentes.
        """

        return (
            OrdemServico.query
            .order_by(
                OrdemServico.data_servico.desc(),
                OrdemServico.id.desc(),
            )
            .limit(limite)
            .all()
        )
