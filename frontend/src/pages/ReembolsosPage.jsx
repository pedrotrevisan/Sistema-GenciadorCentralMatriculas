import { useState, useEffect } from 'react';
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
  DollarSign, Search, Filter, Plus, Eye, Edit, Trash2,
  Clock, CheckCircle, XCircle, Send, CreditCard,
  ChevronLeft, ChevronRight, FileText, User, Building, Calendar
} from 'lucide-react';

const STATUS_CONFIG = {
  aberto: { label: 'Aberto', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  aguardando_dados_bancarios: { label: 'Aguardando Dados Bancários', color: 'bg-blue-100 text-blue-800', icon: CreditCard },
  enviado_financeiro: { label: 'Enviado ao Financeiro', color: 'bg-purple-100 text-purple-800', icon: Send },
  pago: { label: 'Pago', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  cancelado: { label: 'Cancelado', color: 'bg-red-100 text-red-800', icon: XCircle }
};

export default function ReembolsosPage() {
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [reembolsos, setReembolsos] = useState([]);
  const [motivos, setMotivos] = useState([]);
  const [paginacao, setPaginacao] = useState({ pagina_atual: 1, total_paginas: 1, total_itens: 0 });
  
  // Filtros
  const [filtroStatus, setFiltroStatus] = useState('');
  const [filtroMotivo, setFiltroMotivo] = useState('');
  const [filtroNome, setFiltroNome] = useState('');
  
  // Modais
  const [modalNovo, setModalNovo] = useState(false);
  const [modalDetalhes, setModalDetalhes] = useState(null);
  const [modalEditar, setModalEditar] = useState(null);
  
  // Formulário novo reembolso
  const [novoForm, setNovoForm] = useState({
    aluno_nome: '',
    aluno_cpf: '',
    curso: '',
    turma: '',
    motivo: '',
    motivo_descricao: '',
    numero_chamado_sgc: '',
    observacoes: ''
  });
  
  // Formulário edição
  const [editarForm, setEditarForm] = useState({
    status: '',
    numero_chamado_sgc: '',
    data_retorno_financeiro: '',
    data_provisao_pagamento: '',
    observacoes: ''
  });

  useEffect(() => {
    carregarDados();
  }, []);

  useEffect(() => {
    carregarReembolsos();
  }, [filtroStatus, filtroMotivo]);

  const carregarDados = async () => {
    try {
      const [dashRes, motivosRes] = await Promise.all([
        api.get('/reembolsos/dashboard'),
        api.get('/reembolsos/motivos')
      ]);
      setDashboard(dashRes.data);
      setMotivos(motivosRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    }
  };

  const carregarReembolsos = async (pagina = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('pagina', pagina);
      params.append('por_pagina', 15);
      if (filtroStatus && filtroStatus !== 'todos') params.append('status', filtroStatus);
      if (filtroMotivo && filtroMotivo !== 'todos') params.append('motivo', filtroMotivo);
      if (filtroNome) params.append('aluno_nome', filtroNome);
      
      const response = await api.get(`/reembolsos?${params.toString()}`);
      setReembolsos(response.data.reembolsos);
      setPaginacao(response.data.paginacao);
    } catch (error) {
      toast.error('Erro ao carregar reembolsos');
    } finally {
      setLoading(false);
    }
  };

  const buscarDetalhes = async (reembolsoId) => {
    try {
      const response = await api.get(`/reembolsos/${reembolsoId}`);
      setModalDetalhes(response.data);
    } catch (error) {
      toast.error('Erro ao carregar detalhes');
    }
  };

  const criarReembolso = async () => {
    if (!novoForm.aluno_nome.trim() || !novoForm.curso.trim() || !novoForm.motivo) {
      toast.error('Preencha os campos obrigatórios');
      return;
    }
    
    try {
      await api.post('/reembolsos', novoForm);
      toast.success('Reembolso criado com sucesso');
      setModalNovo(false);
      setNovoForm({
        aluno_nome: '',
        aluno_cpf: '',
        curso: '',
        turma: '',
        motivo: '',
        motivo_descricao: '',
        numero_chamado_sgc: '',
        observacoes: ''
      });
      carregarReembolsos(paginacao.pagina_atual);
      carregarDados();
    } catch (error) {
      toast.error('Erro ao criar reembolso');
    }
  };

  const atualizarReembolso = async () => {
    try {
      await api.put(`/reembolsos/${modalEditar.id}`, editarForm);
      toast.success('Reembolso atualizado com sucesso');
      setModalEditar(null);
      carregarReembolsos(paginacao.pagina_atual);
      carregarDados();
    } catch (error) {
      toast.error('Erro ao atualizar reembolso');
    }
  };

  const formatarData = (dataStr) => {
    if (!dataStr) return '-';
    const data = new Date(dataStr);
    return data.toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric'
    });
  };

  const formatarDataHora = (dataStr) => {
    if (!dataStr) return '-';
    const data = new Date(dataStr);
    return data.toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const StatusBadge = ({ status }) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.aberto;
    const Icon = config.icon;
    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  const abrirModalEditar = (reembolso) => {
    setEditarForm({
      status: reembolso.status,
      numero_chamado_sgc: reembolso.numero_chamado_sgc || '',
      data_retorno_financeiro: reembolso.data_retorno_financeiro ? reembolso.data_retorno_financeiro.split('T')[0] : '',
      data_provisao_pagamento: reembolso.data_provisao_pagamento ? reembolso.data_provisao_pagamento.split('T')[0] : '',
      observacoes: reembolso.observacoes || ''
    });
    setModalEditar(reembolso);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
            Módulo de Reembolsos
          </h1>
          <p className="text-slate-500">
            Gerencie solicitações de reembolso e acompanhe o status
          </p>
        </div>
        <Button 
          onClick={() => setModalNovo(true)}
          className="bg-[#E30613] hover:bg-[#b9050f]"
          data-testid="btn-novo-reembolso"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nova Solicitação
        </Button>
      </div>

      {/* Dashboard Cards */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <Card className="bg-yellow-50 border-yellow-200">
            <CardContent className="p-4 text-center">
              <Clock className="w-8 h-8 mx-auto text-yellow-600 mb-2" />
              <p className="text-2xl font-bold text-yellow-700">{dashboard.total_aberto}</p>
              <p className="text-sm text-yellow-600">Abertos</p>
            </CardContent>
          </Card>
          
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4 text-center">
              <CreditCard className="w-8 h-8 mx-auto text-blue-600 mb-2" />
              <p className="text-2xl font-bold text-blue-700">{dashboard.total_aguardando}</p>
              <p className="text-sm text-blue-600">Aguardando</p>
            </CardContent>
          </Card>
          
          <Card className="bg-purple-50 border-purple-200">
            <CardContent className="p-4 text-center">
              <Send className="w-8 h-8 mx-auto text-purple-600 mb-2" />
              <p className="text-2xl font-bold text-purple-700">{dashboard.total_enviado}</p>
              <p className="text-sm text-purple-600">No Financeiro</p>
            </CardContent>
          </Card>
          
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4 text-center">
              <CheckCircle className="w-8 h-8 mx-auto text-green-600 mb-2" />
              <p className="text-2xl font-bold text-green-700">{dashboard.total_pago}</p>
              <p className="text-sm text-green-600">Pagos</p>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-50 border-slate-200">
            <CardContent className="p-4 text-center">
              <DollarSign className="w-8 h-8 mx-auto text-slate-600 mb-2" />
              <p className="text-2xl font-bold text-slate-700">{dashboard.total}</p>
              <p className="text-sm text-slate-600">Total Geral</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtros */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <Label>Buscar por Nome do Aluno</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="Nome do aluno..."
                  value={filtroNome}
                  onChange={(e) => setFiltroNome(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && carregarReembolsos()}
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
            
            <div className="w-[200px]">
              <Label>Motivo</Label>
              <Select value={filtroMotivo} onValueChange={setFiltroMotivo}>
                <SelectTrigger data-testid="filtro-motivo">
                  <SelectValue placeholder="Todos os motivos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  {motivos.map((m) => (
                    <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button onClick={() => carregarReembolsos()} className="bg-[#004587]">
              <Filter className="w-4 h-4 mr-2" />
              Filtrar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Reembolsos */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            Reembolsos ({paginacao.total_itens})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004587] mx-auto"></div>
              <p className="mt-4 text-slate-500">Carregando...</p>
            </div>
          ) : reembolsos.length === 0 ? (
            <div className="text-center py-12">
              <DollarSign className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">Nenhum reembolso encontrado</p>
              <Button
                className="mt-4 bg-[#E30613] hover:bg-[#b9050f]"
                onClick={() => setModalNovo(true)}
              >
                Criar Primeira Solicitação
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-slate-50">
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Aluno</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Curso</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Motivo</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Chamado SGC</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Status</th>
                      <th className="text-left p-3 text-sm font-medium text-slate-600">Abertura</th>
                      <th className="text-center p-3 text-sm font-medium text-slate-600">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reembolsos.map((r) => (
                      <tr key={r.id} className="border-b hover:bg-slate-50" data-testid={`reembolso-row-${r.id}`}>
                        <td className="p-3">
                          <div>
                            <p className="font-medium text-slate-900">{r.aluno_nome}</p>
                            {r.aluno_cpf && <p className="text-sm text-slate-500">{r.aluno_cpf}</p>}
                          </div>
                        </td>
                        <td className="p-3">
                          <div>
                            <p className="text-sm">{r.curso}</p>
                            {r.turma && <p className="text-xs text-slate-500">Turma: {r.turma}</p>}
                          </div>
                        </td>
                        <td className="p-3">
                          <div>
                            <p className="text-sm">{r.motivo_label}</p>
                            {r.reter_taxa && (
                              <Badge variant="outline" className="text-xs text-orange-600 border-orange-300">
                                Reter 10%
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="p-3 text-sm text-slate-600">
                          {r.numero_chamado_sgc || '-'}
                        </td>
                        <td className="p-3">
                          <StatusBadge status={r.status} />
                        </td>
                        <td className="p-3 text-sm text-slate-500">
                          {formatarData(r.data_abertura)}
                        </td>
                        <td className="p-3">
                          <div className="flex justify-center gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => buscarDetalhes(r.id)}
                              title="Ver detalhes"
                              data-testid={`btn-detalhes-${r.id}`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => abrirModalEditar(r)}
                              title="Editar"
                              className="text-blue-600"
                              data-testid={`btn-editar-${r.id}`}
                            >
                              <Edit className="w-4 h-4" />
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
                      onClick={() => carregarReembolsos(paginacao.pagina_atual - 1)}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={paginacao.pagina_atual === paginacao.total_paginas}
                      onClick={() => carregarReembolsos(paginacao.pagina_atual + 1)}
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

      {/* Modal Novo Reembolso */}
      <Dialog open={modalNovo} onOpenChange={setModalNovo}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5" />
              Nova Solicitação de Reembolso
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label>Nome do Aluno *</Label>
                <Input
                  value={novoForm.aluno_nome}
                  onChange={(e) => setNovoForm({ ...novoForm, aluno_nome: e.target.value })}
                  placeholder="Nome completo do aluno"
                  data-testid="input-aluno-nome"
                />
              </div>
              
              <div>
                <Label>CPF</Label>
                <Input
                  value={novoForm.aluno_cpf}
                  onChange={(e) => setNovoForm({ ...novoForm, aluno_cpf: e.target.value })}
                  placeholder="000.000.000-00"
                  data-testid="input-aluno-cpf"
                />
              </div>
              
              <div>
                <Label>Turma</Label>
                <Input
                  value={novoForm.turma}
                  onChange={(e) => setNovoForm({ ...novoForm, turma: e.target.value })}
                  placeholder="Ex: T1, T2, Manhã"
                  data-testid="input-turma"
                />
              </div>
              
              <div className="col-span-2">
                <Label>Curso *</Label>
                <Input
                  value={novoForm.curso}
                  onChange={(e) => setNovoForm({ ...novoForm, curso: e.target.value })}
                  placeholder="Nome do curso"
                  data-testid="input-curso"
                />
              </div>
              
              <div className="col-span-2">
                <Label>Motivo do Reembolso *</Label>
                <Select
                  value={novoForm.motivo}
                  onValueChange={(v) => setNovoForm({ ...novoForm, motivo: v })}
                >
                  <SelectTrigger data-testid="select-motivo">
                    <SelectValue placeholder="Selecione o motivo" />
                  </SelectTrigger>
                  <SelectContent>
                    {motivos.map((m) => (
                      <SelectItem key={m.value} value={m.value}>
                        {m.label} {m.reter_taxa && '(Reter 10%)'}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {novoForm.motivo === 'outros' && (
                <div className="col-span-2">
                  <Label>Descrição do Motivo</Label>
                  <Textarea
                    value={novoForm.motivo_descricao}
                    onChange={(e) => setNovoForm({ ...novoForm, motivo_descricao: e.target.value })}
                    placeholder="Descreva o motivo..."
                    rows={2}
                    data-testid="input-motivo-descricao"
                  />
                </div>
              )}
              
              <div className="col-span-2">
                <Label>Nº Chamado SGC Plus</Label>
                <Input
                  value={novoForm.numero_chamado_sgc}
                  onChange={(e) => setNovoForm({ ...novoForm, numero_chamado_sgc: e.target.value })}
                  placeholder="Ex: 12345"
                  data-testid="input-chamado-sgc"
                />
              </div>
              
              <div className="col-span-2">
                <Label>Observações</Label>
                <Textarea
                  value={novoForm.observacoes}
                  onChange={(e) => setNovoForm({ ...novoForm, observacoes: e.target.value })}
                  placeholder="Observações adicionais..."
                  rows={2}
                  data-testid="input-observacoes"
                />
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalNovo(false)}>
              Cancelar
            </Button>
            <Button onClick={criarReembolso} className="bg-[#E30613]" data-testid="btn-salvar-reembolso">
              Criar Solicitação
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Detalhes */}
      <Dialog open={!!modalDetalhes} onOpenChange={() => setModalDetalhes(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              Detalhes do Reembolso
            </DialogTitle>
          </DialogHeader>
          
          {modalDetalhes && (
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <User className="w-4 h-4" /> Dados do Aluno
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-slate-500">Nome</p>
                    <p className="font-medium">{modalDetalhes.aluno_nome}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">CPF</p>
                    <p className="font-medium">{modalDetalhes.aluno_cpf || '-'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Curso</p>
                    <p className="font-medium">{modalDetalhes.curso}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Turma</p>
                    <p className="font-medium">{modalDetalhes.turma || '-'}</p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <FileText className="w-4 h-4" /> Dados da Solicitação
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-slate-500">Motivo</p>
                      <p className="font-medium">{modalDetalhes.motivo_label}</p>
                    </div>
                    <StatusBadge status={modalDetalhes.status} />
                  </div>
                  {modalDetalhes.reter_taxa && (
                    <div>
                      <Badge className="bg-orange-100 text-orange-800">Reter Taxa de 10%</Badge>
                    </div>
                  )}
                  {modalDetalhes.motivo_descricao && (
                    <div>
                      <p className="text-slate-500">Descrição</p>
                      <p className="font-medium">{modalDetalhes.motivo_descricao}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-slate-500">Nº Chamado SGC Plus</p>
                    <p className="font-medium">{modalDetalhes.numero_chamado_sgc || '-'}</p>
                  </div>
                  {modalDetalhes.observacoes && (
                    <div>
                      <p className="text-slate-500">Observações</p>
                      <p className="font-medium">{modalDetalhes.observacoes}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Calendar className="w-4 h-4" /> Datas do Fluxo
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-slate-500">Abertura</p>
                    <p className="font-medium">{formatarDataHora(modalDetalhes.data_abertura)}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Retorno Financeiro</p>
                    <p className="font-medium">{formatarData(modalDetalhes.data_retorno_financeiro)}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Provisão Pagamento</p>
                    <p className="font-medium">{formatarData(modalDetalhes.data_provisao_pagamento)}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Data Pagamento</p>
                    <p className="font-medium">{formatarData(modalDetalhes.data_pagamento)}</p>
                  </div>
                </CardContent>
              </Card>

              <div className="text-xs text-slate-500 border-t pt-3">
                Criado por: {modalDetalhes.criado_por_nome} em {formatarDataHora(modalDetalhes.created_at)}
                {modalDetalhes.atualizado_por_nome && (
                  <span> • Atualizado por: {modalDetalhes.atualizado_por_nome}</span>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal Editar */}
      <Dialog open={!!modalEditar} onOpenChange={() => setModalEditar(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="w-5 h-5" />
              Atualizar Reembolso
            </DialogTitle>
          </DialogHeader>
          
          {modalEditar && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="font-medium">{modalEditar.aluno_nome}</p>
                <p className="text-sm text-slate-500">{modalEditar.curso}</p>
              </div>
              
              <div>
                <Label>Status</Label>
                <Select
                  value={editarForm.status}
                  onValueChange={(v) => setEditarForm({ ...editarForm, status: v })}
                >
                  <SelectTrigger data-testid="select-status-editar">
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
                <Label>Nº Chamado SGC Plus</Label>
                <Input
                  value={editarForm.numero_chamado_sgc}
                  onChange={(e) => setEditarForm({ ...editarForm, numero_chamado_sgc: e.target.value })}
                  placeholder="Ex: 12345"
                  data-testid="input-chamado-editar"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Data Retorno Financeiro</Label>
                  <Input
                    type="date"
                    value={editarForm.data_retorno_financeiro}
                    onChange={(e) => setEditarForm({ ...editarForm, data_retorno_financeiro: e.target.value })}
                    data-testid="input-data-retorno"
                  />
                </div>
                <div>
                  <Label>Data Provisão Pagamento</Label>
                  <Input
                    type="date"
                    value={editarForm.data_provisao_pagamento}
                    onChange={(e) => setEditarForm({ ...editarForm, data_provisao_pagamento: e.target.value })}
                    data-testid="input-data-provisao"
                  />
                </div>
              </div>
              
              <div>
                <Label>Observações</Label>
                <Textarea
                  value={editarForm.observacoes}
                  onChange={(e) => setEditarForm({ ...editarForm, observacoes: e.target.value })}
                  placeholder="Observações..."
                  rows={2}
                  data-testid="input-observacoes-editar"
                />
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalEditar(null)}>
              Cancelar
            </Button>
            <Button onClick={atualizarReembolso} className="bg-[#004587]" data-testid="btn-salvar-edicao">
              Salvar Alterações
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
