import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { pedidosAPI, usuariosAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { toast } from 'sonner';
import { 
  FileText, 
  Users, 
  Clock, 
  CheckCircle,
  Plus,
  RefreshCw,
  Download,
  TrendingUp,
  BarChart3
} from 'lucide-react';

const AdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [totalUsuarios, setTotalUsuarios] = useState(0);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashboardRes, usuariosRes] = await Promise.all([
        pedidosAPI.getDashboard(),
        usuariosAPI.listar({ pagina: 1, por_pagina: 1 })
      ]);
      setDashboard(dashboardRes.data);
      setTotalUsuarios(usuariosRes.data.total);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

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
      toast.error(error.response?.data?.error || 'Erro ao exportar');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6" data-testid="admin-dashboard-loading">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  const contagem = dashboard?.contagem_status || {};

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="admin-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
            Dashboard Administrativo
          </h1>
          <p className="text-slate-500">
            Visão geral do sistema
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
        </div>
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="dashboard-metric-card border-l-4 border-l-[#004587]">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Total de Pedidos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-[#004587]">
              {contagem.total || 0}
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Todos os pedidos no sistema
            </p>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card border-l-4 border-l-amber-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Aguardando Ação
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-amber-600">
              {(contagem.pendente || 0) + (contagem.em_analise || 0) + (contagem.documentacao_pendente || 0)}
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Pedidos que precisam de atenção
            </p>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card border-l-4 border-l-emerald-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Concluídos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-emerald-600">
              {(contagem.realizado || 0) + (contagem.exportado || 0)}
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Matrículas finalizadas
            </p>
          </CardContent>
        </Card>

        <Card className="dashboard-metric-card border-l-4 border-l-purple-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
              <Users className="h-4 w-4" />
              Usuários
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-purple-600">
              {totalUsuarios}
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Usuários cadastrados
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Status dos Pedidos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { key: 'pendente', label: 'Pendente', color: 'bg-amber-500' },
                { key: 'em_analise', label: 'Em Análise', color: 'bg-blue-500' },
                { key: 'documentacao_pendente', label: 'Doc. Pendente', color: 'bg-orange-500' },
                { key: 'aprovado', label: 'Aprovado', color: 'bg-emerald-500' },
                { key: 'realizado', label: 'Realizado', color: 'bg-green-500' },
                { key: 'exportado', label: 'Exportado', color: 'bg-purple-500' },
                { key: 'rejeitado', label: 'Rejeitado', color: 'bg-red-500' },
                { key: 'cancelado', label: 'Cancelado', color: 'bg-slate-400' },
              ].map(({ key, label, color }) => (
                <div key={key} className="flex items-center gap-4">
                  <div className="w-24 text-sm text-slate-600">{label}</div>
                  <div className="flex-1 h-6 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${color} rounded-full transition-all duration-500`}
                      style={{
                        width: `${contagem.total ? ((contagem[key] || 0) / contagem.total) * 100 : 0}%`
                      }}
                    />
                  </div>
                  <div className="w-12 text-right text-sm font-medium">
                    {contagem[key] || 0}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Ações Rápidas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4">
              <Button
                className="w-full h-16 bg-[#E30613] hover:bg-[#b9050f] text-left justify-start"
                onClick={() => navigate('/admin/novo-pedido')}
                data-testid="quick-new-order"
              >
                <Plus className="h-6 w-6 mr-4" />
                <div>
                  <p className="font-semibold">Nova Matrícula</p>
                  <p className="text-sm opacity-80">Criar novo pedido de matrícula</p>
                </div>
              </Button>

              <Button
                variant="outline"
                className="w-full h-16 text-left justify-start"
                onClick={() => navigate('/admin/pedidos')}
                data-testid="quick-orders"
              >
                <FileText className="h-6 w-6 mr-4" />
                <div>
                  <p className="font-semibold">Gerenciar Pedidos</p>
                  <p className="text-sm text-slate-500">Ver e gerenciar todos os pedidos</p>
                </div>
              </Button>

              <Button
                variant="outline"
                className="w-full h-16 text-left justify-start"
                onClick={() => navigate('/admin/usuarios')}
                data-testid="quick-users"
              >
                <Users className="h-6 w-6 mr-4" />
                <div>
                  <p className="font-semibold">Gestão de Usuários</p>
                  <p className="text-sm text-slate-500">Gerenciar usuários do sistema</p>
                </div>
              </Button>

              <Button
                variant="outline"
                className="w-full h-16 text-left justify-start"
                onClick={handleExport}
                data-testid="quick-export"
              >
                <Download className="h-6 w-6 mr-4" />
                <div>
                  <p className="font-semibold">Exportar TOTVS</p>
                  <p className="text-sm text-slate-500">Exportar pedidos realizados</p>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;
