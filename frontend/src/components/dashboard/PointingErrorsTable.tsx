import React, { useState, useMemo } from 'react';
import { Search, ArrowUpDown, Download, Filter } from 'lucide-react';
import { ErroApontamento } from '../../types';

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
  const [sortField, setSortField] = useState<keyof ErroApontamento>('data_entrega');
  const [sortAsc, setSortAsc] = useState<boolean>(true);
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  // Extrai lista única de fábricas
  const fabricas = useMemo(() => {
    const set = new Set(records.map((r) => r.fabrica).filter(Boolean));
    return Array.from(set).sort();
  }, [records]);

  // Filtragem
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

      return matchSearch && matchFab && matchSev;
    });
  }, [records, searchTerm, selectedFabrica, selectedSeverity]);

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

  return (
    <div className="bg-lider-card border border-lider-border rounded-md shadow-card overflow-hidden">
      {/* Barra de Ações & Filtros */}
      <div className="p-5 border-b border-lider-divider flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Busca textual */}
          <div className="relative min-w-[220px] flex-1 max-w-sm">
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
              <option value="ALL">Todas as Fábricas ({records.length})</option>
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
        </div>

        {/* Botões de Exportação */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onExportCsv}
            disabled={records.length === 0}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium border border-lider-border rounded-sm bg-lider-canvas hover:bg-lider-subtle text-lider-primary transition-colors disabled:opacity-40"
          >
            <Download className="w-3.5 h-3.5 text-lider-tertiary" />
            <span>Exportar CSV</span>
          </button>
          <button
            onClick={onExportJson}
            disabled={records.length === 0}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium border border-lider-border rounded-sm bg-lider-canvas hover:bg-lider-subtle text-lider-primary transition-colors disabled:opacity-40"
          >
            <Download className="w-3.5 h-3.5 text-lider-tertiary" />
            <span>Exportar JSON</span>
          </button>
        </div>
      </div>

      {/* Tabela com bordas de 1px e respiro generoso */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-lider-canvas/80 text-lider-secondary border-b border-lider-border uppercase tracking-wider text-[10px]">
              <th className="py-3 px-4 font-semibold cursor-pointer" onClick={() => handleSort('fabrica')}>
                <div className="flex items-center space-x-1">
                  <span>Fábrica</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold cursor-pointer" onClick={() => handleSort('op')}>
                <div className="flex items-center space-x-1">
                  <span>OP / Ordem</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold cursor-pointer" onClick={() => handleSort('data_entrega')}>
                <div className="flex items-center space-x-1">
                  <span>Entrega / Fila</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold cursor-pointer" onClick={() => handleSort('local_producao')}>
                <div className="flex items-center space-x-1">
                  <span>Local Produção</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold cursor-pointer" onClick={() => handleSort('codigo_componente')}>
                <div className="flex items-center space-x-1">
                  <span>Insumo / Componente</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold text-right cursor-pointer" onClick={() => handleSort('qtd_necessaria')}>
                <div className="flex items-center justify-end space-x-1">
                  <span>Necessário</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold text-right cursor-pointer" onClick={() => handleSort('saldo_remanescente')}>
                <div className="flex items-center justify-end space-x-1">
                  <span>Saldo Fila</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold text-right cursor-pointer" onClick={() => handleSort('deficit_saldo')}>
                <div className="flex items-center justify-end space-x-1">
                  <span>Déficit</span>
                  <ArrowUpDown className="w-2.5 h-2.5" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold text-center">Status / Severidade</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-lider-divider">
            {pagedRecords.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-12 text-center text-lider-tertiary">
                  {records.length === 0
                    ? 'Nenhum erro de apontamento identificado. Todos os componentes possuem saldo no local.'
                    : 'Nenhum registro corresponde aos filtros selecionados.'}
                </td>
              </tr>
            ) : (
              pagedRecords.map((r) => (
                <tr key={r.id} className="hover:bg-lider-canvas/50 transition-colors">
                  <td className="py-3 px-4 font-medium text-lider-primary whitespace-nowrap">{r.fabrica}</td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="font-semibold text-lider-primary">{r.op}</span>
                    {r.produto_op && (
                      <div className="text-[10px] text-lider-tertiary truncate max-w-[180px]">{r.produto_op}</div>
                    )}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap text-lider-secondary">
                    <div>{r.data_entrega || '-'}</div>
                    <div className="text-[10px] text-lider-tertiary">Fila #{r.prioridade_fila}</div>
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap text-lider-secondary font-mono text-[11px]">
                    {r.local_producao}
                  </td>
                  <td className="py-3 px-4">
                    <div className="font-medium text-lider-primary">{r.codigo_componente}</div>
                    <div className="text-[10px] text-lider-tertiary truncate max-w-[200px]">
                      {r.descricao_componente}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right font-medium text-lider-secondary whitespace-nowrap">
                    {r.qtd_necessaria.toLocaleString('pt-BR', { minimumFractionDigits: 1 })}
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
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
                  <td className="py-3 px-4 text-right font-bold whitespace-nowrap">
                    {r.deficit_saldo > 0 ? (
                      <span className="text-lider-danger">
                        -{r.deficit_saldo.toLocaleString('pt-BR', { minimumFractionDigits: 1 })}
                      </span>
                    ) : (
                      <span className="text-lider-tertiary font-normal">0,0</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-center whitespace-nowrap">
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
              ))
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
    </div>
  );
};
