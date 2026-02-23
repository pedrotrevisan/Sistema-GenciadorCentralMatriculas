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

// Pendências API
export const pendenciasAPI = {
  listar: (params) => api.get('/pendencias', { params }),
  getDashboard: () => api.get('/pendencias/dashboard'),
  getTiposDocumento: () => api.get('/pendencias/tipos-documento'),
  criar: (data) => api.post('/pendencias', data),
  criarLote: (data) => api.post('/pendencias/lote', data),
  buscarPorId: (id) => api.get(`/pendencias/${id}`),
  atualizar: (id, data) => api.put(`/pendencias/${id}`, data),
  registrarContato: (id, data) => api.post(`/pendencias/${id}/contatos`, data),
  listarPorAluno: (alunoId) => api.get(`/pendencias/aluno/${alunoId}`),
};

// Reembolsos API
export const reembolsosAPI = {
  listar: (params) => api.get('/reembolsos', { params }),
  getDashboard: () => api.get('/reembolsos/dashboard'),
  getMotivos: () => api.get('/reembolsos/motivos'),
  getStatus: () => api.get('/reembolsos/status'),
  getTemplatesEmail: () => api.get('/reembolsos/templates-email'),
  criar: (data) => api.post('/reembolsos', data),
  buscarPorId: (id) => api.get(`/reembolsos/${id}`),
  atualizar: (id, data) => api.put(`/reembolsos/${id}`, data),
  registrarDadosBancarios: (id, data) => api.post(`/reembolsos/${id}/dados-bancarios`, data),
  marcarEmailEnviado: (id) => api.post(`/reembolsos/${id}/marcar-email-enviado`),
};

// Documentos API (Clean Architecture - Fase 2)
export const documentosAPI = {
  // Referência
  getTipos: () => api.get('/documentos/tipos'),
  getStatus: () => api.get('/documentos/status'),
  getPrioridades: () => api.get('/documentos/prioridades'),
  
  // Estatísticas
  getStatsResumo: () => api.get('/documentos/stats/resumo'),
  getStatsPorTipo: () => api.get('/documentos/stats/por-tipo'),
  getStatsVencendo: (dias = 3) => api.get('/documentos/stats/vencendo', { params: { dias } }),
  
  // Dashboard BI
  getBIMatriculas: () => api.get('/documentos/bi/matriculas'),
  getBIEvolucao: (meses = 6) => api.get('/documentos/bi/evolucao', { params: { meses } }),
  getBIReembolsos: () => api.get('/documentos/bi/reembolsos'),
  getBIPendencias: () => api.get('/documentos/bi/pendencias'),
  getBICompleto: () => api.get('/documentos/bi/completo'),
  
  // CRUD
  criar: (data) => api.post('/documentos', data),
  criarPadrao: (pedidoId, prazoDias = 7) => api.post(`/documentos/padrao/${pedidoId}`, null, { params: { prazo_dias: prazoDias } }),
  listarPorPedido: (pedidoId, status) => api.get(`/documentos/pedido/${pedidoId}`, { params: { status } }),
  buscarPorId: (id) => api.get(`/documentos/${id}`),
  enviar: (id, data) => api.post(`/documentos/${id}/enviar`, data),
  validar: (id, data) => api.post(`/documentos/${id}/validar`, data),
  atualizarObservacoes: (id, data) => api.put(`/documentos/${id}/observacoes`, data),
  getFilaValidacao: (limite = 20) => api.get('/documentos/validacao/fila', { params: { limite } }),
};

export default api;
