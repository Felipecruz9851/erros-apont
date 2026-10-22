import axios from 'axios';
import {
  Contact,
  EmailPreviewData,
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
      limit?: number;
      offset?: number;
    }
  ): Promise<ResultsResponse> {
    const response = await api.get(`/results/${executionId}`, { params });
    return response.data;
  },

  getExportUrl(executionId: string, format: 'csv' | 'json' = 'csv', fabrica?: string): string {
    const baseUrl = `/api/v1/results/${executionId}/export?format=${format}`;
    return fabrica ? `${baseUrl}&fabrica=${encodeURIComponent(fabrica)}` : baseUrl;
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
  async getSummary(executionId?: string): Promise<EmailSummaryResponse> {
    const params = executionId ? { execution_id: executionId } : undefined;
    const response = await api.get<EmailSummaryResponse>('/emails/summary', { params });
    return response.data;
  },

  async preview(contactId: string, executionId?: string): Promise<EmailPreviewData> {
    const response = await api.post<EmailPreviewData>('/emails/preview', {
      contact_id: contactId,
      execution_id: executionId,
    });
    return response.data;
  },

  async send(payload: {
    execution_id?: string;
    contact_ids?: string[];
    send_all_with_errors?: boolean;
  }): Promise<EmailSendResponse> {
    const response = await api.post<EmailSendResponse>('/emails/send', payload);
    return response.data;
  },
};

export default api;
