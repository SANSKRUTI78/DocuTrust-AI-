import axios from 'axios'
import { useAuthStore } from '../store/authStore'


const token = useAuthStore.getState().token

const api = axios.create({ baseURL: '/api', timeout: 120000 })

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (email, password) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form)
  },
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
}

export const documentsAPI = {
  upload: (formData, onProgress) =>
    api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => onProgress && onProgress(Math.round((e.loaded * 100) / e.total)),
    }),
  list: (params) => api.get('/documents/', { params }),
  get: (id) => api.get('/documents/' + id),
  delete: (id) => api.delete('/documents/' + id),
}

export const chatAPI = {
  createSession: (data) => api.post('/chat/sessions', data),
  listSessions: () => api.get('/chat/sessions'),
  getMessages: (sessionId) => api.get('/chat/sessions/' + sessionId + '/messages'),
  sendMessage: (sessionId, data) => api.post('/chat/sessions/' + sessionId + '/messages', data),
  submitFeedback: (messageId, data) => api.post('/chat/messages/' + messageId + '/feedback', data),
  deleteSession: (id) => api.delete('/chat/sessions/' + id),
}

export const analyticsAPI = {
  dashboard: () => api.get('/analytics/dashboard'),
  recentActivity: () => api.get('/analytics/recent-activity'),
}

export const adminAPI = {
  listUsers: () => api.get('/admin/users'),
  updateRole: (userId, role) => api.patch('/admin/users/' + userId + '/role', null, { params: { role } }),
}

export default api
