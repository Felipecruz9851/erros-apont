import tempfile
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.contacts_service import ContactsService
from backend.app.services.email_service import email_service
import backend.app.services.contacts_service as cs_module


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_contacts(monkeypatch):
    """Isola o arquivo de contatos durante os testes."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_path = tf.name

    test_service = ContactsService(file_path=temp_path)
    monkeypatch.setattr(cs_module, "contacts_service", test_service)
    # Atualiza também nas rotas e email_service
    import backend.app.api.contacts as api_c
    import backend.app.services.email_service as s_email
    monkeypatch.setattr(api_c, "contacts_service", test_service)
    monkeypatch.setattr(s_email, "contacts_service", test_service)

    yield test_service


def test_contacts_crud(isolated_contacts):
    # 1. Lista inicial vazia
    res = client.get("/api/v1/contacts")
    assert res.status_code == 200
    assert res.json() == []

    # 2. Criação de contato
    payload = {
        "nome": "Carlos Supervisor",
        "email": "carlos@lider.com.br",
        "locais": ["COLCHOES", "BOX"],
    }
    res = client.post("/api/v1/contacts", json=payload)
    assert res.status_code == 201
    created = res.json()
    assert created["nome"] == "Carlos Supervisor"
    assert created["email"] == "carlos@lider.com.br"
    assert set(created["locais"]) == {"COLCHOES", "BOX"}
    contact_id = created["id"]

    # 3. Consulta de contato
    res = client.get(f"/api/v1/contacts/{contact_id}")
    assert res.status_code == 200
    assert res.json()["id"] == contact_id

    # 4. Atualização de contato
    update_payload = {
        "nome": "Carlos Roberto",
        "locais": ["COLCHOES", "BOX", "COZINHA"],
    }
    res = client.put(f"/api/v1/contacts/{contact_id}", json=update_payload)
    assert res.status_code == 200
    updated = res.json()
    assert updated["nome"] == "Carlos Roberto"
    assert "COZINHA" in updated["locais"]

    # 5. Listagem de locais disponíveis
    res = client.get("/api/v1/contacts/locations")
    assert res.status_code == 200
    locs = res.json()
    assert isinstance(locs, list)
    assert len(locs) > 0
    assert "COLCHOES" in locs

    # 6. Exclusão de contato
    res = client.delete(f"/api/v1/contacts/{contact_id}")
    assert res.status_code == 204

    res = client.get(f"/api/v1/contacts/{contact_id}")
    assert res.status_code == 404


def test_email_compilation_and_preview(isolated_contacts):
    # Cria contato de teste
    c = isolated_contacts.create_contact(
        nome="Mariana Gestora",
        email="mariana@lider.com.br",
        locais=["COLCHOES"],
    )

    # Mock de registros de execução
    mock_records = [
        {
            "id": "1",
            "op": "OP-999",
            "produto_op": "COLCHAO CASAL",
            "local_producao": "COLCHOES",
            "codigo_componente": "MOLA-01",
            "descricao_componente": "MOLA ENSACADA",
            "qtd_necessaria": 50.0,
            "saldo_inicial_local": 10.0,
            "saldo_remanescente": 10.0,
            "deficit_saldo": 40.0,
            "status_divergencia": "SALDO_INSUFICIENTE",
            "severidade": "ALTA",
            "data_entrega": "2026-10-25",
        },
        {
            "id": "2",
            "op": "OP-888",
            "produto_op": "BOX QUEEN",
            "local_producao": "BOX",  # Local diferente, não atribuído a Mariana
            "codigo_componente": "MADEIRA-01",
            "descricao_componente": "CHAPA MADEIRA",
            "qtd_necessaria": 20.0,
            "saldo_inicial_local": 0.0,
            "saldo_remanescente": 0.0,
            "deficit_saldo": 20.0,
            "status_divergencia": "SALDO_ZERADO_NO_LOCAL",
            "severidade": "ALTA",
            "data_entrega": "2026-10-25",
        },
        {
            "id": "3",
            "op": "OP-777",
            "produto_op": "COLCHAO SOLTEIRO",
            "local_producao": "COLCHOES",
            "codigo_componente": "ESPUMA-01",
            "descricao_componente": "ESPUMA D33",
            "qtd_necessaria": 10.0,
            "saldo_inicial_local": 100.0,
            "saldo_remanescente": 90.0,
            "deficit_saldo": 0.0,
            "status_divergencia": "OK",  # Item OK, não é erro
            "severidade": "OK",
            "data_entrega": "2026-10-25",
        },
    ]

    filtered = email_service.filter_errors_for_contact(mock_records, ["COLCHOES"])
    # Deve conter somente OP-999 (pois OP-888 é de outro local e OP-777 é status OK)
    assert len(filtered) == 1
    assert filtered[0]["op"] == "OP-999"

    # Testa formatação da mensagem obrigatória:
    # "(Bom dia ou boa tarde a depender do horário), (Nome do contato) segue lista de erros de apontamento dos próximos x dias."
    saudacao = email_service.get_greeting()
    assert saudacao in ["Bom dia", "Boa tarde"]

    subject, plain, html_out = email_service.build_email_content(
        contact_name=c["nome"],
        locais=c["locais"],
        error_records=filtered,
        dias_uteis=3,
    )

    expected_prefix = f"{saudacao}, Mariana Gestora segue lista de erros de apontamento dos próximos 3 dias."
    assert expected_prefix in plain
    assert expected_prefix in html_out
    assert "OP-999" in plain
    assert "MOLA-01" in plain
    assert "OP-888" not in plain  # Não deve vazar outro local

    # Garante que as colunas removidas não constam no e-mail
    for col in ["Qtd Nec.", "Saldo Local", "Saldo Rem.", ">Status<"]:
        assert col not in html_out


def test_tipo_componente_separation_in_email():
    """Valida separação de itens produzidos (P) e comprados (C) nas tabelas do e-mail."""
    records = [
        {
            "id": "1",
            "op": "OP-101",
            "produto_op": "CADEIRA",
            "local_producao": "CADEIRAS",
            "codigo_componente": "PER-01",
            "descricao_componente": "PERFIL ALUMINIO",
            "tipo_componente": "P",
            "qtd_necessaria": 10.0,
            "saldo_inicial_local": 0.0,
            "saldo_remanescente": 0.0,
            "deficit_saldo": 10.0,
            "status_divergencia": "SALDO_ZERADO_NO_LOCAL",
            "severidade": "ALTA",
            "data_entrega": "2026-10-25",
        },
        {
            "id": "2",
            "op": "OP-102",
            "produto_op": "MESA",
            "local_producao": "CADEIRAS",
            "codigo_componente": "PAR-01",
            "descricao_componente": "PARAFUSO INOX",
            "tipo_componente": "C",
            "qtd_necessaria": 50.0,
            "saldo_inicial_local": 0.0,
            "saldo_remanescente": 0.0,
            "deficit_saldo": 50.0,
            "status_divergencia": "SALDO_ZERADO_NO_LOCAL",
            "severidade": "ALTA",
            "data_entrega": "2026-10-25",
        },
    ]

    # Teste de filtro P
    p_only = email_service.filter_errors_for_contact(records, ["CADEIRAS"], tipo_filtro="P")
    assert len(p_only) == 1
    assert p_only[0]["codigo_componente"] == "PER-01"

    # Teste de filtro C
    c_only = email_service.filter_errors_for_contact(records, ["CADEIRAS"], tipo_filtro="C")
    assert len(c_only) == 1
    assert c_only[0]["codigo_componente"] == "PAR-01"

    # Teste de e-mail com ambos: deve conter blocos separados para Produzidos e Comprados
    _, plain, html_out = email_service.build_email_content(
        contact_name="Supervisor Cadeiras",
        locais=["CADEIRAS"],
        error_records=records,
        dias_uteis=3,
        tipo_filtro="TODOS",
    )

    assert "COMPONENTES PRODUZIDOS (P)" in plain
    assert "COMPONENTES COMPRADOS (C)" in plain
    assert "Componentes Produzidos (P)" in html_out
    assert "Componentes Comprados (C)" in html_out
    assert "PER-01" in html_out
    assert "PAR-01" in html_out


def test_dispatch_selected_records_to_locais_and_target_email(isolated_contacts, monkeypatch):
    """Valida envio de linhas selecionadas para responsáveis de locais e envio para e-mail específico."""
    c1 = isolated_contacts.create_contact(nome="Resp Acessorios", email="acess@lider.com.br", locais=["ACESSORIOS"])
    c2 = isolated_contacts.create_contact(nome="Resp Colchoes", email="colch@lider.com.br", locais=["COLCHOES"])

    mock_records = [
        {
            "id": "rec_acess_1",
            "op": "OP-1",
            "local_producao": "ACESSORIOS",
            "codigo_componente": "COMP-A",
            "tipo_componente": "P",
            "deficit_saldo": 5.0,
            "status_divergencia": "SALDO_INSUFICIENTE",
            "severidade": "ALTA",
            "data_entrega": "2026-10-25",
        },
        {
            "id": "rec_colch_1",
            "op": "OP-2",
            "local_producao": "COLCHOES",
            "codigo_componente": "COMP-C",
            "tipo_componente": "C",
            "deficit_saldo": 15.0,
            "status_divergencia": "SALDO_ZERADO_NO_LOCAL",
            "severidade": "ALTA",
            "data_entrega": "2026-10-25",
        },
        {
            "id": "rec_colch_2",
            "op": "OP-3",
            "local_producao": "COLCHOES",
            "codigo_componente": "COMP-D",
            "tipo_componente": "P",
            "deficit_saldo": 8.0,
            "status_divergencia": "SALDO_INSUFICIENTE",
            "severidade": "ALTA",
            "data_entrega": "2026-10-25",
        },
    ]

    monkeypatch.setattr(email_service, "get_execution_data", lambda eid=None: (mock_records, 3, "2026-10-22"))

    # 1. Enviar apenas as linhas rec_acess_1 e rec_colch_1 para os responsáveis dos locais
    res_locais = email_service.dispatch_for_contacts(
        selected_record_ids=["rec_acess_1", "rec_colch_1"]
    )
    assert res_locais["total_processed"] == 2
    assert res_locais["total_sent"] == 2
    res_by_email = {item["email"]: item for item in res_locais["results"]}
    assert "acess@lider.com.br" in res_by_email
    assert res_by_email["acess@lider.com.br"]["total_erros"] == 1
    assert "colch@lider.com.br" in res_by_email
    assert res_by_email["colch@lider.com.br"]["total_erros"] == 1  # Apenas rec_colch_1, rec_colch_2 não foi marcada

    # 2. Enviar linha rec_colch_2 para um e-mail específico
    res_especifico = email_service.dispatch_for_contacts(
        selected_record_ids=["rec_colch_2"],
        target_email="auditoria@lider.com.br",
        target_name="Auditoria Central",
    )
    assert res_especifico["total_processed"] == 1
    assert res_especifico["total_sent"] == 1
    assert res_especifico["results"][0]["email"] == "auditoria@lider.com.br"
    assert res_especifico["results"][0]["total_erros"] == 1
