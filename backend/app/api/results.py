import io
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
import pandas as pd
from backend.app.engine.orchestrator import orchestrator
from backend.app.models.requests import PaginationInfo, ResultsResponse, SummaryMetrics

router = APIRouter()


@router.get(
    "/{execution_id}",
    response_model=ResultsResponse,
    summary="Recupera o resumo de métricas e lista de erros de apontamento",
)
async def get_results(
    execution_id: str,
    fabrica: Optional[str] = Query(None, description="Filtrar por fábrica"),
    local_producao: Optional[str] = Query(None, description="Filtrar por local de produção"),
    status_divergencia: Optional[str] = Query(None, description="Filtrar por tipo de divergência"),
    tipo_componente: Optional[str] = Query(None, description="Filtrar por tipo de componente ('C', 'P')"),
    limit: int = Query(5000, ge=1, le=50000, description="Limite de registros por página"),
    offset: int = Query(0, ge=0, description="Deslocamento para paginação"),
):
    ctx = orchestrator.get_context(execution_id)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execução '{execution_id}' não encontrada.",
        )

    if ctx.state not in ["COMPLETED", "SERIALIZING"] and ctx.final_response is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Execução ainda em andamento (estágio atual: {ctx.state}).",
        )

    final = ctx.final_response or {}
    all_records = final.get("records", [])

    # Aplica filtros em memória
    filtered = all_records
    if fabrica:
        fab_norm = fabrica.strip().upper()
        filtered = [r for r in filtered if r.get("fabrica", "").upper() == fab_norm]
    if local_producao:
        loc_norm = local_producao.strip().upper()
        filtered = [r for r in filtered if r.get("local_producao", "").upper() == loc_norm]
    if status_divergencia:
        div_norm = status_divergencia.strip().upper()
        filtered = [r for r in filtered if r.get("status_divergencia", "").upper() == div_norm]
    if tipo_componente:
        tipo_norm = tipo_componente.strip().upper()
        if tipo_norm in ["C", "P"]:
            filtered = [r for r in filtered if str(r.get("tipo_componente", "C")).upper() == tipo_norm]

    total_filtered = len(filtered)
    paged_records = filtered[offset : offset + limit]

    summary_data = final.get("summary", {})
    summary = SummaryMetrics(**summary_data) if summary_data else SummaryMetrics()

    return ResultsResponse(
        execution_id=execution_id,
        summary=summary,
        pagination=PaginationInfo(total=total_filtered, limit=limit, offset=offset),
        records=paged_records,
    )


@router.get(
    "/{execution_id}/export",
    summary="Exporta o relatório consolidado de divergências em CSV ou JSON",
)
async def export_results(
    execution_id: str,
    format: Literal["csv", "json"] = Query("csv", description="Formato do arquivo exportado"),
    fabrica: Optional[str] = Query(None, description="Filtrar fábrica na exportação"),
    tipo_componente: Optional[str] = Query(None, description="Filtrar tipo de componente ('C', 'P') na exportação"),
):
    ctx = orchestrator.get_context(execution_id)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execução '{execution_id}' não encontrada.",
        )

    df = ctx.divergences_df
    if df is None:
        df = pd.DataFrame()

    if not df.empty and fabrica:
        df = df[df["fabrica"].str.upper() == fabrica.strip().upper()]

    if not df.empty and tipo_componente and "tipo_componente" in df.columns:
        tipo_norm = tipo_componente.strip().upper()
        if tipo_norm in ["C", "P"]:
            df = df[df["tipo_componente"].str.upper() == tipo_norm]

    if format == "csv":
        stream = io.StringIO()
        df.to_csv(stream, index=False, sep=";", encoding="utf-8-sig")
        csv_bytes = stream.getvalue().encode("utf-8-sig")

        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=erros_apontamento_{execution_id}.csv",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )
    else:
        records = df.to_dict(orient="records") if not df.empty else []
        return JSONResponse(
            content={
                "execution_id": execution_id,
                "total": len(records),
                "records": records,
            },
            headers={
                "Content-Disposition": f"attachment; filename=erros_apontamento_{execution_id}.json",
            },
        )
