import React, { useState, useEffect, useMemo } from 'react';
import {
  UserPlus,
  Edit2,
  Trash2,
  Search,
  X,
  Check,
  AlertCircle,
  Building2,
  Mail,
  User,
  CheckSquare,
  Square,
} from 'lucide-react';
import { contactsApi } from '../../services/api';
import { Contact } from '../../types';

export const ContactsManager: React.FC = () => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [availableLocations, setAvailableLocations] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filtro de busca na lista de contatos
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Estado do Modal
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [formNome, setFormNome] = useState<string>('');
  const [formEmail, setFormEmail] = useState<string>('');
  const [selectedLocais, setSelectedLocais] = useState<string[]>([]);
  const [locationSearch, setLocationSearch] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Carrega contatos e locais disponíveis
  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [contactsData, locsData] = await Promise.all([
        contactsApi.list(),
        contactsApi.getLocations(),
      ]);
      setContacts(contactsData);
      setAvailableLocations(locsData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro ao carregar dados de contatos e locais.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openCreateModal = () => {
    setEditingContact(null);
    setFormNome('');
    setFormEmail('');
    setSelectedLocais([]);
    setLocationSearch('');
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (contact: Contact) => {
    setEditingContact(contact);
    setFormNome(contact.nome);
    setFormEmail(contact.email);
    setSelectedLocais([...contact.locais]);
    setLocationSearch('');
    setFormError(null);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingContact(null);
    setFormError(null);
  };

  const toggleLocation = (loc: string) => {
    setSelectedLocais((prev) =>
      prev.includes(loc) ? prev.filter((item) => item !== loc) : [...prev, loc]
    );
  };

  const selectAllFilteredLocations = () => {
    const toAdd = filteredAvailableLocations.filter((l) => !selectedLocais.includes(l));
    setSelectedLocais((prev) => [...prev, ...toAdd]);
  };

  const clearSelectedLocations = () => {
    setSelectedLocais([]);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formNome.trim()) {
      setFormError('Informe o nome do contato.');
      return;
    }
    if (!formEmail.trim() || !formEmail.includes('@')) {
      setFormError('Informe um e-mail válido.');
      return;
    }
    if (selectedLocais.length === 0) {
      setFormError('Selecione ao menos um local de produção para este contato.');
      return;
    }

    setIsSaving(true);
    setFormError(null);
    try {
      if (editingContact) {
        await contactsApi.update(editingContact.id, {
          nome: formNome,
          email: formEmail,
          locais: selectedLocais,
        });
        setSuccessMsg(`Contato "${formNome}" atualizado com sucesso.`);
      } else {
        await contactsApi.create({
          nome: formNome,
          email: formEmail,
          locais: selectedLocais,
        });
        setSuccessMsg(`Contato "${formNome}" cadastrado com sucesso.`);
      }
      closeModal();
      await loadData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setFormError(err?.response?.data?.detail || 'Erro ao salvar contato no servidor.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (contact: Contact) => {
    if (!window.confirm(`Confirma a exclusão do contato "${contact.nome}" (${contact.email})?`)) {
      return;
    }
    try {
      await contactsApi.delete(contact.id);
      setSuccessMsg(`Contato "${contact.nome}" removido com sucesso.`);
      await loadData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro ao excluir contato.');
    }
  };

  // Filtragem de contatos
  const filteredContacts = useMemo(() => {
    if (!searchTerm.trim()) return contacts;
    const term = searchTerm.toLowerCase();
    return contacts.filter(
      (c) =>
        c.nome.toLowerCase().includes(term) ||
        c.email.toLowerCase().includes(term) ||
        c.locais.some((l) => l.toLowerCase().includes(term))
    );
  }, [contacts, searchTerm]);

  // Filtragem de locais no modal
  const filteredAvailableLocations = useMemo(() => {
    if (!locationSearch.trim()) return availableLocations;
    return availableLocations.filter((l) =>
      l.toLowerCase().includes(locationSearch.toLowerCase())
    );
  }, [availableLocations, locationSearch]);

  return (
    <div className="space-y-6">
      {/* Header da Página */}
      <div className="bg-lider-card border border-lider-border rounded-md p-6 shadow-subtle flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-lider-wood font-medium">
            Gerenciamento de Destinatários
          </span>
          <h2 className="text-xl font-semibold text-lider-primary tracking-tight mt-1">
            Cadastro de Contatos & Locais de Produção
          </h2>
          <p className="text-xs text-lider-secondary mt-1">
            Cadastre os responsáveis que receberão os alertas de erros de apontamento dos seus respectivos locais fabris.
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-lider-primary text-white text-xs font-medium rounded-sm hover:bg-[#2A2A2A] active:bg-black transition-all shadow-subtle"
        >
          <UserPlus className="w-4 h-4 text-lider-wood" />
          <span>Novo Contato</span>
        </button>
      </div>

      {/* Alertas */}
      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-sm flex items-center space-x-2">
          <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {error && (
        <div className="p-3 bg-lider-dangerLight border border-lider-danger/20 text-lider-danger text-xs rounded-sm flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Barra de Filtro de Busca */}
      <div className="bg-lider-card border border-lider-border rounded-md p-4 shadow-subtle flex items-center space-x-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-lider-tertiary absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por nome, e-mail ou local atribuído..."
            className="w-full pl-9 pr-3 py-2 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood text-lider-primary"
          />
        </div>
        <div className="text-xs text-lider-tertiary whitespace-nowrap">
          Total: <strong className="text-lider-primary">{filteredContacts.length}</strong> contatos
        </div>
      </div>

      {/* Lista de Contatos */}
      {isLoading ? (
        <div className="bg-lider-card border border-lider-border rounded-md p-12 text-center text-xs text-lider-tertiary">
          <div className="w-6 h-6 border-2 border-lider-wood border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          Carregando contatos cadastrados...
        </div>
      ) : filteredContacts.length === 0 ? (
        <div className="bg-lider-card border border-lider-border rounded-md p-12 text-center space-y-3">
          <User className="w-10 h-10 text-lider-tertiary mx-auto" />
          <h3 className="text-sm font-semibold text-lider-primary">Nenhum contato encontrado</h3>
          <p className="text-xs text-lider-secondary max-w-md mx-auto">
            {searchTerm
              ? 'Nenhum resultado corresponde aos termos da busca.'
              : 'Nenhum responsável fabril cadastrado ainda. Clique em "Novo Contato" para vincular um e-mail aos locais de produção.'}
          </p>
          {!searchTerm && (
            <button
              onClick={openCreateModal}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-lider-primary text-white text-xs font-medium rounded-sm hover:bg-[#2A2A2A]"
            >
              <UserPlus className="w-3.5 h-3.5 text-lider-wood" />
              <span>Cadastrar Primeiro Contato</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredContacts.map((contact) => (
            <div
              key={contact.id}
              className="bg-lider-card border border-lider-border rounded-md p-5 shadow-subtle hover:border-lider-wood/50 transition-all flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div className="w-8 h-8 rounded-full bg-lider-canvas border border-lider-border flex items-center justify-center text-lider-primary font-semibold text-xs">
                      {contact.nome.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-lider-primary leading-tight">
                        {contact.nome}
                      </h4>
                      <div className="flex items-center space-x-1 text-xs text-lider-secondary mt-0.5">
                        <Mail className="w-3 h-3 text-lider-tertiary" />
                        <span className="truncate max-w-[200px]">{contact.email}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => openEditModal(contact)}
                      title="Editar contato"
                      className="p-1.5 text-lider-tertiary hover:text-lider-primary hover:bg-lider-canvas rounded-sm transition-colors"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(contact)}
                      title="Excluir contato"
                      className="p-1.5 text-lider-tertiary hover:text-lider-danger hover:bg-lider-dangerLight rounded-sm transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Locais atribuídos */}
                <div className="mt-4 pt-3 border-t border-lider-divider">
                  <div className="flex items-center space-x-1 text-[11px] font-semibold text-lider-tertiary uppercase tracking-wider mb-2">
                    <Building2 className="w-3 h-3" />
                    <span>Locais Atribuídos ({contact.locais.length})</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto pr-1">
                    {contact.locais.map((loc) => (
                      <span
                        key={loc}
                        className="inline-flex items-center px-2 py-0.5 rounded-sm text-[11px] font-mono bg-lider-canvas text-lider-primary border border-lider-border"
                      >
                        {loc}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="text-[10px] text-lider-tertiary pt-2 border-t border-lider-divider flex justify-between">
                <span>ID: {contact.id}</span>
                <span>Atualizado: {contact.updated_at.slice(0, 10)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal de Criação / Edição */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="bg-lider-card border border-lider-border rounded-md shadow-card w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-fadeIn">
            {/* Top Modal */}
            <div className="px-6 py-4 border-b border-lider-divider flex items-center justify-between bg-lider-card">
              <div>
                <span className="text-xs uppercase tracking-widest text-lider-wood font-medium">
                  {editingContact ? 'Modificação de Contato' : 'Novo Cadastro'}
                </span>
                <h3 className="text-lg font-semibold text-lider-primary">
                  {editingContact ? `Editar: ${editingContact.nome}` : 'Cadastrar Destinatário Fabril'}
                </h3>
              </div>
              <button
                onClick={closeModal}
                className="text-lider-tertiary hover:text-lider-primary p-1 rounded-sm"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-6 space-y-4">
              {formError && (
                <div className="p-3 bg-lider-dangerLight border border-lider-danger/20 text-lider-danger text-xs rounded-sm flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-lider-secondary mb-1">
                    Nome do Responsável *
                  </label>
                  <input
                    type="text"
                    required
                    value={formNome}
                    onChange={(e) => setFormNome(e.target.value)}
                    placeholder="Ex: João da Silva"
                    className="w-full px-3 py-2 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood text-lider-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-lider-secondary mb-1">
                    E-mail Corporativo *
                  </label>
                  <input
                    type="email"
                    required
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    placeholder="Ex: joao.silva@liderinteriores.com.br"
                    className="w-full px-3 py-2 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood text-lider-primary"
                  />
                </div>
              </div>

              {/* Seletor de Locais de Produção */}
              <div className="pt-2">
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-medium text-lider-secondary">
                    Locais de Produção Atribuídos * ({selectedLocais.length} selecionado{selectedLocais.length === 1 ? '' : 's'})
                  </label>
                  <div className="flex items-center space-x-2 text-xs">
                    <button
                      type="button"
                      onClick={selectAllFilteredLocations}
                      className="text-lider-wood hover:underline"
                    >
                      Selecionar Filtrados
                    </button>
                    <span className="text-lider-divider">|</span>
                    <button
                      type="button"
                      onClick={clearSelectedLocations}
                      className="text-lider-tertiary hover:underline"
                    >
                      Limpar
                    </button>
                  </div>
                </div>

                {/* Campo de filtro de locais */}
                <div className="relative mb-2">
                  <Search className="w-3.5 h-3.5 text-lider-tertiary absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={locationSearch}
                    onChange={(e) => setLocationSearch(e.target.value)}
                    placeholder="Filtrar locais de produção (ex: COLCHOES, CC FABRI...)"
                    className="w-full pl-8 pr-3 py-1.5 text-xs bg-lider-canvas border border-lider-border rounded-sm focus:outline-none focus:border-lider-wood text-lider-primary"
                  />
                </div>

                {/* Grade de checkboxes de locais */}
                <div className="border border-lider-border rounded-sm bg-lider-canvas p-2 max-h-56 overflow-y-auto grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                  {filteredAvailableLocations.map((loc) => {
                    const isChecked = selectedLocais.includes(loc);
                    return (
                      <button
                        type="button"
                        key={loc}
                        onClick={() => toggleLocation(loc)}
                        className={`flex items-center space-x-2 px-2 py-1.5 rounded-sm text-left text-xs transition-colors ${
                          isChecked
                            ? 'bg-lider-card text-lider-primary font-medium border border-lider-wood/40 shadow-xs'
                            : 'hover:bg-lider-card/50 text-lider-secondary'
                        }`}
                      >
                        {isChecked ? (
                          <CheckSquare className="w-3.5 h-3.5 text-lider-wood flex-shrink-0" />
                        ) : (
                          <Square className="w-3.5 h-3.5 text-lider-tertiary flex-shrink-0" />
                        )}
                        <span className="font-mono text-[11px] truncate">{loc}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Botões do Rodapé do Modal */}
              <div className="pt-4 border-t border-lider-divider flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-xs font-medium text-lider-secondary hover:bg-lider-canvas rounded-sm border border-lider-border transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="inline-flex items-center space-x-2 px-5 py-2 bg-lider-primary text-white text-xs font-medium rounded-sm hover:bg-[#2A2A2A] transition-all disabled:opacity-50"
                >
                  {isSaving ? (
                    <>
                      <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Salvando...</span>
                    </>
                  ) : (
                    <span>Salvar Contato</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
