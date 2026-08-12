ITENS_POR_PAGINA = 10


def paginar_resultados(
    itens: list,
    pagina: int,
):
    total_registros = len(itens)
    total_paginas = max(
        1,
        (
            total_registros
            + ITENS_POR_PAGINA
            - 1
        )
        // ITENS_POR_PAGINA,
    )

    pagina_atual = pagina or 1
    pagina_atual = max(1, pagina_atual)
    pagina_atual = min(
        pagina_atual,
        total_paginas,
    )

    inicio = (
        pagina_atual - 1
    ) * ITENS_POR_PAGINA
    fim = inicio + ITENS_POR_PAGINA

    return (
        itens[inicio:fim],
        pagina_atual,
        total_paginas,
        total_registros,
    )
