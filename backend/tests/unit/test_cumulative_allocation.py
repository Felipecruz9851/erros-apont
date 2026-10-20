import pandas as pd
from backend.app.engine.calculation import calculation_engine


def test_cumulative_allocation_scenario_3():
    """
    Scenario 3:
    When two OPs require Component CMP-0088 at LOC-MARCENARIA-01 (stock: 30):
    - OP 1 (Delivery: 2026-10-20, need: 24) -> allocated 24, remaining 6 -> Flagged as OK.
    - OP 2 (Delivery: 2026-10-22, need: 16) -> allocated 6, deficit 10 -> Flagged as SALDO_INSUFICIENTE.
    - OP 3 (Delivery: 2026-10-25, > 3 days from 2026-10-20) -> Ignored.
    """
    df_consumo = pd.DataFrame([
        {
            "op": "OP-1",
            "fabrica": "F01",
            "codigo_componente": "CMP-0088",
            "descricao_componente": "PARAFUSO SEXTAVADO",
            "baixa_automatica": True,
            "qtd_necessaria": 24.0,
            "local_producao": "LOC-MARCENARIA-01",
            "data_abertura": "2026-10-15",
            "data_entrega": "2026-10-20",
        },
        {
            "op": "OP-2",
            "fabrica": "F01",
            "codigo_componente": "CMP-0088",
            "descricao_componente": "PARAFUSO SEXTAVADO",
            "baixa_automatica": True,
            "qtd_necessaria": 16.0,
            "local_producao": "LOC-MARCENARIA-01",
            "data_abertura": "2026-10-16",
            "data_entrega": "2026-10-22",
        },
        {
            "op": "OP-3",
            "fabrica": "F01",
            "codigo_componente": "CMP-0088",
            "descricao_componente": "PARAFUSO SEXTAVADO",
            "baixa_automatica": True,
            "qtd_necessaria": 10.0,
            "local_producao": "LOC-MARCENARIA-01",
            "data_abertura": "2026-10-18",
            "data_entrega": "2026-10-25",
        },
        {
            "op": "OP-FUTURA",
            "fabrica": "F01",
            "codigo_componente": "CMP-0088",
            "descricao_componente": "PARAFUSO SEXTAVADO",
            "baixa_automatica": True,
            "qtd_necessaria": 10.0,
            "local_producao": "LOC-MARCENARIA-01",
            "data_abertura": "2026-10-25",  # Abertura > data_atual (2026-10-20), deve ser filtrada
            "data_entrega": "2026-10-21",
        },
    ])

    df_estoque = pd.DataFrame([
        {
            "codigo_item": "CMP-0088",
            "local_estoque": "LOC-MARCENARIA-01",
            "saldo_disponivel": 30.0,
            "saldo_fisico": 30.0,
            "saldo_reservado": 0.0,
        }
    ])

    divergences = calculation_engine.calculate_pointing_errors(
        df_consumo,
        df_estoque,
        data_atual="2026-10-20",
        include_ok=True,
    )

    # Apenas OP-1 (OK) e OP-2 (SALDO_INSUFICIENTE) estão na janela de <= 3 dias e abertura <= 2026-10-20
    assert len(divergences) == 2

    ok_row = divergences[divergences["op"] == "OP-1"].iloc[0]
    assert ok_row["status_divergencia"] == "OK"
    assert ok_row["severidade"] == "OK"
    assert ok_row["deficit_saldo"] == 0.0
    assert ok_row["saldo_remanescente"] == 30.0

    err = divergences[divergences["op"] == "OP-2"].iloc[0]
    assert err["codigo_componente"] == "CMP-0088"
    assert err["saldo_inicial_local"] == 30.0
    assert err["saldo_remanescente"] == 6.0
    assert err["deficit_saldo"] == 10.0
    assert err["status_divergencia"] == "SALDO_INSUFICIENTE"
