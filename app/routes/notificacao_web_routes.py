from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    url_for,
)

from app.services.notificacao_service import (
    NotificacaoService,
)


notificacao_web_bp = Blueprint(
    "notificacao_web",
    __name__,
    url_prefix="/painel/notificacoes",
)


@notificacao_web_bp.get("")
def listar():
    """
    Exibe as notificações disponíveis.
    """

    ordens = (
        NotificacaoService
        .listar_notificacoes_disponiveis()
    )

    return render_template(
        "notificacoes/lista.html",
        ordens=ordens,
    )


@notificacao_web_bp.get(
    "/<int:ordem_id>/visualizar"
)
def visualizar(ordem_id: int):
    """
    Exibe os dados e a mensagem da notificação.
    """

    notificacao = (
        NotificacaoService.preparar_notificacao(
            ordem_id
        )
    )

    if notificacao is None:
        flash(
            (
                "Não foi possível preparar a "
                "notificação."
            ),
            "danger",
        )

        return redirect(
            url_for("notificacao_web.listar")
        )

    return render_template(
        "notificacoes/visualizar.html",
        notificacao=notificacao,
    )