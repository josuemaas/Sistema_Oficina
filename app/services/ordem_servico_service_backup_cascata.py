from datetime import date, datetime

from app.models.ordem_servico import OrdemServico
from app.repositories.ordem_servico_repository import (
    OrdemServicoRepository,
)
from app.services.notificacao_service import (
    NotificacaoService,
)
from app.services.predicao_service import (
    PredicaoService,
)


class OrdemServicoService:
    @staticmethod
    def adicionar_meses(
        data_base: date,
        quantidade_meses: int,
    ) -> date:
        return PredicaoService.adicionar_meses(
            data_base,
            quantidade_meses,
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
    def _converter_data(
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

        if isinstance(valor, datetime):
            return valor.date()

        if isinstance(valor, date):
            return valor

        texto = str(valor).strip()

        formatos = (
            "%Y-%m-%d",
            "%d/%m/%Y",
        )

        for formato in formatos:
            try:
                return datetime.strptime(
                    texto,
                    formato,
                ).date()

            except ValueError:
                continue

        raise ValueError(
            f"O campo '{nome_campo}' "
            "deve possuir uma data válida."
        )

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
    def buscar_por_id(
        ordem_id: int,
    ):
        return (
            OrdemServicoRepository
            .buscar_por_id(
                ordem_id
            )
        )

    @staticmethod
    def calcular_previsao(
        placa: str,
        ordem_atual: OrdemServico,
    ):
        if ordem_atual.data_servico is None:
            raise ValueError(
                "A ordem precisa possuir "
                "uma data de serviço."
            )

        historico = (
            OrdemServicoRepository
            .buscar_historico_ate_data(
                placa=placa,
                data_limite=(
                    ordem_atual.data_servico
                ),
                ordem_id_ignorar=(
                    ordem_atual.id
                ),
            )
        )

        historico.append(
            ordem_atual
        )

        historico = sorted(
            historico,
            key=lambda ordem: (
                ordem.data_servico,
                ordem.id or 0,
            ),
        )

        resultado = (
            PredicaoService.calcular(
                historico
            )
        )

        if resultado is None:
            raise ValueError(
                "Não foi possível calcular "
                "a previsão da próxima troca."
            )

        return resultado

    @staticmethod
    def cadastrar_ordem(
        dados: dict,
    ):
        if not isinstance(dados, dict):
            raise ValueError(
                "Envie um JSON válido com "
                "os dados da ordem."
            )

        cliente_id = (
            OrdemServicoService
            ._converter_int(
                dados.get("cliente_id"),
                "cliente_id",
            )
        )

        placa = (
            OrdemServicoService
            ._normalizar_texto(
                dados.get("placa"),
                "placa",
            )
            .upper()
        )

        marca = (
            OrdemServicoService
            ._normalizar_texto(
                dados.get("marca"),
                "marca",
            )
        )

        modelo = (
            OrdemServicoService
            ._normalizar_texto(
                dados.get("modelo"),
                "modelo",
            )
        )

        quilometragem = (
            OrdemServicoService
            ._converter_int(
                dados.get("quilometragem"),
                "quilometragem",
            )
        )

        if quilometragem < 0:
            raise ValueError(
                "A quilometragem não pode "
                "ser negativa."
            )

        descricao_servico = (
            OrdemServicoService
            ._normalizar_texto(
                dados.get(
                    "descricao_servico"
                ),
                "descricao_servico",
            )
        )

        ano = (
            OrdemServicoService
            ._converter_int(
                dados.get("ano"),
                "ano",
                True,
            )
        )

        quantidade_litros = (
            OrdemServicoService
            ._converter_numero(
                dados.get(
                    "quantidade_litros"
                ),
                "quantidade_litros",
                True,
            )
        )

        data_servico = (
            OrdemServicoService
            ._converter_data(
                dados.get(
                    "data_servico",
                    date.today(),
                ),
                "data_servico",
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
            proxima_troca_km=None,
            proxima_troca_data=data_servico,
            observacoes=(
                dados.get("observacoes")
            ),
        )

        resultado_predicao = (
            OrdemServicoService
            .calcular_previsao(
                placa,
                ordem,
            )
        )

        ordem.proxima_troca_km = (
            resultado_predicao[
                "proxima_troca_km"
            ]
        )

        ordem.proxima_troca_data = (
            resultado_predicao[
                "proxima_troca_data"
            ]
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
            OrdemServicoRepository
            .buscar_por_id(
                ordem_id
            )
        )

        if ordem is None:
            return None

        if "cliente_id" in dados:
            ordem.cliente_id = (
                OrdemServicoService
                ._converter_int(
                    dados["cliente_id"],
                    "cliente_id",
                )
            )

        if "placa" in dados:
            ordem.placa = (
                OrdemServicoService
                ._normalizar_texto(
                    dados["placa"],
                    "placa",
                )
                .upper()
            )

        if "marca" in dados:
            ordem.marca = (
                OrdemServicoService
                ._normalizar_texto(
                    dados["marca"],
                    "marca",
                )
            )

        if "modelo" in dados:
            ordem.modelo = (
                OrdemServicoService
                ._normalizar_texto(
                    dados["modelo"],
                    "modelo",
                )
            )

        if "ano" in dados:
            ordem.ano = (
                OrdemServicoService
                ._converter_int(
                    dados["ano"],
                    "ano",
                    True,
                )
            )

        if "data_servico" in dados:
            ordem.data_servico = (
                OrdemServicoService
                ._converter_data(
                    dados["data_servico"],
                    "data_servico",
                )
            )

        if "quilometragem" in dados:
            ordem.quilometragem = (
                OrdemServicoService
                ._converter_int(
                    dados["quilometragem"],
                    "quilometragem",
                )
            )

            if ordem.quilometragem < 0:
                raise ValueError(
                    "A quilometragem não pode "
                    "ser negativa."
                )

        if "descricao_servico" in dados:
            ordem.descricao_servico = (
                OrdemServicoService
                ._normalizar_texto(
                    dados[
                        "descricao_servico"
                    ],
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
                    dados[
                        "quantidade_litros"
                    ],
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

        if "observacoes" in dados:
            ordem.observacoes = (
                dados["observacoes"]
            )

        resultado_predicao = (
            OrdemServicoService
            .calcular_previsao(
                ordem.placa,
                ordem,
            )
        )

        ordem.proxima_troca_km = (
            resultado_predicao[
                "proxima_troca_km"
            ]
        )

        ordem.proxima_troca_data = (
            resultado_predicao[
                "proxima_troca_data"
            ]
        )

        try:
            NotificacaoService.sincronizar_com_ordem(
                ordem
            )

            OrdemServicoRepository.atualizar()

            return ordem

        except Exception:
            OrdemServicoRepository.desfazer()
            raise

    @staticmethod
    def excluir_ordem(
        ordem_id: int,
    ):
        ordem = (
            OrdemServicoRepository
            .buscar_por_id(
                ordem_id
            )
        )

        if ordem is None:
            return None

        OrdemServicoRepository.excluir(
            ordem
        )

        return True