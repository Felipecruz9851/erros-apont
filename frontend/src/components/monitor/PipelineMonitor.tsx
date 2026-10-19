import React from 'react';
import { CheckCircle2, Clock, Loader2, AlertCircle } from 'lucide-react';
import { StatusResponse } from '../../types';

interface PipelineMonitorProps {
  status: StatusResponse;
}

const STAGES_CONFIG = [
  { key: 'auth', label: '1. Autenticação' },
  { key: 'extraction', label: '2. Extração Multi-Fábrica' },
  { key: 'treatment', label: '3. Tratamento Modular' },
  { key: 'calculation', label: '4. Alocação Cumulativa' },
  { key: 'serialization', label: '5. Montagem do JSON' },
  { key: 'presentation', label: '6. Pronto para Inspeção' },
];

export const PipelineMonitor: React.FC<PipelineMonitorProps> = ({ status }) => {
  const isFailed = status.stage === 'FAILED';
  const isCompleted = status.stage === 'COMPLETED';

  return (
    <div className="bg-lider-card border border-lider-border rounded-md shadow-card p-6 mb-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-lider-divider gap-2">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs uppercase tracking-widest text-lider-wood font-medium">Monitor de Execução</span>
            <span className="text-[10px] text-lider-tertiary">ID: {status.execution_id}</span>
          </div>
          <h3 className="text-base font-semibold text-lider-primary tracking-tight mt-0.5">
            {isCompleted
              ? 'Auditoria Concluída com Sucesso'
              : isFailed
              ? 'Execução Interrompida'
              : 'Processando Pipeline em Tempo Real'}
          </h3>
        </div>

        <div className="flex items-center space-x-4 text-xs text-lider-secondary">
          <div className="flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5 text-lider-tertiary" />
            <span>{status.elapsed_seconds.toFixed(1)}s decorridos</span>
          </div>
          {status.tasks_total > 0 && (
            <div className="text-xs text-lider-tertiary">
              <span className="text-lider-primary font-medium">{status.tasks_completed}</span> / {status.tasks_total} tarefas
            </div>
          )}
        </div>
      </div>

      {/* Barra de progresso ultrafina Líder */}
      <div className="mt-4 mb-6">
        <div className="flex justify-between text-[11px] text-lider-secondary mb-1.5 font-medium">
          <span>Progresso Consolidado</span>
          <span>{status.progress_pct}%</span>
        </div>
        <div className="w-full bg-lider-subtle h-1.5 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ease-out ${
              isFailed ? 'bg-lider-danger' : isCompleted ? 'bg-lider-success' : 'bg-lider-wood'
            }`}
            style={{ width: `${status.progress_pct}%` }}
          />
        </div>
      </div>

      {/* Grid dos 6 Estágios */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {STAGES_CONFIG.map((stg) => {
          const stgStatus = (status.stages as any)[stg.key] || 'PENDING';
          const isStgDone = stgStatus === 'COMPLETED';
          const isStgActive = stgStatus === 'IN_PROGRESS';

          return (
            <div
              key={stg.key}
              className={`p-3 border rounded-sm transition-all ${
                isStgDone
                  ? 'border-lider-border bg-lider-canvas/60 text-lider-primary'
                  : isStgActive
                  ? 'border-lider-wood/40 bg-lider-card shadow-subtle text-lider-primary'
                  : 'border-lider-divider bg-transparent text-lider-tertiary opacity-70'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-medium tracking-wide">{stg.label}</span>
                {isStgDone ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-lider-success" />
                ) : isStgActive ? (
                  <Loader2 className="w-3.5 h-3.5 text-lider-wood animate-spin" />
                ) : (
                  <div className="w-2 h-2 rounded-full bg-lider-divider" />
                )}
              </div>
              <div className="text-[10px]">
                {isStgDone && <span className="text-lider-success font-medium">Concluído</span>}
                {isStgActive && <span className="text-lider-wood font-medium">Em andamento</span>}
                {!isStgDone && !isStgActive && <span>Aguardando</span>}
              </div>
            </div>
          );
        })}
      </div>

      {isFailed && status.error_message && (
        <div className="mt-4 p-3 bg-lider-dangerLight border border-lider-danger/20 rounded-sm flex items-center space-x-2 text-xs text-lider-danger">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{status.error_message}</span>
        </div>
      )}
    </div>
  );
};
