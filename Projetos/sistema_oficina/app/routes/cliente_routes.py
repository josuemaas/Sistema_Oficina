from flask import Blueprint

from app.controllers.cliente_controller import ClienteController


cliente_bp = Blueprint(
    "clientes",
    __name__,
    url_prefix="/clientes",
)


@cliente_bp.get("")
def listar_clientes():
    """
    Lista todos os clientes cadastrados.
    """
    return ClienteController.listar()


@cliente_bp.post("")
def cadastrar_cliente():
    """
    Cadastra um novo cliente.
    """
    return ClienteController.cadastrar()