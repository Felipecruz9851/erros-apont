import { useState } from 'react';
import { usePipeline } from './hooks/usePipeline';
import { MainLayout } from './components/layout/MainLayout';
import { LoginCard } from './components/auth/LoginCard';
import { PipelineMonitor } from './components/monitor/PipelineMonitor';
import { MetricsCards } from './components/dashboard/MetricsCards';
import { PointingErrorsTable } from './components/dashboard/PointingErrorsTable';
import { ContactsManager } from './components/contacts/ContactsManager';
import { EmailDispatcher } from './components/emails/EmailDispatcher';
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

  const [currentTab, setCurrentTab] = useState<'auditoria' | 'emails' | 'contatos'>('auditoria');
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

  const handleNewAnalysis = () => {
    reset();
    setCurrentTab('auditoria');
  };

  return (
    <MainLayout
      summary={results?.summary}
      selectedFabrica={selectedFabrica}
      onSelectFabrica={setSelectedFabrica}
      currentTab={currentTab}
      onSelectTab={setCurrentTab}
      onNewAnalysis={handleNewAnalysis}
      onExportCsv={handleExportCsv}
      onNavigateToEmails={() => setCurrentTab('emails')}
      hasResults={!!results && results.records.length > 0}
      isProcessing={isLoading}
    >
      {/* Aba 1: Auditoria e Resultados */}
      {currentTab === 'auditoria' && (
        <div className="space-y-6">
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
        </div>
      )}

      {/* Aba 2: Disparo de E-mails */}
      {currentTab === 'emails' && (
        <EmailDispatcher
          executionId={executionId}
          onNavigateToAnalysis={() => setCurrentTab('auditoria')}
        />
      )}

      {/* Aba 3: Cadastro de Contatos e Locais */}
      {currentTab === 'contatos' && <ContactsManager />}
    </MainLayout>
  );
}
