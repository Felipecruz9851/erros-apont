from datetime import datetime
import pandas as pd
from backend.app.engine.calculation import calculation_engine


def test_add_business_days_skips_weekends():
    # 2026-10-22 é quinta-feira
    # + 1 dia útil: sexta 2026-10-23
    # + 2 dias úteis: segunda 2026-10-26
    # + 3 dias úteis: terça 2026-10-27
    start_dt = datetime(2026, 10, 22)
    holidays = set()

    d1 = calculation_engine.add_business_days(start_dt, days=1, holidays=holidays)
    assert d1 == datetime(2026, 10, 23)

    d2 = calculation_engine.add_business_days(start_dt, days=2, holidays=holidays)
    assert d2 == datetime(2026, 10, 26)

    d3 = calculation_engine.add_business_days(start_dt, days=3, holidays=holidays)
    assert d3 == datetime(2026, 10, 27)


def test_add_business_days_skips_holidays():
    # 2026-10-29 é quinta-feira
    # Sexta 2026-10-30 = útil
    # Segunda 2026-11-02 = feriado (Finados em feriados.txt)
    # Terça 2026-11-03 = útil
    start_dt = datetime(2026, 10, 29)
    holidays = {"2026-11-02"}

    # + 1 dia útil: sexta 30/10
    assert calculation_engine.add_business_days(start_dt, days=1, holidays=holidays) == datetime(2026, 10, 30)

    # + 2 dias úteis: pula 31/10 (sab), 01/11 (dom) e 02/11 (feriado) -> terça 03/11
    assert calculation_engine.add_business_days(start_dt, days=2, holidays=holidays) == datetime(2026, 11, 3)


def test_calculate_pointing_errors_with_custom_dias_uteis():
    df_consumo = pd.DataFrame([
        {
            "op": "OP-1",
            "fabrica": "F01",
            "codigo_componente": "CMP-01",
            "descricao_componente": "COMPONENTE 1",
            "baixa_automatica": True,
            "qtd_necessaria": 10.0,
            "local_producao": "COLCHOES",
            "data_abertura": "2026-10-20",
            "data_entrega": "2026-10-23",  # Sexta (1 dia útil após 22/10)
        },
        {
            "op": "OP-2",
            "fabrica": "F01",
            "codigo_componente": "CMP-01",
            "descricao_componente": "COMPONENTE 1",
            "baixa_automatica": True,
            "qtd_necessaria": 10.0,
            "local_producao": "COLCHOES",
            "data_abertura": "2026-10-20",
            "data_entrega": "2026-10-27",  # Terça (3 dias úteis após 22/10)
        },
        {
            "op": "OP-3",
            "fabrica": "F01",
            "codigo_componente": "CMP-01",
            "descricao_componente": "COMPONENTE 1",
            "baixa_automatica": True,
            "qtd_necessaria": 10.0,
            "local_producao": "COLCHOES",
            "data_abertura": "2026-10-20",
            "data_entrega": "2026-10-29",  # Quinta (5 dias úteis após 22/10)
        },
    ])

    df_estoque = pd.DataFrame([
        {
            "codigo_item": "CMP-01",
            "local_estoque": "COLCHOES",
            "saldo_disponivel": 5.0,
            "saldo_fisico": 5.0,
            "saldo_reservado": 0.0,
        }
    ])

    # Janela de 1 dia útil: apenas OP-1 (entrega 23/10) deve ser avaliada
    res_1 = calculation_engine.calculate_pointing_errors(
        df_consumo,
        df_estoque,
        data_atual="2026-10-22",
        include_ok=True,
        dias_uteis=1,
    )
    assert len(res_1) == 1
    assert res_1.iloc[0]["op"] == "OP-1"

    # Janela de 3 dias úteis: OP-1 (23/10) e OP-2 (27/10)
    res_3 = calculation_engine.calculate_pointing_errors(
        df_consumo,
        df_estoque,
        data_atual="2026-10-22",
        include_ok=True,
        dias_uteis=3,
    )
    assert len(res_3) == 2
    assert set(res_3["op"].values) == {"OP-1", "OP-2"}

    # Janela de 5 dias úteis: todas as 3 OPs
    res_5 = calculation_engine.calculate_pointing_errors(
        df_consumo,
        df_estoque,
        data_atual="2026-10-22",
        include_ok=True,
        dias_uteis=5,
    )
    assert len(res_5) == 3
