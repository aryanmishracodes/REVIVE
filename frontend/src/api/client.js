import axios from 'axios';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dashboard
export const getDashboardMetrics = async () => {
  const { data } = await apiClient.get('/dashboard/metrics');
  return data;
};

export const getFailureDistribution = async () => {
  const { data } = await apiClient.get('/dashboard/distribution');
  return data;
};

// Transactions
export const getTransactions = async (params = {}) => {
  const { data } = await apiClient.get('/transactions', { params });
  return data;
};

export const getTransactionDetail = async (txId) => {
  const { data } = await apiClient.get(`/transactions/${txId}`);
  return data;
};

export const analyzeTransaction = async (txId) => {
  const { data } = await apiClient.post(`/transactions/${txId}/analyze`);
  return data;
};

// Actions
export const getActions = async (params = {}) => {
  const { data } = await apiClient.get('/actions', { params });
  return data;
};

export const approveAction = async (actionId, notes = '') => {
  const { data } = await apiClient.post(`/actions/${actionId}/approve`, { notes });
  return data;
};

export const rejectAction = async (actionId, reason) => {
  const { data } = await apiClient.post(`/actions/${actionId}/reject`, { reason });
  return data;
};

export const executeAction = async (actionId) => {
  const { data } = await apiClient.post(`/actions/${actionId}/execute`);
  return data;
};

// Simulator
export const runSimulation = async () => {
  const { data } = await apiClient.post('/simulator/run');
  return data;
};

export const getLatestSimulation = async () => {
  const { data } = await apiClient.get('/simulator/latest');
  return data;
};

export const getDemoScenarios = async () => {
  const { data } = await apiClient.get('/simulator/demo-scenarios');
  return data;
};

export const resetDemoState = async () => {
  const { data } = await apiClient.post('/simulator/reset-demo');
  return data;
};

// ML
export const getModelWeights = async () => {
  const { data } = await apiClient.get('/ml/weights');
  return data;
};
