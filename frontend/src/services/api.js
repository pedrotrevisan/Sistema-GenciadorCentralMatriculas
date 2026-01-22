import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email, senha) => api.post('/auth/login', { email, senha }),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
};

// Pedidos API
export const pedidosAPI = {
  criar: (data) => api.post('/pedidos', data),
  listar: (params) => api.get('/pedidos', { params }),
  buscarPorId: (id) => api.get(`/pedidos/${id}`),
  buscarPorProtocolo: (protocolo) => api.get(`/pedidos/buscar/protocolo/${protocolo}`),
  buscarTimeline: (id) => api.get(`/pedidos/${id}/timeline`),
  atualizarStatus: (id, data) => api.patch(`/pedidos/${id}/status`, data),
  getDashboard: () => api.get('/pedidos/dashboard'),
  getAnalytics: () => api.get('/pedidos/analytics'),
  exportarTOTVS: (formato = 'xlsx') => api.get(`/pedidos/exportar/totvs?formato=${formato}`, {
    responseType: 'blob'
  }),
};

// Usuarios API
export const usuariosAPI = {
  listar: (params) => api.get('/usuarios', { params }),
  buscarPorId: (id) => api.get(`/usuarios/${id}`),
  atualizar: (id, data) => api.patch(`/usuarios/${id}`, data),
  deletar: (id) => api.delete(`/usuarios/${id}`),
};

// Dados Auxiliares API
export const auxiliaresAPI = {
  getCursos: () => api.get('/cursos'),
  getProjetos: () => api.get('/projetos'),
  getEmpresas: () => api.get('/empresas'),
  getStatusPedido: () => api.get('/status-pedido'),
};

// CRUD Cursos
export const cursosAPI = {
  listar: (ativo) => api.get('/cursos', { params: { ativo } }),
  criar: (data) => api.post('/cursos', data),
  atualizar: (id, data) => api.put(`/cursos/${id}`, data),
  deletar: (id) => api.delete(`/cursos/${id}`),
};

// CRUD Projetos
export const projetosAPI = {
  listar: (ativo) => api.get('/projetos', { params: { ativo } }),
  criar: (data) => api.post('/projetos', data),
  atualizar: (id, data) => api.put(`/projetos/${id}`, data),
  deletar: (id) => api.delete(`/projetos/${id}`),
};

// CRUD Empresas
export const empresasAPI = {
  listar: (ativo) => api.get('/empresas', { params: { ativo } }),
  criar: (data) => api.post('/empresas', data),
  atualizar: (id, data) => api.put(`/empresas/${id}`, data),
  deletar: (id) => api.delete(`/empresas/${id}`),
};

export default api;
