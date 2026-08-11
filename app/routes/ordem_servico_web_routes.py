from datetime import date

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.services.cliente_service import (
    ClienteService,
)
from app.services.ordem_servico_service import (
    OrdemServicoService,
)


ordem_servico_web_bp = Blueprint(
    "ordem_servico_web",
    __name__,
    url_prefix="/painel/ordens",
)


TIPOS_PESQUISA_ORDEM = {
    "cliente",
    "telefone",
    "placa",
    "marca",
    "modelo",
}


def somente_numeros(
    valor: str,
):
    return "".join(
        caractere
        for caractere in (valor or "")
        if caractere.isdigit()
    )


def normalizar_placa(
    valor: str,
):
    return "".join(
        caractere
        for caractere in (valor or "").upper()
        if caractere.isascii()
        and caractere.isalnum()
    )


def obter_placa_historica(
    placa: str,
):
    for ordem in (
        OrdemServicoService.listar_ordens()
    ):
        if normalizar_placa(
            ordem.placa
        ) == placa:
            return ordem.placa

    return placa


def filtrar_ordens(
    ordens: list,
    pesquisa: str,
    tipo_pesquisa: str,
):
    if not pesquisa:
        return ordens

    if tipo_pesquisa == "telefone":
        termo = somente_numeros(
            pesquisa
        )[:11]

        if not termo:
            return []

        return [
            ordem
            for ordem in ordens
            if ordem.cliente
            and termo
            in somente_numeros(
                ordem.cliente.telefone
            )
        ]

    if tipo_pesquisa == "placa":
        termo = normalizar_placa(
            pesquisa
        )[:7]

        if not termo:
            return []

        return [
            ordem
            for ordem in ordens
            if termo
            in normalizar_placa(
                ordem.placa
            )
        ]

    termo = pesquisa.casefold().strip()

    if tipo_pesquisa == "marca":
        return [
            ordem
            for ordem in ordens
            if termo
            in (ordem.marca or "").casefold()
        ]

    if tipo_pesquisa == "modelo":
        return [
            ordem
            for ordem in ordens
            if termo
            in (ordem.modelo or "").casefold()
        ]

    return [
        ordem
        for ordem in ordens
        if ordem.cliente
        and termo
        in (ordem.cliente.nome or "").casefold()
    ]


def converter_decimal(
    valor: str,
):
    """
    Converte um valor textual em número decimal.
    """

    if not valor:
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    try:
        return float(
            valor.replace(",", ".")
        )

    except (TypeError, ValueError) as erro:
        raise ValueError(
            "Informe uma quantidade de litros válida."
        ) from erro


def converter_inteiro_opcional(
    valor: str,
):
    """
    Converte um campo opcional em número inteiro.
    """

    if valor in (
        None,
        "",
    ):
        return None

    try:
        return int(
            valor
        )

    except (TypeError, ValueError) as erro:
        raise ValueError(
            "Informe um valor inteiro válido."
        ) from erro


def converter_inteiro_obrigatorio(
    valor,
    nome_campo: str,
):
    """
    Converte campos obrigatórios em número inteiro.
    """

    if valor in (
        None,
        "",
    ):
        raise ValueError(
            f"Informe {nome_campo}."
        )

    try:
        return int(
            valor
        )

    except (TypeError, ValueError) as erro:
        raise ValueError(
            f"Informe {nome_campo} válido."
        ) from erro


def converter_data_formulario(
    valor: str,
):
    """
    Converte a data recebida do formulário.
    """

    if not valor:
        return None

    try:
        return date.fromisoformat(
            valor
        )

    except ValueError as erro:
        raise ValueError(
            "Informe uma data de serviço válida."
        ) from erro


