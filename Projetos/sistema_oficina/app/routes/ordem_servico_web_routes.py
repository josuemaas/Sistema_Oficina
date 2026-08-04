from datetime import date

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.services.cliente_service import ClienteService
from app.services.ordem_servico_service import OrdemServicoService


ordem_servico_web_bp = Blueprint(
    "ordem_servico_web",
    __name__,
    url_prefix="/painel/ordens",
)


def converter_decimal(valor: str):
    """
    Converte um valor textual em número decimal.
    """

    if not valor:
        return None

    return float(
        valor.replace(",", ".")
    )


def converter_inteiro_opcional(valor: str):
    """
    Converte um campo opcional em número inteiro.
    """

    if not valor:
        return None

    return int(valor)


def montar_dados_formulario():
    """
    Organiza os dados enviados pelo formulário.
    """

    cliente_id = request.form.get(
        "cliente_id",
        "",
    ).strip()

    return {
        "cliente_id": (
            int(cliente_id)
            if cliente_id
            else None
        ),
        "placa": request.form.get(
            "placa",
            "",
        ).strip(),
        "marca": request.form.get(
            "marca",
            "",
        ).strip(),
        "modelo": request.form.get(
            "modelo",
            "",
        ).strip(),
        "ano": converter_inteiro_opcional(
            request.form.get(
                "ano",
                "",
            )
        ),
        "quilometragem": int(
            request.form.get(
                "quilometragem",
                0,
            )
        ),
        "descricao_servico": request.form.get(
            "descricao_servico",
            "",
        ).strip(),
        "tipo_oleo": (
            request.form.get(
                "tipo_oleo",
                "",
            ).strip()
            or None
        ),
        "quantidade_litros": converter_decimal(
            request.form.get(
                "quantidade_litros",
                "",
            )
        ),
        "filtro_oleo": (
            request.form.get("filtro_oleo")
            == "on"
        ),
        "filtro_ar": (
            request.form.get("filtro_ar")
            == "on"
        ),
        "filtro_combustivel": (
            request.form.get(
                "filtro_combustivel"
            )
            == "on"
        ),
        "proxima_troca_km": (
            converter_inteiro_opcional(
                request.form.get(
                    "proxima_troca_km",
                    "",
                )
            )
        ),
        "observacoes": (
            request.form.get(
                "observacoes",
                "",
            ).strip()
            or None
        ),
    }


def validar_dados(dados: dict):
    """
    Valida os campos obrigatórios da ordem.
    """

    if not dados["cliente_id"]:
        return "Selecione um cliente."

    if not dados["placa"]:
        return "Informe a placa do veículo."

    if not dados["marca"]:
        return "Informe a marca do veículo."

    if not dados["modelo"]:
        return "Informe o modelo do veículo."

    if dados["quilometragem"] < 0:
        return (
            "A quilometragem não pode ser negativa."
        )

    if not dados["descricao_servico"]:
        return "Informe a descrição do serviço."

    return None


def buscar_cliente(cliente_id):
    """
    Busca o cliente selecionado.
    """

    if not cliente_id:
        return None

    try:
        cliente_id = int(cliente_id)
    except (TypeError, ValueError):
        return None

    cliente = ClienteService.buscar_por_id(
        cliente_id
    )

    if cliente is None:
        return None

    if not cliente.ativo:
        return None

    return cliente


