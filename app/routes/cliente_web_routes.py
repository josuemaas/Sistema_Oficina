from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.models.ordem_servico import OrdemServico
from app.services.cliente_service import ClienteService
from app.utils.paginacao import paginar_resultados


cliente_web_bp = Blueprint(
    "cliente_web",
    __name__,
    url_prefix="/painel/clientes",
)


TIPOS_PESQUISA_CLIENTE = {
    "nome",
    "cpf",
    "telefone",
}

SITUACOES_CLIENTE = {
    "todas",
    "ativo",
    "desativado",
}


def obter_contexto_selecao_ordem():
    if request.args.get("modo") != "selecionar":
        return "", None

    ordem_id = request.args.get(
        "ordem_id",
        type=int,
    )

    if ordem_id is not None and ordem_id < 1:
        ordem_id = None

    return "selecionar", ordem_id


def somente_numeros(valor: str):
    return "".join(
        caractere
        for caractere in (valor or "")
        if caractere.isdigit()
    )


def filtrar_clientes(
    clientes: list,
    pesquisa: str,
    tipo_pesquisa: str,
):
    if not pesquisa:
        return clientes

    if tipo_pesquisa == "cpf":
        termo = somente_numeros(
            pesquisa
        )

        if not termo:
            return []

        return [
            cliente
            for cliente in clientes
            if termo
            in somente_numeros(
                cliente.cpf_cnpj
            )
        ]

    if tipo_pesquisa == "telefone":
        termo = somente_numeros(
            pesquisa
        )

        if not termo:
            return []

        return [
            cliente
            for cliente in clientes
            if termo
            in somente_numeros(
                cliente.telefone
            )
        ]

    termo = pesquisa.casefold().strip()

    return [
        cliente
        for cliente in clientes
        if termo
        in cliente.nome.casefold()
    ]


def filtrar_situacao_clientes(
    clientes: list,
    situacao: str,
):
    if situacao == "ativo":
        return [
            cliente
            for cliente in clientes
            if cliente.ativo
        ]

    if situacao == "desativado":
        return [
            cliente
            for cliente in clientes
            if not cliente.ativo
        ]

    return clientes


def buscar_ordens_cliente(
    cliente_id: int,
    pesquisa: str = "",
):
    consulta = (
        OrdemServico.query
        .filter_by(
            cliente_id=cliente_id
        )
        .order_by(
            OrdemServico.data_servico.desc(),
            OrdemServico.id.desc(),
        )
    )

    ordens = consulta.all()

    if not pesquisa:
        return ordens

    termo = pesquisa.lower().strip()

    return [
        ordem
        for ordem in ordens
        if (
            ordem.placa
            and termo in ordem.placa.lower()
        )
        or (
            ordem.marca
            and termo in ordem.marca.lower()
        )
        or (
            ordem.modelo
            and termo in ordem.modelo.lower()
        )
        or (
            ordem.descricao_servico
            and termo
            in ordem.descricao_servico.lower()
        )
        or (
            ordem.tipo_oleo
            and termo
            in ordem.tipo_oleo.lower()
        )
    ]


@cliente_web_bp.get("")
def listar():
    pesquisa = request.args.get(
        "pesquisa",
        "",
    ).strip()

    modo, ordem_id = (
        obter_contexto_selecao_ordem()
    )

    tipo_pesquisa = request.args.get(
        "tipo_pesquisa",
        "nome",
    ).strip().lower()

    if (
        tipo_pesquisa
        not in TIPOS_PESQUISA_CLIENTE
    ):
        tipo_pesquisa = "nome"

    situacao = request.args.get(
        "situacao",
        "todas",
    ).strip().lower()

    if situacao not in SITUACOES_CLIENTE:
        situacao = "todas"

    clientes = (
        ClienteService.listar_clientes()
    )

    clientes = filtrar_situacao_clientes(
        clientes,
        situacao,
    )

    clientes = filtrar_clientes(
        clientes,
        pesquisa,
        tipo_pesquisa,
    )

    pagina_solicitada = request.args.get(
        "pagina",
        1,
        type=int,
    )

    (
        clientes,
        pagina_atual,
        total_paginas,
        total_registros,
    ) = paginar_resultados(
        clientes,
        pagina_solicitada,
    )

    return render_template(
        "clientes/lista.html",
        clientes=clientes,
        pesquisa=pesquisa,
        tipo_pesquisa=tipo_pesquisa,
        situacao=situacao,
        modo=modo,
        ordem_id=ordem_id,
        pagina_atual=pagina_atual,
        total_paginas=total_paginas,
        total_registros=total_registros,
    )


