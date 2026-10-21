import axios from 'axios';
import { ResultsResponse, StartPipelinePayload, StatusResponse } from '../types';

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

export default api;
