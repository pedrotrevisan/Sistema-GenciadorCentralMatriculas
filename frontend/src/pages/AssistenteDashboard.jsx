import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { pedidosAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { 
  FileText, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Plus,
  Eye,
  RefreshCw,
  Download,
  Search,
  Filter,
  Edit
} from 'lucide-react';

const statusConfig = {
  pendente: { icon: Clock, color: 'badge-pendente', label: 'Pendente' },
  em_analise: { icon: AlertCircle, color: 'badge-em_analise', label: 'Em Análise' },
  documentacao_pendente: { icon: FileText, color: 'badge-documentacao_pendente', label: 'Doc. Pendente' },
  aprovado: { icon: CheckCircle, color: 'badge-aprovado', label: 'Aprovado' },
  rejeitado: { icon: XCircle, color: 'badge-rejeitado', label: 'Rejeitado' },
  realizado: { icon: CheckCircle, color: 'badge-realizado', label: 'Realizado' },
  cancelado: { icon: XCircle, color: 'badge-cancelado', label: 'Cancelado' },
  exportado: { icon: CheckCircle, color: 'badge-exportado', label: 'Exportado' },
};

const statusOptions = [
  { value: 'all', label: 'Todos os Status' },
  { value: 'pendente', label: 'Pendente' },
  { value: 'em_analise', label: 'Em Análise' },
  { value: 'documentacao_pendente', label: 'Documentação Pendente' },
  { value: 'aprovado', label: 'Aprovado' },
  { value: 'rejeitado', label: 'Rejeitado' },
  { value: 'realizado', label: 'Realizado' },
  { value: 'cancelado', label: 'Cancelado' },
  { value: 'exportado', label: 'Exportado' },
];

const AssistenteDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [pedidos, setPedidos] = useState([]);
  const [paginacao, setPaginacao] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [pagina, setPagina] = useState(1);
  
  // Status change modal
  const [statusModal, setStatusModal] = useState({ open: false, pedido: null });
  const [newStatus, setNewStatus] = useState('');
  const [motivo, setMotivo] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = { pagina, por_pagina: 10 };
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      
      const [dashboardRes, pedidosRes] = await Promise.all([
        pedidosAPI.getDashboard(),
        pedidosAPI.listar(params)
      ]);
      setDashboard(dashboardRes.data);
      setPedidos(pedidosRes.data.pedidos);
      setPaginacao(pedidosRes.data.paginacao);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter, pagina]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const StatusBadge = ({ status }) => {
    const config = statusConfig[status] || statusConfig.pendente;
    const Icon = config.icon;
    return (
      <Badge variant="outline" className={`${config.color} flex items-center gap-1`}>
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const handleStatusChange = async () => {
    if (!newStatus) {
      toast.error('Selecione um status');
      return;
    }
    
    setUpdatingStatus(true);
    try {
      await pedidosAPI.atualizarStatus(statusModal.pedido.id, {
        status: newStatus,
        motivo: motivo || undefined
      });
      toast.success('Status atualizado com sucesso');
      setStatusModal({ open: false, pedido: null });
      setNewStatus('');
      setMotivo('');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Erro ao atualizar status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await pedidosAPI.exportarTOTVS('xlsx');
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `matriculas_totvs_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Exportação realizada com sucesso');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Erro ao exportar. Verifique se há pedidos com status "Realizado".');
    }
  };

  const contagem = dashboard?.contagem_status || {};

  if (loading && !pedidos.length) {
    return (
      <div className="space-y-6" data-testid="assistente-dashboard-loading">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="assistente-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
            Painel de Gestão
          </h1>
          <p className="text-slate-500">
            Gerencie todos os pedidos de matrícula
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchData}
            data-testid="refresh-btn"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Atualizar
          </Button>
          <Button
            variant="outline"
            onClick={handleExport}
            data-testid="export-btn"
          >
            <Download className="h-4 w-4 mr-2" />
            Exportar TOTVS
          </Button>
          <Button
            className="bg-[#E30613] hover:bg-[#b9050f]"
            onClick={() => navigate('/assistente/novo-pedido')}
            data-testid="new-order-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Nova Matrícula
          </Button>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-xs font-medium text-slate-500">Total</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold text-[#004587]">{contagem.total || 0}</div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-xs font-medium text-slate-500">Pendentes</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold text-amber-600">{contagem.pendente || 0}</div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-xs font-medium text-slate-500">Em Análise</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold text-blue-600">{contagem.em_analise || 0}</div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-xs font-medium text-slate-500">Doc. Pend.</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold text-orange-600">{contagem.documentacao_pendente || 0}</div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-xs font-medium text-slate-500">Aprovados</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold text-emerald-600">{contagem.aprovado || 0}</div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-xs font-medium text-slate-500">Realizados</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold text-green-600">{contagem.realizado || 0}</div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-xs font-medium text-slate-500">Exportados</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold text-purple-600">{contagem.exportado || 0}</div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-xs font-medium text-slate-500">Rejeitados</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold text-red-600">{contagem.rejeitado || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Buscar por curso, consultor..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
            data-testid="search-input"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-48" data-testid="status-filter">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Filtrar por status" />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Pedidos de Matrícula</CardTitle>
        </CardHeader>
        <CardContent>
          {pedidos.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">Nenhum pedido encontrado</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Protocolo</TableHead>
                      <TableHead>Curso</TableHead>
                      <TableHead>Consultor</TableHead>
                      <TableHead>Projeto/Empresa</TableHead>
                      <TableHead>Alunos</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Data</TableHead>
                      <TableHead className="text-right">Ações</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pedidos.map((pedido) => (
                      <TableRow key={pedido.id} className="table-row-hover">
                        <TableCell className="font-mono text-sm font-semibold text-[#004587]">
                          {pedido.numero_protocolo || '-'}
                        </TableCell>
                        <TableCell className="font-medium">
                          {pedido.curso_nome}
                        </TableCell>
                        <TableCell>{pedido.consultor_nome}</TableCell>
                        <TableCell>
                          {pedido.projeto_nome || pedido.empresa_nome}
                        </TableCell>
                        <TableCell>{pedido.total_alunos}</TableCell>
                        <TableCell>
                          <StatusBadge status={pedido.status} />
                        </TableCell>
                        <TableCell>{formatDate(pedido.created_at)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => navigate(`/assistente/pedido/${pedido.id}`)}
                              data-testid={`view-order-${pedido.id}`}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            {pedido.pode_editar && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setStatusModal({ open: true, pedido });
                                  setNewStatus('');
                                }}
                                data-testid={`edit-status-${pedido.id}`}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {paginacao && paginacao.total_paginas > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <p className="text-sm text-slate-500">
                    Página {paginacao.pagina_atual} de {paginacao.total_paginas}
                    {' '}({paginacao.total_itens} itens)
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={paginacao.pagina_atual <= 1}
                      onClick={() => setPagina(p => p - 1)}
                    >
                      Anterior
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={paginacao.pagina_atual >= paginacao.total_paginas}
                      onClick={() => setPagina(p => p + 1)}
                    >
                      Próximo
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Status Change Modal */}
      <Dialog open={statusModal.open} onOpenChange={(open) => setStatusModal({ open, pedido: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Alterar Status do Pedido</DialogTitle>
            <DialogDescription>
              Pedido: {statusModal.pedido?.curso_nome}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Novo Status</label>
              <Select value={newStatus} onValueChange={setNewStatus}>
                <SelectTrigger data-testid="new-status-select">
                  <SelectValue placeholder="Selecione o status" />
                </SelectTrigger>
                <SelectContent>
                  {statusOptions.filter(s => s.value !== 'all').map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {newStatus === 'rejeitado' && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Motivo da Rejeição</label>
                <Textarea
                  placeholder="Informe o motivo..."
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  data-testid="rejection-reason"
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusModal({ open: false, pedido: null })}>
              Cancelar
            </Button>
            <Button 
              className="bg-[#E30613] hover:bg-[#b9050f]"
              onClick={handleStatusChange}
              disabled={updatingStatus}
              data-testid="confirm-status-change"
            >
              {updatingStatus ? 'Salvando...' : 'Confirmar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AssistenteDashboard;
