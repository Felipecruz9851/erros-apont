# Tasks: Frontend UI & Análise de Erros de Apontamento (Líder Design Style)

**Branch**: `001-frontend-ui-layout` | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, environment dependencies, and shared configs.

- [x] T001 Initialize backend and frontend workspace directory structure per implementation plan (`backend/app/api`, `backend/app/core`, `backend/app/engine`, `backend/app/extraction`, `backend/app/models`, `backend/app/tasks`, `backend/storage/snapshots`, `backend/tests/fixtures`, `frontend/src/components`, `frontend/src/hooks`, `frontend/src/services`, `frontend/src/types`)
- [x] T002 Configure backend Python dependencies in `backend/requirements.txt` (`fastapi`, `uvicorn`, `pydantic>=2.0`, `pandas`, `numpy`, `beautifulsoup4`, `lxml`, `httpx`, `pytest`)
- [x] T003 [P] Initialize frontend React + TypeScript + Vite project configuration in `frontend/package.json` and `frontend/vite.config.ts`
- [x] T004 [P] Configure Tailwind CSS with Líder Design tokens (`#F8F8F8`, `#1A1A1A`, `#8B5A2B`, `#E0E0E0`, 1px borders, 2-4px radius) in `frontend/tailwind.config.js` and `frontend/src/index.css`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data models, task generator, snapshot manager, and table parser that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create Pydantic domain models in `backend/app/models/domain.py` quoting exact constraints from `data-model.md` (`OPRecord`, `ConsumoRecord` with `baixa_automatica: bool = True`, `EstoqueRecord` with `saldo_disponivel: float`, `ErroApontamento` with `status_divergencia: Literal["SALDO_INSUFICIENTE", "SALDO_ZERADO_NO_LOCAL", "ITEM_SEM_CADASTRO_ESTOQUE"]`, `severidade: Literal["ALTA", "MEDIA"]`, composite `id: str = f"{fabrica}-{op}-{codigo_componente}"`, and `ExecutionState: Literal["IDLE", "RUNNING", "COMPLETED", "FAILED"]`)
- [x] T006 [P] Create request and response schemas in `backend/app/models/requests.py` (`StartPipelineRequest` with `username`, `password`, `data_inicio`, `data_fim`, `fabricas`, `StatusResponse`, `ResultsResponse`, `SummaryMetrics`)
- [x] T007 [P] Implement in-memory security credential manager in `backend/app/core/security.py` strictly enforcing Principle II (zero credential persistence to disk or log files)
- [x] T008 Implement Task Generator in `backend/app/tasks/generator.py` loading `config/tarefas_esqueleto.json` and expanding tasks via iteration (`for local in locais: tarefas.append(...)`) for endpoints with `iterar_por_local == true`, injecting `cod_empresa: "11"` and temporal date parameters
- [x] T009 [P] Implement raw HTML snapshot manager in `backend/app/extraction/snapshot.py` persisting immutable raw HTML files to `backend/storage/snapshots/{execution_id}_{task_id}.html` to satisfy Constitution Principle III
- [x] T010 [P] Implement resilient BeautifulSoup4 legacy table parser in `backend/app/extraction/parser.py` handling unrolled `colspan`/`rowspan`, HTML entity cleanup, and whitespace trimming to return clean pandas DataFrames
- [x] T011 Create FastAPI application entrypoint with CORS middleware in `backend/app/main.py` and configuration settings in `backend/app/core/config.py`

**Checkpoint**: Foundation ready - task expansion, HTML parsing, domain entities, and snapshot storage are verified.

---

## Phase 3: User Story 1 - Ingestão de Credenciais e Disparo da Extração Dupla Multi-Fábrica (Priority: P1) 🎯 MVP

**Goal**: Permitir ao usuário submeter credenciais corporativas e intervalo de datas (abertura e entrega) no frontend/API para autenticar na intranet e disparar as tarefas de extração paralela dos relatórios de consumo e estoque.

**Independent Test**: Submeter payload com login, senha e período de datas para `POST /api/v1/pipeline/start`, verificando se a sessão HTTP é criada, as tarefas de extração para `consumo_alt.php` e `estoque_lote.php` são geradas via `generator.py` e os workers disparam as requisições salvando os snapshots HTML.

