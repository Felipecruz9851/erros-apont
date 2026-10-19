# Feature Specification: Frontend UI & Análise de Erros de Apontamento (Líder Design Style)

**Feature Branch**: `001-frontend-ui-layout`

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "A ferramenta se trata de um recurso de análise de erros de apontamentos, vou pegar as ordens de produção de todas as fabricas, através de um relatório de consumo de componentes por ordem. Todos os componentes que sofrem baixa automática serão analisados e deverão ter saldo disponível no local de produção da ordem que o consome. Basicamente serão extraidos dois relatórios: consumo componente por ordem e um relatório de estoque."

## Clarifications

### Session 2026-10-19
- Q: Como o cálculo de saldo disponível deve se comportar quando múltiplas Ordens de Produção (OPs) concorrem pelo consumo do mesmo componente no mesmo local de produção? → A: Alocação cumulativa sequencial escalonada pela data/prioridade de entrega da ordem (as OPs com entrega mais urgente alocam o saldo disponível no local de produção prioritariamente; ordens subsequentes cuja demanda acumulada exceder o saldo remanescente são apontadas com erro de déficit).
- Q: Quais status ou critérios de seleção de Ordens de Produção (OPs) devem ser considerados na análise de consumo de componentes? → A: Delimitação e filtragem pelo período operacional das datas de abertura e entrega da ordem (as ordens extraídas e avaliadas são balizadas pelo intervalo entre a data de abertura e a data de entrega).
- Q: No relatório de estoque da intranet, qual campo de saldo deve ser adotado como base para o cruzamento de atendimento da ordem? → A: Tratamento e mapeamento de campos modular e incremental (o pipeline de dados implementará o motor de tratamento de forma desacoplada e evolutiva, permitindo ao usuário refinar e mapear as colunas de saldo e particularidades das tabelas aos poucos conforme inspeciona os relatórios reais).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingestão de Credenciais e Disparo da Extração Dupla Multi-Fábrica (Priority: P1)

Como analista operacional ou de PCP (Planejamento e Controle da Produção), preciso inserir minhas credenciais corporativas da intranet na interface web para disparar a extração automática e paralela dos dois relatórios essenciais de todas as fábricas: **Relatório de Consumo de Componentes por Ordem** e **Relatório de Estoque**, delimitando o período pelas datas de abertura e entrega das ordens.

**Why this priority**: Sem a extração orquestrada dos dois relatórios fundamentais vinculados às credenciais do usuário e ao recorte temporal de abertura e entrega, nenhuma validação de saldo ou erro de apontamento pode ocorrer.

**Independent Test**: Pode ser testado de forma isolada ao submeter login, senha e período de datas no card minimalista de login/disparo, verificando se a API recebe as credenciais e inicializa as tarefas de extração para ambas as fontes de dados em todas as fábricas.

**Acceptance Scenarios**:

1. **Given** o usuário na tela inicial do sistema, **When** insere suas credenciais da intranet, confirma o período de datas de abertura e entrega e clica em "Iniciar Análise", **Then** as credenciais e parâmetros de data são enviados para a memória do gerador de tarefas, iniciando a coleta dos relatórios de consumo por ordem e de estoque.
2. **Given** credenciais inválidas ou erro de rede da intranet, **When** a autenticação falhar, **Then** o formulário exibe mensagem sutil e objetiva em tom discreto, sem recarregar a página ou expor dados sensíveis.

---

### User Story 2 - Acompanhamento do Pipeline de Extração e Cruzamento de Dados (Priority: P2)

Como usuário operacional, preciso visualizar o progresso em tempo real das etapas de extração dos dois relatórios (Consumo por Ordem e Estoque de todas as fábricas), saneamento de dados e cruzamento de saldos por local de produção.

**Why this priority**: A extração de dados multi-fábrica com navegação em HTML legado pode levar algum tempo; o monitor em tempo real fornece visibilidade das fábricas já processadas e do volume de ordens extraídas dentro do período de abertura/entrega.

**Independent Test**: Pode ser testado simulando o avanço do pipeline através dos 6 estágios, validando se o monitor exibe o status de cada relatório (Consumo de Componentes e Estoque), tempo decorrido e total de fábricas concluídas.

**Acceptance Scenarios**:

1. **Given** o pipeline em execução, **When** os workers estiverem raspando o relatório de consumo de componentes e o relatório de estoque, **Then** o card de monitoramento exibe o progresso individualizado de cada relatório e o número de ordens de produção encontradas.
2. **Given** a finalização da extração, **When** o motor iniciar o tratamento e cruzamento de componentes de baixa automática, **Then** a barra de progresso avança com transição fluida para "Cálculo e Análise de Divergências de Saldo".

---

### User Story 3 - Painel Analítico de Erros de Apontamento e Saldo no Local de Produção (Priority: P3)

Como auditor de estoque ou gestor de fábrica, preciso inspecionar os erros de apontamento onde componentes com **baixa automática** não possuem saldo disponível suficiente no **local de produção** da ordem consumidora, considerando a alocação cumulativa por data de entrega da OP, podendo filtrar por fábrica, ordem de produção, data de abertura, data de entrega e severidade do déficit.

