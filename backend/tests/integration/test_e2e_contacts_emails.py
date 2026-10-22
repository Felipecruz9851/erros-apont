import os
import pandas as pd
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.engine.orchestrator import orchestrator
from backend.app.engine.serializer import serialize_results
from backend.app.services.contacts_service import contacts_service

client = TestClient(app)


def test_e2e_contacts_and_emails_flow():
    # 1. Cadastra contatos com diferentes locais
    res_c1 = client.post(
        "/api/v1/contacts",
        json={
            "nome": "Supervisora Marcenaria",
            "email": "marcenaria@lider.com.br",
            "locais": ["CC FABRI01", "COLCHOES"],
        },
    )
    assert res_c1.status_code == 201
    c1_id = res_c1.json()["id"]

    res_c2 = client.post(
        "/api/v1/contacts",
        json={
            "nome": "Supervisor Vidros",
            "email": "vidros@lider.com.br",
            "locais": ["VIDRACARIA"],
        },
    )
    assert res_c2.status_code == 201
    c2_id = res_c2.json()["id"]

    # 2. Cria contexto simulado de execução no orchestrator
    ctx = orchestrator.create_execution()
    ctx.dias_uteis = 3
    ctx.data_ref = "2026-10-22"

    mock_divergences = pd.DataFrame([
        {
            "id": "F01-OP101-CMP01",
            "fabrica": "CC FABRI01",
            "op": "OP-101",
            "produto_op": "CADEIRA LIDER",
            "local_producao": "CC FABRI01",
            "codigo_componente": "CMP-01",
            "descricao_componente": "PARAFUSO",
            "baixa_automatica": True,
            "qtd_necessaria": 20.0,
            "saldo_inicial_local": 0.0,
            "saldo_remanescente": 0.0,
            "deficit_saldo": 20.0,
            "status_divergencia": "SALDO_ZERADO_NO_LOCAL",
            "severidade": "ALTA",
            "data_entrega": "2026-10-25",
        },
        {
            "id": "F01-OP102-CMP02",
            "fabrica": "VIDRACARIA",
            "op": "OP-102",
            "produto_op": "MESA DE VIDRO",
            "local_producao": "VIDRACARIA",
            "codigo_componente": "VIDRO-01",
            "descricao_componente": "TAMPO VIDRO 10MM",
            "baixa_automatica": True,
            "qtd_necessaria": 5.0,
            "saldo_inicial_local": 50.0,
            "saldo_remanescente": 45.0,
            "deficit_saldo": 0.0,
            "status_divergencia": "OK",  # Sem erro
            "severidade": "OK",
            "data_entrega": "2026-10-24",
        },
    ])
    ctx.divergences_df = mock_divergences
    ctx.final_response = serialize_results(
        execution_id=ctx.execution_id,
        divergences_df=mock_divergences,
        total_ops_analisadas=2,
        total_componentes_baixa_auto=2,
        elapsed_seconds=1.2,
        dias_uteis=3,
        data_referencia="2026-10-22",
    )

    # 3. Consulta resumo de e-mails para esta execução
    res_sum = client.get(f"/api/v1/emails/summary?execution_id={ctx.execution_id}")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert sum_data["has_results"] is True
    assert sum_data["dias_uteis"] == 3

    c1_summary = next((c for c in sum_data["contacts"] if c["contact_id"] == c1_id), None)
    assert c1_summary is not None
    assert c1_summary["total_erros"] == 1  # OP-101
    assert c1_summary["ops_com_erro"] == 1

    c2_summary = next((c for c in sum_data["contacts"] if c["contact_id"] == c2_id), None)
    assert c2_summary is not None
    assert c2_summary["total_erros"] == 0  # VIDRACARIA só tinha status OK

    # 4. Consulta prévia do e-mail da Supervisora Marcenaria
    res_prev = client.post(
        "/api/v1/emails/preview",
        json={
            "execution_id": ctx.execution_id,
            "contact_id": c1_id,
        },
    )
    assert res_prev.status_code == 200
    prev_data = res_prev.json()
    assert prev_data["total_erros"] == 1
    assert len(prev_data["records"]) == 1
    assert "Supervisora Marcenaria segue lista de erros de apontamento dos próximos 3 dias" in prev_data["text_body"]
    assert "OP-101" in prev_data["html_body"]

    # 5. Disparo de e-mail (simulado)
    res_send = client.post(
        "/api/v1/emails/send",
        json={
            "execution_id": ctx.execution_id,
            "contact_ids": [c1_id],
        },
    )
    assert res_send.status_code == 200
    send_data = res_send.json()
    assert send_data["total_sent"] >= 1
    c1_res = next(r for r in send_data["results"] if r["contact_id"] == c1_id)
    assert c1_res["status"] in ["SENT", "SIMULATED"]

    # Limpeza
    contacts_service.delete_contact(c1_id)
    contacts_service.delete_contact(c2_id)
