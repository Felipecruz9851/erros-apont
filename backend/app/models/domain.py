from typing import Literal, Optional
from pydantic import BaseModel, Field


ExecutionState = Literal[
    "IDLE",
    "AUTHENTICATING",
    "EXTRACTING",
    "TREATING",
    "CALCULATING",
    "SERIALIZING",
    "COMPLETED",
    "FAILED",
]

StatusDivergencia = Literal[
    "SALDO_INSUFICIENTE",
    "SALDO_ZERADO_NO_LOCAL",
    "ITEM_SEM_CADASTRO_ESTOQUE",
    "OK",
]

Severidade = Literal["ALTA", "MEDIA", "OK"]


class ErroApontamento(BaseModel):
    id: str = Field(description="Composite ID: {fabrica}-{op}-{codigo_componente}")
    fabrica: str
    op: str
    data_abertura: Optional[str] = None
    data_entrega: Optional[str] = None
    prioridade_fila: int = 1
    produto_op: Optional[str] = None
    local_producao: str
    codigo_componente: str
    descricao_componente: str = ""
    tipo_componente: Optional[str] = "C"
    baixa_automatica: bool = True
    qtd_necessaria: float
    saldo_inicial_local: float
    saldo_remanescente: float
    deficit_saldo: float
    status_divergencia: StatusDivergencia
    severidade: Severidade
