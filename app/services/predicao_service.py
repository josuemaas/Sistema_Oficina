from calendar import monthrange
from datetime import date, timedelta

import numpy as np
import pandas as pd


class PredicaoService:
    DATA_BASE = date(1900, 1, 1)

    INTERVALO_TROCA_KM = 10000

    MINIMO_REGISTROS = 3

    @staticmethod
    def adicionar_meses(
        data_original: date,
        meses: int,
    ):
        mes = (
            data_original.month - 1 + meses
        )

        ano = (
            data_original.year
            + mes // 12
        )

        mes = (
            mes % 12
            + 1
        )

        ultimo_dia = monthrange(
            ano,
            mes,
        )[1]

        dia = min(
            data_original.day,
            ultimo_dia,
        )

        return date(
            ano,
            mes,
            dia,
        )

    @staticmethod
    def calcular(
        historico,
    ):
        registros = []

        for ordem in historico:
            if ordem.data_servico is None:
                continue

            if ordem.quilometragem is None:
                continue

            registros.append(
                {
                    "data_servico": (
                        ordem.data_servico
                    ),
                    "quilometragem": (
                        int(ordem.quilometragem)
                    ),
                }
            )

        if not registros:
            return None

        dataframe = pd.DataFrame(
            registros
        )

        dataframe = dataframe.sort_values(
            by="data_servico"
        ).reset_index(
            drop=True
        )

        ultima_linha = (
            dataframe.iloc[-1]
        )

        ultima_data = (
            ultima_linha[
                "data_servico"
            ]
        )

        ultima_quilometragem = int(
            ultima_linha[
                "quilometragem"
            ]
        )

        proxima_troca_km = (
            ultima_quilometragem
            + PredicaoService.INTERVALO_TROCA_KM
        )

        if (
            len(dataframe)
            < PredicaoService.MINIMO_REGISTROS
        ):
            return {
                "metodo": "REGRA_PADRAO",
                "quantidade_registros": (
                    len(dataframe)
                ),
                "proxima_troca_km": (
                    proxima_troca_km
                ),
                "proxima_troca_data": (
                    PredicaoService
                    .adicionar_meses(
                        ultima_data,
                        6,
                    )
                ),
                "inclinacao": None,
                "intersecao": None,
                "km_por_dia": None,
            }

        dataframe[
            "dias"
        ] = (
            pd.to_datetime(
                dataframe[
                    "data_servico"
                ]
            )
            - pd.Timestamp(
                PredicaoService.DATA_BASE
            )
        ).dt.days

        eixo_x = (
            dataframe[
                "quilometragem"
            ]
            .astype(float)
            .to_numpy()
        )

        eixo_y = (
            dataframe[
                "dias"
            ]
            .astype(float)
            .to_numpy()
        )

        if np.ptp(eixo_x) == 0:
            return {
                "metodo": "REGRA_PADRAO",
                "quantidade_registros": (
                    len(dataframe)
                ),
                "proxima_troca_km": (
                    proxima_troca_km
                ),
                "proxima_troca_data": (
                    PredicaoService
                    .adicionar_meses(
                        ultima_data,
                        6,
                    )
                ),
                "inclinacao": None,
                "intersecao": None,
                "km_por_dia": None,
            }

        inclinacao, intersecao = (
            np.polyfit(
                eixo_x,
                eixo_y,
                1,
            )
        )

        if inclinacao <= 0:
            return {
                "metodo": "REGRA_PADRAO",
                "quantidade_registros": (
                    len(dataframe)
                ),
                "proxima_troca_km": (
                    proxima_troca_km
                ),
                "proxima_troca_data": (
                    PredicaoService
                    .adicionar_meses(
                        ultima_data,
                        6,
                    )
                ),
                "inclinacao": None,
                "intersecao": None,
                "km_por_dia": None,
            }

        dia_previsto = int(
            intersecao
            + (
                inclinacao
                * proxima_troca_km
            )
        )

        data_prevista = (
            PredicaoService.DATA_BASE
            + timedelta(
                days=dia_previsto
            )
        )

        km_por_dia = (
            1 / inclinacao
        )

        return {
            "metodo": "REGRESSAO_LINEAR",
            "quantidade_registros": (
                len(dataframe)
            ),
            "proxima_troca_km": (
                proxima_troca_km
            ),
            "proxima_troca_data": (
                data_prevista
            ),
            "inclinacao": float(
                inclinacao
            ),
            "intersecao": float(
                intersecao
            ),
            "km_por_dia": float(
                km_por_dia
            ),
        }