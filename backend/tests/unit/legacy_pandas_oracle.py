"""
Oráculo de regressão double-entry: motor de cálculo legado em Pandas (groupby + iterrows).

Preservado exclusivamente para o teste de confronto contra o motor vetorizado em Polars
(`CalculationEngine.calculate_pointing_errors_polars`). Não é utilizado em produção.
"""
from typing import List, Optional
import pandas as pd
from backend.app.engine.calculation import CalculationEngine


def calculate_pointing_errors_pandas(
    engine: CalculationEngine,
    df_consumo: pd.DataFrame,
    df_estoque: pd.DataFrame,
    data_atual: Optional[str] = None,
    include_ok: bool = True,
    dias_uteis: int = 3,
) -> pd.DataFrame:
    cols = engine.COLS
    if df_consumo.empty:
        return pd.DataFrame(columns=cols)

    df_c = df_consumo[df_consumo["baixa_automatica"] == True].copy()
    if df_c.empty:
        return pd.DataFrame(columns=cols)

    ref_dt = engine._parse_dt(data_atual)
    if ref_dt is None:
        raise ValueError(f"Data atual de referência inválida ou ausente: {data_atual!r}.")
    limit_dt = engine.add_business_days(ref_dt, days=dias_uteis)

    if "data_abertura" in df_c.columns:
        def _abertura_valida(val: object) -> bool:
            dt_ab = engine._parse_dt(val)
            return dt_ab is None or dt_ab <= ref_dt

        df_c = df_c[df_c["data_abertura"].apply(_abertura_valida)].copy()
        if df_c.empty:
            return pd.DataFrame(columns=cols)

    if "data_entrega" in df_c.columns:
        def _entrega_valida(val: object) -> bool:
            dt_ent = engine._parse_dt(val)
            return dt_ent is not None and dt_ent <= limit_dt

        df_c = df_c[df_c["data_entrega"].apply(_entrega_valida)].copy()
        if df_c.empty:
            return pd.DataFrame(columns=cols)

    df_c["_sort_data_entrega"] = df_c["data_entrega"].astype(str)
    if "data_abertura" in df_c.columns:
        df_c["_sort_data_abertura"] = df_c["data_abertura"].replace("", "9999-12-31").fillna("9999-12-31")
    else:
        df_c["_sort_data_abertura"] = "9999-12-31"

    df_c = df_c.sort_values(
        by=["codigo_componente", "local_producao", "_sort_data_entrega", "_sort_data_abertura", "op"]
    ).reset_index(drop=True)

    stock_map = {}
    if not df_estoque.empty:
        for _, row in df_estoque.iterrows():
            key = (str(row["codigo_item"]).strip().upper(), str(row["local_estoque"]).strip().upper())
            stock_map[key] = stock_map.get(key, 0.0) + float(row.get("saldo_disponivel", 0.0))

    registros: List[dict] = []
    for (cod_comp, loc_prod), group_rows in df_c.groupby(["codigo_componente", "local_producao"], sort=False):
        saldo_inicial = stock_map.get((cod_comp, loc_prod), 0.0)
        saldo_corrente = saldo_inicial
        prioridade = 1

        for _, row in group_rows.iterrows():
            op = str(row["op"]).strip()
            fabrica = str(row.get("fabrica", loc_prod)).strip()
            qtd_necessaria = float(row.get("qtd_necessaria", 0.0))
            if qtd_necessaria <= 0.0:
                qtd_necessaria = 1.0
            data_ent_str = str(row.get("data_entrega", "") or "").strip()
            dt_ent = engine._parse_dt(data_ent_str)
            if dt_ent is None or dt_ent > limit_dt:
                continue

            saldo_rem = saldo_corrente
            tipo_comp = str(row.get("tipo_componente", "C")).strip().upper()
            if not tipo_comp or tipo_comp not in ["P", "C"]:
                tipo_comp = "P" if tipo_comp.startswith("P") else "C"

            base = {
                "id": f"{fabrica}-{op}-{cod_comp}",
                "fabrica": fabrica,
                "op": op,
                "data_abertura": row.get("data_abertura", ""),
                "data_entrega": data_ent_str,
                "prioridade_fila": prioridade,
                "produto_op": row.get("produto_op", ""),
                "local_producao": loc_prod,
                "codigo_componente": cod_comp,
                "descricao_componente": row.get("descricao_componente", ""),
                "tipo_componente": tipo_comp,
                "baixa_automatica": True,
                "qtd_necessaria": qtd_necessaria,
                "saldo_inicial_local": round(saldo_inicial, 4),
                "saldo_remanescente": round(saldo_rem, 4),
            }

            if saldo_rem < qtd_necessaria:
                deficit = round(qtd_necessaria - max(0.0, saldo_rem), 4)
                status_div = "SALDO_ZERADO_NO_LOCAL" if saldo_inicial <= 0.0 else "SALDO_INSUFICIENTE"
                severidade = "ALTA" if deficit >= (qtd_necessaria * 0.5) or saldo_rem <= 0.0 else "MEDIA"
                saldo_corrente = max(0.0, saldo_corrente - qtd_necessaria)
                registros.append(
                    {**base, "deficit_saldo": deficit, "status_divergencia": status_div, "severidade": severidade}
                )
            else:
                saldo_corrente = round(saldo_corrente - qtd_necessaria, 4)
                if include_ok:
                    registros.append(
                        {**base, "deficit_saldo": 0.0, "status_divergencia": "OK", "severidade": "OK"}
                    )
            prioridade += 1

    if not registros:
        return pd.DataFrame(columns=cols)

    df_out = pd.DataFrame(registros)
    df_out["_sort_ent"] = df_out["data_entrega"].replace("", "9999-12-31").fillna("9999-12-31")
    return (
        df_out.sort_values(by=["_sort_ent", "prioridade_fila", "op", "codigo_componente"])
        .drop(columns=["_sort_ent"])
        .reset_index(drop=True)
    )
