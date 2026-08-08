from flask import Blueprint, jsonify, request

from app.controllers.cliente_controller import ClienteController
from app.services.cliente_service import ClienteService


cliente_bp = Blueprint(
    "clientes",
    __name__,
    url_prefix="/clientes",
)


@cliente_bp.get("")
def listar_clientes():
    return ClienteController.listar()


@cliente_bp.post("")
def cadastrar_cliente():
    return ClienteController.cadastrar()


@cliente_bp.get("/busca")
def buscar_clientes():
    termo = request.args.get(
        "q",
        "",
        type=str,
    )

    clientes = ClienteService.buscar_para_modal(
        termo
    )

    return jsonify(
        {
            "clientes": clientes,
        }
    )


@cliente_bp.post("/rapido")
def cadastrar_cliente_rapido():
    dados = request.get_json(
        silent=True
    ) or {}

    try:
        cliente = (
            ClienteService.cadastrar_cliente_rapido(
                dados
            )
        )

        return jsonify(
            {
                "sucesso": True,
                "mensagem": (
                    f"Cliente {cliente['nome']} "
                    "cadastrado com sucesso!"
                ),
                "cliente": cliente,
            }
        ), 201

    except ValueError as erro:
        return jsonify(
            {
                "sucesso": False,
                "mensagem": str(erro),
            }
        ), 400

    except Exception:
        return jsonify(
            {
                "sucesso": False,
                "mensagem": (
                    "Não foi possível cadastrar "
                    "o cliente."
                ),
            }
        ), 500