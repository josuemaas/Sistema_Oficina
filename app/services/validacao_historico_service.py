from datetime import date

from app.repositories.ordem_servico_repository import (
    OrdemServicoRepository,
)


class ValidacaoHistoricoService:
    @staticmethod
    def formatar_quilometragem(
        quilometragem: int,
    ) -> str:
        return (
            f"{quilometragem:,}"
            .replace(",", ".")
        )

    @staticmethod
    def formatar_data(
        data_servico: date,
    ) -> str:
        return data_servico.strftime(
            "%d/%m/%Y"
        )

    @staticmethod
    def validar(
        placa: str,
        data_servico: date,
        quilometragem: int,
        ordem_id_ignorar: int | None = None,
    ):
        """
        Valida a consistência cronológica da
        quilometragem de um veículo.

        Regras:

        1. Não permite outra revisão da mesma
           placa na mesma data.

        2. A quilometragem precisa ser maior
           que a revisão imediatamente anterior.

        3. A quilometragem precisa ser menor
           que a revisão imediatamente posterior.

        Isso permite inclusive inserir registros
        históricos retroativamente, desde que
        respeitem a evolução do hodômetro.
        """

        if not placa:
            raise ValueError(
                "A placa do veículo é obrigatória."
            )

        if data_servico is None:
            raise ValueError(
                "A data do serviço é obrigatória."
            )

        if quilometragem is None:
            raise ValueError(
                "A quilometragem é obrigatória."
            )

        if quilometragem < 0:
            raise ValueError(
                "A quilometragem não pode "
                "ser negativa."
            )

        placa_normalizada = (
            placa.strip().upper()
        )

        historico = (
            OrdemServicoRepository
            .buscar_historico_por_placa(
                placa_normalizada
            )
        )

        historico = [
            ordem
            for ordem in historico
            if (
                ordem_id_ignorar is None
                or ordem.id
                != ordem_id_ignorar
            )
        ]

        if not historico:
            return {
                "valido": True,
                "anterior": None,
                "posterior": None,
            }

        ordem_mesma_data = next(
            (
                ordem
                for ordem in historico
                if ordem.data_servico
                == data_servico
            ),
            None,
        )

        if ordem_mesma_data is not None:
            data_formatada = (
                ValidacaoHistoricoService
                .formatar_data(
                    data_servico
                )
            )

            raise ValueError(
                (
                    "Já existe uma revisão cadastrada "
                    f"para o veículo {placa_normalizada} "
                    f"na data {data_formatada}."
                )
            )

        anteriores = [
            ordem
            for ordem in historico
            if ordem.data_servico
            < data_servico
        ]

        posteriores = [
            ordem
            for ordem in historico
            if ordem.data_servico
            > data_servico
        ]

        ordem_anterior = None
        ordem_posterior = None

        if anteriores:
            ordem_anterior = max(
                anteriores,
                key=lambda ordem: (
                    ordem.data_servico,
                    ordem.id or 0,
                ),
            )

        if posteriores:
            ordem_posterior = min(
                posteriores,
                key=lambda ordem: (
                    ordem.data_servico,
                    ordem.id or 0,
                ),
            )

        if ordem_anterior is not None:
            if (
                quilometragem
                <= ordem_anterior.quilometragem
            ):
                km_anterior = (
                    ValidacaoHistoricoService
                    .formatar_quilometragem(
                        ordem_anterior
                        .quilometragem
                    )
                )

                data_anterior = (
                    ValidacaoHistoricoService
                    .formatar_data(
                        ordem_anterior
                        .data_servico
                    )
                )

                raise ValueError(
                    (
                        "A quilometragem informada é "
                        "incompatível com o histórico "
                        "do veículo. "
                        f"Em {data_anterior}, o veículo "
                        f"já possuía {km_anterior} km. "
                        "A nova quilometragem deve ser "
                        "maior que esse valor."
                    )
                )

        if ordem_posterior is not None:
            if (
                quilometragem
                >= ordem_posterior.quilometragem
            ):
                km_posterior = (
                    ValidacaoHistoricoService
                    .formatar_quilometragem(
                        ordem_posterior
                        .quilometragem
                    )
                )

                data_posterior = (
                    ValidacaoHistoricoService
                    .formatar_data(
                        ordem_posterior
                        .data_servico
                    )
                )

                raise ValueError(
                    (
                        "A quilometragem informada é "
                        "incompatível com o histórico "
                        "do veículo. "
                        f"Em {data_posterior}, o veículo "
                        f"possuía {km_posterior} km. "
                        "Para essa data, a quilometragem "
                        "deve ser menor que esse valor."
                    )
                )

        return {
            "valido": True,
            "anterior": ordem_anterior,
            "posterior": ordem_posterior,
        }