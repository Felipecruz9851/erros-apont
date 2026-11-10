# Implementation Plan: Frontend UI & Análise de Erros de Apontamento (Líder Design Style)

**Branch**: `001-frontend-ui-layout` | **Date**: 2026-10-19 | **Spec**: [spec.md](file:///c:/Users/engli/Desktop/Erros-apont/specs/001-frontend-ui-layout/spec.md)

**Input**: Feature specification from `specs/001-frontend-ui-layout/spec.md`

## Summary

Build an end-to-end industrial pointing error analysis system with an editorial, minimalist web dashboard adhering to the **Líder Design** visual identity (off-white palette, 1px fine dividers, rectangular buttons, generous whitespace). The solution ingests intranet credentials in memory to trigger a 6-stage pipeline: asynchronous parallel scraping of two core reports (**Consumo de Componentes por Ordem** across all factories and **Estoque por Local**), local raw HTML snapshot persistence, fault-tolerant BeautifulSoup table parsing, modular data treatment, cumulative stock balance allocation prioritized by OP delivery date, and standardized JSON serialization exposed via FastAPI to a React + Vite + Tailwind CSS frontend.

## Technical Context

**Language/Version**: Python 3.10+ (Backend) & TypeScript / React 18+ (Frontend)  
**Primary Dependencies**:
- Backend: FastAPI, Uvicorn, Pydantic v2, Pandas, NumPy, BeautifulSoup4, Lxml, HTTPX / Requests
- Frontend: React 18, Vite, Tailwind CSS, Lucide React (line icons)  
**Storage**: Local filesystem for immutable raw HTML snapshots (`backend/storage/snapshots/`); ephemeral in-memory cache for execution session tokens and DataFrames.  
**Testing**: Pytest (unit & integration with offline mock HTML fixtures); Vitest / React Testing Library.  
**Target Platform**: Desktop web browser (Chrome, Edge, Firefox) on standard corporate workstations.  
**Project Type**: Web application (FastAPI backend + Vite React frontend).  
**Performance Goals**:
- Table filtering and sorting: <200ms for up to 5,000 rows.
- Calculation & JSON assembly: <5 seconds for 50,000 component consumption records.  
**Constraints**:
- Zero disk persistence for intranet passwords (in-memory only).
- Visual compliance: 100% adherence to Líder Design guidelines (borders $\le 1\text{px}$, corner radiuses $\le 4\text{px}$, shadows $\le 5\%$).  
**Scale/Scope**: All company factories, OPs active within configured opening/delivery date windows.

## Constitution Check

*GATE: Evaluated against Erros-apont Constitution v1.1.0*

| Principle / Rule | Status | Evaluation & Compliance Notes |
|---|:---:|---|
| **I. Modular Pipeline & Decoupled Data Flow** | **PASS** | Strict separation: Task generator $\rightarrow$ Async scraping workers $\rightarrow$ Modular data treatment $\rightarrow$ Cumulative pandas calculation $\rightarrow$ JSON assembly $\rightarrow$ FastAPI presentation. |
| **II. Isolated & Authenticated Workers** | **PASS** | Workers maintain independent `httpx.AsyncClient` / session contexts. User credentials ingested in memory at trigger and never saved to disk or logs. |
| **III. Raw HTML Snapshotting & Auditability** | **PASS** | Full raw HTML payloads stored under `backend/storage/snapshots/` prior to parsing to enable offline reproducibility. |
| **IV. Resilient Legacy Table Parsing (BS4)** | **PASS** | BeautifulSoup with `lxml` parser inspects tags, unrolls `colspan`/`rowspan`, and sanitizes non-standard legacy markup. |
| **V. Standardized DataFrame Contract & JSON Assembly** | **PASS** | Extraction returns `Dict[str, pd.DataFrame]`; calculation performs cumulative allocation prioritized by delivery date and outputs validated JSON payload. |

## Project Structure

### Documentation (this feature)

```text
specs/001-frontend-ui-layout/
├── spec.md                  # Feature Specification
├── plan.md                  # This Implementation Plan
├── research.md              # Technical research & decisions (Phase 0)
├── data-model.md            # Entity schemas & state machines (Phase 1)
├── quickstart.md            # End-to-end run & validation scenarios (Phase 1)
├── contracts/               # Interface schemas & API contracts (Phase 1)
│   ├── api-routes.md
│   ├── task-skeleton.json
│   └── pointing-errors-response.json
└── checklists/
    └── requirements.md      # Spec Quality Checklist
```

### Source Code Structure

```text
backend/
├── app/
│   ├── api/                 # FastAPI routers
│   │   ├── deps.py          # Session and parameter dependencies
│   │   ├── pipeline.py      # POST /start, GET /status endpoints
│   │   └── results.py       # GET /results, GET /export endpoints
│   ├── core/                # System configuration & logging
│   │   ├── config.py
│   │   └── security.py      # In-memory token & credential sanitation
│   ├── engine/              # Computational & domain logic
│   │   ├── calculation.py   # Cumulative stock allocation by OP delivery date
│   │   ├── treatment.py     # Modular & incremental data cleaning functions
│   │   └── serializer.py    # DataFrame to JSON assembly
│   ├── extraction/          # Intranet scraping & HTML parsing
│   │   ├── parser.py        # Resilient BeautifulSoup legacy table extractor
│   │   ├── snapshot.py      # Raw HTML disk snapshot manager
│   │   └── worker.py        # Asynchronous isolated worker & session runner
│   ├── models/              # Pydantic data schemas
│   │   ├── domain.py        # OP, Consumo, Estoque, ErroApontamento
│   │   └── requests.py      # LoginPayload, StatusResponse
│   ├── tasks/               # Task generator
│   │   └── generator.py     # Task skeleton expansion & factory parameterization
│   └── main.py              # FastAPI app initialization & CORS setup
├── storage/
│   └── snapshots/           # Immutable HTML snapshots directory
├── tests/
│   ├── fixtures/            # Mock intranet HTML table pages
│   ├── unit/                # Parser, calculation, treatment tests
│   └── integration/         # Full pipeline offline tests
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── components/          # Líder Design UI components
│   │   ├── layout/
│   │   │   ├── Header.tsx   # Fixed top bar with title & export button
│   │   │   ├── Sidebar.tsx  # Fixed left navigation & factory summary
│   │   │   └── MainLayout.tsx
│   │   ├── auth/
│   │   │   └── LoginCard.tsx # Discreet credential input modal/card
│   │   ├── monitor/
│   │   │   └── PipelineMonitor.tsx # 6-stage visual progress tracker
│   │   ├── dashboard/
│   │   │   ├── MetricsCards.tsx # Summary KPI cards
│   │   │   └── PointingErrorsTable.tsx # 1px divider table with filters
│   ├── hooks/
│   │   └── usePipeline.ts   # Pipeline execution, polling & state hook
│   ├── services/
│   │   └── api.ts           # Axios HTTP client
│   ├── types/
│   │   └── index.ts         # TypeScript definitions
│   ├── App.tsx
│   └── main.tsx
├── tailwind.config.js       # Líder Design palette, borders & font tokens
├── package.json
└── vite.config.ts
```

**Structure Decision**: Selected the decoupled Web Application layout (`backend/` + `frontend/`) to strictly satisfy the separation of concerns between Python-based data processing (FastAPI/Pandas/BS4) and modern interactive presentation (React/Tailwind) following the Líder Design visual guidelines.

## Complexity Tracking

> **Constitution Check has ZERO violations.** All architectural principles are strictly adhered to without exceptional complexity waivers needed.
