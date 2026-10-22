import os
import pytest
from backend.app.extraction.parser import table_parser
from backend.app.engine.treatment import treatment_engine
from backend.app.engine.calculation import calculation_engine
from backend.app.engine.serializer import serialize_results

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
)


def load_fixture(filename: str) -> str:
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_full_pipeline_offline():
    # 1. Carrega HTMLs mockados
    html_consumo = load_fixture("mock_consumo.html")
    html_estoque = load_fixture("mock_estoque.html")
    html_ordens = load_fixture("mock_atrasadas.html")

    # 2. Parsing das tabelas com BS4
    df_consumo_raw = table_parser.parse_html_to_dataframe(html_consumo)
    df_estoque_raw = table_parser.parse_html_to_dataframe(html_estoque)
    df_ordens_raw = table_parser.parse_html_to_dataframe(html_ordens)

    assert not df_consumo_raw.empty, "DataFrame de consumo não deve estar vazio"
    assert not df_estoque_raw.empty, "DataFrame de estoque não deve estar vazio"
    assert not df_ordens_raw.empty, "DataFrame de ordens não deve estar vazio"

    # 3. Tratamento e Normalização Modular
    df_consumo_clean, df_estoque_clean = treatment_engine.clean_and_normalize(
        df_consumo=df_consumo_raw,
        df_estoque=df_estoque_raw,
        df_ordens=df_ordens_raw,
    )

    # Verifica se itens com baixa == N foram excluídos da avaliação
    assert "CMP-002" not in df_consumo_clean["codigo_componente"].values
    assert "CMP-001" in df_consumo_clean["codigo_componente"].values
    assert "CMP-003" in df_consumo_clean["codigo_componente"].values

    # 4. Cálculo de Alocação Cumulativa
    divergences_df = calculation_engine.calculate_pointing_errors(
        df_consumo=df_consumo_clean,
        df_estoque=df_estoque_clean,
        data_atual="2026-10-28",  # cobre todas as aberturas/entregas do mock_atrasadas.html
    )

    # 5. Validação das Regras Cardeais de Negócio
    # Com include_ok=True (padrão), retorna 3 registros: OP-1001 (OK), OP-1002 (SALDO_INSUFICIENTE), OP-1003 (SALDO_ZERADO_NO_LOCAL)
    assert len(divergences_df) == 3, f"Esperado 3 registros avaliados, obtido: {len(divergences_df)}"

    op1001_ok = divergences_df[divergences_df["op"] == "OP-1001"].iloc[0]
    assert op1001_ok["status_divergencia"] == "OK"
    assert op1001_ok["deficit_saldo"] == 0.0

    # Erro 1: OP-1002 deve ter déficit de 20 no componente CMP-001 (saldo físico inicial era 100, OP-1001 consumiu 50 -> restam 50 para necessidade de 70)
    op1002_err = divergences_df[divergences_df["op"] == "OP-1002"]
    assert len(op1002_err) == 1
    row_1002 = op1002_err.iloc[0]
    assert row_1002["codigo_componente"] == "CMP-001"
    assert row_1002["saldo_inicial_local"] == 100.0
    assert row_1002["saldo_remanescente"] == 50.0
    assert row_1002["deficit_saldo"] == 20.0
    assert row_1002["status_divergencia"] == "SALDO_INSUFICIENTE"

    # Erro 2: OP-1003 deve ter déficit de 15 no componente CMP-003 (saldo zero no local)
    op1003_err = divergences_df[divergences_df["op"] == "OP-1003"]
    assert len(op1003_err) == 1
    row_1003 = op1003_err.iloc[0]
    assert row_1003["codigo_componente"] == "CMP-003"
    assert row_1003["saldo_inicial_local"] == 0.0
    assert row_1003["deficit_saldo"] == 15.0
    assert row_1003["status_divergencia"] == "SALDO_ZERADO_NO_LOCAL"
    assert row_1003["severidade"] == "ALTA"

    # Regra Crítica: Saldo em ALMOXARIFADO_GERAL (5000) NÃO deve ter anulado o déficit em COLCHOES!
    assert "ALMOXARIFADO_GERAL" not in divergences_df["local_producao"].values

    # 6. Serialização para Contrato JSON
    results = serialize_results(
        execution_id="exec_test_offline",
        divergences_df=divergences_df,
        total_ops_analisadas=3,
        total_componentes_baixa_auto=3,
        elapsed_seconds=0.12,
    )

    assert results["execution_id"] == "exec_test_offline"
    assert results["summary"]["total_erros_apontamento"] == 2
    assert results["summary"]["total_ops_com_erro"] == 2
    assert len(results["records"]) == 3
