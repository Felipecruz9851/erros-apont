import React from 'react';
import { Factory, ShieldAlert, Mail, Users, BarChart3 } from 'lucide-react';
import { SummaryMetrics } from '../../types';

interface SidebarProps {
  summary?: SummaryMetrics | null;
  selectedFabrica?: string;
  onSelectFabrica?: (fabrica: string) => void;
  currentTab: 'auditoria' | 'emails' | 'contatos';
  onSelectTab: (tab: 'auditoria' | 'emails' | 'contatos') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  summary,
  selectedFabrica = 'ALL',
  onSelectFabrica,
  currentTab,
  onSelectTab,
}) => {
  const dist = summary?.distribuicao_por_fabrica || {};
  const fabricasEntries = Object.entries(dist);

  return (
    <aside className="w-64 bg-lider-card border-r border-lider-border flex flex-col justify-between h-screen fixed left-0 top-0 z-40 select-none">
      <div>
        {/* Top Branding */}
        <div className="h-16 px-6 border-b border-lider-divider flex items-center justify-between">
          <div className="flex flex-col space-y-1">
            <img
              src="/logo_lider.png"
              alt="Líder Interiores"
              className="h-5 w-auto object-contain object-left"
            />
            <span className="text-[10px] uppercase tracking-widest text-lider-wood font-semibold">
              PCP Industrial
            </span>
          </div>
          <div className="w-2 h-2 rounded-full bg-lider-wood" />
        </div>

        {/* Módulos do Sistema */}
        <div className="p-4 space-y-1 border-b border-lider-divider">
          <div className="px-3 py-1 text-[11px] font-semibold text-lider-tertiary uppercase tracking-wider">
            Módulos
          </div>

          <button
            onClick={() => onSelectTab('auditoria')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 text-xs rounded-sm transition-colors text-left ${
              currentTab === 'auditoria'
                ? 'bg-lider-canvas font-semibold text-lider-primary border-l-2 border-lider-wood'
                : 'text-lider-secondary hover:bg-lider-canvas/60'
            }`}
          >
            <BarChart3 className="w-4 h-4 text-lider-wood flex-shrink-0" />
            <span>Auditoria & Estoque</span>
          </button>

          <button
            onClick={() => onSelectTab('emails')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 text-xs rounded-sm transition-colors text-left ${
              currentTab === 'emails'
                ? 'bg-lider-canvas font-semibold text-lider-primary border-l-2 border-lider-wood'
                : 'text-lider-secondary hover:bg-lider-canvas/60'
            }`}
          >
            <Mail className="w-4 h-4 text-lider-wood flex-shrink-0" />
            <span>Envio de E-mails</span>
          </button>

          <button
            onClick={() => onSelectTab('contatos')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 text-xs rounded-sm transition-colors text-left ${
              currentTab === 'contatos'
                ? 'bg-lider-canvas font-semibold text-lider-primary border-l-2 border-lider-wood'
                : 'text-lider-secondary hover:bg-lider-canvas/60'
            }`}
          >
            <Users className="w-4 h-4 text-lider-wood flex-shrink-0" />
            <span>Cadastro de Destinatários</span>
          </button>
        </div>

        {/* Seção de Filtro por Fábrica (ativa no módulo de auditoria) */}
        {currentTab === 'auditoria' && (
          <div className="p-4 space-y-1">
            <div className="px-3 py-1.5 text-[11px] font-semibold text-lider-tertiary uppercase tracking-wider">
              Filtrar Unidade
            </div>
            <button
              onClick={() => onSelectFabrica && onSelectFabrica('ALL')}
              className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-sm transition-colors text-left ${
                selectedFabrica === 'ALL'
                  ? 'bg-lider-canvas font-semibold text-lider-primary border-l-2 border-lider-wood'
                  : 'text-lider-secondary hover:bg-lider-canvas/60'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <Factory className="w-3.5 h-3.5 text-lider-wood" />
                <span>Todas as Fábricas</span>
              </div>
              {summary && (
                <span className="text-[10px] text-lider-tertiary font-mono">
                  {summary.total_erros_apontamento}
                </span>
              )}
            </button>

            {/* Fábricas particionadas */}
            {fabricasEntries.length > 0 && (
              <div className="pt-2">
                <div className="max-h-52 overflow-y-auto space-y-1 pr-1">
                  {fabricasEntries.map(([fabName, data]) => {
                    const isSelected = selectedFabrica === fabName;
                    return (
                      <button
                        key={fabName}
                        onClick={() => onSelectFabrica && onSelectFabrica(fabName)}
                        className={`w-full flex items-center justify-between px-3 py-1.5 text-xs rounded-sm transition-colors text-left ${
                          isSelected
                            ? 'bg-lider-canvas font-medium text-lider-primary'
                            : 'text-lider-secondary hover:bg-lider-canvas/50'
                        }`}
                      >
                        <span className="truncate pr-2">{fabName}</span>
                        <span
                          className={`text-[10px] font-mono px-1.5 py-0.2 rounded-sm ${
                            data.total_erros > 0
                              ? 'bg-lider-dangerLight text-lider-danger font-medium'
                              : 'text-lider-tertiary'
                          }`}
                        >
                          {data.total_erros}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Rodapé da Sidebar */}
      <div className="p-4 border-t border-lider-divider bg-lider-canvas/30 text-[11px] text-lider-tertiary space-y-2">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-3.5 h-3.5 text-lider-wood" />
          <span className="font-medium text-lider-secondary">Baixa Automática</span>
        </div>
        <p className="text-[10px] leading-relaxed">
          Verificação estrita de saldo no local de produção da ordem com fila por data de entrega e janela em dias úteis.
        </p>
      </div>
    </aside>
  );
};
