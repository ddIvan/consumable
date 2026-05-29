import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('API Error:', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export default api

// ─── Manufacturers ─────────────────────────────────
export const manufacturerApi = {
  list: () => api.get('/manufacturers'),
  create: (data: any) => api.post('/manufacturers', data),
  update: (id: number, data: any) => api.put(`/manufacturers/${id}`, data),
  delete: (id: number) => api.delete(`/manufacturers/${id}`),
}

// ─── Filaments ──────────────────────────────────────
export const filamentApi = {
  list: () => api.get('/filaments'),
  create: (data: any) => api.post('/filaments', data),
  update: (id: number, data: any) => api.put(`/filaments/${id}`, data),
  delete: (id: number) => api.delete(`/filaments/${id}`),
}

// ─── Spools ─────────────────────────────────────────
export const spoolApi = {
  list: () => api.get('/spools'),
  create: (data: any) => api.post('/spools', data),
  update: (id: number, data: any) => api.put(`/spools/${id}`, data),
  delete: (id: number) => api.delete(`/spools/${id}`),
}

// ─── Print Records ──────────────────────────────────
export const printRecordApi = {
  list: (params?: any) => api.get('/print-records', { params }),
  deductDetail: (detailId: number) => api.post(`/print-records/details/${detailId}/deduct`),
}

// ─── MQTT Messages ─────────────────────────────
export const mqttMessageApi = {
  list: (params?: any) => api.get('/mqtt-messages', { params }),
  delete: (id: number) => api.delete(`/mqtt-messages/${id}`),
  clear: () => api.delete('/mqtt-messages'),
}

// ─── Printers ───────────────────────────────────────
export const printerApi = {
  list: () => api.get('/printers'),
  create: (data: any) => api.post('/printers', data),
  update: (id: number, data: any) => api.put(`/printers/${id}`, data),
  delete: (id: number) => api.delete(`/printers/${id}`),
  connect: (id: number) => api.post(`/printer/${id}/connect`),
  disconnect: (id: number) => api.post(`/printer/${id}/disconnect`),
  status: (id: number) => api.get(`/printer/${id}/status`),
}

// ─── Operation Logs ─────────────────────────────
export const operationLogApi = {
  list: (params?: any) => api.get('/operation-logs', { params }),
  clear: () => api.delete('/operation-logs'),
}

// ─── Dashboard ──────────────────────────────────────
export const dashboardApi = {
  summary: () => api.get('/dashboard/summary'),
  locations: () => api.get('/dashboard/locations'),
}
