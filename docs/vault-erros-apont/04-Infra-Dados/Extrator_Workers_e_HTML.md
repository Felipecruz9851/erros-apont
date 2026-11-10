---
modulo: "Extrator_Workers_e_HTML"
tipo: "infra"
linguagem: "python"
data_atualizacao: 2026-10-20
tags: [codigo, infra, scraping, workers, beautifulsoup, httpx, login]
---

# Módulo: Extrator_Workers_e_HTML

**Responsabilidade:** Orquestrador do pool de workers assíncronos e paralelos (`backend/app/extraction/worker.py`). Cada worker instancia sua própria sessão HTTP isolada (`self.session`), realiza seu próprio `login()` uma única vez durante o seu ciclo de vida (obtendo um `PHPSESSID` exclusivo para evitar bloqueio de sessão no servidor PHP), baixa o HTML bruto da intranet, armazena snapshot completo em disco e executa extração robusta de tabelas com BeautifulSoup.

## Principais Funções / Métodos
* `ExtractionWorker.login()`: Realiza o login individual do worker na intranet (`GET` + `POST` em `/home/login/`) uma única vez em seu ciclo de vida (`self._logged_in = True`), validando a criação do cookie `PHPSESSID` e verificando ausência de erros de credenciais no HTML/URL de resposta.
* `ExtractionWorker.execute_task()`: Garante o login único do worker, efetua requisição HTTP (`GET`/`POST`) reutilizando `self.session`, salva o snapshot HTML bruto integral e extrai o `pd.DataFrame`.
* `execute_task_pool()`: Instancia $N$ workers independentes (`ExtractionWorker`), executa o `login()` individual de cada worker no início do seu ciclo de vida, distribui as tarefas via `asyncio.Queue` e encerra as sessões ao fim do ciclo.
* `TableParser.parse_html_to_dataframe()`: Analisa tags HTML legadas (`table`, `tr`, `td`, `th`, `colspan`, `rowspan`) e converte para `pd.DataFrame`.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/Rotas_FastAPI_e_Sessao]]
* [[05-Automacoes/Gerador_Tarefas_Scraping]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[03-Dominio-Calculos/Motor_Calculo_Pandas]]
* **Bibliotecas Externas:** `httpx`, `beautifulsoup4`, `lxml`, `pandas`, `asyncio`.
