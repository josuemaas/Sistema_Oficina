from flask import Blueprint

from app.controllers.ordem_servico_controller import OrdemServicoController


ordem_servico_bp = Blueprint(
    "ordem_servico",
    __name__,
    url_prefix="/ordens",
)


@ordem_servico_bp.get("")
def listar():
    return OrdemServicoController.listar()


@ordem_servico_bp.get("/<int:ordem_id>")
def buscar(ordem_id: int):
    return OrdemServicoController.buscar_por_id(ordem_id)


@ordem_servico_bp.post("")
def cadastrar():
    return OrdemServicoController.cadastrar()


@ordem_servico_bp.put("/<int:ordem_id>")
def atualizar(ordem_id: int):
    return OrdemServicoController.atualizar(ordem_id)


@ordem_servico_bp.delete("/<int:ordem_id>")
def excluir(ordem_id: int):
    return OrdemServicoController.excluir(ordem_id)