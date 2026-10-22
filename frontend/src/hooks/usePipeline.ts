import { useState, useEffect, useCallback, useRef } from 'react';
import { pipelineApi } from '../services/api';
import { ResultsResponse, StartPipelinePayload, StatusResponse } from '../types';

export function usePipeline() {
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const pollingRef = useRef<number | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      window.clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const loadResults = useCallback(
    async (execId: string, filters?: { fabrica?: string; local_producao?: string; status_divergencia?: string }) => {
      try {
        // Busca TODAS as páginas: o backend limita a resposta (padrão 5000) e os registros vêm
        // ordenados por data de entrega crescente. Sem paginar, uma data de referência futura
        // exibia só as entregas mais próximas de hoje.
        const PAGE_SIZE = 50000;
        const first = await pipelineApi.getResults(execId, { ...filters, limit: PAGE_SIZE, offset: 0 });
        const records = [...first.records];
        const total = first.pagination?.total ?? records.length;
        while (records.length < total) {
          const page = await pipelineApi.getResults(execId, { ...filters, limit: PAGE_SIZE, offset: records.length });
          if (!page.records.length) break;
          records.push(...page.records);
        }
        setResults({ ...first, records, pagination: { ...first.pagination, total, limit: records.length, offset: 0 } });
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Erro ao carregar resultados da análise.');
      }
    },
    []
  );

  const startAnalysis = async (payload: StartPipelinePayload) => {
    setIsLoading(true);
    setError(null);
    setResults(null);
    stopPolling();

    try {
      const res = await pipelineApi.start(payload);
      setExecutionId(res.execution_id);
      setStatus({
        execution_id: res.execution_id,
        stage: 'AUTHENTICATING',
        progress_pct: 5,
        stages: {
          auth: 'IN_PROGRESS',
          extraction: 'PENDING',
          treatment: 'PENDING',
          calculation: 'PENDING',
          serialization: 'PENDING',
          presentation: 'PENDING',
        },
        tasks_completed: 0,
        tasks_total: 0,
        elapsed_seconds: 0,
      });

      // Inicia polling a cada 1.5s
      pollingRef.current = window.setInterval(async () => {
        try {
          const currentStatus = await pipelineApi.getStatus(res.execution_id);
          setStatus(currentStatus);

          if (currentStatus.stage === 'COMPLETED') {
            stopPolling();
            setIsLoading(false);
            await loadResults(res.execution_id);
          } else if (currentStatus.stage === 'FAILED') {
            stopPolling();
            setIsLoading(false);
            setError(currentStatus.error_message || 'Falha no processamento do pipeline.');
          }
        } catch (err: any) {
          stopPolling();
          setIsLoading(false);
          setError(err.response?.data?.detail || 'Erro ao comunicar com a API.');
        }
      }, 1500);
    } catch (err: any) {
      setIsLoading(false);
      setError(err.response?.data?.detail || 'Falha ao iniciar a análise. Verifique as credenciais.');
    }
  };

  const reset = () => {
    stopPolling();
    setExecutionId(null);
    setStatus(null);
    setResults(null);
    setIsLoading(false);
    setError(null);
  };

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  return {
    executionId,
    status,
    results,
    isLoading,
    error,
    startAnalysis,
    loadResults,
    reset,
  };
}
