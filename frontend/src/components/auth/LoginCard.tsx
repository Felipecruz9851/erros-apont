import React, { useState } from 'react';
import { Lock, Calendar, Play, AlertCircle } from 'lucide-react';
import { StartPipelinePayload } from '../../types';

interface LoginCardProps {
  onStart: (payload: StartPipelinePayload) => void;
  isLoading: boolean;
  error?: string | null;
}

export const LoginCard: React.FC<LoginCardProps> = ({ onStart, isLoading, error }) => {
  const today = new Date().toISOString().split('T')[0];
  const [username, setUsername] = useState('operador.pcp');
  const [password, setPassword] = useState('PHPSESSID=3eeero9cktl23hpo78aba98gai');
  const [dataInicio, setDataInicio] = useState(today);
  const [dataFim, setDataFim] = useState(today);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStart({
      username,
      password,
      data_inicio: dataInicio,
      data_fim: dataFim,
    });
  };

  return (
    <div className="bg-lider-card border border-lider-border rounded-md shadow-card p-8 max-w-xl mx-auto">
      <div className="border-b border-lider-divider pb-4 mb-6">
        <span className="text-xs uppercase tracking-widest text-lider-wood font-medium">Autenticação & Escopo</span>
        <h2 className="text-xl font-semibold text-lider-primary tracking-tight mt-1">Disparar Auditoria de Apontamentos</h2>
        <p className="text-xs text-lider-secondary mt-1">
          Informe suas credenciais da intranet e delimite a janela temporal de abertura e entrega das ordens.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-3 bg-lider-dangerLight border border-lider-danger/20 rounded-sm flex items-start space-x-2 text-lider-danger text-xs">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-lider-secondary mb-1">Usuário Intranet</label>
            <div className="relative">
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="nome.sobrenome"
                className="w-full px-3 py-2 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood transition-colors text-lider-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-lider-secondary mb-1">Senha ou Cookie de Sessão</label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Senha ou PHPSESSID=..."
                className="w-full px-3 py-2 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood transition-colors text-lider-primary"
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="block text-xs font-medium text-lider-secondary mb-1 flex items-center space-x-1">
              <Calendar className="w-3.5 h-3.5 text-lider-tertiary" />
              <span>Data de Abertura (Início)</span>
            </label>
            <input
              type="date"
              required
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood transition-colors text-lider-primary"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-lider-secondary mb-1 flex items-center space-x-1">
              <Calendar className="w-3.5 h-3.5 text-lider-tertiary" />
              <span>Data de Entrega (Fim)</span>
            </label>
            <input
              type="date"
              required
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood transition-colors text-lider-primary"
            />
          </div>
        </div>

        <div className="pt-4 border-t border-lider-divider flex items-center justify-between">
          <div className="flex items-center space-x-1.5 text-xs text-lider-tertiary">
            <Lock className="w-3.5 h-3.5" />
            <span>Credenciais processadas estritamente em memória</span>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center space-x-2 px-5 py-2.5 bg-lider-primary text-white text-xs font-medium rounded-sm hover:bg-[#2A2A2A] active:bg-black transition-all shadow-subtle disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Iniciando...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                <span>Iniciar Análise</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
