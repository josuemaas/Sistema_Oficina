from app.models.cliente import Cliente
from app.repositories.cliente_repository import ClienteRepository


class ClienteService:
    @staticmethod
    def _texto(valor):
        if valor is None:
            return ""

        return str(valor).strip()

    @staticmethod
    def listar_clientes():
        return ClienteRepository.listar()

    @staticmethod
    def buscar_cliente(cliente_id: int):
        return ClienteRepository.buscar_por_id(
            cliente_id
        )

    @staticmethod
    def buscar_por_id(cliente_id: int):
        return ClienteRepository.buscar_por_id(
            cliente_id
        )

    @staticmethod
    def buscar_para_modal(
        termo: str,
        limite: int = 20,
    ):
        clientes = ClienteRepository.buscar_ativos(
            termo=termo,
            limite=limite,
        )

        return [
            {
                "id": cliente.id,
                "nome": cliente.nome,
                "cpf_cnpj": cliente.cpf_cnpj,
                "telefone": cliente.telefone,
            }
            for cliente in clientes
        ]

    @staticmethod
    def cadastrar_cliente(dados: dict):
        nome = ClienteService._texto(
            dados.get("nome")
        )

        telefone = ClienteService._texto(
            dados.get("telefone")
        )

        cpf_cnpj = (
            ClienteService._texto(
                dados.get("cpf_cnpj")
            )
            or None
        )

        email = (
            ClienteService._texto(
                dados.get("email")
            )
            or None
        )

        observacoes = (
            ClienteService._texto(
                dados.get("observacoes")
            )
            or None
        )

        if not nome:
            raise ValueError(
                "Informe o nome do cliente."
            )

        if not telefone:
            raise ValueError(
                "Informe o WhatsApp do cliente."
            )

        if cpf_cnpj:
            cliente_existente = (
                ClienteRepository.buscar_por_cpf_cnpj(
                    cpf_cnpj
                )
            )

            if cliente_existente:
                raise ValueError(
                    "Já existe um cliente com este CPF/CNPJ."
                )

        cliente = Cliente(
            nome=nome,
            cpf_cnpj=cpf_cnpj,
            telefone=telefone,
            email=email,
            observacoes=observacoes,
            recebe_notificacao=dados.get(
                "recebe_notificacao",
                False,
            ),
        )

        return ClienteRepository.salvar(
            cliente
        )

    @staticmethod
    def cadastrar_cliente_rapido(
        dados: dict,
    ):
        nome = ClienteService._texto(
            dados.get("nome")
        )

        telefone = ClienteService._texto(
            dados.get("telefone")
        )

        if not nome:
            raise ValueError(
                "Informe o nome completo."
            )

        if not telefone:
            raise ValueError(
                "Informe o WhatsApp com DDD."
            )

        cliente = Cliente(
            nome=nome,
            telefone=telefone,
            recebe_notificacao=False,
        )

        cliente = ClienteRepository.salvar(
            cliente
        )

        return {
            "id": cliente.id,
            "nome": cliente.nome,
            "cpf_cnpj": cliente.cpf_cnpj,
            "telefone": cliente.telefone,
        }

    @staticmethod
    def atualizar_cliente(
        cliente_id: int,
        dados: dict,
    ):
        cliente = ClienteRepository.buscar_por_id(
            cliente_id
        )

        if cliente is None:
            return None

        nome = ClienteService._texto(
            dados.get(
                "nome",
                cliente.nome,
            )
        )

        telefone = ClienteService._texto(
            dados.get(
                "telefone",
                cliente.telefone,
            )
        )

        cpf_cnpj = (
            ClienteService._texto(
                dados.get(
                    "cpf_cnpj",
                    cliente.cpf_cnpj,
                )
            )
            or None
        )

        email = (
            ClienteService._texto(
                dados.get(
                    "email",
                    cliente.email,
                )
            )
            or None
        )

        observacoes = (
            ClienteService._texto(
                dados.get(
                    "observacoes",
                    cliente.observacoes,
                )
            )
            or None
        )

        if not nome:
            raise ValueError(
                "Informe o nome do cliente."
            )

        if not telefone:
            raise ValueError(
                "Informe o WhatsApp do cliente."
            )

        if (
            cpf_cnpj
            and cpf_cnpj != cliente.cpf_cnpj
        ):
            cliente_existente = (
                ClienteRepository.buscar_por_cpf_cnpj(
                    cpf_cnpj
                )
            )

            if (
                cliente_existente
                and cliente_existente.id != cliente.id
            ):
                raise ValueError(
                    "Já existe um cliente com este CPF/CNPJ."
                )

        cliente.nome = nome
        cliente.telefone = telefone
        cliente.cpf_cnpj = cpf_cnpj
        cliente.email = email
        cliente.observacoes = observacoes

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
        cliente = ClienteRepository.buscar_por_id(
            cliente_id
        )

        if cliente is None:
            return None

        ClienteRepository.excluir(
            cliente
        )

        return True