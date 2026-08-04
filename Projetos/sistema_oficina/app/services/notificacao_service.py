from urllib.parse import quote

from app.models.ordem_servico import OrdemServico


class NotificacaoService:
    """
    Responsável por preparar as notificações
    de manutenção enviadas aos clientes.
    """

    @staticmethod
    def listar_notificacoes_disponiveis():
        """
        Retorna ordens que possuem uma próxima troca.
        """

        return (
            OrdemServico.query
            .filter(
                (
                    OrdemServico.proxima_troca_km.isnot(
                        None
                    )
                )
                | (
                    OrdemServico.proxima_troca_data.isnot(
                        None
                    )
                )
            )
            .order_by(
                OrdemServico.proxima_troca_data.asc(),
                OrdemServico.id.desc(),
            )
            .all()
        )

    @staticmethod
    def buscar_ordem(ordem_id: int):
        """
        Busca uma ordem de serviço pelo ID.
        """

        return OrdemServico.query.get(
            ordem_id
        )

    @staticmethod
    def montar_mensagem(
        ordem: OrdemServico,
    ):
        """
        Monta a mensagem de manutenção.
        """

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

        return "\n".join(linhas)

    @staticmethod
    def normalizar_telefone(
        telefone: str,
    ):
        """
        Remove caracteres não numéricos do telefone.
        """

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
        """
        Gera o link do WhatsApp.
        """

        telefone_normalizado = (
            NotificacaoService.normalizar_telefone(
                telefone
            )
        )

        mensagem_codificada = quote(
            mensagem
        )

        return (
            f"https://wa.me/{telefone_normalizado}"
            f"?text={mensagem_codificada}"
        )

    @staticmethod
    def preparar_notificacao(
        ordem_id: int,
    ):
        """
        Prepara os dados da notificação.
        """

        ordem = (
            NotificacaoService.buscar_ordem(
                ordem_id
            )
        )

        if ordem is None:
            return None

        if ordem.cliente is None:
            return None

        cliente = ordem.cliente

        mensagem = (
            NotificacaoService.montar_mensagem(
                ordem
            )
        )

        link_whatsapp = (
            NotificacaoService.gerar_link_whatsapp(
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