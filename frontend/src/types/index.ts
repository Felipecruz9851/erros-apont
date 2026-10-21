export type ExecutionStage =
  | 'IDLE'
  | 'AUTHENTICATING'
  | 'EXTRACTING'
  | 'TREATING'
  | 'CALCULATING'
  | 'SERIALIZING'
  | 'COMPLETED'
  | 'FAILED';

export type StatusDivergencia =
  | 'SALDO_INSUFICIENTE'
  | 'SALDO_ZERADO_NO_LOCAL'
  | 'ITEM_SEM_CADASTRO_ESTOQUE'
  | 'OK';

export type Severidade = 'ALTA' | 'MEDIA' | 'OK';

export interface ErroApontamento {
  id: string;
  fabrica: string;
  op: string;
  data_abertura?: string;
  data_entrega?: string;
  prioridade_fila: number;
  produto_op?: string;
  local_producao: string;
  codigo_componente: string;
  descricao_componente: string;
  baixa_automatica: boolean;
  qtd_necessaria: number;
  saldo_inicial_local: number;
  saldo_remanescente: number;
  deficit_saldo: number;
  status_divergencia: StatusDivergencia;
  severidade: Severidade;
}

export interface StagesProgress {
  auth: string;
  extraction: string;
  treatment: string;
  calculation: string;
  serialization: string;
  presentation: string;
}

export interface StatusResponse {
  execution_id: string;
  stage: ExecutionStage;
  progress_pct: number;
  stages: StagesProgress;
  tasks_completed: number;
  tasks_total: number;
  elapsed_seconds: number;
  error_message?: string | null;
}

export interface SummaryMetrics {
  total_ops_analisadas: number;
  total_componentes_baixa_auto: number;
  total_erros_apontamento: number;
  total_ops_com_erro: number;
  taxa_conformidade_pct: number;
  distribuicao_por_fabrica: Record<string, { total_erros: number; ops_com_erro: number; deficit_total: number }>;
  tempo_processamento_segundos: number;
}

export interface PaginationInfo {
  total: number;
  limit: number;
  offset: number;
}

export interface ResultsResponse {
  execution_id: string;
  summary: SummaryMetrics;
  pagination: PaginationInfo;
  records: ErroApontamento[];
}

export interface StartPipelinePayload {
  username: string;
  password: string;
  data_inicio?: string;
  data_fim: string;
  fabricas?: string[];
  debug?: boolean;
}
