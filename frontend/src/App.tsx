import { useState } from 'react';
import { usePipeline } from './hooks/usePipeline';
import { MainLayout } from './components/layout/MainLayout';
import { LoginCard } from './components/auth/LoginCard';
import { PipelineMonitor } from './components/monitor/PipelineMonitor';
import { MetricsCards } from './components/dashboard/MetricsCards';
import { PointingErrorsTable } from './components/dashboard/PointingErrorsTable';
import { pipelineApi } from './services/api';

export default function App() {
  const {
    executionId,
    status,
    results,
    isLoading,
    error,
    startAnalysis,
    reset,
  } = usePipeline();

  const [selectedFabrica, setSelectedFabrica] = useState<string>('ALL');

  const handleExportCsv = () => {
    if (!executionId) return;
    const fabFilter = selectedFabrica !== 'ALL' ? selectedFabrica : undefined;
    window.location.href = pipelineApi.getExportUrl(executionId, 'csv', fabFilter);
  };

  const handleExportJson = () => {
    if (!executionId) return;
    const fabFilter = selectedFabrica !== 'ALL' ? selectedFabrica : undefined;
    window.location.href = pipelineApi.getExportUrl(executionId, 'json', fabFilter);
  };

  return (
    <MainLayout
      summary={results?.summary}
      selectedFabrica={selectedFabrica}
      onSelectFabrica={setSelectedFabrica}
      onNewAnalysis={reset}
      onExportCsv={handleExportCsv}
      hasResults={!!results && results.records.length > 0}
      isProcessing={isLoading}
    >
      {/* Estado 1: Tela Inicial de Login e Delimitação de Janela Temporal */}
      {!executionId && (
        <div className="py-8">
          <LoginCard onStart={startAnalysis} isLoading={isLoading} error={error} />
        </div>
      )}

      {/* Estado 2: Monitor em Tempo Real */}
      {status && (
        <div>
          <PipelineMonitor status={status} />
        </div>
      )}

      {/* Estado 3: Resultados e Dashboard Analítico */}
      {results && (
        <div>
          <MetricsCards summary={results.summary} />
          <PointingErrorsTable
            records={results.records}
            onExportCsv={handleExportCsv}
            onExportJson={handleExportJson}
          />
        </div>
      )}
    </MainLayout>
  );
}
