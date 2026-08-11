(function () {
    function somenteNumeros(valor) {
        return String(valor || "").replace(/\D/g, "");
    }

    function limitarNumeros(valor, limite) {
        return somenteNumeros(valor).slice(0, limite);
    }

    function formatarCpf(valor) {
        const numeros = limitarNumeros(valor, 11);

        return numeros
            .replace(/^(\d{3})(\d)/, "$1.$2")
            .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
            .replace(/\.(\d{3})(\d)/, ".$1-$2");
    }

    function formatarCpfCnpj(valor) {
        const numeros = somenteNumeros(valor);

        if (numeros.length <= 11) {
            return formatarCpf(numeros);
        }

        return numeros
            .slice(0, 14)
            .replace(/^(\d{2})(\d)/, "$1.$2")
            .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
            .replace(/\.(\d{3})(\d)/, ".$1/$2")
            .replace(/(\d{4})(\d)/, "$1-$2");
    }

    function formatarTelefoneLocal(valor) {
        const numeros = limitarNumeros(valor, 11);

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
        const numeros = somenteNumeros(valor);

        if (
            numeros.length > 11
            && numeros.length <= 13
            && numeros.startsWith("55")
        ) {
            return `+55 ${formatarTelefoneLocal(
                numeros.slice(2)
            )}`;
        }

        if (numeros.length <= 11) {
            return formatarTelefoneLocal(numeros);
        }

        return numeros;
    }

    function obterFormatadorTexto(tipo) {
        if (tipo === "cpf-cnpj") {
            return formatarCpfCnpj;
        }

        return formatarTelefoneExibicao;
    }

    function obterFormatadorEntrada(tipo) {
        if (tipo === "cpf") {
            return formatarCpf;
        }

        if (tipo === "telefone-local") {
            return formatarTelefoneLocal;
        }

        return null;
    }

    document.querySelectorAll("[data-mask-text]").forEach(
        function (elemento) {
            const formatador = obterFormatadorTexto(
                elemento.dataset.maskText
            );

            elemento.textContent = formatador(
                elemento.textContent.trim()
            );
        }
    );

    document.querySelectorAll("[data-mask-input]").forEach(
        function (campo) {
            const formatador = obterFormatadorEntrada(
                campo.dataset.maskInput
            );

            if (!formatador) {
                return;
            }

            campo.value = formatador(campo.value);

            campo.addEventListener(
                "input",
                function () {
                    campo.value = formatador(campo.value);
                }
            );

            if (campo.form) {
                campo.form.addEventListener(
                    "submit",
                    function () {
                        campo.value = limitarNumeros(
                            campo.value,
                            11
                        );
                    }
                );
            }
        }
    );

    const tipoPesquisa = document.querySelector(
        "[data-client-search-type]"
    );

    const campoPesquisa = document.querySelector(
        "[data-client-search-term]"
    );

    function obterTipoMascaraPesquisa() {
        if (!tipoPesquisa) {
            return null;
        }

        if (tipoPesquisa.value === "cpf") {
            return "cpf";
        }

        if (tipoPesquisa.value === "telefone") {
            return "telefone-local";
        }

        return null;
    }

    function atualizarMascaraPesquisa() {
        if (!campoPesquisa) {
            return;
        }

        const tipoMascara = obterTipoMascaraPesquisa();
        const formatador = obterFormatadorEntrada(
            tipoMascara
        );

        if (!formatador) {
            campoPesquisa.removeAttribute("maxlength");
            campoPesquisa.removeAttribute("inputmode");
            campoPesquisa.placeholder = (
                "Digite o termo para consulta"
            );
            return;
        }

        campoPesquisa.maxLength = (
            tipoMascara === "cpf" ? 14 : 15
        );
        campoPesquisa.inputMode = "numeric";
        campoPesquisa.placeholder = (
            tipoMascara === "cpf"
                ? "000.000.000-00"
                : "(00) 00000-0000"
        );
        campoPesquisa.value = formatador(
            campoPesquisa.value
        );
    }

    if (tipoPesquisa && campoPesquisa) {
        tipoPesquisa.addEventListener(
            "change",
            atualizarMascaraPesquisa
        );

        campoPesquisa.addEventListener(
            "input",
            function () {
                const formatador = obterFormatadorEntrada(
                    obterTipoMascaraPesquisa()
                );

                if (formatador) {
                    campoPesquisa.value = formatador(
                        campoPesquisa.value
                    );
                }
            }
        );

        if (campoPesquisa.form) {
            campoPesquisa.form.addEventListener(
                "submit",
                function () {
                    if (obterTipoMascaraPesquisa()) {
                        campoPesquisa.value = limitarNumeros(
                            campoPesquisa.value,
                            11
                        );
                    }
                }
            );
        }

        atualizarMascaraPesquisa();
    }

    const selecoes = Array.from(
        document.querySelectorAll(
            "[data-cliente-selection]"
        )
    );

    const acaoAlterar = document.getElementById(
        "acaoAlterarCliente"
    );

    const acaoVisualizar = document.getElementById(
        "acaoVisualizarCliente"
    );

    const acaoSelecionar = document.getElementById(
        "acaoSelecionarCliente"
    );

    function obterClienteSelecionado() {
        return selecoes.find(
            function (selecao) {
                return selecao.checked;
            }
        ) || null;
    }

    function atualizarAcoes() {
        const clienteSelecionado = obterClienteSelecionado();

        selecoes.forEach(
            function (selecao) {
                const linha = selecao.closest(
                    "[data-cliente-row]"
                );

                if (linha) {
                    linha.classList.toggle(
                        "is-selected",
                        selecao.checked
                    );
                }
            }
        );

        if (acaoAlterar) {
            acaoAlterar.disabled = !clienteSelecionado;
        }

        if (acaoVisualizar) {
            acaoVisualizar.disabled = !clienteSelecionado;
        }

        if (acaoSelecionar) {
            acaoSelecionar.disabled = (
                !clienteSelecionado
                || clienteSelecionado.dataset.clienteAtivo
                !== "true"
            );
        }
    }

    selecoes.forEach(
        function (selecaoAtual) {
            selecaoAtual.addEventListener(
                "change",
                function () {
                    if (selecaoAtual.checked) {
                        selecoes.forEach(
                            function (selecao) {
                                if (selecao !== selecaoAtual) {
                                    selecao.checked = false;
                                }
                            }
                        );
                    }

                    atualizarAcoes();
                }
            );
        }
    );

    if (acaoAlterar) {
        acaoAlterar.addEventListener(
            "click",
            function () {
                const clienteSelecionado = obterClienteSelecionado();

                if (clienteSelecionado) {
                    window.location.href = (
                        clienteSelecionado.dataset.urlAlterar
                    );
                }
            }
        );
    }

    if (acaoVisualizar) {
        acaoVisualizar.addEventListener(
            "click",
            function () {
                const clienteSelecionado = obterClienteSelecionado();

                if (clienteSelecionado) {
                    window.location.href = (
                        clienteSelecionado.dataset.urlVisualizar
                    );
                }
            }
        );
    }

    if (acaoSelecionar) {
        acaoSelecionar.addEventListener(
            "click",
            function () {
                const clienteSelecionado = obterClienteSelecionado();

                if (
                    clienteSelecionado
                    && clienteSelecionado.dataset.clienteAtivo
                    === "true"
                ) {
                    window.location.href = (
                        clienteSelecionado.dataset.urlSelecionar
                    );
                }
            }
        );
    }

    atualizarAcoes();
})();
