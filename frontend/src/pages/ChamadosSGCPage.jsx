import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import {
  Search,
  Plus,
  Clock,
  AlertTriangle,
  CheckCircle,
  MessageSquare,
  User,
  Building,
  Calendar,
  Timer,
  ArrowRight,
  Filter,
  RefreshCw
} from 'lucide-react';
import api from '../services/api';

const STATUS_CONFIG = {
  backlog: { label: 'Backlog', color: 'bg-slate-500', textColor: 'text-slate-700' },
  em_atendimento: { label: 'Em Atendimento', color: 'bg-blue-500', textColor: 'text-blue-700' },
  aguardando_retorno: { label: 'Aguardando Retorno', color: 'bg-amber-500', textColor: 'text-amber-700' },
  concluido: { label: 'Concluído', color: 'bg-green-500', textColor: 'text-green-700' },
  cancelado: { label: 'Cancelado', color: 'bg-red-500', textColor: 'text-red-700' },
};

const ChamadosSGCPage = () => {
  const navigate = useNavigate();
  const [chamados, setChamados] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('');
  const [showNovoChamado, setShowNovoChamado] = useState(false);
  const [showDetalhes, setShowDetalhes] = useState(false);
  const [chamadoSelecionado, setChamadoSelecionado] = useState(null);
  const [novaInteracao, setNovaInteracao] = useState('');

  const [novoChamado, setNovoChamado] = useState({
    numero_ticket: '',
    titulo: '',
    descricao: '',
    data_abertura: new Date().toISOString().slice(0, 16),
    data_previsao_fim: '',
    sla_horas: 32,
    solicitante_nome: '',
    solicitante_unidade: 'SENAI - CIMATEC',
    area: '',
    classificacao: 'Matrícula',
    produto: 'MATRÍCULA BMP',
    tecnico_responsavel: '',
    prioridade: 0,
    critico: false,
    // Campos do Formulário SGC Plus BMP
    codigo_curso: '',
    nome_curso: '',
    turno: '',
    periodo_letivo: '',
    quantidade_vagas: '',
    modalidade: '',
    forma_pagamento: '',
    cont: '',
    requisito_acesso: '',
    empresa_nome: '',
    empresa_contato: '',
    empresa_email: '',
    empresa_telefone: '',
    data_inicio_curso: '',
    data_fim_curso: '',
    documentos_obrigatorios: ''
  });

  useEffect(() => {
    carregarDados();
  }, [filtroStatus, busca]);

  const carregarDados = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filtroStatus) params.append('status', filtroStatus);
      if (busca) params.append('busca', busca);
      
      const [chamadosRes, dashboardRes] = await Promise.all([
        api.get(`/chamados-sgc?${params.toString()}`),
        api.get('/chamados-sgc/dashboard')
      ]);
      
      setChamados(chamadosRes.data.chamados || []);
      setDashboard(dashboardRes.data);
    } catch (error) {
      console.error('Erro ao carregar chamados:', error);
      toast.error('Erro ao carregar chamados');
    } finally {
      setLoading(false);
    }
  };

  const criarChamado = async () => {
    try {
      if (!novoChamado.numero_ticket) {
        toast.error('Número do ticket é obrigatório');
        return;
      }
      
      await api.post('/chamados-sgc', {
        ...novoChamado,
        data_abertura: new Date(novoChamado.data_abertura).toISOString(),
        data_previsao_fim: novoChamado.data_previsao_fim ? new Date(novoChamado.data_previsao_fim).toISOString() : null,
        data_inicio_curso: novoChamado.data_inicio_curso ? new Date(novoChamado.data_inicio_curso).toISOString() : null,
        data_fim_curso: novoChamado.data_fim_curso ? new Date(novoChamado.data_fim_curso).toISOString() : null,
        quantidade_vagas: novoChamado.quantidade_vagas ? parseInt(novoChamado.quantidade_vagas) : null
      });
      
      toast.success('Chamado criado com sucesso!');
      setShowNovoChamado(false);
      setNovoChamado({
        numero_ticket: '',
        titulo: '',
        descricao: '',
        data_abertura: new Date().toISOString().slice(0, 16),
        data_previsao_fim: '',
        sla_horas: 32,
        solicitante_nome: '',
        solicitante_unidade: 'SENAI - CIMATEC',
        area: '',
        classificacao: 'Matrícula',
        produto: 'MATRÍCULA BMP',
        tecnico_responsavel: '',
        prioridade: 0,
        critico: false,
        codigo_curso: '',
        nome_curso: '',
        turno: '',
        periodo_letivo: '',
        quantidade_vagas: '',
        modalidade: '',
        forma_pagamento: '',
        cont: '',
        requisito_acesso: '',
        empresa_nome: '',
        empresa_contato: '',
        empresa_email: '',
        empresa_telefone: '',
        data_inicio_curso: '',
        data_fim_curso: '',
        documentos_obrigatorios: ''
      });
      carregarDados();
    } catch (error) {
      console.error('Erro ao criar chamado:', error);
      toast.error('Erro ao criar chamado');
    }
  };

  const abrirDetalhes = async (chamadoId) => {
    try {
      const response = await api.get(`/chamados-sgc/${chamadoId}`);
      setChamadoSelecionado(response.data);
      setShowDetalhes(true);
    } catch (error) {
      console.error('Erro ao carregar detalhes:', error);
      toast.error('Erro ao carregar detalhes do chamado');
    }
  };

  const atualizarStatus = async (chamadoId, novoStatus) => {
    try {
      await api.put(`/chamados-sgc/${chamadoId}`, { status: novoStatus });
      toast.success('Status atualizado!');
      carregarDados();
      if (chamadoSelecionado) {
        abrirDetalhes(chamadoId);
      }
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
      toast.error('Erro ao atualizar status');
    }
  };

  const adicionarInteracao = async () => {
    if (!novaInteracao.trim()) return;
    
    try {
      await api.post(`/chamados-sgc/${chamadoSelecionado.chamado.id}/interacao`, {
        tipo: 'comunicacao',
        mensagem: novaInteracao
      });
      toast.success('Interação adicionada!');
      setNovaInteracao('');
      abrirDetalhes(chamadoSelecionado.chamado.id);
    } catch (error) {
      console.error('Erro ao adicionar interação:', error);
      toast.error('Erro ao adicionar interação');
    }
  };

  const calcularProgresso = (chamado) => {
    if (!chamado.sla_horas) return 0;
    return Math.min(100, (chamado.sla_consumido / chamado.sla_horas) * 100);
  };

  const formatarData = (data) => {
    if (!data) return '-';
    return new Date(data).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Chamados SGC Plus</h1>
          <p className="text-slate-500">Gerencie solicitações de matrícula BMP</p>
        </div>
        <Button onClick={() => setShowNovoChamado(true)} data-testid="novo-chamado-btn">
          <Plus className="h-4 w-4 mr-2" />
          Novo Chamado
        </Button>
      </div>

      {/* Dashboard Cards - Todos clicáveis para filtrar */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white cursor-pointer hover:shadow-lg hover:scale-105 transition-all duration-200"
                onClick={() => { setFiltroStatus(''); carregarDados(); }}
                data-testid="card-abertos">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <Clock className="h-8 w-8 opacity-80" />
                <div className="text-right">
                  <p className="text-3xl font-bold">{dashboard.total_abertos}</p>
                  <p className="text-xs opacity-80">Em Aberto</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white cursor-pointer hover:shadow-lg hover:scale-105 transition-all duration-200"
                onClick={() => { setFiltroStatus('backlog'); setBusca('critico'); carregarDados(); }}
                data-testid="card-criticos">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <AlertTriangle className="h-8 w-8 opacity-80" />
                <div className="text-right">
                  <p className="text-3xl font-bold">{dashboard.criticos}</p>
                  <p className="text-xs opacity-80">Críticos</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white cursor-pointer hover:shadow-lg hover:scale-105 transition-all duration-200"
                onClick={() => { setFiltroStatus('em_atendimento'); carregarDados(); }}
                data-testid="card-sla-critico">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <Timer className="h-8 w-8 opacity-80" />
                <div className="text-right">
                  <p className="text-3xl font-bold">{dashboard.sla_critico}</p>
                  <p className="text-xs opacity-80">SLA Crítico</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white cursor-pointer hover:shadow-lg hover:scale-105 transition-all duration-200"
                onClick={() => { setFiltroStatus('concluido'); carregarDados(); }}
                data-testid="card-fechados">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <CheckCircle className="h-8 w-8 opacity-80" />
                <div className="text-right">
                  <p className="text-3xl font-bold">{dashboard.fechados_hoje}</p>
                  <p className="text-xs opacity-80">Fechados Hoje</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Buscar por ticket, título ou solicitante..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="pl-10"
                data-testid="busca-chamados"
              />
            </div>
            <Select value={filtroStatus || "all"} onValueChange={(v) => setFiltroStatus(v === "all" ? "" : v)}>
              <SelectTrigger className="w-[200px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filtrar por status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="backlog">Backlog</SelectItem>
                <SelectItem value="em_atendimento">Em Atendimento</SelectItem>
                <SelectItem value="aguardando_retorno">Aguardando Retorno</SelectItem>
                <SelectItem value="concluido">Concluído</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={carregarDados}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Chamados */}
      <div className="space-y-3">
        {loading ? (
          <Card>
            <CardContent className="p-8 text-center text-slate-500">
              Carregando chamados...
            </CardContent>
          </Card>
        ) : chamados.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-slate-500">
              Nenhum chamado encontrado
            </CardContent>
          </Card>
        ) : (
          chamados.map((chamado) => (
            <Card 
              key={chamado.id} 
              className={`hover:shadow-md transition-shadow cursor-pointer ${chamado.critico ? 'border-l-4 border-l-red-500' : ''}`}
              onClick={() => abrirDetalhes(chamado.id)}
              data-testid={`chamado-${chamado.numero_ticket}`}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-sm font-semibold text-blue-600">
                        {chamado.numero_ticket}
                      </span>
                      <Badge className={`${STATUS_CONFIG[chamado.status]?.color || 'bg-slate-500'} text-white`}>
                        {STATUS_CONFIG[chamado.status]?.label || chamado.status}
                      </Badge>
                      {chamado.critico && (
                        <Badge variant="destructive">
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          Crítico
                        </Badge>
                      )}
                    </div>
                    
                    <h3 className="font-medium text-slate-800 mb-1">
                      {chamado.titulo || 'Sem título'}
                    </h3>
                    
                    <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                      {chamado.solicitante_nome && (
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          {chamado.solicitante_nome}
                        </span>
                      )}
                      {chamado.solicitante_unidade && (
                        <span className="flex items-center gap-1">
                          <Building className="h-3 w-3" />
                          {chamado.solicitante_unidade}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatarData(chamado.data_abertura)}
                      </span>
                    </div>
                  </div>

                  <div className="text-right ml-4">
                    <div className="text-xs text-slate-500 mb-1">
                      SLA: {chamado.sla_consumido?.toFixed(1) || 0}h / {chamado.sla_horas}h
                    </div>
                    <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${calcularProgresso(chamado) > 80 ? 'bg-red-500' : calcularProgresso(chamado) > 50 ? 'bg-amber-500' : 'bg-green-500'}`}
                        style={{ width: `${calcularProgresso(chamado)}%` }}
                      />
                    </div>
                    {chamado.tecnico_responsavel && (
                      <p className="text-xs text-slate-400 mt-2">
                        {chamado.tecnico_responsavel}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Modal Novo Chamado */}
      <Dialog open={showNovoChamado} onOpenChange={setShowNovoChamado}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Novo Chamado SGC Plus - BMP</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Seção: Dados do Chamado */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-700 border-b pb-2">Dados do Chamado</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Nº Ticket *</Label>
                  <Input
                    placeholder="CACCM260000XXX"
                    value={novoChamado.numero_ticket}
                    onChange={(e) => setNovoChamado({...novoChamado, numero_ticket: e.target.value})}
                    data-testid="input-numero-ticket"
                  />
                </div>
                <div>
                  <Label>Data Abertura</Label>
                  <Input
                    type="datetime-local"
                    value={novoChamado.data_abertura}
                    onChange={(e) => setNovoChamado({...novoChamado, data_abertura: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Solicitante</Label>
                  <Input
                    placeholder="Nome do solicitante"
                    value={novoChamado.solicitante_nome}
                    onChange={(e) => setNovoChamado({...novoChamado, solicitante_nome: e.target.value})}
                  />
                </div>
              </div>
            </div>

            {/* Seção: Informações do Curso */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-blue-700 border-b border-blue-200 pb-2">Informações do Curso</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Código do Curso</Label>
                  <Input
                    placeholder="Ex: 1234"
                    value={novoChamado.codigo_curso}
                    onChange={(e) => setNovoChamado({...novoChamado, codigo_curso: e.target.value})}
                  />
                </div>
                <div className="col-span-2">
                  <Label>Nome do Curso</Label>
                  <Input
                    placeholder="Ex: Lean Manufacturing"
                    value={novoChamado.nome_curso}
                    onChange={(e) => setNovoChamado({...novoChamado, nome_curso: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Turno</Label>
                  <Select 
                    value={novoChamado.turno || undefined} 
                    onValueChange={(value) => setNovoChamado({...novoChamado, turno: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o turno" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Manhã">Manhã</SelectItem>
                      <SelectItem value="Tarde">Tarde</SelectItem>
                      <SelectItem value="Noite">Noite</SelectItem>
                      <SelectItem value="Integral">Integral</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Período Letivo</Label>
                  <Input
                    placeholder="Ex: 2026.1"
                    value={novoChamado.periodo_letivo}
                    onChange={(e) => setNovoChamado({...novoChamado, periodo_letivo: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Quantidade de Vagas</Label>
                  <Input
                    type="number"
                    placeholder="Ex: 25"
                    value={novoChamado.quantidade_vagas}
                    onChange={(e) => setNovoChamado({...novoChamado, quantidade_vagas: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Modalidade</Label>
                  <Select 
                    value={novoChamado.modalidade || undefined} 
                    onValueChange={(value) => setNovoChamado({...novoChamado, modalidade: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione a modalidade" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CAP">CAP - Capacitação</SelectItem>
                      <SelectItem value="IP">IP - Iniciação Profissional</SelectItem>
                      <SelectItem value="CAI">CAI - Aprendizagem Industrial</SelectItem>
                      <SelectItem value="CQPH">CQPH - Qualificação Prof. Habilitação</SelectItem>
                      <SelectItem value="CQP">CQP - Qualificação Profissional</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Forma de Pagamento</Label>
                  <Select 
                    value={novoChamado.forma_pagamento || undefined} 
                    onValueChange={(value) => setNovoChamado({...novoChamado, forma_pagamento: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Empresa">Pago por Empresa</SelectItem>
                      <SelectItem value="Aluno">Pago pelo Aluno</SelectItem>
                      <SelectItem value="Gratuidade">Gratuidade Regimental</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>CONT</Label>
                  <Input
                    placeholder="Número do CONT"
                    value={novoChamado.cont}
                    onChange={(e) => setNovoChamado({...novoChamado, cont: e.target.value})}
                  />
                </div>
              </div>
            </div>

            {/* Seção: Dados da Empresa */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-green-700 border-b border-green-200 pb-2">Dados da Empresa</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Nome da Empresa</Label>
                  <Input
                    placeholder="Ex: Empresa LTDA"
                    value={novoChamado.empresa_nome}
                    onChange={(e) => setNovoChamado({...novoChamado, empresa_nome: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Contato da Empresa</Label>
                  <Input
                    placeholder="Nome do contato"
                    value={novoChamado.empresa_contato}
                    onChange={(e) => setNovoChamado({...novoChamado, empresa_contato: e.target.value})}
                  />
                </div>
                <div>
                  <Label>E-mail</Label>
                  <Input
                    type="email"
                    placeholder="contato@empresa.com.br"
                    value={novoChamado.empresa_email}
                    onChange={(e) => setNovoChamado({...novoChamado, empresa_email: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Telefone</Label>
                  <Input
                    placeholder="(71) 99999-9999"
                    value={novoChamado.empresa_telefone}
                    onChange={(e) => setNovoChamado({...novoChamado, empresa_telefone: e.target.value})}
                  />
                </div>
              </div>
            </div>

            {/* Seção: Período do Curso */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-amber-700 border-b border-amber-200 pb-2">Período do Curso</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Data de Início</Label>
                  <Input
                    type="date"
                    value={novoChamado.data_inicio_curso}
                    onChange={(e) => setNovoChamado({...novoChamado, data_inicio_curso: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Data Final</Label>
                  <Input
                    type="date"
                    value={novoChamado.data_fim_curso}
                    onChange={(e) => setNovoChamado({...novoChamado, data_fim_curso: e.target.value})}
                  />
                </div>
              </div>
            </div>

            {/* Seção: Documentos e Requisitos */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-purple-700 border-b border-purple-200 pb-2">Documentos e Requisitos</h3>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <Label>Documentos Obrigatórios</Label>
                  <Textarea
                    placeholder="Ex: RG, CPF, Comprovante de Escolaridade, Comprovante de Residência..."
                    value={novoChamado.documentos_obrigatorios}
                    onChange={(e) => setNovoChamado({...novoChamado, documentos_obrigatorios: e.target.value})}
                    rows={2}
                  />
                </div>
                <div>
                  <Label>Requisito de Acesso ao Curso</Label>
                  <Textarea
                    placeholder="Ex: Ensino Médio Completo, Idade mínima 18 anos..."
                    value={novoChamado.requisito_acesso}
                    onChange={(e) => setNovoChamado({...novoChamado, requisito_acesso: e.target.value})}
                    rows={2}
                  />
                </div>
              </div>
            </div>

            {/* Seção: Controle Interno */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-700 border-b pb-2">Controle Interno</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Técnico Responsável</Label>
                  <Input
                    placeholder="Nome do técnico"
                    value={novoChamado.tecnico_responsavel}
                    onChange={(e) => setNovoChamado({...novoChamado, tecnico_responsavel: e.target.value})}
                  />
                </div>
                <div>
                  <Label>SLA (horas)</Label>
                  <Input
                    type="number"
                    value={novoChamado.sla_horas}
                    onChange={(e) => setNovoChamado({...novoChamado, sla_horas: parseFloat(e.target.value)})}
                  />
                </div>
                <div>
                  <Label>Previsão de Conclusão</Label>
                  <Input
                    type="datetime-local"
                    value={novoChamado.data_previsao_fim}
                    onChange={(e) => setNovoChamado({...novoChamado, data_previsao_fim: e.target.value})}
                  />
                </div>
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={novoChamado.critico}
                    onChange={(e) => setNovoChamado({...novoChamado, critico: e.target.checked})}
                    className="rounded"
                  />
                  <span className="text-sm text-red-600 font-medium">Marcar como Crítico</span>
                </label>
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNovoChamado(false)}>
              Cancelar
            </Button>
            <Button onClick={criarChamado} data-testid="salvar-chamado-btn">
              Criar Chamado
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Detalhes do Chamado */}
      <Dialog open={showDetalhes} onOpenChange={setShowDetalhes}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          {chamadoSelecionado && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-lg font-bold text-blue-600">
                    {chamadoSelecionado.chamado.numero_ticket}
                  </span>
                  <Badge className={`${STATUS_CONFIG[chamadoSelecionado.chamado.status]?.color} text-white`}>
                    {STATUS_CONFIG[chamadoSelecionado.chamado.status]?.label}
                  </Badge>
                  {chamadoSelecionado.chamado.critico && (
                    <Badge variant="destructive">Crítico</Badge>
                  )}
                </div>
                <DialogTitle className="text-left mt-2">
                  {chamadoSelecionado.chamado.titulo || 'Sem título'}
                </DialogTitle>
              </DialogHeader>
              
              <div className="space-y-6 py-4">
                {/* Informações Gerais */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Solicitante:</span>
                    <p className="font-medium">{chamadoSelecionado.chamado.solicitante_nome || '-'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Unidade:</span>
                    <p className="font-medium">{chamadoSelecionado.chamado.solicitante_unidade || '-'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Técnico:</span>
                    <p className="font-medium">{chamadoSelecionado.chamado.tecnico_responsavel || '-'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Abertura:</span>
                    <p className="font-medium">{formatarData(chamadoSelecionado.chamado.data_abertura)}</p>
                  </div>
                </div>
                
                {/* Descrição */}
                {chamadoSelecionado.chamado.descricao && (
                  <div>
                    <h4 className="font-medium text-slate-700 mb-2">Descrição</h4>
                    <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg">
                      {chamadoSelecionado.chamado.descricao}
                    </p>
                  </div>
                )}
                
                {/* SLA */}
                <div>
                  <h4 className="font-medium text-slate-700 mb-2">SLA</h4>
                  <div className="flex items-center gap-4">
                    <div className="flex-1 h-3 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${calcularProgresso(chamadoSelecionado.chamado) > 80 ? 'bg-red-500' : calcularProgresso(chamadoSelecionado.chamado) > 50 ? 'bg-amber-500' : 'bg-green-500'}`}
                        style={{ width: `${calcularProgresso(chamadoSelecionado.chamado)}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {chamadoSelecionado.chamado.sla_consumido?.toFixed(1) || 0}h / {chamadoSelecionado.chamado.sla_horas}h
                    </span>
                  </div>
                </div>
                
                {/* Ações de Status */}
                <div>
                  <h4 className="font-medium text-slate-700 mb-2">Alterar Status</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                      <Button
                        key={key}
                        variant={chamadoSelecionado.chamado.status === key ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => atualizarStatus(chamadoSelecionado.chamado.id, key)}
                        className={chamadoSelecionado.chamado.status === key ? config.color : ''}
                      >
                        {config.label}
                      </Button>
                    ))}
                  </div>
                </div>
                
                {/* Andamentos */}
                <div>
                  <h4 className="font-medium text-slate-700 mb-2">Andamentos</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {chamadoSelecionado.andamentos.length === 0 ? (
                      <p className="text-sm text-slate-500">Nenhum andamento registrado</p>
                    ) : (
                      chamadoSelecionado.andamentos.map((and) => (
                        <div key={and.id} className="flex items-center gap-3 text-sm bg-slate-50 p-2 rounded">
                          <Badge variant="outline">{and.andamento}</Badge>
                          <span className="text-slate-500">{and.usuario}</span>
                          <span className="text-slate-400 text-xs">{formatarData(and.data)}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
                
                {/* Interações */}
                <div>
                  <h4 className="font-medium text-slate-700 mb-2">Interações</h4>
                  <div className="space-y-3 max-h-60 overflow-y-auto mb-3">
                    {chamadoSelecionado.interacoes.length === 0 ? (
                      <p className="text-sm text-slate-500">Nenhuma interação registrada</p>
                    ) : (
                      chamadoSelecionado.interacoes.map((int) => (
                        <div key={int.id} className="bg-blue-50 p-3 rounded-lg">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-blue-700">{int.usuario}</span>
                            <span className="text-xs text-slate-400">{formatarData(int.data)}</span>
                          </div>
                          <p className="text-sm text-slate-700">{int.mensagem}</p>
                        </div>
                      ))
                    )}
                  </div>
                  
                  {/* Nova Interação */}
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Adicionar comunicação..."
                      value={novaInteracao}
                      onChange={(e) => setNovaInteracao(e.target.value)}
                      rows={2}
                      className="flex-1"
                    />
                    <Button onClick={adicionarInteracao} disabled={!novaInteracao.trim()}>
                      <MessageSquare className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ChamadosSGCPage;
