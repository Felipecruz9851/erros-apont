import os
import pickle
import time
import numpy as np
import pytest
from backend.app.engine.calculation import calculation_engine
from backend.app.engine.treatment import treatment_engine
from backend.tests.unit.legacy_pandas_oracle import calculate_pointing_errors_pandas


@pytest.fixture(scope="module")
def real_snapshot_data():
    """Carrega dados do snapshot real de extração (55.000 linhas)."""
    snapshot_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "storage",
        "snapshots",
        "latest_extraction.pkl",
    )
    if not os.path.exists(snapshot_path):
        pytest.skip("Snapshot real latest_extraction.pkl não encontrado.")

    with open(snapshot_path, "rb") as f:
        data = pickle.load(f)

    dfs = data.get("dfs_by_group", {})
    return dfs


def test_confrontation_pandas_vs_polars_exact_precision(real_snapshot_data):
    """
    Teste de Confronto Estrito (Double-Entry Regression Test):
    Executa o motor legado (Pandas iterrows) e o novo motor vetorizado (Polars Window Functions)
    sobre os dados reais da fábrica e confronta 100% dos resultados.
    """
    consumo_raw = real_snapshot_data["consumo"]
    estoque_raw = real_snapshot_data["estoque"]
    ordens_raw = real_snapshot_data.get("ordens")

    # 1. Tratamento e normalização
    c_clean, e_clean = treatment_engine.clean_and_normalize(
        consumo_raw, estoque_raw, ordens_raw
    )

    data_referencia = "2026-10-23"
    dias_uteis = 3

    # 2. Executa Motor Legado em Pandas (Medindo tempo)
    t0_pd = time.perf_counter()
    res_pandas = calculate_pointing_errors_pandas(
        calculation_engine,
        df_consumo=c_clean,
        df_estoque=e_clean,
        data_atual=data_referencia,
        include_ok=True,
        dias_uteis=dias_uteis,
    )
    t1_pd = time.perf_counter()
    pandas_duration = t1_pd - t0_pd

    # 3. Executa Novo Motor Vetorizado em Polars (Medindo tempo)
    t0_pl = time.perf_counter()
    res_polars = calculation_engine.calculate_pointing_errors_polars(
        df_consumo=c_clean,
        df_estoque=e_clean,
        data_atual=data_referencia,
        include_ok=True,
        dias_uteis=dias_uteis,
    )
    t1_pl = time.perf_counter()
    polars_duration = t1_pl - t0_pl

    # 4. Confronto Estrito de Integridade e Precisão
    assert len(res_polars) == len(res_pandas), (
        f"Quantidade de linhas divergente: Polars={len(res_polars)}, Pandas={len(res_pandas)}"
    )

    res_polars_df = res_polars.to_pandas()

    cols_to_check = [
        "id",
        "op",
        "codigo_componente",
        "local_producao",
        "data_entrega",
        "prioridade_fila",
        "status_divergencia",
        "severidade",
    ]

    for col in cols_to_check:
        pd_vals = res_pandas[col].tolist()
        pl_vals = res_polars_df[col].tolist()
        assert pl_vals == pd_vals, f"Divergência na coluna '{col}' entre Polars e Pandas"

    # Confronto Numérico com tolerância estrita de ponto flutuante
    numeric_cols = [
        "qtd_necessaria",
        "saldo_inicial_local",
        "saldo_remanescente",
        "deficit_saldo",
    ]
    for num_col in numeric_cols:
        pd_num = res_pandas[num_col].to_numpy(dtype=float)
        pl_num = res_polars_df[num_col].to_numpy(dtype=float)
        np.testing.assert_allclose(
            pl_num,
            pd_num,
            rtol=1e-5,
            atol=1e-5,
            err_msg=f"Divergência numérica na coluna '{num_col}'",
        )

    # 5. Validação de Ganho de Performance
    speedup = pandas_duration / max(polars_duration, 1e-6)
    print(
        f"\n[BENCHMARK CONFRONTATION]"
        f"\n  Pandas Engine Duration: {pandas_duration:.4f}s"
        f"\n  Polars Engine Duration: {polars_duration:.4f}s"
        f"\n  Speedup Factor: {speedup:.2f}x mais rápido!"
    )
    assert polars_duration < pandas_duration, "O motor Polars deve ser mais rápido que o Pandas."