**Why this priority**: Esta visualização entrega o valor central de negócio da ferramenta, permitindo correções ágeis antes do fechamento das ordens ou de paradas de linha por falta de saldo.

**Independent Test**: Pode ser testado carregando um payload consolidado com erros conhecidos, verificando se os cards exibem o total de OPs com déficit de saldo, a tabela lista apenas os componentes com `baixa_automática == Sim` e `saldo_disponível < quantidade_necessária` (considerando a fila por data de entrega), e os seletores de filtros refinam instantaneamente os registros.

**Acceptance Scenarios**:

1. **Given** a conclusão do cálculo analítico, **When** a tela de resultados carrega, **Then** o topo exibe cartões com métricas-chave: Total de OPs Analisadas, Componentes com Baixa Automática, Total de Erros de Apontamento (Saldo Insuficiente) e Índice de Conformidade Fabril.
2. **Given** a tabela analítica de dados, **When** o usuário filtra por uma "Fábrica", "Local de Produção" ou "Intervalo de Datas de Entrega", **Then** a tabela exibe apenas as ordens daquele recorte, destacando a OP, data de abertura, data de entrega, código do componente, quantidade necessária, saldo disponível no local e o déficit cumulativo calculado.
3. **Given** uma lista de erros filtrada, **When** o usuário clica no botão "Exportar Relatório", **Then** o sistema gera um arquivo (JSON/CSV) pronto para envio às equipes de fábrica para regularização de estoque.

---

### Edge Cases

- **Concorrência de Múltiplas OPs para o Mesmo Componente e Local**: O sistema NÃO DEVE avaliar OPs de forma isolada; deve simular o consumo cumulativo ordenado pela data de entrega da ordem. OPs com datas posteriores sofrerão erro de apontamento assim que o saldo físico no local for esgotado pelas OPs precedentes.
- **Componente de Baixa Automática com Saldo em Outro Depósito, mas Zero no Local da Ordem**: O sistema DEVE obrigatoriamente apontar erro, pois a baixa automática exige saldo no *local de produção específico da ordem*, e não em um almoxarifado geral distante.
- **Componente com Baixa Manual**: Componentes não configurados para baixa automática DEVEM ser desconsiderados na contagem de erros de apontamento de saldo automático, evitando falsos positivos.
- **Ordens com Data de Entrega Vencida**: O sistema deve manter a alocação cumulativa prioritária destacando visualmente ordens em atraso.
- **Ordens de Produção sem Componentes Associados**: O sistema deve registrar status neutro ("Sem componentes") sem abortar o processamento das demais ordens.
- **Fábrica sem Ordens no Período**: O dashboard deve exibir aviso sóbrio indicando que a respectiva fábrica não possui OPs abertas na extração realizada.
- **Divergência de Nomenclatura de Locais de Estoque**: Caso o local de produção na OP tenha formatação ligeiramente diferente do relatório de estoque (espaços adicionais, zeros à esquerda), a etapa de tratamento deve normalizar os identificadores para evitar falso erro de saldo ausente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE extrair exatamente dois conjuntos de dados principais da intranet corporativa, delimitados pelo intervalo de **data de abertura** e **data de entrega** das ordens:
  1. **Relatório de Consumo de Componentes por Ordem** (englobando todas as fábricas).
  2. **Relatório de Estoque** (saldos disponíveis por item e por local de estoque/produção).
- **FR-002**: O sistema DEVE filtrar estritamente os componentes identificados com indicador de **baixa automática** para a análise de erros de apontamento.
- **FR-003**: O motor de cálculo DEVE verificar a suficiência de saldo através de **alocação cumulativa**: quando múltiplas OPs requisitarem o mesmo componente no mesmo local de produção, o saldo disponível no local DEVE ser consumido sequencialmente de acordo com a **escala de prioridade/data de entrega da OP**. Ordens subsequentes cuja demanda acumulada exceder o saldo remanescente no local DEVEM ser marcadas com erro de apontamento por déficit.
- **FR-004**: O sistema DEVE classificar como **Erro de Apontamento por Saldo Insuficiente** qualquer ocorrência em que:
  - O saldo disponível no local de produção (ou saldo remanescente na alocação cumulativa) for menor que a quantidade requisitada pela OP (`saldo_disponivel_remanescente < quantidade_necessaria`), inclusive saldo zerado ou inexistente no local.
- **FR-005**: O layout visual DEVE adotar integralmente o **Estilo Líder Design** documentado em `refs_layout`:
  - Canvas neutro com fundos claros (`#FFFFFF`, `#F8F8F8`, `#EDEDED`).
  - Tipografia de alta legibilidade com títulos em grafite (`#1A1A1A` / `#222222`) e corpo em cinza médio (`#666666`).
  - Destaques pontuais em tons amadeirados/terrosos (`#8B5A2B`).
  - Cantos quase retos (raio de 2px a 4px) e sombras difusas quase imperceptíveis ($\le 5\%$).
  - Bordas ultrafinas de 1px (`#E0E0E0`) ou separação baseada em respiros generosos (whitespace de 24px a 48px).
