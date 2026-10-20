import asyncio
from typing import Any, Callable, Dict, List, Optional
import httpx
import pandas as pd
from backend.app.core.config import settings
from backend.app.extraction.parser import table_parser
from backend.app.extraction.snapshot import snapshot_manager


class ExtractionWorker:
    """
    Worker assíncrono isolado de extração.
    Atende ao Princípio II da Constituição:
    - Cada worker possui sua própria sessão HTTP isolada (self.session).
    - Cada worker realiza seu próprio login() uma única vez durante seu ciclo de vida,
      obtendo um PHPSESSID independente e exclusivo.
    - Autenticação e cookies gerenciados estritamente em memória.
    - Salvamento imutável de snapshot antes do parsing.
    """

    BASE_URL: str = settings.INTRANET_HOST.rstrip("/")
    LOGIN_PAGE: str = f"{BASE_URL}/home/login/"
    LOGIN_POST: str = f"{BASE_URL}/home/login/"

    def __init__(
        self,
        username: str = "",
        password: str = "",
        worker_id: int = 1,
        cookies: Optional[Dict[str, str]] = None,
        timeout: float = 120.0,
        base_url: Optional[str] = None,
    ):
        self.worker_id = worker_id
        self.username = username
        self.password = password
        self.timeout = timeout

        if base_url:
            self.BASE_URL = base_url.rstrip("/")
        else:
            self.BASE_URL = settings.INTRANET_HOST.rstrip("/")

        self.LOGIN_PAGE = f"{self.BASE_URL}/home/login/"
        self.LOGIN_POST = f"{self.BASE_URL}/home/login/"

        self._initial_cookies = dict(cookies or {})
        self.session: httpx.AsyncClient = httpx.AsyncClient(
            cookies=dict(self._initial_cookies),
            timeout=self.timeout,
            follow_redirects=True,
        )
        self._logged_in: bool = False

    async def __aenter__(self) -> "ExtractionWorker":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        """Encerra a sessão HTTP exclusiva deste worker ao fim do seu ciclo de vida."""
        if self.session is not None and not self.session.is_closed:
            await self.session.aclose()

    async def login(self) -> None:
        """
        Realiza o login individual do worker na intranet uma única vez
        durante o seu ciclo de vida, obtendo uma sessão (PHPSESSID) própria.
        """
        if self._logged_in:
            return

        await self.session.get(self.LOGIN_PAGE, timeout=10.0)

        response = await self.session.post(
            self.LOGIN_POST,
            data={
                "pagina_acessada": f"{self.BASE_URL}/home/login/",
                "action": "login",
                "usuario": self.username,
                "senha": self.password,
                "logar": "Acessar",
            },
            headers={
                "Referer": self.LOGIN_PAGE,
                "Origin": self.BASE_URL,
                "User-Agent": "Mozilla/5.0",
            },
            follow_redirects=True,
            timeout=10.0,
        )

        response.raise_for_status()

        if "PHPSESSID" not in self.session.cookies:
            raise RuntimeError("Login falhou: sessão não criada")

        # Verifica pela URL ou se o HTML de resposta ainda contém o formulário de login
        resp_url = str(response.url).lower()
        resp_text = response.text.lower()
        if (
            "login" in resp_url
            or 'name="logar"' in resp_text
            or "senha incorreta" in resp_text
        ):
            raise RuntimeError("Login falhou: credenciais inválidas")

        self._logged_in = True

    async def execute_task(
        self,
        execution_id: str,
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executa uma tarefa individual de scraping utilizando a sessão autenticada do worker:
        1. Garante que o login único do ciclo de vida do worker foi realizado.
        2. Dispara a requisição HTTP.
        3. Salva o snapshot HTML bruto em disco.
        4. Executa o parser BS4 e retorna o DataFrame estruturado.
        """
        task_id = task.get("task_id", "unknown_task")
        url = task.get("url")
        metodo = task.get("metodo", "POST").upper()
        headers = task.get("headers", {})
        payload = task.get("payload", {})
        grupo = task.get("grupo", "geral")
        local = task.get("local")

        try:
            # Garante que o worker fez login uma única vez em seu ciclo de vida
            if not self._logged_in:
                await self.login()

            if metodo == "POST":
                # Envia payload como form data (application/x-www-form-urlencoded)
                response = await self.session.post(url, data=payload, headers=headers)
            else:
                response = await self.session.get(url, params=payload, headers=headers)

            response.raise_for_status()
            html_text = response.text

            # 1. Salva o snapshot imutável em disco (Princípio III)
            snapshot_path = snapshot_manager.save_snapshot(execution_id, task_id, html_text)

            # 2. Executa o parser de tabela heurístico (Princípio IV)
            df = table_parser.parse_html_to_dataframe(html_text)

            # 3. Anexa metadados da tarefa ao DataFrame se não for vazio
            if not df.empty:
                df["_task_id"] = task_id
                df["_grupo"] = grupo
                df["_worker_id"] = self.worker_id
                if local:
                    df["_local_filtro"] = local

            return {
                "task_id": task_id,
                "worker_id": self.worker_id,
                "status": "SUCCESS",
                "snapshot_path": snapshot_path,
                "rows_extracted": len(df),
                "dataframe": df,
                "error": None,
            }

        except Exception as e:
            return {
                "task_id": task_id,
                "worker_id": self.worker_id,
                "status": "FAILED",
                "snapshot_path": None,
                "rows_extracted": 0,
                "dataframe": pd.DataFrame(),
                "error": str(e),
            }


async def execute_task_pool(
    execution_id: str,
    tasks: List[Dict[str, Any]],
    username: str = "",
    password: str = "",
    cookies: Optional[Dict[str, str]] = None,
    concurrency_limit: int = 15,
    on_auth_completed: Optional[Callable[[], None]] = None,
    on_task_completed: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> List[Dict[str, Any]]:
    """
    Orquestra um pool de workers assíncronos independentes.
    - Instancia N workers isolados (até concurrency_limit).
    - Cada worker possui sua própria sessão HTTP e realiza exatamente 1 login
      próprio no início de seu ciclo de vida (obtendo um PHPSESSID distinto).
    - As tarefas são distribuídas via fila (asyncio.Queue) entre os workers autenticados.
    - Ao final do ciclo de vida do pool, cada worker fecha sua própria sessão.
    """
    if not tasks:
        if on_auth_completed:
            on_auth_completed()
        return []

    num_workers = min(max(1, concurrency_limit), len(tasks))
    workers: List[ExtractionWorker] = [
        ExtractionWorker(
            username=username,
            password=password,
            worker_id=i + 1,
            cookies=cookies,
        )
        for i in range(num_workers)
    ]

    results: List[Optional[Dict[str, Any]]] = [None] * len(tasks)
    queue: asyncio.Queue = asyncio.Queue()
    for idx, task in enumerate(tasks):
        queue.put_nowait((idx, task))

    try:
        # 1. Cada worker realiza seu login individual uma única vez no início do ciclo de vida
        await asyncio.gather(*(w.login() for w in workers))

        if on_auth_completed:
            on_auth_completed()

        # 2. Cada worker consome tarefas da fila reutilizando sua sessão autenticada
        async def _worker_lifecycle(worker: ExtractionWorker) -> None:
            while not queue.empty():
                try:
                    idx, task = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

                try:
                    res = await worker.execute_task(execution_id, task)
                    results[idx] = res
                    if on_task_completed:
                        on_task_completed(res)
                finally:
                    queue.task_done()

        await asyncio.gather(*(_worker_lifecycle(w) for w in workers))

    finally:
        # 3. Encerra a sessão individual de cada worker ao fim do ciclo de vida
        await asyncio.gather(*(w.close() for w in workers), return_exceptions=True)

    return [r for r in results if r is not None]
