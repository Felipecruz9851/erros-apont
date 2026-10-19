# Quickstart & Validation Guide: 001-frontend-ui-layout

**Feature**: Frontend UI & Análise de Erros de Apontamento (Líder Design Style)  
**Date**: 2026-10-19  
**Status**: Ready for Implementation

This guide describes how to run and validate the complete end-to-end pipeline using offline mock intranet fixtures and test environments.

---

## 1. Prerequisites & Environment Setup

### 1.1 Backend (Python 3.10+)
Ensure virtual environment is active:
```powershell
# In repo root:
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic pandas numpy beautifulsoup4 lxml httpx requests pytest
```

### 1.2 Frontend (Node.js 18+)
```bash
cd frontend
npm install
```

---

## 2. Running the Development Servers

### 2.1 Start Backend Server
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
- API Documentation available at: `http://localhost:8000/docs`

### 2.2 Start Frontend Dev Server
```powershell
cd frontend
npm run dev
```
- Web Application available at: `http://localhost:5173`

---

## 3. End-to-End Validation Scenarios

### Scenario 1: Authentication & Pipeline Trigger
1. Access `http://localhost:5173` in a desktop browser.
2. Verify the Líder Design visual principles:
   - Off-white canvas (`#F8F8F8`) with dark rectangular button (`#222222`).
   - Clean whitespace, no heavy drop-shadows.
3. Enter intranet credentials and set date range (`data_inicio`, `data_fim`).
4. Click **"Iniciar Análise"**.
5. **Expected Outcome**:
   - Status 202 received from `POST /api/v1/pipeline/start`.
   - UI transitions to `PipelineMonitor`, displaying the 6-stage tracker.

### Scenario 2: Offline Mock Scraping & BS4 Table Extraction
Run the automated fixture-based integration test:
```powershell
pytest backend/tests/integration/test_pipeline_offline.py -v
```
- **Expected Outcome**:
  - Mock HTML snapshots loaded from `backend/tests/fixtures/`.
  - BeautifulSoup extracts both `df_consumo` and `df_estoque` without syntax exceptions.
  - Raw HTML snapshots saved under `backend/storage/snapshots/`.

### Scenario 3: Cumulative Allocation Verification (Prioritized by Delivery Date)
Run the calculation engine unit test:
```powershell
pytest backend/tests/unit/test_cumulative_allocation.py -v
```
- **Expected Outcome**:
  - When two OPs require Component `CMP-0088` at `LOC-MARCENARIA-01` (stock: 30):
    - OP 1 (Delivery: 2026-10-22, need: 24) $\rightarrow$ allocated 24, remaining 6 (No error).
    - OP 2 (Delivery: 2026-10-25, need: 16) $\rightarrow$ allocated 6, deficit 10 $\rightarrow$ Flagged as `SALDO_INSUFICIENTE`.

### Scenario 4: Results Dashboard & Líder Design Export
1. On frontend, once execution finishes, verify:
   - **MetricsCards** display summary totals (Total OPs, Automatic Deduction items, Deficit count, Compliance %).
   - **PointingErrorsTable** displays records with 1px fine dividers (`#E0E0E0`).
   - Filter dropdown by "Fábrica" instantly filters rows.
2. Click **"Exportar Resultados (CSV)"**.
3. **Expected Outcome**:
   - Browser initiates instant CSV download containing the filtered discrepancy rows.