- **FR-006**: A composição de tela DEVE seguir a estrutura de 3 zonas:
  - **Sidebar Fixa (Esquerda):** Identidade visual, status da sessão, seletor multi-fábrica, filtro de período e resumo numérico de apontamentos.
  - **Header Fixo (Topo):** Título editorial do painel, totalizadores gerais e botão global de exportação.
  - **Main Content (Canvas de Rolagem):** Cards de métricas consolidadas (MetricsCards), monitor de progresso das 6 fases e Tabela de Apontamentos (PurchaseTable/PointingErrorsTable).
- **FR-007**: A tabela de resultados DEVE apresentar as seguintes colunas essenciais:
  - `Fábrica`
  - `Ordem de Produção (OP)`
  - `Data de Abertura`
  - `Data de Entrega / Prioridade`
  - `Produto / Descrição da OP`
  - `Local de Produção`
  - `Código do Componente`
  - `Descrição do Componente`
  - `Baixa Automática` (Indicador)
  - `Qtd. Necessária / Consumo`
  - `Saldo Inicial no Local`
  - `Saldo Remanescente Alocado`
  - `Déficit de Saldo`
  - `Status da Divergência`
- **FR-008**: O sistema DEVE permitir ordenação por qualquer coluna e filtros simultâneos por:
  - Fábrica
  - Local de Produção
  - Código/Descrição do Componente
  - Data de Abertura da Ordem
  - Data de Entrega da Ordem
  - Apenas erros com déficit crítico
- **FR-009**: O sistema DEVE montar e serializar o DataFrame consolidado de resultados em formato JSON estruturado exposto via endpoint FastAPI para consumo do frontend.
- **FR-010**: A interface DEVE disponibilizar exportação instantânea dos erros identificados nos formatos JSON e CSV.
- **FR-011**: A camada de **Tratamento de Dados** DEVE ser implementada de forma modular, extensível e incremental, permitindo que as regras específicas de limpeza, conversões de tipo e mapeamento de colunas de saldo sejam refinadas e expandidas progressivamente pelo usuário sem acoplamento rígido ao motor de extração.

### Key Entities

- **Ordem de Produção (OP)**: Ordem fabril contendo número identificador, fábrica emitente, data de abertura, data de entrega/prioridade da ordem, local de produção alocado, código do produto pai e status de produção.
- **Componente de Consumo**: Insumo associado a uma OP, contendo código do item, descrição, quantidade necessária, unidade de medida, local de produção da ordem consumidora e a flag indicadora de `baixa_automatica` (Booleano).
- **Registro de Saldo em Estoque**: Informação de inventário contendo código do item, código do depósito/local de estoque e quantidade de saldo físico disponível.
- **Erro de Apontamento de Saldo**: Registro resultante do cruzamento analítico onde um componente com baixa automática apresenta saldo disponível (ou remanescente na alocação cronológica) no local de produção inferior à quantidade necessária para o atendimento da ordem.
- **Fábrica**: Unidade fabril agregadora de ordens e locais de produção.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos componentes com baixa automática presentes no relatório de consumo dentro do recorte de datas de abertura e entrega são validados contra o saldo disponível de seu respectivo local de produção no relatório de estoque via alocação cumulativa prioritária por data de entrega.
- **SC-002**: Zero falsos positivos para componentes que possuam saldo suficiente no local de produção da ordem.
- **SC-003**: Usuário consegue filtrar e isolar os erros de apontamento de qualquer fábrica ou intervalo de datas em menos de 2 segundos após a carga dos resultados.
- **SC-004**: Renderização visual da interface atende 100% das diretrizes do Estilo Líder Design (ausência de cores berrantes, botões escuros retangulares, respiros amplos, sombras $\le 5\%$).
- **SC-005**: O tempo total de processamento do cruzamento e montagem do JSON em memória para um volume de até 50.000 linhas de consumo não ultrapassa 5 segundos após a finalização da extração dos HTMLs.

## Assumptions

- Os relatórios de consumo por ordem e de estoque são acessíveis via intranet através de endpoints com parâmetros configuráveis por fábrica e por intervalo de datas de abertura e entrega.
- O campo que indica se o componente sofre baixa automática é determinístico e extraível diretamente do relatório de consumo de componentes.
- O campo `local de produção` está explícito na ordem de produção ou no apontamento de consumo da OP, permitindo correlação direta com o código de local presente no relatório de estoque.
- A `data de abertura` e `data de entrega` estão presentes no relatório de consumo ou nos dados da OP para orientar a filtragem temporal e a fila de alocação cumulativa.
- A lógica de tratamento e normalização de campos específicos dos relatórios (ex: distinção fina entre tipos de saldo e cabeçalhos legados) será implementada e calibrada aos poucos de forma modular e incremental pelo usuário.
- Os relatórios extraídos utilizam tabelas HTML legadas que serão normalizadas pelo extrator BeautifulSoup antes da fase de cruzamento.
