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


cliente_web_bp = Blueprint(
    "cliente_web",
    __name__,
    url_prefix="/painel/clientes",
)


def filtrar_clientes(
    clientes: list,
    pesquisa: str,
):
    """
    Filtra clientes por nome, telefone ou e-mail.
    """

    if not pesquisa:
        return clientes

    termo = pesquisa.lower().strip()

    return [
        cliente
        for cliente in clientes
        if (
            termo in cliente.nome.lower()
            or termo in cliente.telefone.lower()
            or (
                cliente.email
                and termo in cliente.email.lower()
            )
        )
    ]


def buscar_ordens_cliente(
    cliente_id: int,
    pesquisa: str = "",
):
    """
    Retorna as ordens de serviço do cliente,
    permitindo pesquisar pelos dados do veículo
    ou pelo serviço realizado.
    """

    consulta = (
        OrdemServico.query
        .filter_by(cliente_id=cliente_id)
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
            and termo in ordem.tipo_oleo.lower()
        )
    ]


@cliente_web_bp.get("")
def listar():
    """
    Exibe os clientes cadastrados.

    Também permite utilizar a página no modo
    de seleção de cliente para uma ordem.
    """

    pesquisa = request.args.get(
        "pesquisa",
        "",
    ).strip()

    modo = request.args.get(
        "modo",
        "",
    ).strip()

    clientes = ClienteService.listar_clientes()

    clientes = filtrar_clientes(
        clientes,
        pesquisa,
    )

    return render_template(
        "clientes/lista.html",
        clientes=clientes,
        pesquisa=pesquisa,
        modo=modo,
    )


@cliente_web_bp.get(
    "/<int:cliente_id>/detalhes"
)
def detalhes(cliente_id: int):
    """
    Exibe os dados do cliente e seu histórico
    completo de ordens de serviço.
    """

    cliente = ClienteService.buscar_por_id(
        cliente_id
    )

    if cliente is None:
        flash(
            "Cliente não encontrado.",
            "danger",
        )

        return redirect(
            url_for("cliente_web.listar")
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

    total_ordens = len(todas_ordens)

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
    """
    Exibe o formulário e cadastra
    um novo cliente.
    """

    if request.method == "POST":
        dados = {
            "nome": request.form.get(
                "nome",
                "",
            ).strip(),
            "telefone": request.form.get(
                "telefone",
                "",
            ).strip(),
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

        if not dados["nome"]:
            flash(
                "Informe o nome do cliente.",
                "danger",
            )

            return render_template(
                "clientes/formulario.html",
                cliente=None,
            )

        if not dados["telefone"]:
            flash(
                "Informe o telefone do cliente.",
                "danger",
            )

            return render_template(
                "clientes/formulario.html",
                cliente=None,
            )

        ClienteService.cadastrar_cliente(
            dados
        )

        flash(
            "Cliente cadastrado com sucesso.",
            "success",
        )

        return redirect(
            url_for("cliente_web.listar")
        )

    return render_template(
        "clientes/formulario.html",
        cliente=None,
    )


@cliente_web_bp.route(
    "/<int:cliente_id>/editar",
    methods=["GET", "POST"],
)
def editar(cliente_id: int):
    """
    Exibe o formulário e atualiza
    um cliente existente.
    """

    cliente = ClienteService.buscar_por_id(
        cliente_id
    )

    if cliente is None:
        flash(
            "Cliente não encontrado.",
            "danger",
        )

        return redirect(
            url_for("cliente_web.listar")
        )

    if request.method == "POST":
        dados = {
            "nome": request.form.get(
                "nome",
                "",
            ).strip(),
            "telefone": request.form.get(
                "telefone",
                "",
            ).strip(),
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

        ClienteService.atualizar_cliente(
            cliente_id,
            dados,
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
    "/<int:cliente_id>/excluir"
)
def excluir(cliente_id: int):
    """
    Realiza a exclusão lógica
    de um cliente.
    """

    resultado = ClienteService.excluir_cliente(
        cliente_id
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
        url_for("cliente_web.listar")
    )