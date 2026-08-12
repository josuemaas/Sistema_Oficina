from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)
from urllib.parse import quote
from zoneinfo import ZoneInfo

from app.extensions import db
from app.integrations.evolution_api import EvolutionAPI
from app.models.notificacao import Notificacao
from app.models.ordem_servico import OrdemServico
from app.repositories.notificacao_repository import NotificacaoRepository


class NotificacaoService:
    FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

    FILAS_VALIDAS = {
        "todas",
        "hoje",
        "proximas",
    }

    SITUACOES_VALIDAS = {
        "PENDENTE",
        "ENVIADO",
        "FALHA",
        "CANCELADO",
    }

    TIPOS_PESQUISA_VALIDOS = {
        "cliente",
        "telefone",
        "placa",
    }

    STATUS_OPCOES = (
        ("PENDENTE", "Pendente"),
        ("ENVIADO", "Enviada"),
        ("FALHA", "Falha"),
        ("CANCELADO", "Cancelada"),
    )

    STATUS_APRESENTACAO = {
        "PENDENTE": (
            "Pendente",
            "badge-warning",
        ),
        "ENVIADO": (
            "Enviada",
            "badge-success",
        ),
        "FALHA": (
            "Falha",
            "badge-danger",
        ),
        "CANCELADO": (
            "Cancelada",
            "badge-neutral",
        ),
    }

    @staticmethod
    def data_atual():
        return datetime.now(
            NotificacaoService.FUSO_BRASIL
        ).date()

    @staticmethod
    def normalizar_fila(fila: str):
        valor = (fila or "").strip().lower()

        if valor not in NotificacaoService.FILAS_VALIDAS:
            return "todas"

        return valor

    @staticmethod
    def normalizar_situacao(situacao: str):
        valor = (situacao or "").strip()

        if valor.lower() == "todas":
            return "todas"

        valor = valor.upper()

        if valor not in NotificacaoService.SITUACOES_VALIDAS:
            return "todas"

        return valor

    @staticmethod
    def normalizar_tipo_pesquisa(
        tipo_pesquisa: str,
    ):
        valor = (
            tipo_pesquisa
            or "cliente"
        ).strip().lower()

        if (
            valor
            not in NotificacaoService.TIPOS_PESQUISA_VALIDOS
        ):
            return "cliente"

        return valor

    @staticmethod
    def normalizar_pesquisa(
        pesquisa: str,
        tipo_pesquisa: str,
    ):
        valor = (pesquisa or "").strip()

        if tipo_pesquisa == "telefone":
            return "".join(
                caractere
                for caractere in valor
                if caractere.isdigit()
            )[:11]

        if tipo_pesquisa == "placa":
            return "".join(
                caractere
                for caractere in valor
                if (
                    caractere.isascii()
                    and caractere.isalnum()
                )
            ).upper()[:7]

        return valor

    @staticmethod
    def converter_data_envio_local(
        data_envio: datetime | None,
    ):
        if data_envio is None:
            return None

        if data_envio.tzinfo is None:
            data_envio = data_envio.replace(
                tzinfo=timezone.utc
            )

        return data_envio.astimezone(
            NotificacaoService.FUSO_BRASIL
        )

    @staticmethod
    def preparar_dados_exibicao(
        notificacao: Notificacao,
        data_referencia: date | None = None,
    ):
        if notificacao is None:
            return None

        if data_referencia is None:
            data_referencia = (
                NotificacaoService.data_atual()
            )

        data_agendada = (
            notificacao.data_agendada_disparo
        )

        diferenca_dias = 0

        if data_agendada is not None:
            diferenca_dias = (
                data_agendada
                - data_referencia
            ).days

        atrasada = (
            notificacao.status == "PENDENTE"
            and data_agendada is not None
            and diferenca_dias < 0
        )

        dias_atraso = (
            abs(diferenca_dias)
            if atrasada
            else 0
        )

        if data_agendada is None:
            envio_texto = "-"

        elif atrasada:
            unidade = (
                "dia"
                if dias_atraso == 1
                else "dias"
            )

            envio_texto = (
                f"Atrasada há {dias_atraso} "
                f"{unidade}"
            )

        elif diferenca_dias == 0:
            envio_texto = "Hoje"

        elif diferenca_dias == 1:
            envio_texto = "Amanhã"

        elif diferenca_dias > 1:
            envio_texto = (
                f"Em {diferenca_dias} dias"
            )

        else:
            envio_texto = (
                data_agendada.strftime(
                    "%d/%m/%Y"
                )
            )

        (
            situacao_texto,
            situacao_classe,
        ) = (
            NotificacaoService
            .STATUS_APRESENTACAO
            .get(
                notificacao.status,
                (
                    notificacao.status.title(),
                    "badge-neutral",
                ),
            )
        )

        notificacao.envio_texto = envio_texto
        notificacao.atrasada = atrasada
        notificacao.dias_atraso = dias_atraso

        notificacao.data_envio_local = (
            NotificacaoService
            .converter_data_envio_local(
                notificacao.data_envio
            )
        )

        notificacao.situacao_texto = (
            situacao_texto
        )

        notificacao.situacao_classe = (
            situacao_classe
        )

        return notificacao

    @staticmethod
    def consultar_notificacoes(
        fila: str = "todas",
        situacao: str = "todas",
        data_inicial: date | None = None,
        data_final: date | None = None,
        tipo_pesquisa: str = "cliente",
        pesquisa: str = "",
        data_referencia: date | None = None,
    ):
        if data_referencia is None:
            data_referencia = (
                NotificacaoService.data_atual()
            )

        fila = (
            NotificacaoService
            .normalizar_fila(
                fila
            )
        )

        situacao = (
            NotificacaoService
            .normalizar_situacao(
                situacao
            )
        )

        tipo_pesquisa = (
            NotificacaoService
            .normalizar_tipo_pesquisa(
                tipo_pesquisa
            )
        )

        pesquisa_original = (
            pesquisa or ""
        ).strip()

        pesquisa = (
            NotificacaoService
            .normalizar_pesquisa(
                pesquisa_original,
                tipo_pesquisa,
            )
        )

        if (
            pesquisa_original
            and not pesquisa
        ):
            return []

        notificacoes = (
            NotificacaoRepository.consultar(
                fila=fila,
                situacao=situacao,
                data_inicial=data_inicial,
                data_final=data_final,
                tipo_pesquisa=tipo_pesquisa,
                pesquisa=pesquisa,
                data_referencia=data_referencia,
            )
        )

        return [
            NotificacaoService
            .preparar_dados_exibicao(
                notificacao,
                data_referencia,
            )
            for notificacao
            in notificacoes
        ]

    @staticmethod
    def obter_indicadores(
        data_referencia: date | None = None,
    ):
        if data_referencia is None:
            data_referencia = (
                NotificacaoService.data_atual()
            )

        inicio_local = datetime.combine(
            data_referencia,
            time.min,
            tzinfo=NotificacaoService.FUSO_BRASIL,
        )

        fim_local = (
            inicio_local
            + timedelta(days=1)
        )

        return (
            NotificacaoRepository
            .obter_indicadores(
                data_referencia=data_referencia,
                inicio_dia_utc=(
                    inicio_local.astimezone(
                        timezone.utc
                    )
                ),
                fim_dia_utc=(
                    fim_local.astimezone(
                        timezone.utc
                    )
                ),
            )
        )

    @staticmethod
    def buscar_notificacao_para_visualizacao(
        notificacao_id: int,
    ):
        notificacao = (
            NotificacaoRepository
            .buscar_por_id(
                notificacao_id
            )
        )

        return (
            NotificacaoService
            .preparar_dados_exibicao(
                notificacao
            )
        )

    @staticmethod
    def listar_notificacoes_disponiveis():
        return (
            OrdemServico.query
            .filter(
                (
                    OrdemServico
                    .proxima_troca_km
                    .isnot(None)
                )
                | (
                    OrdemServico
                    .proxima_troca_data
                    .isnot(None)
                )
            )
            .order_by(
                OrdemServico
                .proxima_troca_data
                .asc(),
                OrdemServico.id.desc(),
            )
            .all()
        )

    @staticmethod
    def buscar_ordem(ordem_id: int):
        return db.session.get(
            OrdemServico,
            ordem_id,
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

        if (
            ordem.proxima_troca_km
            is not None
        ):
            linhas.append(
                (
                    "Próxima troca prevista em: "
                    f"{ordem.proxima_troca_km} km"
                )
            )

        if (
            ordem.proxima_troca_data
            is not None
        ):
            data_formatada = (
                ordem.proxima_troca_data
                .strftime(
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

        if len(somente_numeros) in (
            10,
            11,
        ):
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
            "https://wa.me/"
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
    def garantir_notificacao(
        ordem: OrdemServico,
    ):
        if ordem is None:
            return None

        if ordem.id is None:
            return None

        if (
            ordem.proxima_troca_data
            is None
        ):
            return None

        notificacao = (
            NotificacaoRepository
            .buscar_por_ordem(
                ordem.id
            )
        )

        if notificacao is None:
            data_agendada = (
                ordem.proxima_troca_data
                - timedelta(days=7)
            )

            notificacao = Notificacao(
                cliente_id=(
                    ordem.cliente_id
                ),
                ordem_servico_id=(
                    ordem.id
                ),
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

        return notificacao

    @staticmethod
    def atualizar_dados_notificacao(
        notificacao: Notificacao,
        ordem: OrdemServico,
    ):
        if notificacao is None:
            return None

        if ordem is None:
            return notificacao

        if (
            notificacao.status
            == "ENVIADO"
        ):
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

        return notificacao

    @staticmethod
    def sincronizar_com_ordem(
        ordem: OrdemServico,
    ):
        if ordem is None:
            return None

        notificacao = (
            NotificacaoService
            .garantir_notificacao(
                ordem
            )
        )

        if notificacao is None:
            return None

        return (
            NotificacaoService
            .atualizar_dados_notificacao(
                notificacao,
                ordem,
            )
        )

    @staticmethod
    def sincronizar_historico_placa(
        placa: str,
    ):
        if not placa:
            return {
                "total_ordens": 0,
                "canceladas": 0,
                "pendentes": 0,
            }

        placa_normalizada = (
            placa.strip().upper()
        )

        ordens = (
            OrdemServico.query
            .filter(
                OrdemServico.placa
                == placa_normalizada
            )
            .order_by(
                OrdemServico
                .data_servico
                .asc(),
                OrdemServico.id.asc(),
            )
            .all()
        )

        if not ordens:
            return {
                "total_ordens": 0,
                "canceladas": 0,
                "pendentes": 0,
            }

        ultima_ordem = ordens[-1]

        canceladas = 0
        pendentes = 0

        for ordem in ordens:
            notificacao = (
                NotificacaoService
                .garantir_notificacao(
                    ordem
                )
            )

            if notificacao is None:
                continue

            if (
                notificacao.status
                == "ENVIADO"
            ):
                continue

            NotificacaoService \
                .atualizar_dados_notificacao(
                    notificacao,
                    ordem,
                )

            if (
                ordem.id
                == ultima_ordem.id
            ):
                notificacao.status = (
                    "PENDENTE"
                )

                notificacao.tentativas = 0
                notificacao.data_envio = None
                notificacao.erro = None

                pendentes += 1

            else:
                notificacao.status = (
                    "CANCELADO"
                )

                notificacao.erro = None

                canceladas += 1

        return {
            "total_ordens": len(
                ordens
            ),
            "canceladas": canceladas,
            "pendentes": pendentes,
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

        if (
            ordem.proxima_troca_data
            is None
        ):
            return None

        notificacao = (
            NotificacaoService
            .garantir_notificacao(
                ordem
            )
        )

        NotificacaoService \
            .sincronizar_historico_placa(
                ordem.placa
            )

        return notificacao

    @staticmethod
    def enviar_notificacao(
        notificacao: Notificacao,
    ):
        if notificacao is None:
            raise ValueError(
                "Notificação não informada."
            )

        if (
            notificacao.status
            == "ENVIADO"
        ):
            raise ValueError(
                "Esta notificação já foi enviada."
            )

        if (
            notificacao.status
            == "CANCELADO"
        ):
            raise ValueError(
                "Esta notificação foi cancelada."
            )

        ordem = (
            notificacao.ordem_servico
        )

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

        if not cliente.ativo:
            raise ValueError(
                "O cliente está desativado."
            )

        if not cliente.recebe_notificacao:
            raise ValueError(
                "O cliente não está autorizado "
                "a receber notificações."
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
            resposta = (
                EvolutionAPI.enviar_texto(
                    cliente.telefone,
                    mensagem,
                )
            )

            notificacao.status = (
                "ENVIADO"
            )

            notificacao.data_envio = (
                datetime.now(
                    timezone.utc
                )
            )

            notificacao.erro = None

            NotificacaoRepository.confirmar()

            return resposta

        except Exception as erro:
            notificacao.status = (
                "FALHA"
            )

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
            data_referencia = (
                NotificacaoService.data_atual()
            )

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
                        "erro": str(erro),
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