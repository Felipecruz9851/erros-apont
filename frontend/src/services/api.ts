import axios from 'axios';
import {
  Contact,
  EmailPreviewData,
  EmailSendPayload,
  EmailSendResponse,
  EmailSummaryResponse,
  ResultsResponse,
  StartPipelinePayload,
  StatusResponse,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const pipelineApi = {
  async start(payload: StartPipelinePayload): Promise<{ execution_id: string; status: string; message: string }> {
    const urlParams = new URLSearchParams(window.location.search);
    const isDebug =
      payload.debug === true ||
      urlParams.get('debug')?.toLowerCase() === 'true' ||
      urlParams.get('debug') === '1';
    const endpoint = isDebug ? '/pipeline/start?debug=true' : '/pipeline/start';
    const response = await api.post(endpoint, { ...payload, debug: isDebug });
    return response.data;
  },

  async getStatus(executionId: string): Promise<StatusResponse> {
    const response = await api.get(`/pipeline/status/${executionId}`);
    return response.data;
  },

  async getResults(
    executionId: string,
    params?: {
      fabrica?: string;
      local_producao?: string;
      status_divergencia?: string;
      tipo_componente?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<ResultsResponse> {
    const response = await api.get(`/results/${executionId}`, { params });
    return response.data;
  },

  getExportUrl(executionId: string, format: 'csv' | 'json' = 'csv', fabrica?: string, tipo_componente?: string): string {
    let url = `/api/v1/results/${executionId}/export?format=${format}`;
    if (fabrica) url += `&fabrica=${encodeURIComponent(fabrica)}`;
    if (tipo_componente && tipo_componente !== 'ALL') url += `&tipo_componente=${encodeURIComponent(tipo_componente)}`;
    return url;
  },
};

export const contactsApi = {
  async list(): Promise<Contact[]> {
    const response = await api.get<Contact[]>('/contacts');
    return response.data;
  },

  async getLocations(): Promise<string[]> {
    const response = await api.get<string[]>('/contacts/locations');
    return response.data;
  },

  async create(payload: { nome: string; email: string; locais: string[] }): Promise<Contact> {
    const response = await api.post<Contact>('/contacts', payload);
    return response.data;
  },

  async update(
    contactId: string,
    payload: { nome?: string; email?: string; locais?: string[] }
  ): Promise<Contact> {
    const response = await api.put<Contact>(`/contacts/${contactId}`, payload);
    return response.data;
  },

  async delete(contactId: string): Promise<void> {
    await api.delete(`/contacts/${contactId}`);
  },
};

export const emailsApi = {
  async getSummary(executionId?: string, tipoFiltro?: string): Promise<EmailSummaryResponse> {
    const params: Record<string, string> = {};
    if (executionId) params.execution_id = executionId;
    if (tipoFiltro && tipoFiltro !== 'TODOS') params.tipo_filtro = tipoFiltro;
    const response = await api.get<EmailSummaryResponse>('/emails/summary', { params: Object.keys(params).length ? params : undefined });
    return response.data;
  },

  async preview(contactId: string, executionId?: string, tipoFiltro?: string): Promise<EmailPreviewData> {
    const response = await api.post<EmailPreviewData>('/emails/preview', {
      contact_id: contactId,
      execution_id: executionId,
      tipo_filtro: tipoFiltro || 'TODOS',
    });
    return response.data;
  },

  async send(payload: EmailSendPayload): Promise<EmailSendResponse> {
    const response = await api.post<EmailSendResponse>('/emails/send', payload);
    return response.data;
  },
};

export default api;
