---
modulo: "Rotas_FastAPI_e_Sessao"
tipo: "backend"
linguagem: "python"
data_atualizacao: 2026-10-19
tags: [codigo, backend, api, fastapi, pydantic]
---

# Módulo: Rotas_FastAPI_e_Sessao

**Responsabilidade:** Servidor FastAPI responsável por receber credenciais efêmeras em memória, gerenciar ciclo de vida da execução assíncrona, orquestrar os workers e expor dados calculados para o dashboard Líder Design.

## Rotas Implementadas (`backend/app/api/`)
* `POST /api/v1/pipeline/start` (`pipeline.py`): Recebe `StartPipelineRequest` com credenciais, período de datas e filtro de fábricas; armazena senhas temporariamente via `InMemorySecurityManager` e dispara o orquestrador em background retornando `202 Accepted` com `execution_id`.
* `GET /api/v1/pipeline/status/{execution_id}` (`pipeline.py`): Retorna o percentual de progresso, estágio atual (`ExecutionState`), contagem de tarefas concluídas e tempo decorrido.
* `GET /api/v1/results/{execution_id}` (`results.py`): Retorna `ResultsResponse` com KPIs consolidados (`SummaryMetrics`) e lista paginada de divergências com suporte a filtros por `fabrica`, `local_producao` e `status_divergencia`.
* `GET /api/v1/results/{execution_id}/export` (`results.py`): Gera download instantâneo nos formatos `csv` (separador `;` com encoding `utf-8-sig` para Excel) ou `json`.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[Interface_Login_e_Resultados]]
* [[usePipeline]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[Extrator_Workers_e_HTML]]
* [[Motor_Calculo_Pandas]]
* [[Gerador_Tarefas_Scraping]]
* **Bibliotecas Externas:** `fastapi`, `uvicorn`, `pydantic`.