### Implementation for User Story 1

- [x] T012 [P] [US1] Implement asynchronous isolated worker runner in `backend/app/extraction/worker.py` handling intranet session login, cookie management, and concurrent task execution via `httpx.AsyncClient`
- [x] T013 [US1] Implement execution orchestrator in `backend/app/engine/orchestrator.py` coordinating the 6 stages, maintaining in-memory task queues and updating execution state
- [x] T014 [US1] Implement FastAPI pipeline trigger route `POST /api/v1/pipeline/start` in `backend/app/api/pipeline.py` accepting `StartPipelineRequest` and returning `202 Accepted` with `execution_id`
- [x] T015 [P] [US1] Create frontend API client service in `frontend/src/services/api.ts` with Axios configuring base URL and error handlers
- [x] T016 [P] [US1] Implement discrete Líder-styled credential login card component in `frontend/src/components/auth/LoginCard.tsx` with date pickers (data de abertura/entrega), submit button, and subtle inline error display

**Checkpoint**: User Story 1 is functional. An analyst can trigger extraction with credentials and dates, generating snapshots on disk.

---

## Phase 4: User Story 2 - Acompanhamento do Pipeline de Extração e Cruzamento de Dados (Priority: P2)

**Goal**: Apresentar visibilidade em tempo real do status das 6 fases do pipeline (Auth, Extração de Consumo, Extração de Estoque, Tratamento, Cálculo e Conclusão), com volume de ordens extraídas e progresso percentual.

**Independent Test**: Polling no endpoint `GET /api/v1/pipeline/status/{execution_id}` refletindo a transição de estágios e renderização da barra de progresso no componente `PipelineMonitor.tsx`.

### Implementation for User Story 2

- [x] T017 [US2] Implement pipeline status endpoint `GET /api/v1/pipeline/status/{execution_id}` in `backend/app/api/pipeline.py` returning stage progress, elapsed time, and task completion counts
- [x] T018 [US2] Create React pipeline polling hook in `frontend/src/hooks/usePipeline.ts` managing execution state, active stage, and auto-refresh intervals
- [x] T019 [P] [US2] Implement 6-stage visual pipeline monitor component in `frontend/src/components/monitor/PipelineMonitor.tsx` with Líder Design understated progress bar, stage chips, and task counters

**Checkpoint**: User Stories 1 AND 2 work together. The user starts extraction and watches real-time progress across all 6 stages.

---

## Phase 5: User Story 3 - Painel Analítico de Erros de Apontamento e Saldo no Local de Produção (Priority: P3)

**Goal**: Executar o saneamento modular, calcular a alocação cumulativa sequencial de saldo por data de entrega da OP, apontar déficits para componentes de baixa automática e exibir os resultados no dashboard analítico Estilo Líder com filtros e exportação.

**Independent Test**: Carregar dados de consumo e estoque mockados (ou reais extraídos), executar `calculate_pointing_errors`, verificar que ordens com menor data de entrega consomem saldo primeiro e ordens posteriores que excedem o saldo geram `ErroApontamento` na rota `GET /api/v1/results/{execution_id}`, exibindo na tabela do dashboard.

### Implementation for User Story 3

- [x] T020 [P] [US3] Implement modular and incremental data treatment functions in `backend/app/engine/treatment.py` normalizing factory codes, location strings (`local_producao`), OP numbers, and date formats (`data_abertura`, `data_entrega`)
- [x] T021 [US3] Implement cumulative stock allocation calculation engine in `backend/app/engine/calculation.py` sorting OPs by `data_entrega` ascending, computing running cumulative consumption per component and location, and flagging errors where `baixa == 'S'` and `saldo_remanescente < qtd_necessaria`
- [x] T022 [US3] Implement JSON results serializer and summary KPI aggregator in `backend/app/engine/serializer.py` outputting `total_ops_analisadas`, `total_componentes_baixa_auto`, `total_erros_apontamento`, and formatted record items
- [x] T023 [US3] Implement results retrieval endpoint `GET /api/v1/results/{execution_id}` in `backend/app/api/results.py` with pagination and query filters (`fabrica`, `local_producao`, `status_divergencia`)
- [x] T024 [P] [US3] Implement report export endpoint `GET /api/v1/results/{execution_id}/export` in `backend/app/api/results.py` supporting `csv` and `json` formats
- [x] T025 [P] [US3] Implement KPI metric cards component in `frontend/src/components/dashboard/MetricsCards.tsx` rendering summary totals in Líder off-white cards with editorial typography
- [x] T026 [US3] Implement analytical results table in `frontend/src/components/dashboard/PointingErrorsTable.tsx` featuring 1px dividers, sticky headers, sorting, multi-column search, severity badges, and pagination
- [x] T027 [P] [US3] Implement fixed Header and Sidebar layout components in `frontend/src/components/layout/Header.tsx`, `frontend/src/components/layout/Sidebar.tsx`, and `frontend/src/components/layout/MainLayout.tsx` providing factory selectors, date indicators, and export actions
- [x] T028 [US3] Integrate full dashboard view in `frontend/src/App.tsx` connecting auth trigger, pipeline monitor, metrics cards, table filters, and CSV/JSON downloads

