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

    function formatarPlaca(valor) {
        return String(valor || "")
            .replace(/[^a-zA-Z0-9]/g, "")
            .toUpperCase()
            .slice(0, 7);
    }

    const camposPlaca = Array.from(
        document.querySelectorAll(
            "[data-order-plate-input]"
        )
    );

    camposPlaca.forEach(
        function (campo) {
            campo.value = formatarPlaca(
                campo.value
            );

            campo.addEventListener(
                "input",
                function () {
                    campo.value = formatarPlaca(
                        campo.value
                    );
                }
            );

            campo.addEventListener(
                "paste",
                function (evento) {
                    if (!evento.clipboardData) {
                        return;
                    }

                    evento.preventDefault();
                    campo.value = formatarPlaca(
                        evento.clipboardData.getData(
                            "text"
                        )
                    );
                }
            );
        }
    );

    const tipoPesquisa = document.querySelector(
        "[data-order-search-type]"
    );

    const campoPesquisa = document.querySelector(
        "[data-order-search-term]"
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
            campoPesquisa.placeholder = (
                "Digite o termo para consulta"
            );
            return;
        }

        if (tipoPesquisa.value === "telefone") {
            campoPesquisa.inputMode = "numeric";
            campoPesquisa.removeAttribute("autocapitalize");
            campoPesquisa.placeholder = "(00) 00000-0000";
        } else {
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
                        campoPesquisa.value = (
                            campoPesquisa.value.trim()
                        );
                    }
                }
            );
        }

        atualizarCampoPesquisa();
    }

    const campoCliente = document.querySelector(
        "[data-client-selection-url]"
    );

    function abrirConsultaClientes() {
        if (campoCliente) {
            window.location.href = (
                campoCliente.dataset.clientSelectionUrl
            );
        }
    }

    if (campoCliente) {
        campoCliente.addEventListener(
            "click",
            abrirConsultaClientes
        );

        campoCliente.addEventListener(
            "keydown",
            function (evento) {
                if (
                    evento.key === "Enter"
                    || evento.key === " "
                ) {
                    evento.preventDefault();
                    abrirConsultaClientes();
                }
            }
        );
    }

    const selecoes = Array.from(
        document.querySelectorAll(
            "[data-ordem-selection]"
        )
    );

    const acaoAlterar = document.getElementById(
        "acaoAlterarOrdem"
    );

    const acaoVisualizar = document.getElementById(
        "acaoVisualizarOrdem"
    );

    const acaoExcluir = document.getElementById(
        "acaoExcluirOrdem"
    );

    const formExcluir = document.getElementById(
        "formExcluirOrdem"
    );

    function obterOrdemSelecionada() {
        return selecoes.find(
            function (selecao) {
                return selecao.checked;
            }
        ) || null;
    }

    function atualizarAcoes() {
        const ordemSelecionada = obterOrdemSelecionada();

        selecoes.forEach(
            function (selecao) {
                const linha = selecao.closest(
                    "[data-ordem-row]"
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
            acaoAlterar.disabled = !ordemSelecionada;
        }

        if (acaoVisualizar) {
            acaoVisualizar.disabled = !ordemSelecionada;
        }

        if (acaoExcluir) {
            acaoExcluir.disabled = !ordemSelecionada;
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
                const ordemSelecionada = obterOrdemSelecionada();

                if (ordemSelecionada) {
                    window.location.href = (
                        ordemSelecionada.dataset.urlAlterar
                    );
                }
            }
        );
    }

    if (acaoVisualizar) {
        acaoVisualizar.addEventListener(
            "click",
            function () {
                const ordemSelecionada = obterOrdemSelecionada();

                if (ordemSelecionada) {
                    window.location.href = (
                        ordemSelecionada.dataset.urlVisualizar
                    );
                }
            }
        );
    }

    if (acaoExcluir && formExcluir) {
        acaoExcluir.addEventListener(
            "click",
            function () {
                const ordemSelecionada = obterOrdemSelecionada();

                if (
                    ordemSelecionada
                    && window.confirm(
                        "Deseja excluir esta ordem de serviço?"
                    )
                ) {
                    formExcluir.action = (
                        ordemSelecionada.dataset.urlExcluir
                    );
                    formExcluir.submit();
                }
            }
        );
    }

    atualizarAcoes();
})();
