---
modulo: "Extrator_Workers_e_HTML"
tipo: "infra"
linguagem: "python"
data_atualizacao: 2026-10-19
tags: [codigo, infra, scraping, workers, beautifulsoup, requests]
---

# Módulo: Extrator_Workers_e_HTML

**Responsabilidade:** Orquestrador do pool de workers assíncronos e paralelos. Cada worker realiza autenticação individual, guarda seu token, baixa o HTML bruto da intranet, armazena snapshot completo em disco e executa extração robusta de tabelas com BeautifulSoup.

## Principais Funções / Métodos
* `Worker.authenticate()`: Realiza o login na intranet e retém os cookies/token de sessão.
* `Worker.fetch_page()`: Efetua requisição HTTP (GET/POST) com payload e salva o HTML bruto integral.
* `parse_legacy_tables()`: Analisa tags HTML legadas (`table`, `tr`, `td`, `th`, `colspan`, `rowspan`) e converte para `pd.DataFrame`.
* `ExtractionPool.run_all()`: Executa tarefas paralelamente e compila o `Dict[str, pd.DataFrame]`.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/Rotas_FastAPI_e_Sessao]]
* [[05-Automacoes/Gerador_Tarefas_Scraping]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[03-Dominio-Calculos/Motor_Calculo_Pandas]]
* **Bibliotecas Externas:** `requests`, `httpx`, `beautifulsoup4`, `lxml`, `pandas`, `asyncio`.
