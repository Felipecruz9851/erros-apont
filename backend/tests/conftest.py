import pytest
from backend.app.services.email_service import email_service


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
