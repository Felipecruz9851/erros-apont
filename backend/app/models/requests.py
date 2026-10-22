from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.models.domain import ErroApontamento, ExecutionState


class StartPipelineRequest(BaseModel):
    username: Optional[str] = Field(default="", description="Usuário corporativo da intranet (em branco para carregar pickle)")
    password: Optional[str] = Field(default="", description="Senha corporativa da intranet")
    data_inicio: Optional[str] = Field(default="2000-01-01", description="Data de início (YYYY-MM-DD), padrão 2000-01-01")
    data_fim: str = Field(..., description="Data atual de referência preenchida no frontend (YYYY-MM-DD)")
    dias_uteis: Optional[int] = Field(default=3, ge=1, le=60, description="Número de dias úteis para a janela de entrega")
    fabricas: Optional[List[str]] = Field(default=None, description="Filtro opcional de fábricas")
    debug: Optional[bool] = Field(default=False, description="Quando True, preserva os arquivos HTML temporários")


class StartPipelineResponse(BaseModel):
    execution_id: str
    status: str = "RUNNING"
    message: str = "Pipeline iniciado com sucesso. Acompanhe pelo status endpoint."


class StagesProgress(BaseModel):
    auth: str = "PENDING"
    extraction: str = "PENDING"
    treatment: str = "PENDING"
    calculation: str = "PENDING"
    serialization: str = "PENDING"
    presentation: str = "PENDING"


class StatusResponse(BaseModel):
    execution_id: str
    stage: ExecutionState
    progress_pct: int = 0
    stages: StagesProgress
    tasks_completed: int = 0
    tasks_total: int = 0
    elapsed_seconds: float = 0.0
    error_message: Optional[str] = None


class SummaryMetrics(BaseModel):
    total_ops_analisadas: int = 0
    total_componentes_baixa_auto: int = 0
    total_erros_apontamento: int = 0
    total_ops_com_erro: int = 0
    taxa_conformidade_pct: float = 100.0
    dias_uteis: int = 3
    data_referencia: Optional[str] = None
    distribuicao_por_fabrica: Dict[str, Dict] = Field(default_factory=dict)
    tempo_processamento_segundos: float = 0.0


class PaginationInfo(BaseModel):
    total: int = 0
    limit: int = 100
    offset: int = 0


class ResultsResponse(BaseModel):
    execution_id: str
    summary: SummaryMetrics
    pagination: PaginationInfo
    records: List[ErroApontamento] = Field(default_factory=list)
