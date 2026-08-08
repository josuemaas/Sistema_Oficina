import requests
from flask import current_app


class EvolutionAPI:
    @staticmethod
    def _configuracao():
        url = current_app.config.get(
            "EVOLUTION_API_URL"
        )

        api_key = current_app.config.get(
            "EVOLUTION_API_KEY"
        )

        instancia = current_app.config.get(
            "EVOLUTION_INSTANCE"
        )

        if not url:
            raise ValueError(
                "EVOLUTION_API_URL não configurada."
            )

        if not api_key:
            raise ValueError(
                "EVOLUTION_API_KEY não configurada."
            )

        if not instancia:
            raise ValueError(
                "EVOLUTION_INSTANCE não configurada."
            )

        return (
            url.rstrip("/"),
            api_key,
            instancia,
        )

    @staticmethod
    def verificar_conexao():
        url, api_key, instancia = (
            EvolutionAPI._configuracao()
        )

        resposta = requests.get(
            f"{url}/instance/connectionState/{instancia}",
            headers={
                "apikey": api_key,
            },
            timeout=15,
        )

        resposta.raise_for_status()

        return resposta.json()

    @staticmethod
    def enviar_texto(
        telefone: str,
        mensagem: str,
    ):
        url, api_key, instancia = (
            EvolutionAPI._configuracao()
        )

        telefone = "".join(
            caractere
            for caractere in telefone
            if caractere.isdigit()
        )

        if len(telefone) in (10, 11):
            telefone = f"55{telefone}"

        if not telefone:
            raise ValueError(
                "Telefone inválido."
            )

        if not mensagem or not mensagem.strip():
            raise ValueError(
                "Mensagem não informada."
            )

        resposta = requests.post(
            f"{url}/message/sendText/{instancia}",
            headers={
                "apikey": api_key,
                "Content-Type": "application/json",
            },
            json={
                "number": telefone,
                "text": mensagem.strip(),
            },
            timeout=30,
        )

        resposta.raise_for_status()

        return resposta.json()