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


def test_clean_item_code_without_space_before_unit_suffix():
    """
    Garante que códigos de 15 caracteres do relatório de consumo que vêm colados
    no sufixo de unidade (ex: '3LEDDP73000K24V-UN') sejam limpos corretamente para
    '3LEDDP73000K24V' e cruzem com o saldo do local no relatório de estoque.
    """
    from backend.app.engine.treatment import treatment_engine

    assert treatment_engine._clean_item_code("3LEDDP73000K24V-UN") == "3LEDDP73000K24V"
    assert treatment_engine._clean_item_code("3CH01900ACMDPGR-M2") == "3CH01900ACMDPGR"
    assert treatment_engine._clean_item_code("3COUPCOU378    -M2") == "3COUPCOU378"
    assert treatment_engine._clean_item_code("COMP-001") == "COMP-001"


def test_empty_delivery_date_is_ignored():
    """
    Garante que ordens sem data de entrega (ou data vazia) sejam desconsideradas
    do cálculo, pois não pertencem ao recorte temporal de próximos X dias.
    """
    df_consumo = pd.DataFrame([
        {
            "op": "OP-VALIDA",
            "fabrica": "F01",
            "codigo_componente": "CMP-01",
            "descricao_componente": "COMPONENTE",
            "baixa_automatica": True,
            "qtd_necessaria": 10.0,
            "local_producao": "LOC-01",
            "data_abertura": "2026-10-15",
            "data_entrega": "2026-10-23",
        },
        {
            "op": "OP-SEM-ENTREGA",
            "fabrica": "F01",
            "codigo_componente": "CMP-01",
            "descricao_componente": "COMPONENTE",
            "baixa_automatica": True,
            "qtd_necessaria": 5.0,
            "local_producao": "LOC-01",
            "data_abertura": "2026-10-15",
            "data_entrega": "",  # Vazia
        },
    ])

    df_estoque = pd.DataFrame([
        {
            "codigo_item": "CMP-01",
            "local_estoque": "LOC-01",
            "saldo_disponivel": 20.0,
            "saldo_fisico": 20.0,
            "saldo_reservado": 0.0,
        }
    ])

    res = calculation_engine.calculate_pointing_errors(
        df_consumo,
        df_estoque,
        data_atual="2026-10-22",
        include_ok=True,
        dias_uteis=3,
    )

    # Apenas OP-VALIDA deve constar; OP-SEM-ENTREGA deve ser ignorada
    assert len(res) == 1
    assert res.iloc[0]["op"] == "OP-VALIDA"
    assert res.iloc[0]["data_entrega"] == "2026-10-23"


def test_clean_op_with_leaked_php():
    """
    Garante que trechos de PHP vazados na coluna Ordem de relatórios legados
    sejam limpos corretamente para a identificação da OP numérica.
    """
    from backend.app.engine.treatment import treatment_engine

    dirty = '1985883 if ($exibir_codbar == "S") { $bar = new WBarCode("{$r[\'num_ordem\']}"); } ?>'
    assert treatment_engine._clean_op(dirty) == "1985883"
    assert treatment_engine._clean_op("  OP-1234  ") == "OP-1234"
    assert treatment_engine._clean_op("") == ""


def test_empty_product_falls_back_to_item_code_from_ordens():
    """
    Garante que quando a descrição do produto for vazia, o sistema use
    o código do item vindo da tabela de ordens atrasadas.
    """
    from backend.app.engine.treatment import treatment_engine

    df_consumo = pd.DataFrame([
        {
            "op": "OP-700",
            "fabrica": "COLCHOES",
            "codigo_componente": "CMP-01",
            "descricao_componente": "PARAFUSO",
            "baixa_automatica": True,
            "qtd_necessaria": 10.0,
            "local_producao": "COLCHOES",
            "data_abertura": "2026-10-15",
            "data_entrega": "2026-10-23",
            "produto_op": "",  # Vazio
        }
    ])

    df_ordens = pd.DataFrame([
        {
            "Ordem": "OP-700",
            "Item": "1BCLN140003495",  # Código do item na tabela ordens atrasadas
            "Descrição do Item": "",    # Descrição vazia
            "Data Entrega": "2026-10-23",
            "Data Abertura": "2026-10-15",
        }
    ])

    df_estoque = pd.DataFrame([
        {
            "codigo_item": "CMP-01",
            "local_estoque": "COLCHOES",
            "saldo_disponivel": 50.0,
        }
    ])

    c_clean, _ = treatment_engine.clean_and_normalize(df_consumo, df_estoque, df_ordens)
    assert c_clean.iloc[0]["produto_op"] == "1BCLN140003495"


def test_inactive_item_stock_allocation_kit():
    """
    Garante que itens com cadastro inativo (sit == 'I', como 4RIP0110500074)
    mas com saldo físico no local de produção (ex: KIT) sejam devidamente
    reconhecidos e consumidos, evitando falsos erros de SALDO_ZERADO_NO_LOCAL.
    """
    from backend.app.engine.treatment import treatment_engine

    df_consumo_raw = pd.DataFrame([
        {
            "Tipo": "P",
            "Grupo": "OSSO ESTAR",
            "Item": "4RIP0110500074 -UN",
            "Local Estoque": "KIT",
            "Baixa": "S",
            "Situação": "I",
            "Den. Item": "CORTE RIPA COMPRADA AVULSA 1050 MM",
            "Consumo": "5,0000",
            "Local Prod.": "KIT",
            "OP": "1926093",
            "Familia": "PAI",
        }
    ])

    df_estoque_raw = pd.DataFrame([
        {
            "Item": "4RIP0110500074",
            "Descrição": "CORTE RIPA COMPRADA AVULSA 1050 MM",
            "FAM": "PAI",
            "Sit.": "I",
            "Local - Sit": "KIT - L",
            "Qtde.": "20,00",
            "Unidade": "UN",
            "Qt.Reser": "0,00",
            "Sofre Baixa?": "SIM",
            "Local Prod.": "KIT",
        }
    ])

    df_ordens_raw = pd.DataFrame([
        {
            "Ordem": "1926093",
            "Item": "PROD-01",
            "Descrição do Item": "PAINEL RIPADO",
            "Data Entrega": "2026-10-23",
            "Data Abertura": "2026-10-15",
        }
    ])

    c_clean, e_clean = treatment_engine.clean_and_normalize(df_consumo_raw, df_estoque_raw, df_ordens_raw)
    assert not e_clean.empty
    assert e_clean.iloc[0]["codigo_item"] == "4RIP0110500074"
    assert e_clean.iloc[0]["saldo_disponivel"] == 20.0

    divergences = calculation_engine.calculate_pointing_errors(
        c_clean,
        e_clean,
        data_atual="2026-10-22",
        include_ok=True,
        dias_uteis=3,
    )

    assert len(divergences) == 1
    row = divergences.iloc[0]
    assert row["codigo_componente"] == "4RIP0110500074"
    assert row["status_divergencia"] == "OK"
    assert row["saldo_inicial_local"] == 20.0
    assert row["saldo_remanescente"] == 20.0




