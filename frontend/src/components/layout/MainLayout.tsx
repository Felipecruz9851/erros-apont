import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { SummaryMetrics } from '../../types';

interface MainLayoutProps {
  children: React.ReactNode;
  summary?: SummaryMetrics | null;
  selectedFabrica?: string;
  onSelectFabrica?: (fabrica: string) => void;
  currentTab: 'auditoria' | 'emails' | 'contatos';
  onSelectTab: (tab: 'auditoria' | 'emails' | 'contatos') => void;
  onNewAnalysis: () => void;
  onExportCsv?: () => void;
  onNavigateToEmails?: () => void;
  hasResults: boolean;
  isProcessing: boolean;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  summary,
  selectedFabrica,
  onSelectFabrica,
  currentTab,
  onSelectTab,
  onNewAnalysis,
  onExportCsv,
  onNavigateToEmails,
  hasResults,
  isProcessing,
}) => {
  return (
    <div className="min-h-screen bg-lider-canvas flex">
      {/* Sidebar Fixa */}
      <Sidebar
        summary={summary}
        selectedFabrica={selectedFabrica}
        onSelectFabrica={onSelectFabrica}
        currentTab={currentTab}
        onSelectTab={onSelectTab}
      />

      {/* Conteúdo Principal com Offset da Sidebar */}
      <div className="flex-1 ml-64 flex flex-col min-h-screen">
        <Header
          onNewAnalysis={onNewAnalysis}
          onExportCsv={onExportCsv}
          onNavigateToEmails={onNavigateToEmails}
          hasResults={hasResults}
          isProcessing={isProcessing}
          currentTab={currentTab}
        />
        <main className="flex-1 p-8 max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
};
