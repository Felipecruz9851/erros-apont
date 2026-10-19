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
    const response = await api.post('/pipeline/start', payload);
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
