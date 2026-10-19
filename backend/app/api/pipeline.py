from fastapi import APIRouter, HTTPException, status
from backend.app.engine.orchestrator import orchestrator
from backend.app.models.requests import StartPipelineRequest, StartPipelineResponse, StatusResponse

router = APIRouter()


@router.post(
    "/start",
    response_model=StartPipelineResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Dispara o pipeline completo de extração e análise",
)
async def start_pipeline(request: StartPipelineRequest):
    """
    Recebe credenciais em memória e parâmetros temporais para
    iniciar o scraping assíncrono multi-fábrica e o cálculo de erros de apontamento.
    """
    if not request.data_inicio or not request.data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datas de início e fim são obrigatórias.",
        )

    # Cria contexto de execução
    ctx = orchestrator.create_execution()

    # Dispara o pipeline em background
    await orchestrator.start_pipeline_background(
        execution_id=ctx.execution_id,
        username=request.username,
        password=request.password,
        data_inicio=request.data_inicio,
        data_fim=request.data_fim,
        fabricas=request.fabricas,
    )

    return StartPipelineResponse(
        execution_id=ctx.execution_id,
        status="RUNNING",
        message="Pipeline iniciado com sucesso. Acompanhe pelo status endpoint.",
    )


@router.get(
    "/status/{execution_id}",
    response_model=StatusResponse,
    summary="Consulta o progresso em tempo real das 6 fases do pipeline",
)
async def get_pipeline_status(execution_id: str):
    """
    Retorna o percentual concluído, estágio atual e contagem de tarefas.
    """
    ctx = orchestrator.get_context(execution_id)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execução '{execution_id}' não encontrada.",
        )

    return ctx.to_status_response()
