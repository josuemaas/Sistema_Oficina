from app.models.cliente import Cliente
from app.repositories.cliente_repository import ClienteRepository


class ClienteService:
    """
    Contém as regras de negócio relacionadas aos clientes.
    """

    @staticmethod
    def listar_clientes():
        """
        Retorna todos os clientes cadastrados.
        """

        return ClienteRepository.listar()

    @staticmethod
    def buscar_cliente(cliente_id: int):
        """
        Busca um cliente pelo ID.

        Este método é mantido para compatibilidade
        com partes antigas do sistema.
        """

        return ClienteRepository.buscar_por_id(
            cliente_id
        )

    @staticmethod
    def buscar_por_id(cliente_id: int):
        """
        Busca um cliente pelo ID.

        Este método é utilizado pelas rotas
        da interface web.
        """

        return ClienteRepository.buscar_por_id(
            cliente_id
        )

    @staticmethod
    def cadastrar_cliente(dados: dict):
        """
        Cadastra um novo cliente.
        """

        cliente = Cliente(
            nome=dados["nome"],
            telefone=dados["telefone"],
            email=dados.get("email"),
            observacoes=dados.get("observacoes"),
            recebe_notificacao=dados.get(
                "recebe_notificacao",
                False,
            ),
        )

        return ClienteRepository.salvar(
            cliente
        )

    @staticmethod
    def atualizar_cliente(
        cliente_id: int,
        dados: dict,
    ):
        """
        Atualiza os dados de um cliente existente.
        """

        cliente = ClienteRepository.buscar_por_id(
            cliente_id
        )

        if cliente is None:
            return None

        cliente.nome = dados.get(
            "nome",
            cliente.nome,
        )

        cliente.telefone = dados.get(
            "telefone",
            cliente.telefone,
        )

        cliente.email = dados.get(
            "email",
            cliente.email,
        )

        cliente.observacoes = dados.get(
            "observacoes",
            cliente.observacoes,
        )

        cliente.recebe_notificacao = dados.get(
            "recebe_notificacao",
            cliente.recebe_notificacao,
        )

        if "ativo" in dados:
            cliente.ativo = dados["ativo"]

        ClienteRepository.atualizar()

        return cliente

    @staticmethod
    def excluir_cliente(cliente_id: int):
        """
        Realiza a exclusão lógica de um cliente.
        """

        cliente = ClienteRepository.buscar_por_id(
            cliente_id
        )

        if cliente is None:
            return None

        ClienteRepository.excluir(
            cliente
        )

        return True