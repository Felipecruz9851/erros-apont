---
modulo: "Extrator_Workers_e_HTML"
tipo: "infra"
linguagem: "python"
data_atualizacao: 2026-11-10
tags: [codigo, infra, scraping, workers, lxml, httpx, login, polars, paralelismo]
---

# Módulo: Extrator_Workers_e_HTML

**Responsabilidade:** Orquestrador do pool de workers assíncronos e paralelos (`backend/app/extraction/worker.py`). Cada worker instancia sua própria sessão HTTP isolada (`self.session`), realiza seu próprio `login()` uma única vez durante o seu ciclo de vida (obtendo um `PHPSESSID` exclusivo para evitar bloqueio de sessão no servidor PHP), baixa o HTML bruto da intranet com pooling otimizado de conexões HTTPX (`httpx.Limits`), despacha o snapshot e parsing de alta velocidade (`lxml.html`) fora do event loop via `asyncio.to_thread` e produz `polars.DataFrame` estruturado.

## Principais Funções / Métodos
* `ExtractionWorker.login()`: Realiza o login individual do worker na intranet (`GET` + `POST` em `/home/login/`) uma única vez em seu ciclo de vida (`self._logged_in = True`), validando a criação do cookie `PHPSESSID` e verificando ausência de erros de credenciais no HTML/URL de resposta.
* `ExtractionWorker.execute_task()`: Garante o login único do worker, efetua requisição HTTP (`GET`/`POST`) reutilizando `self.session` com pooling de conexões assíncronas, desacopla o salvamento em disco e o parsing C (`lxml.html`) via `asyncio.to_thread` e retorna o resultado sem bloquear o loop do `asyncio`.
* `execute_task_pool()`: Instancia $N$ workers independentes (`ExtractionWorker`), executa o `login()` individual de cada worker no início do seu ciclo de vida, distribui as tarefas via `asyncio.Queue` e encerra as sessões ao fim do ciclo.
* `LegacyTableParser.parse_html_to_polars()`: Parser compilado em C (`lxml.html`) com retenção de todas as nuances legadas (`colspan`, `rowspan`, links com `local=`, snippets de PHP) e fallback automático para BeautifulSoup em anomalias extremas.
* `SnapshotManager`: Gerenciamento de snapshots imutáveis em disco e persistência de dados em formato de alta performance Apache Parquet (`.parquet`) e Pickle (`.pkl`).

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/Rotas_FastAPI_e_Sessao]]
* [[05-Automacoes/Gerador_Tarefas_Scraping]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[03-Dominio-Calculos/Motor_Calculo_Pandas]]
* **Bibliotecas Externas:** `httpx`, `polars`, `lxml`, `pyarrow`, `beautifulsoup4`, `asyncio`.