@cliente_web_bp.get(
    "/<int:cliente_id>/detalhes"
)
def detalhes(cliente_id: int):
    cliente = (
        ClienteService.buscar_por_id(
            cliente_id
        )
    )

    if cliente is None:
        flash(
            "Cliente não encontrado.",
            "danger",
        )

        return redirect(
            url_for(
                "cliente_web.listar"
            )
        )

    pesquisa = request.args.get(
        "pesquisa",
        "",
    ).strip()

    ordens = buscar_ordens_cliente(
        cliente_id,
        pesquisa,
    )

    todas_ordens = buscar_ordens_cliente(
        cliente_id
    )

    total_ordens = len(
        todas_ordens
    )

    ultima_ordem = (
        todas_ordens[0]
        if todas_ordens
        else None
    )

    ultima_quilometragem = (
        ultima_ordem.quilometragem
        if ultima_ordem
        else None
    )

    ultima_data = (
        ultima_ordem.data_servico
        if ultima_ordem
        else None
    )

    return render_template(
        "clientes/detalhes.html",
        cliente=cliente,
        ordens=ordens,
        pesquisa=pesquisa,
        total_ordens=total_ordens,
        ultima_ordem=ultima_ordem,
        ultima_quilometragem=(
            ultima_quilometragem
        ),
        ultima_data=ultima_data,
    )


@cliente_web_bp.route(
    "/novo",
    methods=["GET", "POST"],
)
def cadastrar():
    modo, ordem_id = (
        obter_contexto_selecao_ordem()
    )

    contexto_selecao = {
        "modo": modo,
        "ordem_id": ordem_id,
    }

    if request.method == "POST":
        dados = {
            "nome": request.form.get(
                "nome",
                "",
            ).strip(),
            "cpf_cnpj": (
                somente_numeros(
                    request.form.get(
                        "cpf_cnpj",
                        "",
                    )
                )
                or None
            ),
            "telefone": request.form.get(
                "telefone",
                "",
            ),
            "email": (
                request.form.get(
                    "email",
                    "",
                ).strip()
                or None
            ),
            "observacoes": (
                request.form.get(
                    "observacoes",
                    "",
                ).strip()
                or None
            ),
            "recebe_notificacao": (
                request.form.get(
                    "recebe_notificacao"
                )
                == "on"
            ),
        }

        dados["telefone"] = (
            somente_numeros(
                dados["telefone"]
            )
        )

        if not dados["nome"]:
            flash(
                "Informe o nome do cliente.",
                "danger",
            )

            return render_template(
                "clientes/formulario.html",
                cliente=None,
                **contexto_selecao,
            )

        if not dados["telefone"]:
            flash(
                "Informe o telefone do cliente.",
                "danger",
            )

            return render_template(
                "clientes/formulario.html",
                cliente=None,
                **contexto_selecao,
            )

        try:
            ClienteService.cadastrar_cliente(
                dados
            )

        except ValueError as erro:
            flash(
                str(erro),
                "danger",
            )

            return render_template(
                "clientes/formulario.html",
                cliente=None,
                **contexto_selecao,
            )

        flash(
            "Cliente cadastrado com sucesso.",
            "success",
        )

        if modo == "selecionar":
            return redirect(
                url_for(
                    "cliente_web.listar",
                    modo=modo,
                    ordem_id=ordem_id,
                )
            )

        return redirect(
            url_for(
                "cliente_web.listar"
            )
        )

    return render_template(
        "clientes/formulario.html",
        cliente=None,
        **contexto_selecao,
    )


