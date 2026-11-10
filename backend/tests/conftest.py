import pytest
from backend.app.extraction.snapshot import snapshot_manager
from backend.app.services.email_service import email_service
from backend.app.tasks.profiler import task_profiler


@pytest.fixture(autouse=True)
def prevent_real_email_sending(monkeypatch):
    """
    Fixture global que impede qualquer disparo real de SMTP durante a execução dos testes,
    simulando o envio de forma segura e evitando tráfego de e-mails para caixas reais.
    """
    def _mock_send_email(to_email: str, subject: str, text_content: str, html_content: str):
        return {
            "status": "SIMULATED",
            "message": f"[TESTE] E-mail simulado com sucesso para {to_email}.",
        }

    monkeypatch.setattr(email_service, "send_email", _mock_send_email)


@pytest.fixture(autouse=True)
def isolate_runtime_storage(monkeypatch, tmp_path):
    """
    Redireciona snapshots HTML e telemetria LPT para um diretório temporário,
    evitando que os testes poluam backend/storage com artefatos de execução.
    """
    monkeypatch.setattr(snapshot_manager, "snapshot_dir", str(tmp_path))
    monkeypatch.setattr(task_profiler, "storage_file", str(tmp_path / "task_execution_times.json"))
    monkeypatch.setattr(task_profiler, "_cache", {})
