(function () {
    function somenteNumeros(valor) {
        return String(valor || "")
            .replace(/\D/g, "")
            .slice(0, 11);
    }

    function formatarTelefone(valor) {
        const numeros = somenteNumeros(valor);

        if (numeros.length <= 10) {
            return numeros
                .replace(/^(\d{2})(\d)/, "($1) $2")
                .replace(/(\d{4})(\d)/, "$1-$2");
        }

        return numeros
            .replace(/^(\d{2})(\d)/, "($1) $2")
            .replace(/(\d{5})(\d)/, "$1-$2");
    }

    function formatarTelefoneExibicao(valor) {
        const numeros = String(valor || "").replace(/\D/g, "");

        if (
            numeros.length > 11
            && numeros.length <= 13
            && numeros.startsWith("55")
        ) {
            return `+55 ${formatarTelefone(numeros.slice(2))}`;
        }

        return formatarTelefone(numeros);
    }

    function formatarPlaca(valor) {
        return String(valor || "")
            .replace(/[^a-zA-Z0-9]/g, "")
            .toUpperCase()
            .slice(0, 7);
    }

    function formatarData(valor) {
        const numeros = String(valor || "")
            .replace(/\D/g, "")
            .slice(0, 8);

        if (numeros.length <= 2) {
            return numeros;
        }

        if (numeros.length <= 4) {
            return `${numeros.slice(0, 2)}/${numeros.slice(2)}`;
        }

        return `${numeros.slice(0, 2)}/${numeros.slice(2, 4)}/${numeros.slice(4)}`;
    }

    function isoParaData(valor) {
        if (!valor) {
            return "";
        }

        const partes = valor.split("-");

        if (partes.length !== 3) {
            return "";
        }

        return `${partes[2]}/${partes[1]}/${partes[0]}`;
    }

    function dataParaIso(valor) {
        const partes = String(valor || "").split("/");

        if (partes.length !== 3) {
            return "";
        }

        const dia = partes[0];
        const mes = partes[1];
        const ano = partes[2];

        if (
            dia.length !== 2
            || mes.length !== 2
            || ano.length !== 4
        ) {
            return "";
        }

        return `${ano}-${mes}-${dia}`;
    }

    document.querySelectorAll(
        "[data-notificacao-telefone]"
    ).forEach(function (elemento) {
        elemento.textContent = formatarTelefoneExibicao(
            elemento.textContent.trim()
        );
    });

    const camposData = Array.from(
        document.querySelectorAll("[data-notificacao-date]")
    );

    camposData.forEach(function (campo, indice) {
        const camposOcultos = document.querySelectorAll(
            "[data-notificacao-date-hidden]"
        );

        const campoOculto = camposOcultos[indice];

        campo.value = isoParaData(
            campo.dataset.dateValue
        );

        campo.addEventListener(
            "input",
            function () {
                campo.value = formatarData(campo.value);

                if (campoOculto) {
                    campoOculto.value = dataParaIso(campo.value);
                }
            }
        );

        campo.addEventListener(
            "paste",
            function (evento) {
                if (!evento.clipboardData) {
                    return;
                }

                evento.preventDefault();

                campo.value = formatarData(
                    evento.clipboardData.getData("text")
                );

                if (campoOculto) {
                    campoOculto.value = dataParaIso(campo.value);
                }
            }
        );
    });

    const tipoPesquisa = document.querySelector(
        "[data-notificacao-search-type]"
    );

    const campoPesquisa = document.querySelector(
        "[data-notificacao-search-term]"
    );

    function obterFormatadorPesquisa() {
        if (!tipoPesquisa) {
            return null;
        }

        if (tipoPesquisa.value === "telefone") {
            return formatarTelefone;
        }

        if (tipoPesquisa.value === "placa") {
            return formatarPlaca;
        }

        return null;
    }

    function atualizarCampoPesquisa() {
        if (!campoPesquisa) {
            return;
        }

        const formatador = obterFormatadorPesquisa();

        campoPesquisa.removeAttribute("maxlength");

        if (!formatador) {
            campoPesquisa.removeAttribute("inputmode");
            campoPesquisa.removeAttribute("autocapitalize");
            campoPesquisa.placeholder = "Digite o termo para consulta";
            return;
        }

        if (tipoPesquisa.value === "telefone") {
            campoPesquisa.maxLength = 15;
            campoPesquisa.inputMode = "numeric";
            campoPesquisa.removeAttribute("autocapitalize");
            campoPesquisa.placeholder = "(00) 00000-0000";
        } else {
            campoPesquisa.maxLength = 7;
            campoPesquisa.removeAttribute("inputmode");
            campoPesquisa.setAttribute(
                "autocapitalize",
                "characters"
            );
            campoPesquisa.placeholder = "ABC1D23";
        }

        campoPesquisa.value = formatador(
            campoPesquisa.value
        );
    }

    if (tipoPesquisa && campoPesquisa) {
        tipoPesquisa.addEventListener(
            "change",
            atualizarCampoPesquisa
        );

        campoPesquisa.addEventListener(
            "input",
            function () {
                const formatador = obterFormatadorPesquisa();

                if (formatador) {
                    campoPesquisa.value = formatador(
                        campoPesquisa.value
                    );
                }
            }
        );

        campoPesquisa.addEventListener(
            "paste",
            function (evento) {
                const formatador = obterFormatadorPesquisa();

                if (!formatador || !evento.clipboardData) {
                    return;
                }

                evento.preventDefault();

                campoPesquisa.value = formatador(
                    evento.clipboardData.getData("text")
                );
            }
        );

        if (campoPesquisa.form) {
            campoPesquisa.form.addEventListener(
                "submit",
                function () {
                    if (tipoPesquisa.value === "telefone") {
                        campoPesquisa.value = somenteNumeros(
                            campoPesquisa.value
                        );
                    } else if (tipoPesquisa.value === "placa") {
                        campoPesquisa.value = formatarPlaca(
                            campoPesquisa.value
                        );
                    } else {
                        campoPesquisa.value = campoPesquisa.value.trim();
                    }
                }
            );
        }

        atualizarCampoPesquisa();
    }

    const selecoes = Array.from(
        document.querySelectorAll(
            "[data-notificacao-selection]"
        )
    );

    const acaoVisualizar = document.getElementById(
        "acaoVisualizarNotificacao"
    );

    function obterNotificacaoSelecionada() {
        return (
            selecoes.find(function (selecao) {
                return selecao.checked;
            }) || null
        );
    }

    function atualizarAcoes() {
        const notificacaoSelecionada = obterNotificacaoSelecionada();

        selecoes.forEach(function (selecao) {
            const linha = selecao.closest(
                "[data-notificacao-row]"
            );

            if (linha) {
                linha.classList.toggle(
                    "is-selected",
                    selecao.checked
                );
            }
        });

        if (acaoVisualizar) {
            acaoVisualizar.disabled = !notificacaoSelecionada;
        }
    }

    selecoes.forEach(function (selecaoAtual) {
        selecaoAtual.addEventListener(
            "change",
            function () {
                if (selecaoAtual.checked) {
                    selecoes.forEach(function (selecao) {
                        if (selecao !== selecaoAtual) {
                            selecao.checked = false;
                        }
                    });
                }

                atualizarAcoes();
            }
        );
    });

    if (acaoVisualizar) {
        acaoVisualizar.addEventListener(
            "click",
            function () {
                const notificacaoSelecionada = obterNotificacaoSelecionada();

                if (notificacaoSelecionada) {
                    window.location.href = (
                        notificacaoSelecionada.dataset.urlVisualizar
                    );
                }
            }
        );
    }

    atualizarAcoes();
})();