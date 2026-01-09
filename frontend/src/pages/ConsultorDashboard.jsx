import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { pedidosAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
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
  FileText, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Plus,
  Eye,
  RefreshCw
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

const ConsultorDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [pedidos, setPedidos] = useState([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashboardRes, pedidosRes] = await Promise.all([
        pedidosAPI.getDashboard(),
        pedidosAPI.listar({ pagina: 1, por_pagina: 10 })
      ]);
      setDashboard(dashboardRes.data);
      setPedidos(pedidosRes.data.pedidos);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

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

  if (loading) {
    return (
      <div className="space-y-6" data-testid="consultor-dashboard-loading">
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

  const contagem = dashboard?.contagem_status || {};

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="consultor-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
            Meus Pedidos
          </h1>
          <p className="text-slate-500">
            Bem-vindo, {user?.nome}
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
            className="bg-[#E30613] hover:bg-[#b9050f]"
            onClick={() => navigate('/consultor/novo-pedido')}
            data-testid="new-order-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Nova Matrícula
          </Button>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Total de Pedidos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-[#004587]">
              {contagem.total || 0}
            </div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Pendentes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600">
              {contagem.pendente || 0}
            </div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Em Análise
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {contagem.em_analise || 0}
            </div>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Realizados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-600">
              {contagem.realizado || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Pedidos Recentes</CardTitle>
        </CardHeader>
        <CardContent>
          {pedidos.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">Nenhum pedido encontrado</p>
              <Button
                className="mt-4 bg-[#E30613] hover:bg-[#b9050f]"
                onClick={() => navigate('/consultor/novo-pedido')}
              >
                Criar Primeiro Pedido
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Curso</TableHead>
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
                      <TableCell className="font-medium">
                        {pedido.curso_nome}
                      </TableCell>
                      <TableCell>
                        {pedido.projeto_nome || pedido.empresa_nome}
                      </TableCell>
                      <TableCell>{pedido.total_alunos}</TableCell>
                      <TableCell>
                        <StatusBadge status={pedido.status} />
                      </TableCell>
                      <TableCell>{formatDate(pedido.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/consultor/pedido/${pedido.id}`)}
                          data-testid={`view-order-${pedido.id}`}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ConsultorDashboard;
