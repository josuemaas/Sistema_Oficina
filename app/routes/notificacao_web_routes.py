from datetime import date

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.services.notificacao_service import (
    NotificacaoService,
)
from app.utils.paginacao import paginar_resultados


notificacao_web_bp = Blueprint(
    "notificacao_web",
    __name__,
    url_prefix="/painel/notificacoes",
)


def converter_data_filtro(
    valor: str,
):
    if not valor:
        return None

    try:
        return date.fromisoformat(valor)

    except ValueError:
        return None


@notificacao_web_bp.get("")
def listar():
    fila = NotificacaoService.normalizar_fila(
        request.args.get(
            "fila",
            "todas",
        )
    )
    situacao = (
        NotificacaoService.normalizar_situacao(
            request.args.get(
                "situacao",
                "todas",
            )
        )
    )
    tipo_pesquisa = (
        NotificacaoService
        .normalizar_tipo_pesquisa(
            request.args.get(
                "tipo_pesquisa",
                "cliente",
            )
        )
    )

    pesquisa_recebida = request.args.get(
        "pesquisa",
        "",
    ).strip()
    pesquisa = (
        NotificacaoService.normalizar_pesquisa(
            pesquisa_recebida,
            tipo_pesquisa,
        )
    )

    data_inicial_texto = request.args.get(
        "data_inicial",
        "",
    ).strip()
    data_final_texto = request.args.get(
        "data_final",
        "",
    ).strip()

    data_inicial = converter_data_filtro(
        data_inicial_texto
    )
    data_final = converter_data_filtro(
        data_final_texto
    )
    data_referencia = (
        NotificacaoService.data_atual()
    )

    notificacoes = (
        NotificacaoService.consultar_notificacoes(
            fila=fila,
            situacao=situacao,
            data_inicial=data_inicial,
            data_final=data_final,
            tipo_pesquisa=tipo_pesquisa,
            pesquisa=pesquisa_recebida,
            data_referencia=data_referencia,
        )
    )

    pagina_solicitada = request.args.get(
        "pagina",
        1,
        type=int,
    )

    (
        notificacoes,
        pagina_atual,
        total_paginas,
        total_registros,
    ) = paginar_resultados(
        notificacoes,
        pagina_solicitada,
    )

    return render_template(
        "notificacoes/lista.html",
        notificacoes=notificacoes,
        indicadores=(
            NotificacaoService.obter_indicadores(
                data_referencia
            )
        ),
        fila=fila,
        situacao=situacao,
        data_inicial=(
            data_inicial_texto
            if data_inicial is not None
            else ""
        ),
        data_final=(
            data_final_texto
            if data_final is not None
            else ""
        ),
        tipo_pesquisa=tipo_pesquisa,
        pesquisa=pesquisa,
        pagina_atual=pagina_atual,
        total_paginas=total_paginas,
        total_registros=total_registros,
        status_opcoes=(
            NotificacaoService.STATUS_OPCOES
        ),
    )


@notificacao_web_bp.get(
    "/<int:notificacao_id>/visualizar"
)
def visualizar(notificacao_id: int):
    notificacao = (
        NotificacaoService
        .buscar_notificacao_para_visualizacao(
            notificacao_id
        )
    )

    if notificacao is None:
        flash(
            (
                "Notificação não encontrada."
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
