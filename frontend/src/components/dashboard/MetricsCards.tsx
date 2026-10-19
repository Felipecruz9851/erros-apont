import React from 'react';
import { AlertTriangle, ShieldCheck, Factory, Layers } from 'lucide-react';
import { SummaryMetrics } from '../../types';

interface MetricsCardsProps {
  summary: SummaryMetrics;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ summary }) => {
  const cards = [
    {
      title: 'OPs Analisadas',
      value: summary.total_ops_analisadas.toLocaleString('pt-BR'),
      subtitle: 'Ordens dentro da janela temporal',
      icon: Factory,
      highlight: false,
    },
    {
      title: 'Insumos com Baixa Auto',
      value: summary.total_componentes_baixa_auto.toLocaleString('pt-BR'),
      subtitle: 'Componentes submetidos a auditoria',
      icon: Layers,
      highlight: false,
    },
    {
      title: 'Erros de Apontamento',
      value: summary.total_erros_apontamento.toLocaleString('pt-BR'),
      subtitle: `${summary.total_ops_com_erro} OPs impactadas com déficit`,
      icon: AlertTriangle,
      highlight: summary.total_erros_apontamento > 0,
      danger: true,
    },
    {
      title: 'Taxa de Conformidade',
      value: `${summary.taxa_conformidade_pct.toFixed(1)}%`,
      subtitle: 'Aderência de saldo no local de produção',
      icon: ShieldCheck,
      highlight: true,
      success: summary.taxa_conformidade_pct >= 95,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {cards.map((c, idx) => {
        const IconComponent = c.icon;
        return (
          <div
            key={idx}
            className="bg-lider-card border border-lider-border rounded-md shadow-card p-5 hover:border-lider-wood/30 transition-colors"
          >
            <div className="flex items-center justify-between text-lider-tertiary mb-3">
              <span className="text-xs uppercase tracking-wider font-medium text-lider-secondary">{c.title}</span>
              <IconComponent
                className={`w-4 h-4 ${
                  c.danger && c.highlight
                    ? 'text-lider-danger'
                    : c.success
                    ? 'text-lider-success'
                    : 'text-lider-wood'
                }`}
              />
            </div>
            <div className="flex items-baseline space-x-2">
              <span
                className={`text-2xl font-bold tracking-tight ${
                  c.danger && c.highlight
                    ? 'text-lider-danger'
                    : c.success
                    ? 'text-lider-success'
                    : 'text-lider-primary'
                }`}
              >
                {c.value}
              </span>
            </div>
            <p className="text-[11px] text-lider-tertiary mt-1.5">{c.subtitle}</p>
          </div>
        );
      })}
    </div>
  );
};
