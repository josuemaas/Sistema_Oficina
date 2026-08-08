import calendar
from datetime import date

from app.models.ordem_servico import OrdemServico
from app.repositories.ordem_servico_repository import OrdemServicoRepository
from app.services.notificacao_service import NotificacaoService


class OrdemServicoService:
    @staticmethod
    def adicionar_meses(
        data_base: date,
        quantidade_meses: int,
    ) -> date:
        mes_calculado = (
            data_base.month
            - 1
            + quantidade_meses
        )

        ano = (
            data_base.year
            + mes_calculado // 12
        )

        mes = mes_calculado % 12 + 1

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
    def _normalizar_texto(
        valor,
        nome_campo: str,
    ):
        if valor is None:
            raise ValueError(
                f"O campo '{nome_campo}' é obrigatório."
            )

        texto = str(valor).strip()

        if not texto:
            raise ValueError(
                f"O campo '{nome_campo}' é obrigatório."
            )

        return texto

    @staticmethod
    def _converter_int(
        valor,
        nome_campo: str,
        permitir_vazio: bool = False,
    ):
        if valor in (None, ""):
            if permitir_vazio:
                return None

            raise ValueError(
                f"O campo '{nome_campo}' é obrigatório."
            )

        if isinstance(valor, bool):
            raise ValueError(
                f"O campo '{nome_campo}' "
                "deve ser um número inteiro."
            )

        try:
            return int(valor)

        except (TypeError, ValueError) as erro:
            raise ValueError(
                f"O campo '{nome_campo}' "
                "deve ser um número inteiro."
            ) from erro

    @staticmethod
    def _converter_numero(
        valor,
        nome_campo: str,
        permitir_vazio: bool = False,
    ):
        if valor in (None, ""):
            if permitir_vazio:
                return None

            raise ValueError(
                f"O campo '{nome_campo}' é obrigatório."
            )

        try:
            return float(valor)

        except (TypeError, ValueError) as erro:
            raise ValueError(
                f"O campo '{nome_campo}' "
                "deve ser numérico."
            ) from erro

    @staticmethod
    def _normalizar_booleano(
        valor,
        nome_campo: str,
        padrao: bool = False,
    ):
        if valor is None:
            return padrao

        if isinstance(valor, bool):
            return valor

        if isinstance(valor, str):
            texto = valor.strip().lower()

            if texto in {
                "true",
                "1",
                "sim",
                "s",
            }:
                return True

            if texto in {
                "false",
                "0",
                "nao",
                "não",
                "n",
            }:
                return False

        return bool(valor)

    @staticmethod
    def listar_ordens():
        return OrdemServicoRepository.listar()

    @staticmethod
    def buscar_por_id(ordem_id: int):
        return OrdemServicoRepository.buscar_por_id(
            ordem_id
        )

    @staticmethod
    def cadastrar_ordem(dados: dict):
        if not isinstance(dados, dict):
            raise ValueError(
                "Envie um JSON válido com "
                "os dados da ordem."
            )

        cliente_id = (
            OrdemServicoService._converter_int(
                dados.get("cliente_id"),
                "cliente_id",
            )
        )

        placa = (
            OrdemServicoService._normalizar_texto(
                dados.get("placa"),
                "placa",
            )
            .upper()
        )

        marca = (
            OrdemServicoService._normalizar_texto(
                dados.get("marca"),
                "marca",
            )
        )

        modelo = (
            OrdemServicoService._normalizar_texto(
                dados.get("modelo"),
                "modelo",
            )
        )

        quilometragem = (
            OrdemServicoService._converter_int(
                dados.get("quilometragem"),
                "quilometragem",
            )
        )

        descricao_servico = (
            OrdemServicoService._normalizar_texto(
                dados.get("descricao_servico"),
                "descricao_servico",
            )
        )

        ano = (
            OrdemServicoService._converter_int(
                dados.get("ano"),
                "ano",
                True,
            )
        )

        quantidade_litros = (
            OrdemServicoService._converter_numero(
                dados.get("quantidade_litros"),
                "quantidade_litros",
                True,
            )
        )

        proxima_troca_km = (
            OrdemServicoService._converter_int(
                dados.get("proxima_troca_km"),
                "proxima_troca_km",
                True,
            )
        )

        data_servico = date.today()

        proxima_troca_data = (
            OrdemServicoService.adicionar_meses(
                data_servico,
                6,
            )
        )

        ordem = OrdemServico(
            cliente_id=cliente_id,
            placa=placa,
            marca=marca,
            modelo=modelo,
            ano=ano,
            data_servico=data_servico,
            quilometragem=quilometragem,
            descricao_servico=(
                descricao_servico
            ),
            tipo_oleo=(
                dados.get("tipo_oleo")
            ),
            quantidade_litros=(
                quantidade_litros
            ),
            filtro_oleo=(
                OrdemServicoService
                ._normalizar_booleano(
                    dados.get("filtro_oleo"),
                    "filtro_oleo",
                )
            ),
            filtro_ar=(
                OrdemServicoService
                ._normalizar_booleano(
                    dados.get("filtro_ar"),
                    "filtro_ar",
                )
            ),
            filtro_combustivel=(
                OrdemServicoService
                ._normalizar_booleano(
                    dados.get(
                        "filtro_combustivel"
                    ),
                    "filtro_combustivel",
                )
            ),
            proxima_troca_km=(
                proxima_troca_km
            ),
            proxima_troca_data=(
                proxima_troca_data
            ),
            observacoes=(
                dados.get("observacoes")
            ),
        )

        try:
            OrdemServicoRepository.adicionar(
                ordem
            )

            NotificacaoService.criar_para_ordem(
                ordem
            )

            OrdemServicoRepository.confirmar()

            return ordem

        except Exception:
            OrdemServicoRepository.desfazer()
            raise

    @staticmethod
    def atualizar_ordem(
        ordem_id: int,
        dados: dict,
    ):
        if not isinstance(dados, dict):
            raise ValueError(
                "Envie um JSON válido com "
                "os dados da ordem."
            )

        ordem = (
            OrdemServicoRepository.buscar_por_id(
                ordem_id
            )
        )

        if ordem is None:
            return None

        if "cliente_id" in dados:
            ordem.cliente_id = (
                OrdemServicoService._converter_int(
                    dados["cliente_id"],
                    "cliente_id",
                )
            )

        if "placa" in dados:
            ordem.placa = (
                OrdemServicoService._normalizar_texto(
                    dados["placa"],
                    "placa",
                )
                .upper()
            )

        if "marca" in dados:
            ordem.marca = (
                OrdemServicoService._normalizar_texto(
                    dados["marca"],
                    "marca",
                )
            )

        if "modelo" in dados:
            ordem.modelo = (
                OrdemServicoService._normalizar_texto(
                    dados["modelo"],
                    "modelo",
                )
            )

        if "ano" in dados:
            ordem.ano = (
                OrdemServicoService._converter_int(
                    dados["ano"],
                    "ano",
                    True,
                )
            )

        if "quilometragem" in dados:
            ordem.quilometragem = (
                OrdemServicoService._converter_int(
                    dados["quilometragem"],
                    "quilometragem",
                )
            )

        if "descricao_servico" in dados:
            ordem.descricao_servico = (
                OrdemServicoService
                ._normalizar_texto(
                    dados["descricao_servico"],
                    "descricao_servico",
                )
            )

        if "tipo_oleo" in dados:
            ordem.tipo_oleo = (
                dados["tipo_oleo"]
            )

        if "quantidade_litros" in dados:
            ordem.quantidade_litros = (
                OrdemServicoService
                ._converter_numero(
                    dados["quantidade_litros"],
                    "quantidade_litros",
                    True,
                )
            )

        if "filtro_oleo" in dados:
            ordem.filtro_oleo = (
                OrdemServicoService
                ._normalizar_booleano(
                    dados["filtro_oleo"],
                    "filtro_oleo",
                )
            )

        if "filtro_ar" in dados:
            ordem.filtro_ar = (
                OrdemServicoService
                ._normalizar_booleano(
                    dados["filtro_ar"],
                    "filtro_ar",
                )
            )

        if "filtro_combustivel" in dados:
            ordem.filtro_combustivel = (
                OrdemServicoService
                ._normalizar_booleano(
                    dados[
                        "filtro_combustivel"
                    ],
                    "filtro_combustivel",
                )
            )

        if "proxima_troca_km" in dados:
            ordem.proxima_troca_km = (
                OrdemServicoService
                ._converter_int(
                    dados["proxima_troca_km"],
                    "proxima_troca_km",
                    True,
                )
            )

        if "observacoes" in dados:
            ordem.observacoes = (
                dados["observacoes"]
            )

        OrdemServicoRepository.atualizar()

        return ordem

    @staticmethod
    def excluir_ordem(ordem_id: int):
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