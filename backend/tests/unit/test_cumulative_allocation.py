import pandas as pd
from backend.app.engine.calculation import calculation_engine


def test_cumulative_allocation_scenario_3():
    """
    Scenario 3:
    When two OPs require Component CMP-0088 at LOC-MARCENARIA-01 (stock: 30):
    - OP 1 (Delivery: 2026-10-22, need: 24) -> allocated 24, remaining 6 (No error).
    - OP 2 (Delivery: 2026-10-25, need: 16) -> allocated 6, deficit 10 -> Flagged as SALDO_INSUFICIENTE.
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
            "data_entrega": "2026-10-22",
        },
        {
            "op": "OP-2",
            "fabrica": "F01",
            "codigo_componente": "CMP-0088",
            "descricao_componente": "PARAFUSO SEXTAVADO",
            "baixa_automatica": True,
            "qtd_necessaria": 16.0,
            "local_producao": "LOC-MARCENARIA-01",
            "data_entrega": "2026-10-25",
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

    divergences = calculation_engine.calculate_pointing_errors(df_consumo, df_estoque)

    assert len(divergences) == 1
    err = divergences.iloc[0]
    assert err["op"] == "OP-2"
    assert err["codigo_componente"] == "CMP-0088"
    assert err["saldo_inicial_local"] == 30.0
    assert err["saldo_remanescente"] == 6.0
    assert err["deficit_saldo"] == 10.0
    assert err["status_divergencia"] == "SALDO_INSUFICIENTE"
