import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token to all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid - clear auth and redirect
      localStorage.removeItem('auth_token');
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }
    return Promise.reject(error);
  }
);

// Strategies API
export const strategiesAPI = {
  generate: async (data) => {
    const response = await apiClient.post('/strategies/generate', data);
    return response.data;
  },
  list: async (limit = 100, offset = 0) => {
    const response = await apiClient.get('/strategies/', { params: { limit, offset } });
    return response.data;
  },
  get: async (strategyId) => {
    const response = await apiClient.get(`/strategies/${strategyId}`);
    return response.data;
  },
};

// Backtests API
export const backtestsAPI = {
  run: async (strategyId, data) => {
    const response = await apiClient.post(`/backtests/run/${strategyId}`, data);
    return response.data;
  },
  list: async (strategyId = null, limit = 100, offset = 0) => {
    const url = strategyId ? `/backtests/strategy/${strategyId}` : '/backtests/';
    const response = await apiClient.get(url, { params: { limit, offset } });
    return response.data;
  },
  get: async (backtestId) => {
    const response = await apiClient.get(`/backtests/${backtestId}`);
    return response.data;
  },
};

// Validations API
export const validationsAPI = {
  run: async (strategyId, data) => {
    const response = await apiClient.post(`/validation/run/${strategyId}`, data);
    return response.data;
  },
  list: async (strategyId = null, limit = 100, offset = 0) => {
    const url = strategyId ? `/validation/strategy/${strategyId}` : '/validation/';
    const response = await apiClient.get(url, { params: { limit, offset } });
    return response.data;
  },
  get: async (validationId) => {
    const response = await apiClient.get(`/validation/${validationId}`);
    return response.data;
  },
};

// Gates API
export const gatesAPI = {
  runDev: async (strategyId, data) => {
    const response = await apiClient.post(`/gates/dev/${strategyId}`, data);
    return response.data;
  },
  runCRV: async (strategyId, data) => {
    const response = await apiClient.post(`/gates/crv/${strategyId}`, data);
    return response.data;
  },
  runProduct: async (strategyId) => {
    const response = await apiClient.post(`/gates/product/${strategyId}`);
    return response.data;
  },
  getStatus: async (strategyId) => {
    const response = await apiClient.get(`/gates/status/${strategyId}`);
    return response.data;
  },
  listByStrategy: async (strategyId, gateType = null) => {
    const params = gateType ? { gate_type: gateType } : {};
    const response = await apiClient.get(`/gates/strategy/${strategyId}`, { params });
    return response.data;
  },
};

// Reflexion API
export const reflexionAPI = {
  run: async (strategyId, data) => {
    const response = await apiClient.post(`/reflexion/run/${strategyId}`, data);
    return response.data;
  },
  getHistory: async (strategyId) => {
    const response = await apiClient.get(`/reflexion/history/${strategyId}`);
    return response.data;
  },
};

// Orchestrator API
export const orchestratorAPI = {
  run: async (data) => {
    const response = await apiClient.post('/orchestrator/run', data);
    return response.data;
  },
  getStatus: async (runId) => {
    const response = await apiClient.get(`/orchestrator/status/${runId}`);
    return response.data;
  },
};

// Health check
export const healthAPI = {
  check: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default apiClient;