def montar_dados_formulario(
    simplificado: bool = False,
):
    """
    Organiza e converte os dados enviados
    pelo formulário de ordem de serviço.
    """

    cliente_id = (
        request.form.get(
            "cliente_id",
            "",
        )
        .strip()
    )

    quilometragem = (
        request.form.get(
            "quilometragem",
            "",
        )
        .strip()
    )

    placa_recebida = request.form.get(
        "placa",
        "",
    )

    troca_oleo = (
        request.form.get("troca_oleo")
        == "on"
    )

    filtro_ar = (
        request.form.get("filtro_ar")
        == "on"
    )

    filtro_combustivel = (
        request.form.get(
            "filtro_combustivel"
        )
        == "on"
    )

    if simplificado:
        servicos = []

        if troca_oleo:
            servicos.append("Troca de óleo")

        if filtro_ar:
            servicos.append("Filtro de ar")

        if filtro_combustivel:
            servicos.append(
                "Filtro de gasolina"
            )

        placa = normalizar_placa(
            placa_recebida
        )[:7]
        marca = "Não informada"
        modelo = "Não informado"
        ano = None
        data_servico = date.today()
        descricao_servico = ", ".join(
            servicos
        )
        tipo_oleo = None
        quantidade_litros = None
        filtro_oleo = False
    else:
        placa = placa_recebida.strip().upper()
        marca = request.form.get(
            "marca",
            "",
        ).strip()
        modelo = request.form.get(
            "modelo",
            "",
        ).strip()
        ano = converter_inteiro_opcional(
            request.form.get(
                "ano",
                "",
            )
        )
        data_servico = converter_data_formulario(
            request.form.get(
                "data_servico",
                "",
            )
        )
        descricao_servico = request.form.get(
            "descricao_servico",
            "",
        ).strip()
        tipo_oleo = (
            request.form.get(
                "tipo_oleo",
                "",
            ).strip()
            or None
        )
        quantidade_litros = converter_decimal(
            request.form.get(
                "quantidade_litros",
                "",
            )
        )
        filtro_oleo = (
            request.form.get("filtro_oleo")
            == "on"
        )

    return {
        "cliente_id": (
            converter_inteiro_obrigatorio(
                cliente_id,
                "um cliente",
            )
            if cliente_id
            else None
        ),
        "placa": placa,
        "marca": marca,
        "modelo": modelo,
        "ano": ano,
        "quilometragem": (
            converter_inteiro_obrigatorio(
                quilometragem,
                "uma quilometragem",
            )
        ),
        "data_servico": data_servico,
        "descricao_servico": descricao_servico,
        "tipo_oleo": tipo_oleo,
        "quantidade_litros": quantidade_litros,
        "filtro_oleo": filtro_oleo,
        "filtro_ar": filtro_ar,
        "filtro_combustivel": filtro_combustivel,
        "observacoes": (
            request.form.get(
                "observacoes",
                "",
            )
            .strip()
            or None
        ),
    }


def validar_dados(
    dados: dict,
    simplificado: bool = False,
):
    """
    Valida os campos obrigatórios da ordem.
    """

    if not dados.get(
        "cliente_id"
    ):
        return (
            "Selecione um cliente."
        )

    if not dados.get(
        "placa"
    ):
        return (
            "Informe a placa do veículo."
        )

    if not dados.get(
        "marca"
    ):
        return (
            "Informe a marca do veículo."
        )

    if not dados.get(
        "modelo"
    ):
        return (
            "Informe o modelo do veículo."
        )

    quilometragem = dados.get(
        "quilometragem"
    )

    if quilometragem is None:
        return (
            "Informe a quilometragem do veículo."
        )

    if quilometragem < 0:
        return (
            "A quilometragem não pode ser negativa."
        )

    if not dados.get(
        "data_servico"
    ):
        return (
            "Informe a data do serviço."
        )

    if not dados.get(
        "descricao_servico"
    ):
        if simplificado:
            return (
                "Selecione ao menos um serviço realizado."
            )

        return (
            "Informe a descrição do serviço."
        )

    return None


