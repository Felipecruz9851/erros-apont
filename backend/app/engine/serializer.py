from typing import Any, Dict
import pandas as pd


def serialize_results(
    execution_id: str,
    divergences_df: pd.DataFrame,
    total_ops_analisadas: int,
    total_componentes_baixa_auto: int,
    elapsed_seconds: float,
) -> Dict[str, Any]:
    """
    Serializa o DataFrame de divergências em formato JSON estruturado,
    calculando KPIs agregados para apresentação no frontend Líder Design.
    """
    if divergences_df.empty:
        records = []
        total_erros = 0
        total_ops_com_erro = 0
        distribuicao = {}
    else:
        records = divergences_df.to_dict(orient="records")
        total_erros = len(divergences_df)
        total_ops_com_erro = int(divergences_df["op"].nunique()) if "op" in divergences_df.columns else 0

        # Distribuição de erros por fábrica
        distribuicao = {}
        if "fabrica" in divergences_df.columns:
            for fab, group in divergences_df.groupby("fabrica"):
                distribuicao[str(fab)] = {
                    "total_erros": len(group),
                    "ops_com_erro": int(group["op"].nunique()),
                    "deficit_total": round(float(group["deficit_saldo"].sum()), 2),
                }

    # Taxa de conformidade fabril
    if total_ops_analisadas > 0:
        taxa_conf = round(max(0.0, ((total_ops_analisadas - total_ops_com_erro) / total_ops_analisadas) * 100), 1)
    else:
        taxa_conf = 100.0

    return {
        "execution_id": execution_id,
        "summary": {
            "total_ops_analisadas": total_ops_analisadas,
            "total_componentes_baixa_auto": total_componentes_baixa_auto,
            "total_erros_apontamento": total_erros,
            "total_ops_com_erro": total_ops_com_erro,
            "taxa_conformidade_pct": taxa_conf,
            "distribuicao_por_fabrica": distribuicao,
            "tempo_processamento_segundos": elapsed_seconds,
        },
        "pagination": {
            "total": total_erros,
            "limit": 100,
            "offset": 0,
        },
        "records": records,
    }
