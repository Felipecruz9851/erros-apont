# Research & Technical Decisions: 001-frontend-ui-layout

**Feature**: Frontend UI & Análise de Erros de Apontamento (Líder Design Style)  
**Date**: 2026-10-19  
**Status**: Completed

## 1. Frontend Architecture & Líder Design System

### Decision
Adopt **React 18+ with Vite and Tailwind CSS**, structured as a 3-zone layout (Fixed Sidebar, Fixed Header, Scrollable Main Canvas).

### Rationale
- Strictly aligns with the project's consolidated guidelines (`refs_layout/Guia_Consolidado_UI_UX_Lider.md`).
- Tailwind CSS enables precise control over custom color tokens (`#F8F8F8`, `#1A1A1A`, `#8B5A2B`), razor-thin 1px borders (`#E0E0E0`), and minimal border radiuses (`2px-4px` / `rounded-sm`).
- Shadow limitations ($\le 5\%$ opacity: `rgba(0,0,0,0.05)`) and generous whitespace (paddings of `24px` to `48px`) reproduce the sophisticated "catálogo de luxo digital" aesthetic.
- Component architecture maps directly to business requirements:
  - `LoginCard`: Discreet modal/card for in-memory credential input.
  - `PipelineMonitor`: Restrained 6-stage tracker.
  - `MetricsCards`: Key indicator summary tiles.
  - `PointingErrorsTable`: High-performance data table with sorting, multi-column filtering, and pagination.

### Alternatives Considered
- *FastAPI + Jinja2 + Alpine.js*: Lacks the rich component ecosystem and fluid interactive state needed for high-volume multi-factory tabular filtering and instantaneous sorting specified in the Líder Design guide.
- *Material UI / Ant Design*: Rejected because pre-packaged opinionated UI component libraries enforce bulky border radiuses and shadows that conflict with the Líder Design minimal aesthetic.

---

## 2. Scraping Engine & Worker Session Isolation

### Decision
Implement an asynchronous worker pool using `asyncio` and `httpx` (or worker-isolated `requests.Session` instances within an async thread pool).

### Rationale
- Constitution Principle II mandates that each worker instance authenticate independently, retain its own token/cookies, and prevent state leakage.
- Python `httpx.AsyncClient` or worker-bound `requests.Session` ensures complete cookie jar and authorization header isolation.
- Credential security: The user's intranet password is received in memory during the trigger request, provisioned directly into worker instantiation, and discarded without touching disk storage or log files.

### Alternatives Considered
- *Single shared session for all workers*: Violates Constitution Principle II and causes session collision / token race conditions on legacy intranet endpoints.
- *Headless browser (Playwright / Selenium)*: Excessive resource overhead, slow execution, and unnecessary for HTML table endpoints that respond to standard HTTP GET/POST.

---

## 3. Resilient Legacy Table Parsing (BeautifulSoup)

### Decision
Parse HTML snapshots using **BeautifulSoup4 with the `lxml` parser**, implementing heuristic pattern matching over table structures.

### Rationale
- Vintage intranet HTML frequently contains unclosed tags (`<tr>` without `</tr>`), uppercase markup (`<TABLE>`, `<TD>`), presentation tables nested inside data tables, and irregular `colspan` / `rowspan` usage.
- Heuristic algorithm:
  1. Detect target tables by examining header cell contents (e.g. matching keywords like "Ordem", "Componente", "Baixa", "Saldo", "Local").
  2. Handle merged cells by unrolling `colspan` and `rowspan` into regular 2D matrices.
  3. Strip whitespace, non-breaking spaces (`&nbsp;`), and formatting characters cleanly.
  4. Convert parsed rows into typed pandas DataFrames.

### Alternatives Considered
- *`pd.read_html()` exclusively*: Prone to throwing errors on malformed nested tables or misaligning headers with multi-row spans.
- *Rigid CSS / XPath selectors*: Extremely fragile; small template updates in the intranet break the extraction.

---

## 4. Cumulative Allocation Algorithm (Prioritized by OP Delivery Date)

### Decision
Calculate available balance by simulating a **cumulative consumption queue** grouped by `(codigo_componente, local_producao)`, sorted in ascending order of `data_entrega` (and `data_abertura` as secondary tie-breaker).

### Rationale
- Resolves Clarification Q1: When multiple open OPs compete for the same component in the same production location, earlier-delivery orders consume physical inventory first.
- Algorithmic formulation:
  $$\text{saldo\_remanescente}_i = \text{saldo\_inicial} - \sum_{k=1}^{i-1} \text{qtd\_necessaria}_k$$
  $$\text{deficit}_i = \max(0, \text{qtd\_necessaria}_i - \max(0, \text{saldo\_remanescente}_i))$$
- If $\text{deficit}_i > 0$, the record is flagged as `SALDO_INSUFICIENTE` (or `SALDO_ZERADO` if initial balance is 0).

### Alternatives Considered
- *Independent evaluation per OP*: Creates false-positive compliance where multiple OPs individually see enough stock, but simultaneously exhaust physical inventory.
- *Bulk aggregated group comparison without OP mapping*: Fails to identify *which* specific production orders will suffer stoppage, making actionable factory intervention impossible.

---

## 5. Modular & Incremental Data Treatment

### Decision
Structure the data treatment layer as an extensible chain of pure transformation functions in `backend/app/engine/treatment.py`.

### Rationale
- Directly addresses Clarification Q3 ("tratamento de dados vou fazer aos poucos").
- Allows the user to incrementally add, refine, or adjust column mappings, string cleaning rules, date parsing formats, and balance field definitions as actual intranet report variations are discovered.
- Separates structural raw table parsing (BS4) from domain-specific data sanitization.
