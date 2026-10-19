from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Erros de Apontamento" in data["service"]


def test_pipeline_validation():
    # Test missing dates
    response = client.post(
        "/api/v1/pipeline/start",
        json={"username": "user", "password": "pwd", "data_inicio": "", "data_fim": ""},
    )
    assert response.status_code == 400


def test_results_not_found():
    response = client.get("/api/v1/results/exec_inexistente")
    assert response.status_code == 404
