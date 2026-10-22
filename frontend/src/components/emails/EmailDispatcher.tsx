import React, { useState, useEffect, useMemo } from 'react';
import {
  Mail,
  Send,
  Eye,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Search,
  RefreshCw,
  X,
  Sparkles,
} from 'lucide-react';
import { emailsApi } from '../../services/api';
import { ContactSummary, EmailPreviewData, EmailSendItemResult } from '../../types';

interface EmailDispatcherProps {
  executionId?: string | null;
  onNavigateToAnalysis?: () => void;
}

export const EmailDispatcher: React.FC<EmailDispatcherProps> = ({
  executionId,
  onNavigateToAnalysis,
}) => {
  const [contactsSummary, setContactsSummary] = useState<ContactSummary[]>([]);
  const [diasUteis, setDiasUteis] = useState<number>(3);
  const [dataRef, setDataRef] = useState<string>('');
  const [hasResults, setHasResults] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filtro de Tipo de Insumo (TODOS, P ou C)
  const [tipoFiltro, setTipoFiltro] = useState<'TODOS' | 'P' | 'C'>('TODOS');

  // Seleção de contatos para envio em lote
  const [selectedContactIds, setSelectedContactIds] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Status de envio por contato (contact_id -> { status, message })
  const [sendStatuses, setSendStatuses] = useState<Record<string, { status: string; message: string }>>({});
  const [isSendingBatch, setIsSendingBatch] = useState<boolean>(false);
  const [sendingContactId, setSendingContactId] = useState<string | null>(null);

  // Modal de Prévia
  const [previewData, setPreviewData] = useState<EmailPreviewData | null>(null);
  const [loadingPreviewContactId, setLoadingPreviewContactId] = useState<string | null>(null);
  const [previewTab, setPreviewTab] = useState<'visual' | 'tabela' | 'texto'>('visual');

  const loadSummary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await emailsApi.getSummary(executionId || undefined, tipoFiltro);
      setContactsSummary(data.contacts);
      setDiasUteis(data.dias_uteis || 3);
      setDataRef(data.data_ref || '');
      setHasResults(data.has_results);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro ao compilar resumo de divergências por contato.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [executionId, tipoFiltro]);

  const toggleSelectContact = (id: string) => {
    setSelectedContactIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectAllWithErrors = () => {
    const withErrors = contactsSummary
      .filter((c) => c.total_erros > 0)
      .map((c) => c.contact_id);
    setSelectedContactIds(withErrors);
  };

  const clearSelection = () => {
    setSelectedContactIds([]);
  };

  const handleOpenPreview = async (contactId: string) => {
    setLoadingPreviewContactId(contactId);
    try {
      const preview = await emailsApi.preview(contactId, executionId || undefined, tipoFiltro);
      setPreviewData(preview);
      setPreviewTab('visual');
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Erro ao gerar prévia do e-mail.');
    } finally {
      setLoadingPreviewContactId(null);
    }
  };

  const handleSendSingle = async (contactId: string) => {
    setSendingContactId(contactId);
    try {
      const res = await emailsApi.send({
        execution_id: executionId || undefined,
        contact_ids: [contactId],
        tipo_filtro: tipoFiltro,
      });
      const item = res.results.find((r) => r.contact_id === contactId);
      if (item) {
        setSendStatuses((prev) => ({
          ...prev,
          [contactId]: { status: item.status, message: item.message },
        }));
      }
    } catch (err: any) {
      setSendStatuses((prev) => ({
        ...prev,
        [contactId]: { status: 'FAILED', message: err?.response?.data?.detail || 'Falha ao enviar e-mail.' },
      }));
    } finally {
      setSendingContactId(null);
    }
  };

  const handleSendBatch = async (sendAllWithErrors: boolean = false) => {
    const idsToSend = sendAllWithErrors
      ? undefined
      : selectedContactIds;

    if (!sendAllWithErrors && (!idsToSend || idsToSend.length === 0)) {
      alert('Selecione ao menos um contato para envio.');
      return;
    }

    setIsSendingBatch(true);
    try {
      const res = await emailsApi.send({
        execution_id: executionId || undefined,
        contact_ids: idsToSend,
        send_all_with_errors: sendAllWithErrors,
        tipo_filtro: tipoFiltro,
      });

      const newStatuses = { ...sendStatuses };
      res.results.forEach((item: EmailSendItemResult) => {
        newStatuses[item.contact_id] = { status: item.status, message: item.message };
      });
      setSendStatuses(newStatuses);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Erro ao processar disparo em lote.');
    } finally {
      setIsSendingBatch(false);
    }
  };

  const filteredContacts = useMemo(() => {
    if (!searchTerm.trim()) return contactsSummary;
    const term = searchTerm.toLowerCase();
    return contactsSummary.filter(
      (c) =>
        c.nome.toLowerCase().includes(term) ||
        c.email.toLowerCase().includes(term) ||
        c.locais.some((l) => l.toLowerCase().includes(term))
    );
  }, [contactsSummary, searchTerm]);

  const totalContactsWithErrors = useMemo(
    () => contactsSummary.filter((c) => c.total_erros > 0).length,
    [contactsSummary]
  );

  return (
    <div className="space-y-6">
      {/* Banner Principal */}
      <div className="bg-lider-card border border-lider-border rounded-md p-6 shadow-subtle flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-lider-wood font-medium flex items-center space-x-1.5">
            <Mail className="w-3.5 h-3.5" />
            <span>Disparo Automatizado & Comunicação Fabril</span>
          </span>
          <h2 className="text-xl font-semibold text-lider-primary tracking-tight mt-1">
            Envio de Notificações de Erros de Apontamento
          </h2>
          <p className="text-xs text-lider-secondary mt-1">
            Compila ordens com divergência de saldo para os locais de produção de cada destinatário e despacha e-mails com a tabela formatada.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={loadSummary}
            disabled={isLoading}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-medium border border-lider-border rounded-sm bg-lider-canvas hover:bg-lider-card text-lider-primary transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-lider-wood ${isLoading ? 'animate-spin' : ''}`} />
            <span>Recarregar</span>
          </button>

          <button
            onClick={() => handleSendBatch(true)}
            disabled={isSendingBatch || !hasResults || totalContactsWithErrors === 0}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-lider-primary text-white text-xs font-medium rounded-sm hover:bg-[#2A2A2A] active:bg-black transition-all shadow-subtle disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5 text-lider-wood" />
            <span>Enviar para Todos com Divergências ({totalContactsWithErrors})</span>
          </button>
        </div>
      </div>

      {/* Regra de Saudação e Mensagem Obrigatória */}
      <div className="bg-lider-canvas border border-lider-border rounded-md p-4 text-xs flex items-start space-x-3">
        <Sparkles className="w-4 h-4 text-lider-wood mt-0.5 flex-shrink-0" />
        <div className="space-y-1">
          <span className="font-semibold text-lider-primary">
            Padrão de Mensagem Automática Configurado:
          </span>
          <p className="text-lider-secondary italic font-mono text-[11px]">
            "(Bom dia ou boa tarde a depender do horário), [Nome do contato] segue lista de erros de apontamento dos próximos {diasUteis} dias."
          </p>
          <p className="text-[11px] text-lider-tertiary">
            Janela de análise calculada em <strong>{diasUteis} dias úteis</strong> a partir da data de referência {dataRef ? `(${dataRef})` : ''}, desconsiderando sábados, domingos e feriados cadastrados.
          </p>
        </div>
      </div>

      {/* Alerta de erro */}
      {error && (
        <div className="p-3 bg-lider-dangerLight border border-lider-danger/20 text-lider-danger text-xs rounded-sm flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Alerta de ausência de resultados ativos */}
      {!hasResults && (
        <div className="p-4 bg-amber-50 border border-amber-200 text-amber-900 rounded-md text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>
              Nenhuma análise de erros de apontamento ativa no momento. Execute uma auditoria para compilar os dados reais de estoque e consumo.
            </span>
          </div>
          {onNavigateToAnalysis && (
            <button
              onClick={onNavigateToAnalysis}
              className="px-3 py-1 bg-amber-800 text-white rounded-sm font-medium hover:bg-amber-900 transition-colors"
            >
              Ir para Auditoria
            </button>
          )}
        </div>
      )}

      {/* Barra de Ações e Filtro de Contatos */}
      <div className="bg-lider-card border border-lider-border rounded-md p-4 shadow-subtle flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          <div className="relative min-w-[200px] flex-1 max-w-sm">
            <Search className="w-4 h-4 text-lider-tertiary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filtrar por nome, e-mail ou local..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood text-lider-primary"
            />
          </div>

          {/* Seletor de Tipo de Insumo (C / P / TODOS) */}
          <div className="flex items-center space-x-1.5">
            <label className="text-[11px] font-semibold text-lider-secondary shrink-0">
              Tipo:
            </label>
            <select
              value={tipoFiltro}
              onChange={(e) => setTipoFiltro(e.target.value as 'TODOS' | 'P' | 'C')}
              className="px-2.5 py-1.5 text-xs bg-lider-canvas border border-lider-border rounded-sm font-medium focus:outline-none focus:border-lider-wood text-lider-primary"
            >
              <option value="TODOS">Todos (Produzidos e Comprados)</option>
              <option value="P">Apenas Produzidos (P)</option>
              <option value="C">Apenas Comprados (C)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs shrink-0">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={selectAllWithErrors}
              className="text-lider-wood hover:underline font-medium"
            >
              Selecionar com Erros ({totalContactsWithErrors})
            </button>
            <span className="text-lider-divider">|</span>
            <button
              type="button"
              onClick={clearSelection}
              className="text-lider-tertiary hover:underline"
            >
              Limpar Seleção
            </button>
          </div>

          <button
            onClick={() => handleSendBatch(false)}
            disabled={selectedContactIds.length === 0 || isSendingBatch}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-lider-primary text-white font-medium rounded-sm hover:bg-[#2A2A2A] disabled:opacity-50 transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Disparar Selecionados ({selectedContactIds.length})</span>
          </button>
        </div>
      </div>

      {/* Tabela de Destinatários & Compilação */}
      <div className="bg-lider-card border border-lider-border rounded-md shadow-subtle overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-lider-tertiary">
            <div className="w-6 h-6 border-2 border-lider-wood border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Compilando ordens passíveis de erro por responsável...
          </div>
        ) : filteredContacts.length === 0 ? (
          <div className="p-12 text-center space-y-2 text-xs text-lider-secondary">
            <Mail className="w-8 h-8 text-lider-tertiary mx-auto" />
            <p className="font-semibold text-lider-primary">Nenhum destinatário encontrado</p>
            <p className="text-lider-tertiary">
              Cadastre contatos e atribua locais de produção para habilitar o envio automático.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-lider-canvas border-b border-lider-border text-[11px] font-semibold text-lider-tertiary uppercase tracking-wider">
                  <th className="p-3 w-10 text-center">
                    <input
                      type="checkbox"
                      checked={
                        selectedContactIds.length > 0 &&
                        selectedContactIds.length === filteredContacts.length
                      }
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedContactIds(filteredContacts.map((c) => c.contact_id));
                        } else {
                          setSelectedContactIds([]);
                        }
                      }}
                      className="rounded-xs border-lider-border text-lider-wood focus:ring-0 cursor-pointer"
                    />
                  </th>
                  <th className="p-3">Destinatário & E-mail</th>
                  <th className="p-3">Locais de Produção Atribuídos</th>
                  <th className="p-3 text-center">Divergências Identificadas</th>
                  <th className="p-3 text-center">Status de Envio</th>
                  <th className="p-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-lider-divider">
                {filteredContacts.map((c) => {
                  const isSelected = selectedContactIds.includes(c.contact_id);
                  const isSendingThis = sendingContactId === c.contact_id;
                  const sendResult = sendStatuses[c.contact_id];

                  return (
                    <tr
                      key={c.contact_id}
                      className={`hover:bg-lider-canvas/50 transition-colors ${
                        isSelected ? 'bg-lider-canvas/70' : ''
                      }`}
                    >
                      <td className="p-3 text-center">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectContact(c.contact_id)}
                          className="rounded-xs border-lider-border text-lider-wood focus:ring-0 cursor-pointer"
                        />
                      </td>

                      <td className="p-3">
                        <div className="font-medium text-lider-primary">{c.nome}</div>
                        <div className="text-[11px] text-lider-secondary font-mono">{c.email}</div>
                      </td>

                      <td className="p-3">
                        <div className="flex flex-wrap gap-1 max-w-md">
                          {c.locais.map((loc) => (
                            <span
                              key={loc}
                              className="inline-flex items-center px-1.5 py-0.5 rounded-xs text-[10px] font-mono bg-lider-canvas text-lider-primary border border-lider-border"
                            >
                              {loc}
                            </span>
                          ))}
                        </div>
                      </td>

                      <td className="p-3 text-center">
                        {c.total_erros > 0 ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-sm text-xs font-semibold bg-lider-dangerLight text-lider-danger border border-lider-danger/20">
                            <span>{c.total_erros} erros</span>
                            <span className="text-[10px] opacity-75 font-normal">
                              ({c.ops_com_erro} OPs)
                            </span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-sm text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Sem divergências</span>
                          </span>
                        )}
                      </td>

                      <td className="p-3 text-center">
                        {sendResult ? (
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-xs text-[11px] font-medium ${
                              sendResult.status === 'SENT'
                                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                                : sendResult.status === 'SIMULATED'
                                ? 'bg-blue-50 text-blue-800 border border-blue-200'
                                : 'bg-lider-dangerLight text-lider-danger border border-lider-danger/20'
                            }`}
                            title={sendResult.message}
                          >
                            {sendResult.status === 'SENT' && 'Enviado'}
                            {sendResult.status === 'SIMULATED' && 'Simulado (OK)'}
                            {sendResult.status === 'FAILED' && 'Falha no Envio'}
                            {sendResult.status === 'SKIPPED_NO_ERRORS' && 'Ignorado (Sem erros)'}
                          </span>
                        ) : (
                          <span className="text-[11px] text-lider-tertiary">Pendente</span>
                        )}
                      </td>

                      <td className="p-3 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            type="button"
                            onClick={() => handleOpenPreview(c.contact_id)}
                            disabled={loadingPreviewContactId === c.contact_id}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-medium border border-lider-border rounded-sm bg-lider-canvas hover:bg-lider-card text-lider-primary transition-colors disabled:opacity-50"
                          >
                            {loadingPreviewContactId === c.contact_id ? (
                              <div className="w-3 h-3 border-2 border-lider-wood border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <Eye className="w-3.5 h-3.5 text-lider-tertiary" />
                            )}
                            <span>Ver Prévia & Tabela</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleSendSingle(c.contact_id)}
                            disabled={isSendingThis}
                            className="inline-flex items-center space-x-1 px-3 py-1 text-xs font-medium bg-lider-primary text-white rounded-sm hover:bg-[#2A2A2A] transition-colors disabled:opacity-50"
                          >
                            {isSendingThis ? (
                              <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                              <Send className="w-3 h-3 text-lider-wood" />
                            )}
                            <span>Enviar</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal de Prévia do E-mail e Tabela Filtrada */}
      {previewData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-lider-card border border-lider-border rounded-md shadow-card w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden animate-fadeIn">
            {/* Cabeçalho do Modal */}
            <div className="px-6 py-4 border-b border-lider-divider flex items-center justify-between bg-lider-card">
              <div>
                <span className="text-xs uppercase tracking-widest text-lider-wood font-medium">
                  Prévia do E-mail Compilado
                </span>
                <h3 className="text-base font-semibold text-lider-primary">
                  {previewData.subject}
                </h3>
              </div>
              <button
                onClick={() => setPreviewData(null)}
                className="text-lider-tertiary hover:text-lider-primary p-1 rounded-sm"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Metadados do Envio */}
            <div className="px-6 py-3 bg-lider-canvas border-b border-lider-border text-xs space-y-1">
              <div className="flex justify-between">
                <div>
                  <span className="text-lider-tertiary">Para: </span>
                  <strong className="text-lider-primary">{previewData.contact_name}</strong>{' '}
                  <span className="text-lider-secondary">&lt;{previewData.email}&gt;</span>
                </div>
                <div>
                  <span className="text-lider-tertiary">Divergências filtradas: </span>
                  <strong className="text-lider-danger">{previewData.total_erros} ordens</strong>
                </div>
              </div>
              <div className="flex items-center space-x-1 text-[11px] text-lider-secondary">
                <Building2 className="w-3 h-3 text-lider-tertiary" />
                <span>Locais do contato: {previewData.locais.join(', ')}</span>
              </div>
            </div>

            {/* Alternador de Abas */}
            <div className="px-6 border-b border-lider-divider flex space-x-6 text-xs bg-lider-card">
              <button
                onClick={() => setPreviewTab('visual')}
                className={`py-3 font-medium border-b-2 transition-colors ${
                  previewTab === 'visual'
                    ? 'border-lider-wood text-lider-primary'
                    : 'border-transparent text-lider-tertiary hover:text-lider-secondary'
                }`}
              >
                Visualização do E-mail (HTML)
              </button>
              <button
                onClick={() => setPreviewTab('tabela')}
                className={`py-3 font-medium border-b-2 transition-colors ${
                  previewTab === 'tabela'
                    ? 'border-lider-wood text-lider-primary'
                    : 'border-transparent text-lider-tertiary hover:text-lider-secondary'
                }`}
              >
                Tabela de Dados ({previewData.records.length})
              </button>
              <button
                onClick={() => setPreviewTab('texto')}
                className={`py-3 font-medium border-b-2 transition-colors ${
                  previewTab === 'texto'
                    ? 'border-lider-wood text-lider-primary'
                    : 'border-transparent text-lider-tertiary hover:text-lider-secondary'
                }`}
              >
                Corpo em Texto Puro
              </button>
            </div>

            {/* Conteúdo da Aba */}
            <div className="flex-1 overflow-y-auto p-6 bg-lider-canvas">
              {previewTab === 'visual' && (
                <div
                  className="bg-white rounded-sm border border-lider-border p-4 shadow-subtle overflow-x-auto"
                  dangerouslySetInnerHTML={{ __html: previewData.html_body }}
                />
              )}

              {previewTab === 'tabela' && (
                <div className="bg-lider-card border border-lider-border rounded-sm overflow-hidden">
                  <div className="overflow-x-auto max-h-[55vh]">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead className="bg-lider-canvas border-b border-lider-border text-[11px] font-semibold text-lider-tertiary uppercase tracking-wider sticky top-0">
                        <tr>
                          <th className="p-2.5">OP</th>
                          <th className="p-2.5">Produto</th>
                          <th className="p-2.5">Componente</th>
                          <th className="p-2.5 text-center">Tipo</th>
                          <th className="p-2.5">Local</th>
                          <th className="p-2.5">Entrega</th>
                          <th className="p-2.5 text-right">Déficit</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-lider-divider">
                        {previewData.records.length === 0 ? (
                          <tr>
                            <td colSpan={7} className="p-6 text-center text-emerald-700">
                              Nenhuma divergência identificada para os locais deste contato.
                            </td>
                          </tr>
                        ) : (
                          previewData.records.map((r) => {
                            const isP = (r.tipo_componente || 'C').toUpperCase() === 'P';
                            return (
                              <tr key={r.id} className="hover:bg-lider-canvas/40">
                                <td className="p-2.5 font-mono font-medium">{r.op}</td>
                                <td className="p-2.5 text-lider-secondary">{r.produto_op}</td>
                                <td className="p-2.5">
                                  <div className="font-medium text-lider-primary">{r.codigo_componente}</div>
                                  <div className="text-[10px] text-lider-tertiary truncate max-w-xs">{r.descricao_componente}</div>
                                </td>
                                <td className="p-2.5 text-center">
                                  <span
                                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                                      isP
                                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                                        : 'bg-amber-50 text-amber-700 border-amber-200'
                                    }`}
                                  >
                                    {isP ? 'P' : 'C'}
                                  </span>
                                </td>
                                <td className="p-2.5 font-mono text-[11px]">{r.local_producao}</td>
                                <td className="p-2.5 font-mono text-[11px]">{r.data_entrega}</td>
                                <td className="p-2.5 text-right font-mono font-bold text-lider-danger">
                                  -{r.deficit_saldo}
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {previewTab === 'texto' && (
                <pre className="p-4 bg-lider-primary text-white font-mono text-xs rounded-sm whitespace-pre-wrap leading-relaxed overflow-x-auto">
                  {previewData.text_body}
                </pre>
              )}
            </div>

            {/* Rodapé do Modal */}
            <div className="px-6 py-3 border-t border-lider-divider flex items-center justify-between bg-lider-card">
              <span className="text-[11px] text-lider-tertiary">
                Disparo via SMTP corporativo (ou simulação automática em ambiente local).
              </span>

              <div className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={() => setPreviewData(null)}
                  className="px-4 py-2 text-xs font-medium text-lider-secondary hover:bg-lider-canvas rounded-sm border border-lider-border transition-colors"
                >
                  Fechar
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    await handleSendSingle(previewData.contact_id);
                    setPreviewData(null);
                  }}
                  className="inline-flex items-center space-x-2 px-4 py-2 bg-lider-primary text-white text-xs font-medium rounded-sm hover:bg-[#2A2A2A] transition-all"
                >
                  <Send className="w-3.5 h-3.5 text-lider-wood" />
                  <span>Enviar este E-mail</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
