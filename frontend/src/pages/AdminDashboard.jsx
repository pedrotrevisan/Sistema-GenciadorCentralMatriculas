import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { pedidosAPI, pendenciasAPI, reembolsosAPI } from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import AlertaRetornos from '../components/AlertaRetornos';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend
} from 'recharts';
import {
  TrendingUp,
  Clock,
  AlertTriangle,
  Users,
  FileText,
  CheckCircle,
  ArrowRight,
  Plus,
  Download,
  RefreshCw,
  FileWarning,
  Wallet,
  ClipboardList,
  AlertCircle,
  ChevronRight
} from 'lucide-react';

const COLORS = ['#004587', '#E30613', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'];

const AdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [pendenciasDash, setPendenciasDash] = useState(null);
  const [reembolsosDash, setReembolsosDash] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadAllData = async () => {
    try {
      const [analyticsRes, pendenciasRes, reembolsosRes] = await Promise.all([
        pedidosAPI.getAnalytics(),
        pendenciasAPI.getDashboard(),
        reembolsosAPI.getDashboard()
      ]);
      setAnalytics(analyticsRes.data);
      setPendenciasDash(pendenciasRes.data);
      setReembolsosDash(reembolsosRes.data);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadAllData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#004587]"></div>
      </div>
    );
  }

  // Calcular totais de ações pendentes
  const acoesPendentes = {
    solicitacoes: (analytics?.por_status?.pendente || 0) + (analytics?.por_status?.em_analise || 0),
    pendencias: pendenciasDash?.total_abertos || 0,
    reembolsos: (reembolsosDash?.total_aberto || 0) + (reembolsosDash?.total_aguardando || 0)
  };

  const totalAcoes = acoesPendentes.solicitacoes + acoesPendentes.pendencias + acoesPendentes.reembolsos;

  // Dados para gráfico de pizza de status geral
  const statusGeralData = [
    { name: 'Solicitações', value: analytics?.total_pedidos || 0, color: '#004587' },
    { name: 'Pendências', value: pendenciasDash?.total || 0, color: '#F59E0B' },
    { name: 'Reembolsos', value: reembolsosDash?.total || 0, color: '#10B981' }
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-6" data-testid="admin-dashboard">
      {/* Alerta de Retornos Atrasados */}
      <AlertaRetornos variant="banner" />
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Painel de Controle
          </h1>
          <p className="text-gray-600 mt-1">
            Visão geral de todas as operações do SYNAPSE
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Button onClick={() => navigate('/assistente/novo-pedido')}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Solicitação
          </Button>
        </div>
      </div>

      {/* Alerta de Ações Pendentes */}
      {totalAcoes > 0 && (
        <Card className="border-l-4 border-l-amber-500 bg-amber-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-amber-600" />
              <div className="flex-1">
                <p className="font-semibold text-amber-800">
                  Você tem {totalAcoes} {totalAcoes === 1 ? 'ação pendente' : 'ações pendentes'}
                </p>
                <p className="text-sm text-amber-700">
                  {acoesPendentes.solicitacoes > 0 && `${acoesPendentes.solicitacoes} solicitações para analisar`}
                  {acoesPendentes.solicitacoes > 0 && acoesPendentes.pendencias > 0 && ' • '}
                  {acoesPendentes.pendencias > 0 && `${acoesPendentes.pendencias} pendências documentais`}
                  {(acoesPendentes.solicitacoes > 0 || acoesPendentes.pendencias > 0) && acoesPendentes.reembolsos > 0 && ' • '}
                  {acoesPendentes.reembolsos > 0 && `${acoesPendentes.reembolsos} reembolsos em aberto`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cards de Resumo Rápido */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Solicitações */}
        <Card 
          className="cursor-pointer hover:shadow-lg transition-shadow border-t-4 border-t-[#004587]"
          onClick={() => navigate('/admin/pedidos')}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <ClipboardList className="h-4 w-4" />
                Solicitações
              </span>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-[#004587]">
              {analytics?.total_pedidos || 0}
            </div>
            <div className="flex gap-2 mt-2 flex-wrap">
              <Badge variant="outline" className="text-xs">
                {analytics?.por_status?.pendente || 0} pendentes
              </Badge>
              <Badge variant="outline" className="text-xs bg-green-50 text-green-700">
                {analytics?.por_status?.realizado || 0} realizadas
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Pendências Documentais */}
        <Card 
          className="cursor-pointer hover:shadow-lg transition-shadow border-t-4 border-t-amber-500"
          onClick={() => navigate('/pendencias')}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <FileWarning className="h-4 w-4" />
                Pendências
              </span>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600">
              {pendenciasDash?.total_abertos || 0}
            </div>
            <div className="flex gap-2 mt-2 flex-wrap">
              <Badge variant="outline" className="text-xs bg-red-50 text-red-700">
                {pendenciasDash?.total_pendente || 0} aguardando
              </Badge>
              <Badge variant="outline" className="text-xs bg-green-50 text-green-700">
                {pendenciasDash?.total_aprovado || 0} resolvidas
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Reembolsos */}
        <Card 
          className="cursor-pointer hover:shadow-lg transition-shadow border-t-4 border-t-green-500"
          onClick={() => navigate('/reembolsos')}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Wallet className="h-4 w-4" />
                Reembolsos
              </span>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {reembolsosDash?.total || 0}
            </div>
            <div className="flex gap-2 mt-2 flex-wrap">
              <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700">
                {reembolsosDash?.total_aberto || 0} abertos
              </Badge>
              <Badge variant="outline" className="text-xs bg-green-50 text-green-700">
                {reembolsosDash?.total_pago || 0} pagos
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* KPIs */}
        <Card className="border-t-4 border-t-purple-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Tempo Médio</span>
                <span className="font-semibold">{analytics?.tempo_medio_dias || 0} dias</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Taxa Conversão</span>
                <span className="font-semibold">{analytics?.taxa_conversao || 0}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Seção de Detalhamento */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Solicitações por Status */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Solicitações por Status</span>
              <Button variant="ghost" size="sm" onClick={() => navigate('/admin/pedidos')}>
                Ver todas <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { key: 'pendente', label: 'Pendentes', color: 'bg-amber-500', filter: 'pendente' },
                { key: 'em_analise', label: 'Em Análise', color: 'bg-blue-500', filter: 'em_analise' },
                { key: 'documentacao_pendente', label: 'Doc. Pendente', color: 'bg-red-500', filter: 'documentacao_pendente' },
                { key: 'aprovado', label: 'Aprovadas', color: 'bg-green-500', filter: 'aprovado' },
                { key: 'realizado', label: 'Realizadas', color: 'bg-purple-500', filter: 'realizado' },
              ].map(status => (
                <div 
                  key={status.key} 
                  className="flex items-center justify-between cursor-pointer hover:bg-slate-50 p-2 rounded-lg transition-colors -mx-2"
                  onClick={() => navigate(`/admin/pedidos?status=${status.filter}`)}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${status.color}`} />
                    <span className="text-sm">{status.label}</span>
                  </div>
                  <span className="font-semibold">
                    {analytics?.por_status?.[status.key] || 0}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Pendências por Status */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Pendências por Status</span>
              <Button variant="ghost" size="sm" onClick={() => navigate('/pendencias')}>
                Ver todas <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { key: 'total_pendente', label: 'Pendentes', color: 'bg-amber-500' },
                { key: 'total_aguardando', label: 'Aguardando Aluno', color: 'bg-blue-500' },
                { key: 'total_em_analise', label: 'Em Análise', color: 'bg-purple-500' },
                { key: 'total_reenvio', label: 'Reenvio Necessário', color: 'bg-red-500' },
                { key: 'total_aprovado', label: 'Aprovadas', color: 'bg-green-500' },
              ].map(status => (
                <div key={status.key} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${status.color}`} />
                    <span className="text-sm">{status.label}</span>
                  </div>
                  <span className="font-semibold">
                    {pendenciasDash?.[status.key] || 0}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Reembolsos por Status */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Reembolsos por Status</span>
              <Button variant="ghost" size="sm" onClick={() => navigate('/reembolsos')}>
                Ver todos <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { key: 'total_aberto', label: 'Abertos', color: 'bg-amber-500' },
                { key: 'total_aguardando', label: 'Aguardando Dados', color: 'bg-blue-500' },
                { key: 'total_enviado', label: 'No Financeiro', color: 'bg-purple-500' },
                { key: 'total_pago', label: 'Pagos', color: 'bg-green-500' },
                { key: 'total_cancelado', label: 'Cancelados', color: 'bg-gray-400' },
              ].map(status => (
                <div key={status.key} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${status.color}`} />
                    <span className="text-sm">{status.label}</span>
                  </div>
                  <span className="font-semibold">
                    {reembolsosDash?.[status.key] || 0}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribuição Geral */}
        {statusGeralData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Distribuição por Módulo</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusGeralData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {statusGeralData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Top 5 Empresas */}
        {analytics?.top_empresas && analytics.top_empresas.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Top 5 Empresas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.top_empresas} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis 
                      dataKey="empresa" 
                      type="category" 
                      width={100}
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip />
                    <Bar dataKey="total" fill="#004587" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Ações Rápidas */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Ações Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button 
              variant="outline" 
              className="h-auto py-4 flex-col gap-2"
              onClick={() => navigate('/assistente/novo-pedido')}
            >
              <Plus className="h-5 w-5 text-[#004587]" />
              <span className="text-sm">Nova Solicitação</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-auto py-4 flex-col gap-2"
              onClick={() => navigate('/importacao')}
            >
              <Download className="h-5 w-5 text-green-600" />
              <span className="text-sm">Importar Planilha</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-auto py-4 flex-col gap-2"
              onClick={() => navigate('/pendencias')}
            >
              <FileWarning className="h-5 w-5 text-amber-600" />
              <span className="text-sm">Ver Pendências</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-auto py-4 flex-col gap-2"
              onClick={() => navigate('/reembolsos')}
            >
              <Wallet className="h-5 w-5 text-purple-600" />
              <span className="text-sm">Ver Reembolsos</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard;
