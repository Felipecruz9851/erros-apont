import React from 'react';
import { RefreshCw, Download } from 'lucide-react';

interface HeaderProps {
  onNewAnalysis: () => void;
  onExportCsv?: () => void;
  hasResults: boolean;
  isProcessing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  onNewAnalysis,
  onExportCsv,
  hasResults,
  isProcessing,
}) => {
  return (
    <header className="h-16 bg-lider-card border-b border-lider-border px-8 flex items-center justify-between sticky top-0 z-30 shadow-subtle">
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <span className="font-bold tracking-tight text-sm text-lider-primary uppercase">Líder</span>
          <span className="text-lider-border font-light">|</span>
          <span className="text-xs text-lider-secondary font-medium tracking-wide">
            Auditoria de Apontamentos & Estoque
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {hasResults && onExportCsv && (
          <button
            onClick={onExportCsv}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium border border-lider-border rounded-sm bg-lider-canvas hover:bg-lider-subtle text-lider-primary transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-lider-tertiary" />
            <span>Baixar CSV</span>
          </button>
        )}

        <button
          onClick={onNewAnalysis}
          disabled={isProcessing}
          className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-medium bg-lider-primary text-white rounded-sm hover:bg-[#2A2A2A] active:bg-black transition-all shadow-subtle disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
          <span>{isProcessing ? 'Processando...' : 'Nova Análise'}</span>
        </button>
      </div>
    </header>
  );
};