def buscar_cliente(
    cliente_id,
):
    """
    Busca o cliente selecionado.
    """

    if not cliente_id:
        return None

    try:
        cliente_id = int(
            cliente_id
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    cliente = (
        ClienteService
        .buscar_por_id(
            cliente_id
        )
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

    ordens = (
        OrdemServicoService
        .listar_ordens()
    )

    pesquisa = (
        request.args.get(
            "pesquisa",
            "",
        )
        .strip()
    )

    tipo_pesquisa = request.args.get(
        "tipo_pesquisa",
        "cliente",
    ).strip().lower()

    if (
        tipo_pesquisa
        not in TIPOS_PESQUISA_ORDEM
    ):
        tipo_pesquisa = "cliente"

    ordens = filtrar_ordens(
        ordens,
        pesquisa,
        tipo_pesquisa,
    )

    return render_template(
        "ordens/lista.html",
        ordens=ordens,
        pesquisa=pesquisa,
        tipo_pesquisa=tipo_pesquisa,
    )


@ordem_servico_web_bp.get(
    "/<int:ordem_id>/detalhes"
)
def detalhes(
    ordem_id: int,
):
    ordem = (
        OrdemServicoService
        .buscar_por_id(
            ordem_id
        )
    )

    if ordem is None:
        flash(
            (
                "Ordem de serviço "
                "não encontrada."
            ),
            "danger",
        )

        return redirect(
            url_for(
                "ordem_servico_web.listar"
            )
        )

    return render_template(
        "ordens/detalhes.html",
        ordem=ordem,
    )


@ordem_servico_web_bp.route(
    "/nova",
    methods=[
        "GET",
        "POST",
    ],
)
def cadastrar():
    """
    Exibe o formulário completo e cadastra
    uma nova ordem de serviço.
    """

    cliente_id = (
        request.args.get(
            "cliente_id"
        )
    )

    cliente_selecionado = (
        buscar_cliente(
            cliente_id
        )
    )

    data_servico = (
        date.today()
    )

    dados_formulario = None

    if request.method == "POST":
        try:
            dados = (
                montar_dados_formulario(
                    simplificado=True
                )
            )

            dados_formulario = dados

            data_servico = (
                dados.get(
                    "data_servico"
                )
                or date.today()
            )

            cliente_selecionado = (
                buscar_cliente(
                    dados.get(
                        "cliente_id"
                    )
                )
            )

            mensagem_erro = (
                validar_dados(
                    dados,
                    simplificado=True,
                )
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
                    data_servico=(
                        data_servico
                    ),
                    dados_formulario=(
                        dados_formulario
                    ),
                )

            dados["placa"] = (
                obter_placa_historica(
                    dados["placa"]
                )
            )

            OrdemServicoService \
                .cadastrar_ordem(
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

        except ValueError as erro:
            #
            # Aqui entra também a mensagem do
            # ValidacaoHistoricoService.
            #
            # Exemplo:
            #
            # "Em 08/08/2026, o veículo já
            # possuía 71.000 km."
            #
            flash(
                str(
                    erro
                ),
                "danger",
            )

            return render_template(
                "ordens/formulario.html",
                ordem=None,
                cliente_selecionado=(
                    cliente_selecionado
                ),
                data_servico=(
                    data_servico
                ),
                dados_formulario=(
                    dados_formulario
                ),
            )

        except TypeError as erro:
            print(
                (
                    "Erro de tipo ao cadastrar "
                    f"ordem de serviço: {erro}"
                )
            )

            flash(
                (
                    "Verifique os valores "
                    "informados no formulário."
                ),
                "danger",
            )

            return render_template(
                "ordens/formulario.html",
                ordem=None,
                cliente_selecionado=(
                    cliente_selecionado
                ),
                data_servico=(
                    data_servico
                ),
                dados_formulario=(
                    dados_formulario
                ),
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
                data_servico=(
                    data_servico
                ),
                dados_formulario=(
                    dados_formulario
                ),
            )

    return render_template(
        "ordens/formulario.html",
        ordem=None,
        cliente_selecionado=(
            cliente_selecionado
        ),
        data_servico=(
            data_servico
        ),
        dados_formulario=(
            dados_formulario
        ),
    )


@ordem_servico_web_bp.route(
    "/<int:ordem_id>/editar",
    methods=[
        "GET",
        "POST",
    ],
)
def editar(
    ordem_id: int,
):
    """
    Exibe e atualiza uma ordem existente.
    """

    ordem = (
        OrdemServicoService
        .buscar_por_id(
            ordem_id
        )
    )

    if ordem is None:
        flash(
            (
                "Ordem de serviço "
                "não encontrada."
            ),
            "danger",
        )

        return redirect(
            url_for(
                "ordem_servico_web.listar"
            )
        )

    cliente_id = request.args.get(
        "cliente_id"
    )

    cliente_selecionado = (
        buscar_cliente(cliente_id)
        or ordem.cliente
    )

    dados_formulario = None

    if request.method == "POST":
        try:
            dados = (
                montar_dados_formulario()
            )

            dados_formulario = dados

            cliente_selecionado = (
                buscar_cliente(
                    dados.get(
                        "cliente_id"
                    )
                )
            )

            mensagem_erro = (
                validar_dados(
                    dados
                )
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
                        dados.get(
                            "data_servico"
                        )
                        or ordem.data_servico
                    ),
                    dados_formulario=(
                        dados_formulario
                    ),
                )

            resultado = (
                OrdemServicoService
                .atualizar_ordem(
                    ordem_id,
                    dados,
                )
            )

            if resultado is None:
                flash(
                    (
                        "Ordem de serviço "
                        "não encontrada."
                    ),
                    "danger",
                )

                return redirect(
                    url_for(
                        "ordem_servico_web.listar"
                    )
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

        except ValueError as erro:
            #
            # Mostra diretamente a mensagem
            # gerada pelo validador.
            #
            flash(
                str(
                    erro
                ),
                "danger",
            )

            return render_template(
                "ordens/formulario.html",
                ordem=ordem,
                cliente_selecionado=(
                    cliente_selecionado
                ),
                data_servico=(
                    (
                        dados_formulario
                        or {}
                    ).get(
                        "data_servico",
                        ordem.data_servico,
                    )
                ),
                dados_formulario=(
                    dados_formulario
                ),
            )

        except TypeError as erro:
            print(
                (
                    "Erro de tipo ao atualizar "
                    f"ordem de serviço: {erro}"
                )
            )

            flash(
                (
                    "Verifique os valores "
                    "informados no formulário."
                ),
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
                dados_formulario=(
                    dados_formulario
                ),
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
                data_servico=(
                    ordem.data_servico
                ),
                dados_formulario=(
                    dados_formulario
                ),
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
        dados_formulario=(
            dados_formulario
        ),
    )


@ordem_servico_web_bp.post(
    "/<int:ordem_id>/excluir"
)
def excluir(
    ordem_id: int,
):
    """
    Exclui uma ordem de serviço e trata
    possíveis erros de forma amigável.
    """

    try:
        resultado = (
            OrdemServicoService
            .excluir_ordem(
                ordem_id
            )
        )

        if resultado is None:
            flash(
                (
                    "Ordem de serviço "
                    "não encontrada."
                ),
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

    except ValueError as erro:
        flash(
            str(
                erro
            ),
            "danger",
        )

    except Exception as erro:
        print(
            (
                "Erro ao excluir ordem "
                f"de serviço: {erro}"
            )
        )

        flash(
            (
                "Não foi possível excluir "
                "a ordem de serviço."
            ),
            "danger",
        )

    return redirect(
        url_for(
            "ordem_servico_web.listar"
        )
    )
