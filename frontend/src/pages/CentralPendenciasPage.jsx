import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import api from '../services/api';
import {
  FileText, Search, Filter, Phone, Mail, MessageSquare, User,
  AlertTriangle, CheckCircle, Clock, XCircle, RefreshCw, Plus,
  ChevronLeft, ChevronRight, Eye, Building, BookOpen, UserPlus
} from 'lucide-react';

const STATUS_CONFIG = {
  pendente: { label: 'Pendente', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  aguardando_aluno: { label: 'Aguardando Aluno', color: 'bg-blue-100 text-blue-800', icon: User },
  em_analise: { label: 'Em Análise', color: 'bg-purple-100 text-purple-800', icon: Search },
  aprovado: { label: 'Aprovado', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  rejeitado: { label: 'Rejeitado', color: 'bg-red-100 text-red-800', icon: XCircle },
  reenvio_necessario: { label: 'Reenvio Necessário', color: 'bg-orange-100 text-orange-800', icon: RefreshCw }
};

const TIPO_CONTATO_CONFIG = {
  telefone: { label: 'Telefone', icon: Phone },
  whatsapp: { label: 'WhatsApp', icon: MessageSquare },
  email: { label: 'Email', icon: Mail },
  presencial: { label: 'Presencial', icon: User }
};

const RESULTADO_CONTATO = [
  { value: 'atendeu', label: 'Atendeu' },
  { value: 'nao_atendeu', label: 'Não atendeu' },
  { value: 'retornou', label: 'Retornou contato' },
  { value: 'sem_resposta', label: 'Sem resposta' }
];

export default function CentralPendenciasPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [pendencias, setPendencias] = useState([]);
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [paginacao, setPaginacao] = useState({ pagina_atual: 1, total_paginas: 1, total_itens: 0 });
  
  // Filtros
  const [filtroStatus, setFiltroStatus] = useState('');
  const [filtroDocumento, setFiltroDocumento] = useState('');
  const [filtroNome, setFiltroNome] = useState('');
  
  // Modais
  const [modalDetalhes, setModalDetalhes] = useState(null);
  const [modalContato, setModalContato] = useState(null);
  const [modalStatus, setModalStatus] = useState(null);
  
  // Form de contato
  const [contatoForm, setContatoForm] = useState({
    tipo_contato: 'telefone',
    descricao: '',
    resultado: ''
  });
  
  // Form de status
  const [statusForm, setStatusForm] = useState({
    status: '',
    observacoes: '',
    motivo_rejeicao: ''
  });
  
  // Modal Nova Pendência Manual
  const [modalNovaPendencia, setModalNovaPendencia] = useState(false);
  const [novaPendenciaForm, setNovaPendenciaForm] = useState({
    aluno_nome: '',
    aluno_cpf: '',
    aluno_email: '',
    aluno_telefone: '',
    documento_codigo: '',
    curso_nome: '',
    observacoes: ''
  });
  const [buscandoCpf, setBuscandoCpf] = useState(false);
  const [alunoEncontrado, setAlunoEncontrado] = useState(null);
  const [salvandoPendencia, setSalvandoPendencia] = useState(false);

  useEffect(() => {
    carregarDados();
  }, []);

  useEffect(() => {
    carregarPendencias();
  }, [filtroStatus, filtroDocumento]);

  const carregarDados = async () => {
    try {
      const [dashRes, tiposRes] = await Promise.all([
        api.get('/pendencias/dashboard'),
        api.get('/pendencias/tipos-documento')
      ]);
      setDashboard(dashRes.data);
      setTiposDocumento(tiposRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    }
  };

  const carregarPendencias = async (pagina = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('pagina', pagina);
      params.append('por_pagina', 15);
      if (filtroStatus && filtroStatus !== 'todos') params.append('status', filtroStatus);
      if (filtroDocumento && filtroDocumento !== 'todos') params.append('documento_codigo', filtroDocumento);
      if (filtroNome) params.append('aluno_nome', filtroNome);
      
      const response = await api.get(`/pendencias?${params.toString()}`);
      setPendencias(response.data.pendencias);
      setPaginacao(response.data.paginacao);
    } catch (error) {
      toast.error('Erro ao carregar pendências');
    } finally {
      setLoading(false);
    }
  };

  const buscarDetalhes = async (pendenciaId) => {
    try {
      const response = await api.get(`/pendencias/${pendenciaId}`);
      setModalDetalhes(response.data);
    } catch (error) {
      toast.error('Erro ao carregar detalhes');
    }
  };

  const registrarContato = async () => {
    if (!contatoForm.descricao.trim()) {
      toast.error('Descreva o contato realizado');
      return;
    }
    
    try {
      await api.post(`/pendencias/${modalContato.id}/contatos`, contatoForm);
      toast.success('Contato registrado com sucesso');
      setModalContato(null);
      setContatoForm({ tipo_contato: 'telefone', descricao: '', resultado: '' });
      carregarPendencias(paginacao.pagina_atual);
      carregarDados();
    } catch (error) {
      toast.error('Erro ao registrar contato');
    }
  };

  const atualizarStatus = async () => {
    try {
      await api.put(`/pendencias/${modalStatus.id}`, statusForm);
      toast.success('Status atualizado com sucesso');
      setModalStatus(null);
      setStatusForm({ status: '', observacoes: '', motivo_rejeicao: '' });
      carregarPendencias(paginacao.pagina_atual);
      carregarDados();
    } catch (error) {
      toast.error('Erro ao atualizar status');
    }
  };

  // Funções para Nova Pendência Manual
  const buscarAlunoPorCpf = async (cpf) => {
    if (!cpf || cpf.replace(/\D/g, '').length < 11) return;
    
    setBuscandoCpf(true);
    try {
      const response = await api.get(`/pendencias/buscar-aluno/${cpf}`);
      if (response.data.encontrado) {
        setAlunoEncontrado(response.data.aluno);
        setNovaPendenciaForm(prev => ({
          ...prev,
          aluno_nome: response.data.aluno.nome,
          aluno_email: response.data.aluno.email,
          aluno_telefone: response.data.aluno.telefone,
          curso_nome: response.data.aluno.curso_nome
        }));
        toast.info(`Aluno encontrado: ${response.data.aluno.nome}`);
      } else {
        setAlunoEncontrado(null);
        toast.info('Aluno não encontrado. Preencha os dados para criar novo cadastro.');
      }
    } catch (error) {
      setAlunoEncontrado(null);
    } finally {
      setBuscandoCpf(false);
    }
  };

  const criarPendenciaManual = async () => {
    // Validações
    if (!novaPendenciaForm.aluno_nome.trim()) {
      toast.error('Informe o nome do aluno');
      return;
    }
    if (!novaPendenciaForm.aluno_cpf.trim() || novaPendenciaForm.aluno_cpf.replace(/\D/g, '').length !== 11) {
      toast.error('Informe um CPF válido');
      return;
    }
    if (!novaPendenciaForm.documento_codigo) {
      toast.error('Selecione o tipo de documento');
      return;
    }
    
    setSalvandoPendencia(true);
    try {
      await api.post('/pendencias/manual', novaPendenciaForm);
      toast.success('Pendência criada com sucesso!');
      setModalNovaPendencia(false);
      setNovaPendenciaForm({
        aluno_nome: '',
        aluno_cpf: '',
        aluno_email: '',
        aluno_telefone: '',
        documento_codigo: '',
        curso_nome: '',
        observacoes: ''
      });
      setAlunoEncontrado(null);
      carregarPendencias(1);
      carregarDados();
    } catch (error) {
      const msg = error.response?.data?.detail || 'Erro ao criar pendência';
      toast.error(msg);
    } finally {
      setSalvandoPendencia(false);
    }
  };

  const formatarCPF = (value) => {
    const nums = value.replace(/\D/g, '').slice(0, 11);
    if (nums.length <= 3) return nums;
    if (nums.length <= 6) return `${nums.slice(0, 3)}.${nums.slice(3)}`;
    if (nums.length <= 9) return `${nums.slice(0, 3)}.${nums.slice(3, 6)}.${nums.slice(6)}`;
    return `${nums.slice(0, 3)}.${nums.slice(3, 6)}.${nums.slice(6, 9)}-${nums.slice(9)}`;
  };

  const formatarTelefone = (value) => {
    const nums = value.replace(/\D/g, '').slice(0, 11);
    if (nums.length <= 2) return nums;
    if (nums.length <= 7) return `(${nums.slice(0, 2)}) ${nums.slice(2)}`;
    return `(${nums.slice(0, 2)}) ${nums.slice(2, 7)}-${nums.slice(7)}`;
  };

  const formatarData = (dataStr) => {
    if (!dataStr) return '-';
    const data = new Date(dataStr);
    return data.toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const StatusBadge = ({ status }) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.pendente;
    const Icon = config.icon;
    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
          Central de Pendências Documentais
        </h1>
        <p className="text-slate-500">
          Gerencie documentos pendentes e registre contatos com os alunos
        </p>
      </div>

      {/* Dashboard Cards */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
          <Card className="bg-yellow-50 border-yellow-200">
            <CardContent className="p-4 text-center">
              <Clock className="w-8 h-8 mx-auto text-yellow-600 mb-2" />
              <p className="text-2xl font-bold text-yellow-700">{dashboard.total_pendente}</p>
              <p className="text-sm text-yellow-600">Pendentes</p>
            </CardContent>
          </Card>
          
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4 text-center">
              <User className="w-8 h-8 mx-auto text-blue-600 mb-2" />
              <p className="text-2xl font-bold text-blue-700">{dashboard.total_aguardando}</p>
              <p className="text-sm text-blue-600">Aguardando</p>
            </CardContent>
          </Card>
          
          <Card className="bg-purple-50 border-purple-200">
            <CardContent className="p-4 text-center">
              <Search className="w-8 h-8 mx-auto text-purple-600 mb-2" />
              <p className="text-2xl font-bold text-purple-700">{dashboard.total_em_analise}</p>
              <p className="text-sm text-purple-600">Em Análise</p>
            </CardContent>
          </Card>
          
          <Card className="bg-orange-50 border-orange-200">
            <CardContent className="p-4 text-center">
              <RefreshCw className="w-8 h-8 mx-auto text-orange-600 mb-2" />
              <p className="text-2xl font-bold text-orange-700">{dashboard.total_reenvio}</p>
              <p className="text-sm text-orange-600">Reenvio</p>
            </CardContent>
          </Card>
          
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4 text-center">
              <CheckCircle className="w-8 h-8 mx-auto text-green-600 mb-2" />
              <p className="text-2xl font-bold text-green-700">{dashboard.total_aprovado}</p>
              <p className="text-sm text-green-600">Aprovados</p>
            </CardContent>
          </Card>
          
          <Card className="bg-red-50 border-red-200">
            <CardContent className="p-4 text-center">
              <AlertTriangle className="w-8 h-8 mx-auto text-red-600 mb-2" />
              <p className="text-2xl font-bold text-red-700">{dashboard.total_criticas}</p>
              <p className="text-sm text-red-600">Críticas (+7 dias)</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtros */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <Label>Buscar por Nome</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="Nome do aluno..."
                  value={filtroNome}
                  onChange={(e) => setFiltroNome(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && carregarPendencias()}
                  className="pl-10"
                  data-testid="filtro-nome"
                />
              </div>
            </div>
            
            <div className="w-[200px]">
              <Label>Status</Label>
              <Select value={filtroStatus} onValueChange={setFiltroStatus}>
                <SelectTrigger data-testid="filtro-status">
                  <SelectValue placeholder="Todos os status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>{config.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-[250px]">
              <Label>Tipo de Documento</Label>
              <Select value={filtroDocumento} onValueChange={setFiltroDocumento}>
                <SelectTrigger data-testid="filtro-documento">
                  <SelectValue placeholder="Todos os documentos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  {tiposDocumento.map((tipo) => (
                    <SelectItem key={tipo.codigo} value={tipo.codigo}>
                      {tipo.codigo} - {tipo.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button onClick={() => carregarPendencias()} className="bg-[#004587]">
              <Filter className="w-4 h-4 mr-2" />
              Filtrar
            </Button>
            
            <Button 
              onClick={() => setModalNovaPendencia(true)} 
              className="bg-green-600 hover:bg-green-700"
              data-testid="btn-nova-pendencia"
            >
              <UserPlus className="w-4 h-4 mr-2" />
              Nova Pendência
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Pendências */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Pendências ({paginacao.total_itens})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004587] mx-auto"></div>
              <p className="mt-4 text-slate-500">Carregando...</p>
            </div>
          ) : pendencias.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="w-12 h-12 text-green-300 mx-auto mb-4" />
              <p className="text-slate-500">Nenhuma pendência encontrada</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-slate-50">
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Aluno</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Documento</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Curso</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Status</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Contatos</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Criado em</th>
                      <th className="text-center p-3 text-sm font-medium text-slate-600">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendencias.map((pendencia) => (
                      <tr key={pendencia.id} className="border-b hover:bg-slate-50" data-testid={`pendencia-row-${pendencia.id}`}>
                        <td className="p-3">
                          <div>
                            <p className="font-medium text-slate-900">{pendencia.aluno_nome}</p>
                            <p className="text-sm text-slate-500">{pendencia.aluno_cpf}</p>
                          </div>
                        </td>
                        <td className="p-3">
                          <div>
                            <p className="font-medium">{pendencia.documento_codigo}</p>
                            <p className="text-sm text-slate-500 truncate max-w-[200px]" title={pendencia.documento_nome}>
                              {pendencia.documento_nome}
                            </p>
                          </div>
                        </td>
                        <td className="p-3">
                          <p className="text-sm text-slate-600 truncate max-w-[150px]" title={pendencia.curso_nome}>
                            {pendencia.curso_nome}
                          </p>
                        </td>
                        <td className="p-3">
                          <StatusBadge status={pendencia.status} />
                        </td>
                        <td className="p-3">
                          <Badge variant="outline" className="bg-slate-50">
                            {pendencia.total_contatos} contato(s)
                          </Badge>
                        </td>
                        <td className="p-3 text-sm text-slate-500">
                          {formatarData(pendencia.created_at)}
                        </td>
                        <td className="p-3">
                          <div className="flex justify-center gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => buscarDetalhes(pendencia.id)}
                              title="Ver detalhes"
                              data-testid={`btn-detalhes-${pendencia.id}`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setModalContato(pendencia);
                                setContatoForm({ tipo_contato: 'telefone', descricao: '', resultado: '' });
                              }}
                              title="Registrar contato"
                              className="text-blue-600"
                              data-testid={`btn-contato-${pendencia.id}`}
                            >
                              <Phone className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setModalStatus(pendencia);
                                setStatusForm({ status: pendencia.status, observacoes: pendencia.observacoes || '', motivo_rejeicao: pendencia.motivo_rejeicao || '' });
                              }}
                              title="Alterar status"
                              className="text-purple-600"
                              data-testid={`btn-status-${pendencia.id}`}
                            >
                              <RefreshCw className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Paginação */}
              {paginacao.total_paginas > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <p className="text-sm text-slate-500">
                    Página {paginacao.pagina_atual} de {paginacao.total_paginas}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={paginacao.pagina_atual === 1}
                      onClick={() => carregarPendencias(paginacao.pagina_atual - 1)}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={paginacao.pagina_atual === paginacao.total_paginas}
                      onClick={() => carregarPendencias(paginacao.pagina_atual + 1)}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Modal de Detalhes */}
      <Dialog open={!!modalDetalhes} onOpenChange={() => setModalDetalhes(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Detalhes da Pendência
            </DialogTitle>
          </DialogHeader>
          
          {modalDetalhes && (
            <div className="space-y-6">
              {/* Info do Aluno */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <User className="w-4 h-4" /> Dados do Aluno
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-slate-500">Nome</p>
                    <p className="font-medium">{modalDetalhes.aluno.nome}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">CPF</p>
                    <p className="font-medium">{modalDetalhes.aluno.cpf}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Email</p>
                    <p className="font-medium">{modalDetalhes.aluno.email}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Telefone</p>
                    <p className="font-medium">{modalDetalhes.aluno.telefone}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Info do Pedido */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <BookOpen className="w-4 h-4" /> Dados do Pedido
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-slate-500">Protocolo</p>
                    <p className="font-medium">{modalDetalhes.pedido.protocolo}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Curso</p>
                    <p className="font-medium">{modalDetalhes.pedido.curso}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Projeto</p>
                    <p className="font-medium">{modalDetalhes.pedido.projeto || '-'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Empresa</p>
                    <p className="font-medium">{modalDetalhes.pedido.empresa || '-'}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Info da Pendência */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <FileText className="w-4 h-4" /> Documento Pendente
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-slate-500">Código - Documento</p>
                      <p className="font-medium">{modalDetalhes.documento_codigo} - {modalDetalhes.documento_nome}</p>
                    </div>
                    <StatusBadge status={modalDetalhes.status} />
                  </div>
                  {modalDetalhes.observacoes && (
                    <div>
                      <p className="text-slate-500">Observações</p>
                      <p className="font-medium">{modalDetalhes.observacoes}</p>
                    </div>
                  )}
                  {modalDetalhes.motivo_rejeicao && (
                    <div>
                      <p className="text-slate-500">Motivo da Rejeição</p>
                      <p className="font-medium text-red-600">{modalDetalhes.motivo_rejeicao}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Histórico de Contatos */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Phone className="w-4 h-4" /> Histórico de Contatos ({modalDetalhes.historico_contatos.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {modalDetalhes.historico_contatos.length === 0 ? (
                    <p className="text-slate-500 text-center py-4">Nenhum contato registrado</p>
                  ) : (
                    <div className="space-y-3">
                      {modalDetalhes.historico_contatos.map((contato) => {
                        const tipoConfig = TIPO_CONTATO_CONFIG[contato.tipo_contato];
                        const TipoIcon = tipoConfig?.icon || Phone;
                        return (
                          <div key={contato.id} className="border rounded-lg p-3 bg-slate-50">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <TipoIcon className="w-4 h-4 text-slate-600" />
                                <span className="font-medium text-sm">{tipoConfig?.label || contato.tipo_contato}</span>
                                {contato.resultado && (
                                  <Badge variant="outline" className="text-xs">
                                    {RESULTADO_CONTATO.find(r => r.value === contato.resultado)?.label || contato.resultado}
                                  </Badge>
                                )}
                              </div>
                              <span className="text-xs text-slate-500">{formatarData(contato.data_contato)}</span>
                            </div>
                            <p className="text-sm">{contato.descricao}</p>
                            <p className="text-xs text-slate-500 mt-1">Por: {contato.usuario_nome}</p>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal de Registrar Contato */}
      <Dialog open={!!modalContato} onOpenChange={() => setModalContato(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Phone className="w-5 h-5" />
              Registrar Contato
            </DialogTitle>
          </DialogHeader>
          
          {modalContato && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="font-medium">{modalContato.aluno_nome}</p>
                <p className="text-sm text-slate-500">{modalContato.documento_nome}</p>
              </div>
              
              <div>
                <Label>Tipo de Contato</Label>
                <Select
                  value={contatoForm.tipo_contato}
                  onValueChange={(v) => setContatoForm({ ...contatoForm, tipo_contato: v })}
                >
                  <SelectTrigger data-testid="select-tipo-contato">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(TIPO_CONTATO_CONFIG).map(([key, config]) => (
                      <SelectItem key={key} value={key}>{config.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Resultado</Label>
                <Select
                  value={contatoForm.resultado}
                  onValueChange={(v) => setContatoForm({ ...contatoForm, resultado: v })}
                >
                  <SelectTrigger data-testid="select-resultado">
                    <SelectValue placeholder="Selecione o resultado" />
                  </SelectTrigger>
                  <SelectContent>
                    {RESULTADO_CONTATO.map((r) => (
                      <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Descrição do Contato *</Label>
                <Textarea
                  value={contatoForm.descricao}
                  onChange={(e) => setContatoForm({ ...contatoForm, descricao: e.target.value })}
                  placeholder="Descreva o contato realizado..."
                  rows={3}
                  data-testid="input-descricao-contato"
                />
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalContato(null)}>
              Cancelar
            </Button>
            <Button onClick={registrarContato} className="bg-[#004587]" data-testid="btn-salvar-contato">
              Registrar Contato
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal de Alterar Status */}
      <Dialog open={!!modalStatus} onOpenChange={() => setModalStatus(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <RefreshCw className="w-5 h-5" />
              Alterar Status
            </DialogTitle>
          </DialogHeader>
          
          {modalStatus && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="font-medium">{modalStatus.aluno_nome}</p>
                <p className="text-sm text-slate-500">{modalStatus.documento_nome}</p>
              </div>
              
              <div>
                <Label>Novo Status</Label>
                <Select
                  value={statusForm.status}
                  onValueChange={(v) => setStatusForm({ ...statusForm, status: v })}
                >
                  <SelectTrigger data-testid="select-novo-status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                      <SelectItem key={key} value={key}>{config.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Observações</Label>
                <Textarea
                  value={statusForm.observacoes}
                  onChange={(e) => setStatusForm({ ...statusForm, observacoes: e.target.value })}
                  placeholder="Observações sobre a pendência..."
                  rows={2}
                  data-testid="input-observacoes-status"
                />
              </div>
              
              {statusForm.status === 'rejeitado' && (
                <div>
                  <Label>Motivo da Rejeição *</Label>
                  <Textarea
                    value={statusForm.motivo_rejeicao}
                    onChange={(e) => setStatusForm({ ...statusForm, motivo_rejeicao: e.target.value })}
                    placeholder="Informe o motivo da rejeição..."
                    rows={2}
                    data-testid="input-motivo-rejeicao"
                  />
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalStatus(null)}>
              Cancelar
            </Button>
            <Button onClick={atualizarStatus} className="bg-[#004587]" data-testid="btn-salvar-status">
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
