# API Interface Contracts: 001-frontend-ui-layout

**Base Path**: `/api/v1`  
**Protocol**: HTTP/JSON

---

## 1. POST `/api/v1/pipeline/start`
Triggers the full pipeline by receiving credentials and date parameters in memory.

### Request Body
```json
{
  "username": "operador.pcp",
  "password": "secret_password",
  "data_inicio": "2026-10-01",
  "data_fim": "2026-10-19",
  "fabricas": ["F01", "F02", "F03"]
}
```

### Responses
- **`202 Accepted`** (Pipeline dispatched to background workers)
  ```json
  {
    "execution_id": "exec_20261019_141500_abc123",
    "status": "RUNNING",
    "message": "Pipeline iniciado com sucesso. Acompanhe pelo status endpoint."
  }
  ```
- **`400 Bad Request`**: Validation error (invalid dates or missing fields).
- **`401 Unauthorized`**: Intranet authentication failed.

---

## 2. GET `/api/v1/pipeline/status/{execution_id}`
Returns real-time progress across the 6 pipeline stages.

### Response `200 OK`
```json
{
  "execution_id": "exec_20261019_141500_abc123",
  "stage": "EXTRACTING",
  "progress_pct": 45,
  "stages": {
    "auth": "COMPLETED",
    "extraction": "IN_PROGRESS",
    "treatment": "PENDING",
    "calculation": "PENDING",
    "serialization": "PENDING",
    "presentation": "PENDING"
  },
  "tasks_completed": 4,
  "tasks_total": 8,
  "elapsed_seconds": 6.4,
  "error_message": null
}
```

---

## 3. GET `/api/v1/results/{execution_id}`
Retrieves the assembled pointing errors and KPI summary for the Líder Design dashboard.

### Query Parameters
- `fabrica` (optional, string): Filter by factory.
- `local_producao` (optional, string): Filter by production location.
- `status_divergencia` (optional, string): Filter by divergence type (`SALDO_INSUFICIENTE`, `SALDO_ZERADO_NO_LOCAL`).
- `limit` (optional, integer, default: 100): Page limit.
- `offset` (optional, integer, default: 0): Page offset.

### Response `200 OK`
```json
{
  "execution_id": "exec_20261019_141500_abc123",
  "summary": {
    "total_ops_analisadas": 342,
    "total_componentes_baixa_auto": 1280,
    "total_erros_apontamento": 18,
    "total_ops_com_erro": 12,
    "taxa_conformidade_pct": 94.7,
    "tempo_processamento_segundos": 4.2
  },
  "pagination": {
    "total": 18,
    "limit": 100,
    "offset": 0
  },
  "records": [
    {
      "id": "F01-OP10492-CMP0088",
      "fabrica": "F01 - Móveis",
      "op": "OP-10492",
      "data_abertura": "2026-10-15",
      "data_entrega": "2026-10-22",
      "prioridade_fila": 3,
      "produto_op": "MESA DE JANTAR ELO 2.40",
      "local_producao": "LOC-MARCENARIA-01",
      "codigo_componente": "CMP-0088",
      "descricao_componente": "PARAFUSO SEXTAVADO INOX 1/4 X 2",
      "baixa_automatica": true,
      "qtd_necessaria": 24.0,
      "saldo_inicial_local": 30.0,
      "saldo_remanescente": 6.0,
      "deficit_saldo": 18.0,
      "status_divergencia": "SALDO_INSUFICIENTE",
      "severidade": "ALTA"
    }
  ]
}
```

---

## 4. GET `/api/v1/results/{execution_id}/export`
Downloads full processed errors in `csv` or `json` format.

### Query Parameters
- `format`: `csv` or `json`.
- `fabrica` (optional): Filter exported records.
