import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app import create_app
from app.services.notificacao_service import NotificacaoService


FUSO_BRASIL = ZoneInfo(
    "America/Sao_Paulo"
)

app = create_app()


def executar():
    agora = datetime.now(
        FUSO_BRASIL
    )

    print()
    print("=" * 60)
    print(
        "PROCESSAMENTO DE NOTIFICAÇÕES"
    )
    print(
        "Data e hora:",
        agora.strftime(
            "%d/%m/%Y %H:%M:%S"
        ),
    )
    print(
        "Fuso horário: America/Sao_Paulo"
    )
    print("=" * 60)

    try:
        with app.app_context():
            resultado = (
                NotificacaoService
                .processar_fila(
                    data_referencia=agora.date()
                )
            )

        print("Resultado:")
        print(resultado)
        print("=" * 60)
        print()

        return resultado

    except Exception:
        logging.exception(
            "Erro ao processar fila de notificações."
        )
        raise


if __name__ == "__main__":
    executar()