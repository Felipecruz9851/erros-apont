import React, { useState, useMemo, useEffect } from 'react';
import {
  Search,
  ArrowUpDown,
  Download,
  Filter,
  Mail,
  Users,
  X,
  Send,
  CheckCircle2,
  AlertCircle,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { ErroApontamento, Contact } from '../../types';
import { emailsApi, contactsApi } from '../../services/api';

interface PointingErrorsTableProps {
  records: ErroApontamento[];
  onExportCsv: () => void;
  onExportJson: () => void;
}

export const PointingErrorsTable: React.FC<PointingErrorsTableProps> = ({
  records,
  onExportCsv,
  onExportJson,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFabrica, setSelectedFabrica] = useState<string>('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedTipo, setSelectedTipo] = useState<string>('ALL');
  const [sortField, setSortField] = useState<keyof ErroApontamento>('data_entrega');
  const [sortAsc, setSortAsc] = useState<boolean>(true);
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  // Estado de seleção de linhas
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Estados dos Modais de Envio de Linhas Marcadas
  const [isSendToLocaisOpen, setIsSendToLocaisOpen] = useState<boolean>(false);
  const [isSendToEmailOpen, setIsSendToEmailOpen] = useState<boolean>(false);
  const [targetEmail, setTargetEmail] = useState<string>('');
  const [targetName, setTargetName] = useState<string>('');
  const [isSending, setIsSending] = useState<boolean>(false);
  const [actionFeedback, setActionFeedback] = useState<{
    type: 'success' | 'error';
    title: string;
    message: string;
    details?: string[];
  } | null>(null);

  // Extrai lista única de fábricas
  const fabricas = useMemo(() => {
    const set = new Set(records.map((r) => r.fabrica).filter(Boolean));
    return Array.from(set).sort();
  }, [records]);

  // Filtragem multi-critério
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      const matchSearch =
        !searchTerm ||
        r.op.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.codigo_componente.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.descricao_componente.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.local_producao.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (r.produto_op && r.produto_op.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchFab = selectedFabrica === 'ALL' || r.fabrica === selectedFabrica;
      const matchSev =
        selectedSeverity === 'ALL' ||
        (selectedSeverity === 'ERROS' && r.severidade !== 'OK') ||
        r.severidade === selectedSeverity;

      const compTipo = (r.tipo_componente || 'C').toUpperCase();
      const matchTipo =
        selectedTipo === 'ALL' ||
        (selectedTipo === 'P' && compTipo === 'P') ||
        (selectedTipo === 'C' && compTipo !== 'P');

      return matchSearch && matchFab && matchSev && matchTipo;
    });
  }, [records, searchTerm, selectedFabrica, selectedSeverity, selectedTipo]);

  // Ordenação
  const sortedRecords = useMemo(() => {
    return [...filteredRecords].sort((a, b) => {
      const valA = a[sortField] ?? '';
      const valB = b[sortField] ?? '';

      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortAsc ? valA - valB : valB - valA;
      }
      return sortAsc
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredRecords, sortField, sortAsc]);

  // Paginação
  const totalPages = Math.ceil(sortedRecords.length / pageSize) || 1;
  const pagedRecords = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sortedRecords.slice(start, start + pageSize);
  }, [sortedRecords, page]);

  const handleSort = (field: keyof ErroApontamento) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  // Funções de Seleção de Linhas
  const toggleSelectRow = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const isAllCurrentPageSelected = useMemo(() => {
    if (pagedRecords.length === 0) return false;
    return pagedRecords.every((r) => selectedIds.has(r.id));
  }, [pagedRecords, selectedIds]);

  const toggleSelectAllCurrentPage = () => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (isAllCurrentPageSelected) {
        pagedRecords.forEach((r) => next.delete(r.id));
      } else {
        pagedRecords.forEach((r) => next.add(r.id));
      }
      return next;
    });
  };

  const selectAllFiltered = () => {
    setSelectedIds(new Set(filteredRecords.map((r) => r.id)));
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  // Linhas selecionadas e locais envolvidos
  const selectedRecords = useMemo(() => {
    return records.filter((r) => selectedIds.has(r.id));
  }, [records, selectedIds]);

  const selectedLocales = useMemo(() => {
    const set = new Set(selectedRecords.map((r) => r.local_producao).filter(Boolean));
    return Array.from(set).sort();
  }, [selectedRecords]);

  // Carrega contatos para validar vínculos quando o modal de locais for aberto
  const [registeredContacts, setRegisteredContacts] = useState<Contact[]>([]);

  useEffect(() => {
    if (isSendToLocaisOpen) {
      contactsApi.list().then(setRegisteredContacts).catch(() => {});
    }
  }, [isSendToLocaisOpen]);

  // Contatos que possuem atribuição para os locais selecionados
  const matchingContacts = useMemo(() => {
    if (!registeredContacts.length || !selectedLocales.length) return [];
    const localesSet = new Set(selectedLocales.map((l) => l.toUpperCase()));
    return registeredContacts
      .map((c) => {
        const matched = c.locais.filter((l) => localesSet.has(l.toUpperCase()));
        return {
          contact: c,
          matchedLocais: matched,
        };
      })
      .filter((item) => item.matchedLocais.length > 0);
  }, [registeredContacts, selectedLocales]);

  // Locais selecionados que não têm nenhum responsável vinculado
  const unassignedLocales = useMemo(() => {
    const assigned = new Set(
      matchingContacts.flatMap((m) => m.matchedLocais.map((l) => l.toUpperCase()))
    );
    return selectedLocales.filter((l) => !assigned.has(l.toUpperCase()));
  }, [selectedLocales, matchingContacts]);

  // Disparo 1: Enviar linhas marcadas para responsáveis dos locais
  const handleSendToLocais = async () => {
    if (selectedIds.size === 0 || matchingContacts.length === 0) return;
    setIsSending(true);
    setActionFeedback(null);
    try {
      const res = await emailsApi.send({
        selected_record_ids: Array.from(selectedIds),
        selected_records: selectedRecords,
        tipo_filtro: selectedTipo !== 'ALL' ? (selectedTipo as 'C' | 'P') : 'TODOS',
      });

      const details = res.results.map(
        (r) => `${r.contact_name} (${r.email}): ${r.total_erros} item(ns) - ${r.status}`
      );

      setActionFeedback({
        type: 'success',
        title: 'Envio Concluído com Sucesso',
        message: `Disparo realizado para ${res.total_sent} responsável(is) vinculado(s) aos locais das ${selectedIds.size} linhas selecionadas.`,
        details,
      });
      setIsSendToLocaisOpen(false);
      clearSelection();
    } catch (err: any) {
      setActionFeedback({
        type: 'error',
        title: 'Falha no Disparo',
        message: err?.response?.data?.detail || 'Erro ao despachar e-mails para os responsáveis.',
      });
    } finally {
      setIsSending(false);
    }
  };

  // Disparo 2: Enviar linhas marcadas exclusivamente para e-mail específico
  const handleSendToSpecificEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetEmail.trim() || selectedIds.size === 0) return;
    setIsSending(true);
    setActionFeedback(null);
    try {
      const res = await emailsApi.send({
        selected_record_ids: Array.from(selectedIds),
        selected_records: selectedRecords,
        target_email: targetEmail.trim(),
        target_name: targetName.trim() || undefined,
        tipo_filtro: selectedTipo !== 'ALL' ? (selectedTipo as 'C' | 'P') : 'TODOS',
      });

      const firstRes = res.results[0];
      setActionFeedback({
        type: 'success',
        title: 'E-mail Enviado com Sucesso',
        message: `Tabela com ${selectedIds.size} linha(s) marcada(s) enviada exclusivamente para ${targetEmail.trim()} (${firstRes?.status || 'OK'}).`,
      });
      setIsSendToEmailOpen(false);
      setTargetEmail('');
      setTargetName('');
      clearSelection();
    } catch (err: any) {
      setActionFeedback({
        type: 'error',
        title: 'Falha no Envio',
        message: err?.response?.data?.detail || 'Erro ao enviar e-mail para o destinatário informado.',
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="bg-lider-card border border-lider-border rounded-md shadow-card overflow-hidden">
      {/* Feedback Toast/Banner de Ação */}
      {actionFeedback && (
        <div
          className={`p-4 border-b flex items-start justify-between text-xs transition-colors ${
            actionFeedback.type === 'success'
              ? 'bg-emerald-50/90 text-emerald-900 border-emerald-200'
              : 'bg-red-50/90 text-red-900 border-red-200'
          }`}
        >
          <div className="flex items-start space-x-2.5">
            {actionFeedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            )}
            <div>
              <div className="font-semibold">{actionFeedback.title}</div>
              <div className="mt-0.5 opacity-90">{actionFeedback.message}</div>
              {actionFeedback.details && actionFeedback.details.length > 0 && (
                <ul className="mt-2 list-disc list-inside space-y-0.5 opacity-80 text-[11px]">
                  {actionFeedback.details.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          <button
            onClick={() => setActionFeedback(null)}
            className="p-1 hover:bg-black/5 rounded transition-colors text-current opacity-70 hover:opacity-100"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Barra de Ações & Filtros */}
      <div className="p-4 border-b border-lider-divider flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2.5 flex-1">
          {/* Busca textual */}
          <div className="relative min-w-[200px] flex-1 max-w-xs">
            <Search className="w-3.5 h-3.5 text-lider-tertiary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              placeholder="Buscar por OP, componente ou local..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood text-lider-primary placeholder:text-lider-tertiary"
            />
          </div>

          {/* Filtro Fábrica */}
          <div className="flex items-center space-x-1.5">
            <Filter className="w-3 h-3 text-lider-tertiary" />
            <select
              value={selectedFabrica}
              onChange={(e) => {
                setSelectedFabrica(e.target.value);
                setPage(1);
              }}
              className="px-2 py-1.5 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood text-lider-primary"
            >
              <option value="ALL">Todas as Fábricas</option>
              {fabricas.map((fab) => (
                <option key={fab} value={fab}>
                  {fab}
                </option>
              ))}
            </select>
          </div>

          {/* Filtro Severidade / Status */}
          <select
            value={selectedSeverity}
            onChange={(e) => {
              setSelectedSeverity(e.target.value);
              setPage(1);
            }}
            className="px-2 py-1.5 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood text-lider-primary"
          >
            <option value="ALL">Todos na Janela (Erros + OK)</option>
            <option value="ERROS">Apenas Passíveis de Erro</option>
            <option value="ALTA">Alta (Crítica)</option>
            <option value="MEDIA">Média (Parcial)</option>
            <option value="OK">Atendidas (OK)</option>
          </select>

          {/* Filtro Tipo de Componente: C ou P */}
          <select
            value={selectedTipo}
            onChange={(e) => {
              setSelectedTipo(e.target.value);
              setPage(1);
            }}
            className="px-2 py-1.5 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood text-lider-primary font-medium"
          >
            <option value="ALL">Tipos: Produzidos e Comprados</option>
            <option value="P">Apenas Produzidos (P)</option>
            <option value="C">Apenas Comprados (C)</option>
          </select>
        </div>

        {/* Botões de Exportação */}
        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={onExportCsv}
            disabled={records.length === 0}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium border border-lider-border rounded-sm bg-lider-canvas hover:bg-lider-subtle text-lider-primary transition-colors disabled:opacity-40"
          >
            <Download className="w-3.5 h-3.5 text-lider-tertiary" />
            <span>CSV</span>
          </button>
          <button
            onClick={onExportJson}
            disabled={records.length === 0}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium border border-lider-border rounded-sm bg-lider-canvas hover:bg-lider-subtle text-lider-primary transition-colors disabled:opacity-40"
          >
            <Download className="w-3.5 h-3.5 text-lider-tertiary" />
            <span>JSON</span>
          </button>
        </div>
      </div>

      {/* Barra de Ações de Linhas Selecionadas */}
      {selectedIds.size > 0 && (
        <div className="bg-amber-50/80 border-b border-amber-200/80 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-amber-200/80 text-amber-900 font-bold text-[11px]">
              {selectedIds.size} linha(s) marcada(s)
            </span>
            <span className="text-amber-800 text-[11px] hidden sm:inline">
              Locais: {selectedLocales.join(', ') || 'Nenhum'}
            </span>
            <button
              onClick={selectAllFiltered}
              className="text-[11px] text-amber-900 underline hover:text-amber-700"
            >
              Marcar todas as {filteredRecords.length} filtradas
            </button>
            <button
              onClick={clearSelection}
              className="text-[11px] text-lider-tertiary hover:text-red-700 underline"
            >
              Desmarcar
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsSendToLocaisOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-lider-primary text-lider-canvas hover:bg-lider-primary/90 transition-colors shadow-sm"
              title="Dispara e-mails para os responsáveis com base nos locais de produção das linhas marcadas"
            >
              <Users className="w-3.5 h-3.5" />
              <span>Enviar para Responsáveis dos Locais</span>
            </button>
            <button
              onClick={() => setIsSendToEmailOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded border border-lider-border bg-lider-card text-lider-primary hover:bg-lider-canvas transition-colors shadow-sm"
              title="Dispara e-mail com as linhas marcadas para um destinatário avulso"
            >
              <Mail className="w-3.5 h-3.5 text-lider-tertiary" />
              <span>Enviar para E-mail Específico</span>
            </button>
          </div>
        </div>
      )}

      {/* Tabela com bordas de 1px e respiro generoso */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-lider-canvas/80 text-lider-secondary border-b border-lider-border uppercase tracking-wider text-[10px]">
              <th className="py-3 px-3 w-10 text-center">
                <input
                  type="checkbox"
                  checked={isAllCurrentPageSelected}
                  onChange={toggleSelectAllCurrentPage}
                  className="rounded border-lider-border text-lider-primary focus:ring-0 cursor-pointer"
                  title="Marcar todas desta página"
                />
              </th>
              <th className="py-3 px-3 font-semibold cursor-pointer" onClick={() => handleSort('fabrica')}>
                <div className="flex items-center space-x-1">
                  <span>Fábrica</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-3 font-semibold cursor-pointer" onClick={() => handleSort('op')}>
                <div className="flex items-center space-x-1">
                  <span>OP / Ordem</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-3 font-semibold cursor-pointer" onClick={() => handleSort('data_entrega')}>
                <div className="flex items-center space-x-1">
                  <span>Entrega</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-3 font-semibold cursor-pointer" onClick={() => handleSort('local_producao')}>
                <div className="flex items-center space-x-1">
                  <span>Local Produção</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-3 font-semibold cursor-pointer" onClick={() => handleSort('codigo_componente')}>
                <div className="flex items-center space-x-1">
                  <span>Insumo / Componente</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-3 font-semibold text-center cursor-pointer" onClick={() => handleSort('tipo_componente')}>
                <div className="flex items-center justify-center space-x-1">
                  <span>Tipo</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-3 font-semibold text-right cursor-pointer" onClick={() => handleSort('qtd_necessaria')}>
                <div className="flex items-center justify-end space-x-1">
                  <span>Necessário</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-3 font-semibold text-right cursor-pointer" onClick={() => handleSort('saldo_remanescente')}>
                <div className="flex items-center justify-end space-x-1">
                  <span>Saldo Fila</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-3 font-semibold text-right cursor-pointer" onClick={() => handleSort('deficit_saldo')}>
                <div className="flex items-center justify-end space-x-1">
                  <span>Déficit</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-3 font-semibold text-center">Status / Severidade</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-lider-divider">
            {pagedRecords.length === 0 ? (
              <tr>
                <td colSpan={11} className="py-12 text-center text-lider-tertiary">
                  {records.length === 0
                    ? 'Nenhum erro de apontamento identificado. Todos os componentes possuem saldo no local.'
                    : 'Nenhum registro corresponde aos filtros selecionados.'}
                </td>
              </tr>
            ) : (
              pagedRecords.map((r) => {
                const isSelected = selectedIds.has(r.id);
                const isP = (r.tipo_componente || 'C').toUpperCase() === 'P';

                return (
                  <tr
                    key={r.id}
                    className={`transition-colors ${
                      isSelected ? 'bg-amber-50/60 hover:bg-amber-50/80' : 'hover:bg-lider-canvas/50'
                    }`}
                  >
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelectRow(r.id)}
                        className="rounded border-lider-border text-lider-primary focus:ring-0 cursor-pointer"
                      />
                    </td>
                    <td className="py-3 px-3 font-medium text-lider-primary whitespace-nowrap">{r.fabrica}</td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className="font-semibold text-lider-primary">{r.op}</span>
                      {r.produto_op && (
                        <div className="text-[10px] text-lider-tertiary truncate max-w-[170px]" title={r.produto_op}>
                          {r.produto_op}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap text-lider-secondary">
                      <div>{r.data_entrega || '-'}</div>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap text-lider-secondary font-mono text-[11px]">
                      {r.local_producao}
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-medium text-lider-primary">{r.codigo_componente}</div>
                      <div className="text-[10px] text-lider-tertiary truncate max-w-[200px]" title={r.descricao_componente}>
                        {r.descricao_componente}
                      </div>
                    </td>
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      <span
                        title={isP ? 'Componente Produzido (P)' : 'Componente Comprado (C)'}
                        className={`inline-block px-1.5 py-0.5 text-[10px] font-bold rounded border ${
                          isP
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {isP ? 'P' : 'C'}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-medium text-lider-secondary whitespace-nowrap">
                      {r.qtd_necessaria.toLocaleString('pt-BR', { minimumFractionDigits: 1 })}
                    </td>
                    <td className="py-3 px-3 text-right whitespace-nowrap">
                      <span
                        className={
                          r.saldo_remanescente <= 0 ? 'text-lider-danger font-medium' : 'text-lider-secondary'
                        }
                      >
                        {r.saldo_remanescente.toLocaleString('pt-BR', { minimumFractionDigits: 1 })}
                      </span>
                      <div className="text-[10px] text-lider-tertiary">
                        Inicial: {r.saldo_inicial_local.toLocaleString('pt-BR', { minimumFractionDigits: 1 })}
                      </div>
                    </td>
                    <td className="py-3 px-3 text-right font-bold whitespace-nowrap">
                      {r.deficit_saldo > 0 ? (
                        <span className="text-lider-danger">
                          -{r.deficit_saldo.toLocaleString('pt-BR', { minimumFractionDigits: 1 })}
                        </span>
                      ) : (
                        <span className="text-lider-tertiary font-normal">0,0</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      <span
                        className={`inline-block px-2 py-0.5 text-[10px] font-semibold rounded-sm border ${
                          r.severidade === 'OK'
                            ? 'bg-lider-successLight text-lider-success border-lider-success/20'
                            : r.severidade === 'ALTA'
                            ? 'bg-lider-dangerLight text-lider-danger border-lider-danger/20'
                            : 'bg-lider-warningLight text-lider-warning border-lider-warning/20'
                        }`}
                      >
                        {r.severidade === 'OK' ? 'OK' : r.severidade === 'ALTA' ? 'CRÍTICA' : 'PARCIAL'}
                      </span>
                      <div className="text-[9px] text-lider-tertiary mt-0.5">
                        {r.status_divergencia === 'OK'
                          ? 'Saldo Disponível'
                          : r.status_divergencia === 'SALDO_ZERADO_NO_LOCAL'
                          ? 'Saldo Zerado'
                          : 'Saldo Insuficiente'}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Paginação Líder */}
      <div className="p-4 border-t border-lider-divider flex items-center justify-between text-xs text-lider-secondary">
        <div>
          Mostrando <span className="font-medium text-lider-primary">{sortedRecords.length > 0 ? (page - 1) * pageSize + 1 : 0}</span> a{' '}
          <span className="font-medium text-lider-primary">
            {Math.min(page * pageSize, sortedRecords.length)}
          </span>{' '}
          de <span className="font-medium text-lider-primary">{sortedRecords.length}</span> ocorrências
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-2.5 py-1 text-xs border border-lider-border rounded-sm hover:bg-lider-canvas disabled:opacity-40 transition-colors"
          >
            Anterior
          </button>
          <span className="px-2 text-xs text-lider-tertiary">
            Página {page} de {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-2.5 py-1 text-xs border border-lider-border rounded-sm hover:bg-lider-canvas disabled:opacity-40 transition-colors"
          >
            Próxima
          </button>
        </div>
      </div>

      {/* Modal 1: Enviar Linhas Marcadas para Responsáveis dos Locais */}
      {isSendToLocaisOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-lider-card border border-lider-border rounded-lg shadow-2xl max-w-lg w-full overflow-hidden animate-fade-in">
            <div className="p-5 border-b border-lider-divider flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-lider-wood" />
                <h3 className="font-serif text-base text-lider-primary font-semibold">
                  Enviar para Responsáveis dos Locais
                </h3>
              </div>
              <button
                onClick={() => setIsSendToLocaisOpen(false)}
                disabled={isSending}
                className="text-lider-tertiary hover:text-lider-primary p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs">
              <p className="text-lider-secondary leading-relaxed">
                As <strong className="text-lider-primary font-bold">{selectedIds.size} linha(s) marcada(s)</strong> serão compiladas e enviadas <strong className="text-lider-primary">estritamente aos contatos cadastrados que têm vínculo com os locais</strong> dessas linhas:
              </p>

              <div className="bg-lider-canvas border border-lider-border rounded p-3 space-y-2">
                <div className="text-[11px] font-semibold text-lider-primary uppercase tracking-wider">
                  Locais de Produção Envolvidos ({selectedLocales.length}):
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {selectedLocales.map((loc) => (
                    <span
                      key={loc}
                      className="px-2 py-0.5 rounded bg-lider-subtle border border-lider-border text-[11px] font-mono text-lider-secondary"
                    >
                      {loc}
                    </span>
                  ))}
                </div>
              </div>

              {/* Lista dos responsáveis vinculados que receberão */}
              {matchingContacts.length > 0 ? (
                <div className="space-y-2">
                  <div className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider">
                    Responsáveis Vinculados a Notificar ({matchingContacts.length}):
                  </div>
                  <div className="space-y-1.5 max-h-36 overflow-y-auto">
                    {matchingContacts.map(({ contact, matchedLocais }) => (
                      <div
                        key={contact.id}
                        className="p-2 bg-emerald-50/70 border border-emerald-200/80 rounded flex items-center justify-between text-xs"
                      >
                        <div>
                          <div className="font-semibold text-emerald-950">{contact.nome}</div>
                          <div className="text-[11px] text-emerald-700 font-mono">{contact.email}</div>
                        </div>
                        <div className="flex flex-wrap gap-1 justify-end max-w-[50%]">
                          {matchedLocais.map((loc) => (
                            <span
                              key={loc}
                              className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-900 font-mono text-[10px] font-medium"
                            >
                              {loc}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded text-amber-900 text-xs space-y-1">
                  <div className="font-bold flex items-center space-x-1">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Nenhum responsável vinculado</span>
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    Nenhum contato cadastrado possui atribuição para os locais selecionados ({selectedLocales.join(', ')}).
                    Para disparar para responsáveis, vincule os contatos a esses locais na tela de Gestão de Contatos.
                  </p>
                </div>
              )}

              {unassignedLocales.length > 0 && matchingContacts.length > 0 && (
                <div className="p-2 bg-amber-50/60 border border-amber-200/60 rounded text-[11px] text-amber-800">
                  Atenção: Os locais <strong>{unassignedLocales.join(', ')}</strong> não possuem responsáveis cadastrados e não serão enviados.
                </div>
              )}

              <div className="text-[11px] text-lider-tertiary italic">
                Nota: No corpo do e-mail, as tabelas serão automaticamente separadas entre Componentes Produzidos (P) e Comprados (C).
              </div>
            </div>

            <div className="p-4 bg-lider-canvas/60 border-t border-lider-divider flex items-center justify-end space-x-2">
              <button
                type="button"
                onClick={() => setIsSendToLocaisOpen(false)}
                disabled={isSending}
                className="px-3.5 py-1.5 text-xs border border-lider-border rounded bg-lider-card text-lider-secondary hover:text-lider-primary hover:bg-lider-canvas transition-colors disabled:opacity-40"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSendToLocais}
                disabled={isSending || matchingContacts.length === 0}
                className="inline-flex items-center space-x-1.5 px-4 py-1.5 text-xs font-semibold rounded bg-lider-primary text-lider-canvas hover:bg-lider-primary/90 transition-colors shadow-sm disabled:opacity-50"
              >
                {isSending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Enviando...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Confirmar Disparo</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 2: Enviar Linhas Marcadas para E-mail Específico */}
      {isSendToEmailOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleSendToSpecificEmail}
            className="bg-lider-card border border-lider-border rounded-lg shadow-2xl max-w-md w-full overflow-hidden animate-fade-in"
          >
            <div className="p-5 border-b border-lider-divider flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Mail className="w-4 h-4 text-lider-wood" />
                <h3 className="font-serif text-base text-lider-primary font-semibold">
                  Enviar para E-mail Específico
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsSendToEmailOpen(false)}
                disabled={isSending}
                className="text-lider-tertiary hover:text-lider-primary p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs">
              <p className="text-lider-secondary leading-relaxed">
                Dispara um e-mail com as <strong className="text-lider-primary font-bold">{selectedIds.size} linha(s) marcada(s)</strong> <strong className="text-lider-primary">exclusivamente para o endereço informado abaixo</strong>, sem enviar para os responsáveis vinculados aos locais.
              </p>

              <div>
                <label className="block text-[11px] font-semibold text-lider-primary mb-1">
                  E-mail do Destinatário <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={targetEmail}
                  onChange={(e) => setTargetEmail(e.target.value)}
                  placeholder="destinatario@lider.design"
                  className="w-full px-3 py-1.5 text-xs bg-lider-canvas border border-lider-border rounded focus:outline-none focus:border-lider-wood text-lider-primary"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-lider-primary mb-1">
                  Nome do Destinatário ou Setor (Opcional)
                </label>
                <input
                  type="text"
                  value={targetName}
                  onChange={(e) => setTargetName(e.target.value)}
                  placeholder="Ex: Carlos / PCP Central"
                  className="w-full px-3 py-1.5 text-xs bg-lider-canvas border border-lider-border rounded focus:outline-none focus:border-lider-wood text-lider-primary"
                />
              </div>

              <div className="text-[11px] text-lider-tertiary italic">
                A mensagem incluirá as tabelas separadas entre Produzidos (P) e Comprados (C) e o resumo correspondente.
              </div>
            </div>

            <div className="p-4 bg-lider-canvas/60 border-t border-lider-divider flex items-center justify-end space-x-2">
              <button
                type="button"
                onClick={() => setIsSendToEmailOpen(false)}
                disabled={isSending}
                className="px-3.5 py-1.5 text-xs border border-lider-border rounded bg-lider-card text-lider-secondary hover:text-lider-primary hover:bg-lider-canvas transition-colors disabled:opacity-40"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isSending || !targetEmail.trim()}
                className="inline-flex items-center space-x-1.5 px-4 py-1.5 text-xs font-semibold rounded bg-lider-primary text-lider-canvas hover:bg-lider-primary/90 transition-colors shadow-sm disabled:opacity-50"
              >
                {isSending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Enviando...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Enviar Agora</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};