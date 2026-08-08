from flask import request

from app.services.cliente_service import ClienteService


class ClienteController:
    """
    Controller responsável por receber
    as requisições HTTP relacionadas aos clientes.
    """

    @staticmethod
    def listar():
        clientes = ClienteService.listar_clientes()

        resultado = []

        for cliente in clientes:
            resultado.append(
                {
                    "id": cliente.id,
                    "nome": cliente.nome,
                    "telefone": cliente.telefone,
                    "email": cliente.email,
                    "ativo": cliente.ativo,
                }
            )

        return resultado, 200

    @staticmethod
    def cadastrar():
        dados = request.get_json()

        cliente = ClienteService.cadastrar_cliente(dados)

        return {
            "mensagem": "Cliente cadastrado com sucesso.",
            "id": cliente.id,
        }, 201