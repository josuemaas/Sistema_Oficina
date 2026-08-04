from flask import Blueprint, render_template

from app.services.dashboard_service import DashboardService


dashboard_web_bp = Blueprint(
    "dashboard_web",
    __name__,
)


@dashboard_web_bp.get("/")
def index():
    """
    Exibe o painel principal do sistema.
    """

    resumo = DashboardService.obter_resumo()

    ultimas_ordens = (
        DashboardService.listar_ultimas_ordens()
    )

    return render_template(
        "index.html",
        resumo=resumo,
        ultimas_ordens=ultimas_ordens,
    )