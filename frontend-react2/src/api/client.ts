import axios from 'axios'

const BASE = '' 

export const api = axios.create({ 
  baseURL: BASE, 
  timeout: 300000,
  withCredentials: false  // ADD THIS
})

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ───────────────────────────────────────────────────
export const authApi = {
  register: (email: string, full_name: string, password: string) =>
    api.post('/api/v1/auth/register', { email, full_name, password }),
  login: (email: string, password: string) =>
    api.post('/api/v1/auth/login', { email, password }),
  me: () => api.get('/api/v1/auth/me'),
}

// ── Datasets ───────────────────────────────────────────────
export const datasetsApi = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/api/v1/datasets/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
  },
  list: () => api.get('/api/v1/datasets/'),
  get: (id: string) => api.get(`/api/v1/datasets/${id}`),
  preview: (id: string) => api.get(`/api/v1/datasets/${id}/preview`),
  clean: (id: string, config: Record<string, any>) =>
    api.post(`/api/v1/datasets/${id}/clean`, config),
  delete: (id: string) => api.delete(`/api/v1/datasets/${id}`),
}

// ── Chat ───────────────────────────────────────────────────
export const chatApi = {
  createSession: (dataset_id: string) =>
    api.post('/api/v1/chat/sessions', { dataset_id }),
  listSessions: () => api.get('/api/v1/chat/sessions'),
  getSession: (id: string) => api.get(`/api/v1/chat/sessions/${id}`),
  sendMessage: (session_id: string, message: string) =>
    api.post(`/api/v1/chat/sessions/${session_id}/message`, { message }),
  deleteSession: (id: string) => api.delete(`/api/v1/chat/sessions/${id}`),
}

// ── ML ─────────────────────────────────────────────────────
export const mlApi = {
  forecast: (dataset_id: string, target_column: string, n_periods = 3) =>
    api.post('/api/v1/ml/forecast', { dataset_id, target_column, n_periods }),
  anomaly: (dataset_id: string, target_column: string) =>
    api.post('/api/v1/ml/anomaly', { dataset_id, target_column }),
  churn: (dataset_id: string, target_column: string) =>
    api.post('/api/v1/ml/churn', { dataset_id, target_column }),
  getResult: (task_id: string) => api.get(`/api/v1/ml/results/${task_id}`),
  listResults: () => api.get('/api/v1/ml/results'),
}

// ── Reports ────────────────────────────────────────────────
export const reportsApi = {
  generate: (dataset_id: string) =>
    api.post('/api/v1/reports/generate', { dataset_id }),
  list: () => api.get('/api/v1/reports/'),
  getStatus: (id: string) => api.get(`/api/v1/reports/${id}/status`),
  download: (id: string) =>
    api.get(`/api/v1/reports/${id}/download`, { responseType: 'blob' }),
}

// ── Visualization ──────────────────────────────────────────
export const vizApi = {
  explain: (chart_type: string, x_column: string, y_column: string | null, data_summary: string) =>
    api.post('/api/v1/visualization/explain', { chart_type, x_column, y_column, data_summary }),
}

// ── Dashboard ──────────────────────────────────────────────
export const dashboardApi = {
  summary: () => api.get('/api/v1/dashboard/summary'),
}