@ordem_servico_web_bp.get("")
def listar():
    """
    Exibe e pesquisa as ordens de serviço.
    """

    ordens = OrdemServicoService.listar_ordens()

    pesquisa = request.args.get(
        "pesquisa",
        "",
    ).strip()

    if pesquisa:
        termo = pesquisa.lower()

        ordens = [
            ordem
            for ordem in ordens
            if (
                ordem.cliente
                and termo
                in ordem.cliente.nome.lower()
            )
            or (
                ordem.cliente
                and termo
                in ordem.cliente.telefone.lower()
            )
            or (
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
        ]

    return render_template(
        "ordens/lista.html",
        ordens=ordens,
        pesquisa=pesquisa,
    )


@ordem_servico_web_bp.route(
    "/nova",
    methods=["GET", "POST"],
)
def cadastrar():
    """
    Exibe o formulário completo e cadastra
    uma nova ordem de serviço.
    """

    cliente_id = request.args.get(
        "cliente_id"
    )

    cliente_selecionado = buscar_cliente(
        cliente_id
    )

    data_servico = date.today()

    proxima_troca_data = (
        OrdemServicoService.adicionar_meses(
            data_servico,
            6,
        )
    )

    if request.method == "POST":
        try:
            dados = montar_dados_formulario()

            cliente_selecionado = buscar_cliente(
                dados.get("cliente_id")
            )

            mensagem_erro = validar_dados(
                dados
            )

            if mensagem_erro:
                flash(
                    mensagem_erro,
                    "danger",
                )

                return render_template(
                    "ordens/formulario.html",
                    ordem=None,
                    cliente_selecionado=(
                        cliente_selecionado
                    ),
                    data_servico=data_servico,
                    proxima_troca_data=(
                        proxima_troca_data
                    ),
                )

            OrdemServicoService.cadastrar_ordem(
                dados
            )

            flash(
                (
                    "Ordem de serviço cadastrada "
                    "com sucesso."
                ),
                "success",
            )

            return redirect(
                url_for(
                    "ordem_servico_web.listar"
                )
            )

        except (ValueError, TypeError):
            flash(
                (
                    "Verifique os valores informados "
                    "no formulário."
                ),
                "danger",
            )

        except Exception as erro:
            print(
                (
                    "Erro ao cadastrar ordem "
                    f"de serviço: {erro}"
                )
            )

            flash(
                (
                    "Não foi possível cadastrar "
                    "a ordem de serviço."
                ),
                "danger",
            )

    return render_template(
        "ordens/formulario.html",
        ordem=None,
        cliente_selecionado=(
            cliente_selecionado
        ),
        data_servico=data_servico,
        proxima_troca_data=(
            proxima_troca_data
        ),
    )


@ordem_servico_web_bp.route(
    "/<int:ordem_id>/editar",
    methods=["GET", "POST"],
)
def editar(ordem_id: int):
    """
    Exibe e atualiza uma ordem existente.
    """

    ordem = OrdemServicoService.buscar_por_id(
        ordem_id
    )

    if ordem is None:
        flash(
            "Ordem de serviço não encontrada.",
            "danger",
        )

        return redirect(
            url_for(
                "ordem_servico_web.listar"
            )
        )

    cliente_selecionado = ordem.cliente

    if request.method == "POST":
        try:
            dados = montar_dados_formulario()

            cliente_selecionado = buscar_cliente(
                dados.get("cliente_id")
            )

            mensagem_erro = validar_dados(
                dados
            )

            if mensagem_erro:
                flash(
                    mensagem_erro,
                    "danger",
                )

                return render_template(
                    "ordens/formulario.html",
                    ordem=ordem,
                    cliente_selecionado=(
                        cliente_selecionado
                    ),
                    data_servico=(
                        ordem.data_servico
                    ),
                    proxima_troca_data=(
                        ordem.proxima_troca_data
                    ),
                )

            OrdemServicoService.atualizar_ordem(
                ordem_id,
                dados,
            )

            flash(
                (
                    "Ordem de serviço atualizada "
                    "com sucesso."
                ),
                "success",
            )

            return redirect(
                url_for(
                    "ordem_servico_web.listar"
                )
            )

        except (ValueError, TypeError):
            flash(
                (
                    "Verifique os valores informados "
                    "no formulário."
                ),
                "danger",
            )

        except Exception as erro:
            print(
                (
                    "Erro ao atualizar ordem "
                    f"de serviço: {erro}"
                )
            )

            flash(
                (
                    "Não foi possível atualizar "
                    "a ordem de serviço."
                ),
                "danger",
            )

    return render_template(
        "ordens/formulario.html",
        ordem=ordem,
        cliente_selecionado=(
            cliente_selecionado
        ),
        data_servico=ordem.data_servico,
        proxima_troca_data=(
            ordem.proxima_troca_data
        ),
    )


@ordem_servico_web_bp.post(
    "/<int:ordem_id>/excluir"
)
def excluir(ordem_id: int):
    """
    Exclui uma ordem de serviço.
    """

    resultado = OrdemServicoService.excluir_ordem(
        ordem_id
    )

    if resultado is None:
        flash(
            "Ordem de serviço não encontrada.",
            "danger",
        )
    else:
        flash(
            (
                "Ordem de serviço excluída "
                "com sucesso."
            ),
            "success",
        )

    return redirect(
        url_for(
            "ordem_servico_web.listar"
        )
    )