@cliente_web_bp.route(
    "/<int:cliente_id>/editar",
    methods=["GET", "POST"],
)
def editar(cliente_id: int):
    cliente = (
        ClienteService.buscar_por_id(
            cliente_id
        )
    )

    if cliente is None:
        flash(
            "Cliente não encontrado.",
            "danger",
        )

        return redirect(
            url_for(
                "cliente_web.listar"
            )
        )

    if request.method == "POST":
        dados = {
            "nome": request.form.get(
                "nome",
                "",
            ).strip(),
            "cpf_cnpj": (
                somente_numeros(
                    request.form.get(
                        "cpf_cnpj",
                        "",
                    )
                )
                or None
            ),
            "telefone": request.form.get(
                "telefone",
                "",
            ),
            "email": (
                request.form.get(
                    "email",
                    "",
                ).strip()
                or None
            ),
            "observacoes": (
                request.form.get(
                    "observacoes",
                    "",
                ).strip()
                or None
            ),
            "recebe_notificacao": (
                request.form.get(
                    "recebe_notificacao"
                )
                == "on"
            ),
        }

        dados["telefone"] = (
            somente_numeros(
                dados["telefone"]
            )
        )

        if not dados["nome"]:
            flash(
                "Informe o nome do cliente.",
                "danger",
            )

            return render_template(
                "clientes/formulario.html",
                cliente=cliente,
            )

        if not dados["telefone"]:
            flash(
                "Informe o telefone do cliente.",
                "danger",
            )

            return render_template(
                "clientes/formulario.html",
                cliente=cliente,
            )

        try:
            ClienteService.atualizar_cliente(
                cliente_id,
                dados,
            )

        except ValueError as erro:
            flash(
                str(erro),
                "danger",
            )

            return render_template(
                "clientes/formulario.html",
                cliente=cliente,
            )

        flash(
            "Cliente atualizado com sucesso.",
            "success",
        )

        return redirect(
            url_for(
                "cliente_web.detalhes",
                cliente_id=cliente.id,
            )
        )

    return render_template(
        "clientes/formulario.html",
        cliente=cliente,
    )


@cliente_web_bp.post(
    "/<int:cliente_id>/situacao"
)
def alterar_situacao(cliente_id: int):
    cliente = (
        ClienteService.alternar_situacao_cliente(
            cliente_id
        )
    )

    if cliente is None:
        flash(
            "Cliente não encontrado.",
            "danger",
        )
    elif cliente.ativo:
        flash(
            "Cliente ativado com sucesso.",
            "success",
        )
    else:
        flash(
            "Cliente desativado com sucesso.",
            "success",
        )

    parametros = {}

    situacao = request.form.get(
        "situacao",
        "",
    ).strip()

    tipo_pesquisa = request.form.get(
        "tipo_pesquisa",
        "",
    ).strip()

    pesquisa = request.form.get(
        "pesquisa",
        "",
    ).strip()

    pagina = request.form.get(
        "pagina",
        type=int,
    )

    modo = request.form.get(
        "modo",
        "",
    ).strip()

    ordem_id = request.form.get(
        "ordem_id",
        type=int,
    )

    if situacao:
        parametros["situacao"] = situacao

    if tipo_pesquisa:
        parametros[
            "tipo_pesquisa"
        ] = tipo_pesquisa

    if pesquisa:
        parametros["pesquisa"] = pesquisa

    if pagina:
        parametros["pagina"] = pagina

    if modo == "selecionar":
        parametros["modo"] = modo

        if ordem_id:
            parametros[
                "ordem_id"
            ] = ordem_id

    return redirect(
        url_for(
            "cliente_web.listar",
            **parametros,
        )
    )


@cliente_web_bp.post(
    "/<int:cliente_id>/excluir"
)
def excluir(cliente_id: int):
    resultado = (
        ClienteService.excluir_cliente(
            cliente_id
        )
    )

    if resultado is None:
        flash(
            "Cliente não encontrado.",
            "danger",
        )
    else:
        flash(
            "Cliente removido com sucesso.",
            "success",
        )

    return redirect(
        url_for(
            "cliente_web.listar"
        )
    )