**Checkpoint**: Complete end-to-end functionality active. Users can audit pointing errors with full cumulative allocation and export reports.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, offline test fixtures, documentation sync, and logbook recording.

- [x] T029 [P] Create offline test fixtures with mock HTML responses for `consumo_alt.php` and `estoque_lote.php` in `backend/tests/fixtures/`
- [x] T030 Create integration test script `backend/tests/integration/test_pipeline_offline.py` verifying full pipeline execution against offline fixtures without intranet connection
- [x] T031 Validate quickstart scenarios and update `specs/001-frontend-ui-layout/quickstart.md` with verified execution commands
- [x] T032 Update Obsidian Vault notes in `vault-erros-apont/` and record session log in `vault-erros-apont/erros-apont-logbook/2026-10-19.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — executes immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS** all user story phases.
- **User Story 1 (Phase 3 - P1 MVP)**: Depends on Phase 2 completion.
- **User Story 2 (Phase 4 - P2)**: Depends on Phase 3 backend runner and orchestrator.
- **User Story 3 (Phase 5 - P3)**: Depends on Phase 3 and Phase 4.
- **Polish (Phase 6)**: Depends on all user story phases.

### User Story Dependencies

- **US1 (P1)**: Foundational prerequisites $\rightarrow$ Worker $\rightarrow$ Orchestrator $\rightarrow$ Trigger Route $\rightarrow$ Login UI.
- **US2 (P2)**: Integrates with US1 orchestrator $\rightarrow$ Status Route $\rightarrow$ Monitor UI.
- **US3 (P3)**: Consumes extracted DataFrames $\rightarrow$ Treatment $\rightarrow$ Cumulative Calculation $\rightarrow$ Results Route $\rightarrow$ Dashboard UI.

### Parallel Opportunities

- **Phase 1**: T003 (Vite config) and T004 (Tailwind config) can execute in parallel with backend setup.
- **Phase 2**: T006 (Request models), T007 (Security manager), T009 (Snapshot manager), and T010 (BS4 parser) can execute in parallel after T005.
- **Phase 3**: T012 (Worker) and T015/T016 (Frontend client & LoginCard) can execute in parallel.
- **Phase 5**: T020 (Treatment) and T025/T027 (MetricsCards & Layout) can execute in parallel.
- **Phase 6**: T029 (Fixtures) can be created in parallel with integration test writing.

---

## Parallel Example: User Story 3

```bash
# Parallel execution of domain treatment & frontend layout:
Task: "T020 [P] [US3] Implement modular and incremental data treatment functions in backend/app/engine/treatment.py"
Task: "T025 [P] [US3] Implement KPI metric cards component in frontend/src/components/dashboard/MetricsCards.tsx"
Task: "T027 [P] [US3] Implement fixed Header and Sidebar layout components in frontend/src/components/layout/Header.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (blocking prerequisites)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with live intranet credentials or mock server

### Incremental Delivery

1. Setup + Foundational $\rightarrow$ Core engine ready
2. Add User Story 1 $\rightarrow$ Trigger extraction & capture snapshots (MVP!)
3. Add User Story 2 $\rightarrow$ Real-time 6-stage monitor
4. Add User Story 3 $\rightarrow$ Cumulative allocation calculation & Líder Design analytical table
5. Polish $\rightarrow$ Offline fixtures & integration tests
