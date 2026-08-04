from flask import request

from app.services.ordem_servico_service import OrdemServicoService


class OrdemServicoController:
    """
    Controller responsável pelas requisições
    relacionadas às ordens de serviço.
    """

    @staticmethod
    def listar():
        ordens = OrdemServicoService.listar_ordens()

        resultado = []

        for ordem in ordens:
            resultado.append(
                {
                    "id": ordem.id,
                    "veiculo_id": ordem.veiculo_id,
                    "data_servico": ordem.data_servico.isoformat(),
                    "quilometragem": ordem.quilometragem,
                    "descricao_servico": ordem.descricao_servico,
                    "tipo_oleo": ordem.tipo_oleo,
                    "quantidade_litros": (
                        float(ordem.quantidade_litros)
                        if ordem.quantidade_litros is not None
                        else None
                    ),
                    "filtro_oleo": ordem.filtro_oleo,
                    "filtro_ar": ordem.filtro_ar,
                    "filtro_combustivel": ordem.filtro_combustivel,
                    "proxima_troca_km": ordem.proxima_troca_km,
                    "proxima_troca_data": (
                        ordem.proxima_troca_data.isoformat()
                        if ordem.proxima_troca_data
                        else None
                    ),
                    "observacoes": ordem.observacoes,
                }
            )

        return resultado, 200

    @staticmethod
    def buscar_por_id(ordem_id: int):
        ordem = OrdemServicoService.buscar_por_id(ordem_id)

        if ordem is None:
            return {
                "mensagem": "Ordem de serviço não encontrada."
            }, 404

        return {
            "id": ordem.id,
            "veiculo_id": ordem.veiculo_id,
            "data_servico": ordem.data_servico.isoformat(),
            "quilometragem": ordem.quilometragem,
            "descricao_servico": ordem.descricao_servico,
            "tipo_oleo": ordem.tipo_oleo,
            "quantidade_litros": (
                float(ordem.quantidade_litros)
                if ordem.quantidade_litros is not None
                else None
            ),
            "filtro_oleo": ordem.filtro_oleo,
            "filtro_ar": ordem.filtro_ar,
            "filtro_combustivel": ordem.filtro_combustivel,
            "proxima_troca_km": ordem.proxima_troca_km,
            "proxima_troca_data": (
                ordem.proxima_troca_data.isoformat()
                if ordem.proxima_troca_data
                else None
            ),
            "observacoes": ordem.observacoes,
        }, 200

    @staticmethod
    def cadastrar():
        dados = request.get_json()

        ordem = OrdemServicoService.cadastrar_ordem(dados)

        return {
            "mensagem": "Ordem de serviço cadastrada com sucesso.",
            "id": ordem.id,
        }, 201

    @staticmethod
    def atualizar(ordem_id: int):
        dados = request.get_json()

        ordem = OrdemServicoService.atualizar_ordem(
            ordem_id,
            dados,
        )

        if ordem is None:
            return {
                "mensagem": "Ordem de serviço não encontrada."
            }, 404

        return {
            "mensagem": "Ordem de serviço atualizada com sucesso."
        }, 200

    @staticmethod
    def excluir(ordem_id: int):
        resultado = OrdemServicoService.excluir_ordem(ordem_id)

        if resultado is None:
            return {
                "mensagem": "Ordem de serviço não encontrada."
            }, 404

        return {
            "mensagem": "Ordem de serviço excluída com sucesso."
        }, 200