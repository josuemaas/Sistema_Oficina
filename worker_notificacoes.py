import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from zoneinfo import ZoneInfo

from app import create_app
from app.services.notificacao_service import NotificacaoService


FUSO_BRASIL = ZoneInfo(
    "America/Sao_Paulo"
)

app = create_app()


def processar_notificacoes():
    agora = datetime.now(
        FUSO_BRASIL
    )

    print()
    print("=" * 60)

    print(
        "Executando fila de notificações em:",
        agora.strftime(
            "%d/%m/%Y %H:%M:%S"
        ),
    )

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

    except Exception:
        logging.exception(
            "Erro ao processar fila de notificações."
        )

    print("=" * 60)
    print()


def iniciar_worker():
    scheduler = BlockingScheduler(
        timezone=FUSO_BRASIL
    )

    scheduler.add_job(
        processar_notificacoes,
        trigger="cron",
        day_of_week="mon-fri",
        hour=9,
        minute=0,
        id="processar_notificacoes",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    print("=" * 60)
    print(
        "WORKER DE NOTIFICAÇÕES INICIADO"
    )
    print(
        "Horário: segunda a sexta-feira às 09:00"
    )
    print(
        "Fuso horário: America/Sao_Paulo"
    )
    print("=" * 60)

    try:
        scheduler.start()

    except (KeyboardInterrupt, SystemExit):
        print()
        print(
            "Worker de notificações encerrado."
        )


if __name__ == "__main__":
    iniciar_worker()