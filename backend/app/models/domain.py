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


class OPRecord(BaseModel):
    op: str
    fabrica: str
    data_abertura: Optional[str] = None
    data_entrega: Optional[str] = None
    produto_codigo: Optional[str] = None
    produto_descricao: Optional[str] = None
    local_producao: str
    status: Optional[str] = None


class ConsumoRecord(BaseModel):
    op: str
    codigo_componente: str
    descricao_componente: str = ""
    baixa_automatica: bool = True
    qtd_necessaria: float
    unidade_medida: Optional[str] = "UN"
    local_producao: str


class EstoqueRecord(BaseModel):
    codigo_item: str
    local_estoque: str
    saldo_disponivel: float
    saldo_fisico: float = 0.0
    saldo_reservado: float = 0.0


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
    baixa_automatica: bool = True
    qtd_necessaria: float
    saldo_inicial_local: float
    saldo_remanescente: float
    deficit_saldo: float
    status_divergencia: StatusDivergencia
    severidade: Severidade
