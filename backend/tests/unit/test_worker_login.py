import asyncio
from typing import Dict, List
import httpx
import pytest
from backend.app.extraction.worker import ExtractionWorker, execute_task_pool


def _make_mock_transport(
    set_cookie: bool = True,
    redirect_url: str = "http://192.168.0.6/home/app",
    body_html: str = "<html><body>Bem-vindo ao sistema</body></html>",
    call_counter: Dict[str, int] = None,
    session_id_prefix: str = "sess",
) -> httpx.MockTransport:
    if call_counter is None:
        call_counter = {"get_login": 0, "post_login": 0, "task_post": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if request.method == "GET" and "/home/login/" in url_str:
            call_counter["get_login"] += 1
            headers = {}
            if set_cookie:
                sid = f"{session_id_prefix}_{call_counter['get_login']}"
                headers["set-cookie"] = f"PHPSESSID={sid}; path=/"
            return httpx.Response(200, text="<html>login page</html>", headers=headers, request=request)

        if request.method == "POST" and "/home/login/" in url_str:
            call_counter["post_login"] += 1
            headers = {"Location": redirect_url}
            if set_cookie:
                sid = f"{session_id_prefix}_{call_counter['post_login']}"
                headers["set-cookie"] = f"PHPSESSID={sid}; path=/"
            return httpx.Response(302, headers=headers, request=request)

        if request.method == "GET" and url_str == redirect_url:
            return httpx.Response(200, text=body_html, request=request)

        # Task scraping endpoint
        call_counter["task_post"] += 1
        table_html = """
        <html><body>
        <table>
            <tr><th>OP</th><th>Componente</th><th>Qtd</th></tr>
            <tr><td>1001</td><td>CMP-01</td><td>10</td></tr>
        </table>
        </body></html>
        """
        return httpx.Response(200, text=table_html, request=request)

    return httpx.MockTransport(handler)


def test_worker_login_once_per_lifecycle():
    counter = {"get_login": 0, "post_login": 0, "task_post": 0}
    transport = _make_mock_transport(call_counter=counter)

    async def _run():
        async with ExtractionWorker(username="user1", password="secret", worker_id=1) as worker:
            worker.session = httpx.AsyncClient(transport=transport, follow_redirects=True)
            assert worker._logged_in is False

            await worker.login()
            assert worker._logged_in is True
            assert "PHPSESSID" in worker.session.cookies
            assert counter["get_login"] == 1
            assert counter["post_login"] == 1

            # Chamadas subsequentes no mesmo ciclo de vida não devem refazer login
            await worker.login()
            await worker.login()
            assert counter["get_login"] == 1
            assert counter["post_login"] == 1

    asyncio.run(_run())


def test_worker_login_fails_without_phpsessid():
    transport = _make_mock_transport(set_cookie=False)

    async def _run():
        async with ExtractionWorker(username="user1", password="secret") as worker:
            worker.session = httpx.AsyncClient(transport=transport, follow_redirects=True)
            with pytest.raises(RuntimeError, match="sessão não criada"):
                await worker.login()
            assert worker._logged_in is False

    asyncio.run(_run())


def test_worker_login_fails_on_invalid_credentials():
    transport = _make_mock_transport(
        set_cookie=True,
        redirect_url="http://192.168.0.6/home/",
        body_html='<html><form><input type="submit" name="logar" value="Acessar"></form></html>',
    )

    async def _run():
        async with ExtractionWorker(username="user1", password="wrong") as worker:
            worker.session = httpx.AsyncClient(transport=transport, follow_redirects=True)
            with pytest.raises(RuntimeError, match="credenciais inválidas"):
                await worker.login()
            assert worker._logged_in is False

    asyncio.run(_run())


def test_pool_each_worker_logs_in_independently_once(monkeypatch):
    """
    Garante que num pool com 3 workers e 9 tarefas:
    - Exatamente 3 logins independentes ocorrem (1 por worker).
    - Cada worker possui seu próprio PHPSESSID isolado.
    - Todas as 9 tarefas são executadas reutilizando a sessão de cada worker.
    """
    login_sessions: List[str] = []
    counter = {"get_login": 0, "post_login": 0, "task_post": 0}

    orig_init = ExtractionWorker.__init__

    def _patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        transport = _make_mock_transport(
            call_counter=counter,
            session_id_prefix=f"worker_{self.worker_id}_sess",
        )
        self.session = httpx.AsyncClient(transport=transport, follow_redirects=True)

    orig_login = ExtractionWorker.login

    async def _tracked_login(self):
        await orig_login(self)
        login_sessions.append(self.session.cookies.get("PHPSESSID"))

    monkeypatch.setattr(ExtractionWorker, "__init__", _patched_init)
    monkeypatch.setattr(ExtractionWorker, "login", _tracked_login)

    tasks = [
        {
            "task_id": f"task_{i}",
            "url": "http://192.168.0.6/pcp/consumo_alt.php",
            "metodo": "POST",
            "grupo": "consumo_ordem",
            "payload": {"cod_empresa": "11"},
        }
        for i in range(9)
    ]

    auth_done_called = {"called": False}

    def _on_auth():
        auth_done_called["called"] = True

    results = asyncio.run(
        execute_task_pool(
            execution_id="exec_test_pool_login",
            tasks=tasks,
            username="operador",
            password="123",
            concurrency_limit=3,
            on_auth_completed=_on_auth,
        )
    )

    assert auth_done_called["called"] is True
    assert len(results) == 9
    assert all(r["status"] == "SUCCESS" for r in results)
    # 3 workers -> exatamente 3 logins realizados (1 por worker no seu ciclo de vida)
    assert counter["post_login"] == 3
    assert len(login_sessions) == 3
    # Cada worker obteve um PHPSESSID exclusivo
    assert len(set(login_sessions)) == 3
    assert counter["task_post"] == 9
