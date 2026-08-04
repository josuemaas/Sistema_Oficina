import calendar
from datetime import date

from app.models.ordem_servico import OrdemServico
from app.repositories.ordem_servico_repository import (
    OrdemServicoRepository,
)


class OrdemServicoService:
    """
    Responsável pelas regras de negócio
    das ordens de serviço.
    """

    @staticmethod
    def adicionar_meses(
        data_base: date,
        quantidade_meses: int,
    ) -> date:
        """
        Adiciona uma quantidade de meses a uma data,
        respeitando o calendário.
        """

        mes_calculado = (
            data_base.month - 1 + quantidade_meses
        )

        ano = (
            data_base.year
            + mes_calculado // 12
        )

        mes = (
            mes_calculado % 12
            + 1
        )

        ultimo_dia_mes = calendar.monthrange(
            ano,
            mes,
        )[1]

        dia = min(
            data_base.day,
            ultimo_dia_mes,
        )

        return date(
            ano,
            mes,
            dia,
        )

    @staticmethod
    def listar_ordens():
        """
        Retorna todas as ordens de serviço.
        """

        return OrdemServicoRepository.listar()

    @staticmethod
    def buscar_por_id(ordem_id: int):
        """
        Busca uma ordem de serviço pelo ID.
        """

        return OrdemServicoRepository.buscar_por_id(
            ordem_id
        )

    @staticmethod
    def cadastrar_ordem(dados: dict):
        """
        Cadastra uma nova ordem.

        A data do serviço é preenchida automaticamente
        com a data atual.

        A próxima troca por data é definida
        automaticamente para seis meses depois.
        """

        data_servico = date.today()

        proxima_troca_data = (
            OrdemServicoService.adicionar_meses(
                data_servico,
                6,
            )
        )

        ordem = OrdemServico(
            cliente_id=dados["cliente_id"],
            placa=dados["placa"].strip().upper(),
            marca=dados["marca"].strip(),
            modelo=dados["modelo"].strip(),
            ano=dados.get("ano"),
            data_servico=data_servico,
            quilometragem=dados["quilometragem"],
            descricao_servico=dados[
                "descricao_servico"
            ],
            tipo_oleo=dados.get("tipo_oleo"),
            quantidade_litros=dados.get(
                "quantidade_litros"
            ),
            filtro_oleo=dados.get(
                "filtro_oleo",
                False,
            ),
            filtro_ar=dados.get(
                "filtro_ar",
                False,
            ),
            filtro_combustivel=dados.get(
                "filtro_combustivel",
                False,
            ),
            proxima_troca_km=dados.get(
                "proxima_troca_km"
            ),
            proxima_troca_data=(
                proxima_troca_data
            ),
            observacoes=dados.get(
                "observacoes"
            ),
        )

        return OrdemServicoRepository.salvar(
            ordem
        )

    @staticmethod
    def atualizar_ordem(
        ordem_id: int,
        dados: dict,
    ):
        """
        Atualiza uma ordem existente.

        A data original do atendimento e a data
        automática da próxima troca são preservadas.
        """

        ordem = (
            OrdemServicoRepository.buscar_por_id(
                ordem_id
            )
        )

        if ordem is None:
            return None

        ordem.cliente_id = dados.get(
            "cliente_id",
            ordem.cliente_id,
        )

        placa = dados.get(
            "placa",
            ordem.placa,
        )

        ordem.placa = placa.strip().upper()

        ordem.marca = dados.get(
            "marca",
            ordem.marca,
        )

        ordem.modelo = dados.get(
            "modelo",
            ordem.modelo,
        )

        ordem.ano = dados.get(
            "ano",
            ordem.ano,
        )

        ordem.quilometragem = dados.get(
            "quilometragem",
            ordem.quilometragem,
        )

        ordem.descricao_servico = dados.get(
            "descricao_servico",
            ordem.descricao_servico,
        )

        ordem.tipo_oleo = dados.get(
            "tipo_oleo",
            ordem.tipo_oleo,
        )

        ordem.quantidade_litros = dados.get(
            "quantidade_litros",
            ordem.quantidade_litros,
        )

        ordem.filtro_oleo = dados.get(
            "filtro_oleo",
            ordem.filtro_oleo,
        )

        ordem.filtro_ar = dados.get(
            "filtro_ar",
            ordem.filtro_ar,
        )

        ordem.filtro_combustivel = dados.get(
            "filtro_combustivel",
            ordem.filtro_combustivel,
        )

        ordem.proxima_troca_km = dados.get(
            "proxima_troca_km",
            ordem.proxima_troca_km,
        )

        ordem.observacoes = dados.get(
            "observacoes",
            ordem.observacoes,
        )

        OrdemServicoRepository.atualizar()

        return ordem

    @staticmethod
    def excluir_ordem(ordem_id: int):
        """
        Exclui uma ordem de serviço.
        """

        ordem = (
            OrdemServicoRepository.buscar_por_id(
                ordem_id
            )
        )

        if ordem is None:
            return None

        OrdemServicoRepository.excluir(
            ordem
        )

        return True