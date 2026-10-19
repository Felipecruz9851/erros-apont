import asyncio
from typing import Any, Dict, List, Optional
import httpx
import pandas as pd
from backend.app.extraction.parser import table_parser
from backend.app.extraction.snapshot import snapshot_manager


class ExtractionWorker:
    """
    Worker assíncrono isolado de extração.
    Atende ao Princípio II da Constituição:
    - Sessão HTTP isolada por worker com httpx.AsyncClient.
    - Autenticação e cookies gerenciados estritamente em memória.
    - Salvamento imutável de snapshot antes do parsing.
    """

    def __init__(self, cookies: Optional[Dict[str, str]] = None, timeout: float = 60.0):
        self.cookies = cookies or {}
        self.timeout = timeout

    async def execute_task(
        self,
        execution_id: str,
        task: Dict[str, Any],
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """
        Executa uma tarefa individual de scraping:
        1. Dispara a requisição HTTP.
        2. Salva o snapshot HTML bruto em disco.
        3. Executa o parser BS4 e retorna o DataFrame estruturado.
        """
        task_id = task.get("task_id", "unknown_task")
        url = task.get("url")
        metodo = task.get("metodo", "POST").upper()
        headers = task.get("headers", {})
        payload = task.get("payload", {})
        grupo = task.get("grupo", "geral")
        local = task.get("local")

        close_client = False
        if client is None:
            client = httpx.AsyncClient(cookies=self.cookies, timeout=self.timeout, follow_redirects=True)
            close_client = True

        try:
            if metodo == "POST":
                # Envia payload como form data (application/x-www-form-urlencoded)
                response = await client.post(url, data=payload, headers=headers)
            else:
                response = await client.get(url, params=payload, headers=headers)

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
                if local:
                    df["_local_filtro"] = local

            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "snapshot_path": snapshot_path,
                "rows_extracted": len(df),
                "dataframe": df,
                "error": None,
            }

        except Exception as e:
            return {
                "task_id": task_id,
                "status": "FAILED",
                "snapshot_path": None,
                "rows_extracted": 0,
                "dataframe": pd.DataFrame(),
                "error": str(e),
            }
        finally:
            if close_client:
                await client.aclose()


async def execute_task_pool(
    execution_id: str,
    tasks: List[Dict[str, Any]],
    cookies: Optional[Dict[str, str]] = None,
    concurrency_limit: int = 5,
    on_task_completed: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Executa um lote de tarefas concorrentes respeitando limite de concorrência.
    """
    semaphore = asyncio.Semaphore(concurrency_limit)
    results: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(cookies=cookies or {}, timeout=60.0, follow_redirects=True) as client:
        worker = ExtractionWorker(cookies=cookies)

        async def _bounded_task(t: Dict[str, Any]):
            async with semaphore:
                res = await worker.execute_task(execution_id, t, client=client)
                if on_task_completed:
                    on_task_completed(res)
                return res

        coros = [_bounded_task(t) for t in tasks]
        results = await asyncio.gather(*coros)

    return list(results)
