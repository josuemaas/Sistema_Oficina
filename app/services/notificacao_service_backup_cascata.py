from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from urllib.parse import quote

from app.integrations.evolution_api import EvolutionAPI
from app.models.notificacao import Notificacao
from app.models.ordem_servico import OrdemServico
from app.repositories.notificacao_repository import (
    NotificacaoRepository,
)


class NotificacaoService:
    @staticmethod
    def listar_notificacoes_disponiveis():
        return (
            OrdemServico.query
            .filter(
                (
                    OrdemServico.proxima_troca_km
                    .isnot(None)
                )
                | (
                    OrdemServico.proxima_troca_data
                    .isnot(None)
                )
            )
            .order_by(
                OrdemServico.proxima_troca_data.asc(),
                OrdemServico.id.desc(),
            )
            .all()
        )

    @staticmethod
    def buscar_ordem(
        ordem_id: int,
    ):
        return OrdemServico.query.get(
            ordem_id
        )

    @staticmethod
    def montar_mensagem(
        ordem: OrdemServico,
    ):
        cliente = ordem.cliente

        linhas = [
            f"Olá, {cliente.nome}!",
            "",
            (
                "Este é um lembrete de manutenção "
                "do seu veículo."
            ),
            "",
            (
                f"Veículo: {ordem.marca} "
                f"{ordem.modelo}"
            ),
            f"Placa: {ordem.placa}",
        ]

        if ordem.proxima_troca_km is not None:
            linhas.append(
                (
                    "Próxima troca prevista em: "
                    f"{ordem.proxima_troca_km} km"
                )
            )

        if ordem.proxima_troca_data is not None:
            data_formatada = (
                ordem.proxima_troca_data.strftime(
                    "%d/%m/%Y"
                )
            )

            linhas.append(
                (
                    "Data prevista para a próxima "
                    f"troca: {data_formatada}"
                )
            )

        linhas.extend(
            [
                "",
                (
                    "Entre em contato com a oficina "
                    "para agendar seu atendimento."
                ),
                "",
                "Sistema da Oficina",
            ]
        )

        return "\n".join(
            linhas
        )

    @staticmethod
    def normalizar_telefone(
        telefone: str,
    ):
        if not telefone:
            return ""

        somente_numeros = "".join(
            caractere
            for caractere in telefone
            if caractere.isdigit()
        )

        if len(somente_numeros) in (10, 11):
            somente_numeros = (
                f"55{somente_numeros}"
            )

        return somente_numeros

    @staticmethod
    def gerar_link_whatsapp(
        telefone: str,
        mensagem: str,
    ):
        telefone_normalizado = (
            NotificacaoService
            .normalizar_telefone(
                telefone
            )
        )

        mensagem_codificada = quote(
            mensagem
        )

        return (
            f"https://wa.me/"
            f"{telefone_normalizado}"
            f"?text={mensagem_codificada}"
        )

    @staticmethod
    def preparar_notificacao(
        ordem_id: int,
    ):
        ordem = (
            NotificacaoService
            .buscar_ordem(
                ordem_id
            )
        )

        if ordem is None:
            return None

        if ordem.cliente is None:
            return None

        cliente = ordem.cliente

        mensagem = (
            NotificacaoService
            .montar_mensagem(
                ordem
            )
        )

        link_whatsapp = (
            NotificacaoService
            .gerar_link_whatsapp(
                cliente.telefone,
                mensagem,
            )
        )

        return {
            "ordem": ordem,
            "cliente": cliente,
            "mensagem": mensagem,
            "link_whatsapp": link_whatsapp,
        }

    @staticmethod
    def cancelar_notificacoes_anteriores(
        ordem: OrdemServico,
    ):
        if ordem is None:
            return 0

        if not ordem.placa:
            return 0

        return (
            NotificacaoRepository
            .cancelar_ativas_por_placa(
                ordem.placa,
                ordem.id,
            )
        )

    @staticmethod
    def criar_para_ordem(
        ordem: OrdemServico,
    ):
        if ordem is None:
            return None

        if ordem.proxima_troca_data is None:
            return None

        NotificacaoService \
            .cancelar_notificacoes_anteriores(
                ordem
            )

        notificacao_existente = (
            NotificacaoRepository
            .buscar_por_ordem(
                ordem.id
            )
        )

        if notificacao_existente:
            return notificacao_existente

        data_agendada = (
            ordem.proxima_troca_data
            - timedelta(days=7)
        )

        notificacao = Notificacao(
            cliente_id=ordem.cliente_id,
            ordem_servico_id=ordem.id,
            data_agendada_disparo=(
                data_agendada
            ),
            status="PENDENTE",
            mensagem=(
                NotificacaoService
                .montar_mensagem(
                    ordem
                )
            ),
            tentativas=0,
        )

        return (
            NotificacaoRepository
            .adicionar(
                notificacao
            )
        )

    @staticmethod
    def sincronizar_com_ordem(
        ordem: OrdemServico,
    ):
        if ordem is None:
            return None

        if ordem.id is None:
            return None

        if ordem.proxima_troca_data is None:
            return None

        notificacao = (
            NotificacaoRepository
            .buscar_por_ordem(
                ordem.id
            )
        )

        if notificacao is None:
            return None

        if notificacao.status == "ENVIADO":
            return notificacao

        notificacao.cliente_id = (
            ordem.cliente_id
        )

        notificacao.data_agendada_disparo = (
            ordem.proxima_troca_data
            - timedelta(days=7)
        )

        notificacao.mensagem = (
            NotificacaoService
            .montar_mensagem(
                ordem
            )
        )

        notificacao.erro = None

        if notificacao.status in {
            "PENDENTE",
            "FALHA",
        }:
            notificacao.status = "PENDENTE"
            notificacao.tentativas = 0
            notificacao.data_envio = None

        return notificacao

    @staticmethod
    def enviar_notificacao(
        notificacao: Notificacao,
    ):
        if notificacao is None:
            raise ValueError(
                "Notificação não informada."
            )

        if notificacao.status == "ENVIADO":
            raise ValueError(
                "Esta notificação já foi enviada."
            )

        if notificacao.status == "CANCELADO":
            raise ValueError(
                "Esta notificação foi cancelada."
            )

        ordem = notificacao.ordem_servico

        if ordem is None:
            raise ValueError(
                "A notificação não possui uma "
                "ordem de serviço."
            )

        cliente = ordem.cliente

        if cliente is None:
            raise ValueError(
                "A ordem de serviço não possui "
                "um cliente."
            )

        if not cliente.telefone:
            raise ValueError(
                "O cliente não possui telefone "
                "cadastrado."
            )

        mensagem = (
            notificacao.mensagem
            or NotificacaoService
            .montar_mensagem(
                ordem
            )
        )

        notificacao.tentativas = (
            (
                notificacao.tentativas
                or 0
            )
            + 1
        )

        try:
            resposta = EvolutionAPI.enviar_texto(
                cliente.telefone,
                mensagem,
            )

            notificacao.status = "ENVIADO"

            notificacao.data_envio = (
                datetime.now(
                    timezone.utc
                )
            )

            notificacao.erro = None

            NotificacaoRepository.confirmar()

            return resposta

        except Exception as erro:
            notificacao.status = "FALHA"
            notificacao.erro = str(
                erro
            )

            NotificacaoRepository.confirmar()

            raise

    @staticmethod
    def processar_fila(
        data_referencia: date | None = None,
    ):
        if data_referencia is None:
            data_referencia = date.today()

        notificacoes = (
            NotificacaoRepository
            .buscar_pendentes_para_disparo(
                data_referencia
            )
        )

        total = len(
            notificacoes
        )

        enviados = 0
        falhas = 0
        resultados = []

        for notificacao in notificacoes:
            try:
                NotificacaoService \
                    .enviar_notificacao(
                        notificacao
                    )

                enviados += 1

                resultados.append(
                    {
                        "notificacao_id": (
                            notificacao.id
                        ),
                        "status": "ENVIADO",
                        "erro": None,
                    }
                )

            except Exception as erro:
                falhas += 1

                resultados.append(
                    {
                        "notificacao_id": (
                            notificacao.id
                        ),
                        "status": "FALHA",
                        "erro": str(
                            erro
                        ),
                    }
                )

        return {
            "data_referencia": (
                data_referencia.isoformat()
            ),
            "total": total,
            "enviados": enviados,
            "falhas": falhas,
            "resultados": resultados,
        }