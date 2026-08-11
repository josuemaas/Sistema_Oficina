# Sistema da Oficina

## Contexto do projeto

Este projeto é um sistema web para gestão de uma oficina mecânica, desenvolvido como Trabalho de Conclusão de Curso.

O sistema controla clientes, veículos, ordens de serviço, histórico de manutenção, previsão da próxima troca e notificações automáticas por WhatsApp.

O objetivo central do projeto é utilizar o histórico de quilometragem e datas de revisão para prever a próxima manutenção do veículo e auxiliar a oficina na retenção de clientes.

## Tecnologias atuais

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- PostgreSQL
- Jinja2
- HTML
- CSS
- Bootstrap
- pandas
- NumPy
- Evolution API
- APScheduler
- Docker
- Docker Compose
- Gunicorn

## Estrutura principal

- `app/models`: modelos do banco de dados
- `app/repositories`: acesso aos dados
- `app/services`: regras de negócio
- `app/routes`: rotas web e API
- `app/controllers`: controllers
- `app/templates`: páginas HTML
- `app/static/css`: estilos visuais
- `app/integrations`: integrações externas
- `migrations`: migrations do banco de dados
- `worker_notificacoes.py`: processamento automático das notificações

## Regras de desenvolvimento

- Antes de alterar qualquer arquivo, analisar a implementação atual e os arquivos relacionados.
- Não reescrever partes do sistema que não precisam ser alteradas.
- Preservar funcionalidades que já estão funcionando.
- Fazer alterações pequenas e fáceis de validar.
- Manter o código simples, limpo e fácil de explicar durante a banca do TCC.
- Evitar abstrações, padrões ou bibliotecas desnecessárias.
- Não adicionar comentários ao código.
- Não adicionar docstrings novas.
- Não alterar nomes de métodos, rotas, campos ou classes sem necessidade real.
- Não alterar regras de negócio sem solicitação explícita.
- Ao modificar um arquivo, considerar todas as dependências relacionadas.
- Priorizar legibilidade em vez de soluções excessivamente sofisticadas.
- Não criar funcionalidades extras sem solicitação.
- Não remover validações existentes sem analisar seu impacto.
- Não alterar migrations antigas já aplicadas.
- Não modificar arquivos de backup, a menos que seja solicitado explicitamente.

## Regra principal da previsão de manutenção

Todas as revisões válidas do veículo são importantes para a previsão.

Quanto maior o histórico de revisões, melhor o sistema consegue identificar o padrão de utilização daquele veículo e tornar a previsão mais representativa do comportamento real do cliente.

A previsão deve sempre respeitar a ordem cronológica do histórico.

Cada revisão deve ser calculada utilizando somente os registros existentes até aquele atendimento.

Exemplo:

- revisão 1 utiliza `[1]`
- revisão 2 utiliza `[1, 2]`
- revisão 3 utiliza `[1, 2, 3]`
- revisão 4 utiliza `[1, 2, 3, 4]`

Registros futuros nunca podem influenciar a previsão de uma revisão passada.

## Funcionamento atual da previsão

A lógica principal está em `app/services/predicao_service.py`.

O intervalo padrão utilizado para a próxima troca é de 10.000 km.

Com menos de 3 registros válidos, o sistema utiliza a regra padrão:

- próxima troca em `última quilometragem + 10.000 km`
- próxima data em `última data de serviço + 6 meses`

A partir de 3 registros válidos, o sistema tenta utilizar regressão linear com o histórico de quilometragem e datas.

A regressão estima a data em que o veículo deverá atingir a próxima quilometragem de troca.

Se os dados não permitirem uma regressão válida, o sistema retorna para a regra padrão.

A quantidade de registros utilizados na previsão é mantida no resultado para representar a quantidade de histórico disponível.

## Recálculo do histórico

A lógica está principalmente em `app/services/ordem_servico_service.py`.

Ao cadastrar, editar ou alterar uma ordem que afete o histórico de um veículo, as previsões da placa devem permanecer coerentes com a sequência cronológica.

O método `recalcular_historico_placa` percorre as ordens em ordem cronológica e utiliza um histórico acumulado para cada previsão.

Essa regra não deve ser substituída por uma previsão baseada apenas nas duas últimas revisões.

## Validação do histórico

A lógica está em `app/services/validacao_historico_service.py`.

O sistema deve impedir históricos inconsistentes.

A quilometragem precisa ser compatível com a data do serviço em relação aos registros anteriores e posteriores do mesmo veículo.

Ao editar uma ordem, a própria ordem deve ser ignorada durante a validação para que seja possível comparar corretamente o valor proposto com o restante do histórico.

## Notificações

A lógica principal está em `app/services/notificacao_service.py`.

As notificações utilizam a previsão da próxima troca do veículo.

A data de disparo é atualmente definida para 7 dias antes da data prevista da próxima troca.

Para um mesmo veículo, somente a ordem mais recente deve manter uma notificação ativa pendente.

Notificações de ordens anteriores são canceladas, exceto notificações que já foram enviadas, pois fazem parte do histórico real.

O envio é realizado pela Evolution API.

## Worker de notificações

O arquivo `worker_notificacoes.py` executa o processamento automático das notificações.

O agendamento atual é de segunda a sexta-feira às 09:00 no fuso horário `America/Sao_Paulo`.

## Interface

A interface utiliza templates Jinja2 e arquivos CSS próprios.

Arquivos principais de estilo:

- `app/static/css/base.css`
- `app/static/css/components.css`
- `app/static/css/forms.css`
- `app/static/css/layout.css`
- `app/static/css/pages.css`
- `app/static/css/style.css`
- `app/static/css/tables.css`

Ao trabalhar na parte visual:

- preservar todas as funcionalidades existentes
- evitar JavaScript desnecessário
- manter o visual profissional e simples
- manter consistência entre dashboard, clientes, ordens e notificações
- priorizar boa leitura em apresentação para banca
- utilizar componentes visuais reutilizáveis quando já existirem no CSS
- evitar duplicação de estilos
- não alterar lógica de backend apenas para resolver um detalhe visual

## Fluxo esperado antes de qualquer alteração

1. Ler o arquivo solicitado.
2. Ler os arquivos diretamente relacionados.
3. Identificar o comportamento atual.
4. Explicar brevemente o que será alterado.
5. Fazer somente a alteração necessária.
6. Verificar se a mudança afeta outras telas ou regras.
7. Preservar o restante do sistema.

## Git

O Git representa o estado oficial do projeto.

Antes de mudanças maiores, considerar o estado atual do repositório como fonte da verdade.

Não executar comandos destrutivos como `reset --hard`, remoção de branches ou exclusão de arquivos sem solicitação explícita.

Não fazer commit ou push automaticamente sem solicitação.

## Prioridade do projeto

A prioridade é entregar um sistema funcional, coerente, visualmente profissional e simples o suficiente para que seu funcionamento possa ser explicado com segurança durante a banca do TCC.
