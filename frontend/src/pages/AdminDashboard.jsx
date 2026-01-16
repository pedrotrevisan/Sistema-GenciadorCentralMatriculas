import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { pedidosAPI } from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  FunnelChart,
  Funnel,
  LabelList,
  Cell,
  PieChart,
  Pie,
  LineChart,
  Line,
  Legend
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  Users,
  FileText,
  CheckCircle,
  ArrowRight,
  Plus,
  Download,
  RefreshCw
} from 'lucide-react';

const COLORS = ['#004587', '#E30613', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'];

const FUNNEL_COLORS = {
  'pendente': '#F59E0B',
  'em_analise': '#3B82F6', 
  'documentacao_pendente': '#EF4444',
  'aprovado': '#10B981',
  'realizado': '#8B5CF6',
  'exportado': '#004587'
};

const AdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadAnalytics = async () => {
    try {
      const response = await pedidosAPI.getAnalytics();
      setAnalytics(response.data);
    } catch (error) {
      console.error('Erro ao carregar analytics:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadAnalytics();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#004587]"></div>
      </div>
    );
  }

  const tempoMedioStatus = analytics?.tempo_medio_dias > 5 ? 'danger' : 
                          analytics?.tempo_medio_dias > 3 ? 'warning' : 'success';

  const taxaConversaoStatus = analytics?.taxa_conversao >= 80 ? 'success' :
                              analytics?.taxa_conversao >= 50 ? 'warning' : 'danger';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Dashboard Analítico
          </h1>
          <p className="text-gray-600 mt-1">
            Bem-vindo, {user?.nome}! Aqui está o panorama operacional.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Button
            onClick={() => navigate('/admin/novo-pedido')}
            className="bg-[#E30613] hover:bg-[#c00510]"
          >
            <Plus className="w-4 h-4 mr-2" />
            Nova Matrícula
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total de Pedidos */}
        <Card className="border-l-4 border-l-[#004587]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total de Pedidos</p>
                <p className="text-3xl font-bold text-gray-900">{analytics?.total_pedidos || 0}</p>
              </div>
              <div className="p-3 bg-blue-50 rounded-full">
                <FileText className="w-6 h-6 text-[#004587]" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tempo Médio */}
        <Card className={`border-l-4 ${
          tempoMedioStatus === 'success' ? 'border-l-green-500' :
          tempoMedioStatus === 'warning' ? 'border-l-yellow-500' : 'border-l-red-500'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Tempo Médio</p>
                <p className={`text-3xl font-bold ${
                  tempoMedioStatus === 'success' ? 'text-green-600' :
                  tempoMedioStatus === 'warning' ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {analytics?.tempo_medio_dias || 0} dias
                </p>
              </div>
              <div className={`p-3 rounded-full ${
                tempoMedioStatus === 'success' ? 'bg-green-50' :
                tempoMedioStatus === 'warning' ? 'bg-yellow-50' : 'bg-red-50'
              }`}>
                <Clock className={`w-6 h-6 ${
                  tempoMedioStatus === 'success' ? 'text-green-500' :
                  tempoMedioStatus === 'warning' ? 'text-yellow-500' : 'text-red-500'
                }`} />
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">Da criação até exportação</p>
          </CardContent>
        </Card>

        {/* Taxa de Conversão */}
        <Card className={`border-l-4 ${
          taxaConversaoStatus === 'success' ? 'border-l-green-500' :
          taxaConversaoStatus === 'warning' ? 'border-l-yellow-500' : 'border-l-red-500'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Taxa de Conversão</p>
                <p className={`text-3xl font-bold ${
                  taxaConversaoStatus === 'success' ? 'text-green-600' :
                  taxaConversaoStatus === 'warning' ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {analytics?.taxa_conversao || 0}%
                </p>
              </div>
              <div className={`p-3 rounded-full ${
                taxaConversaoStatus === 'success' ? 'bg-green-50' :
                taxaConversaoStatus === 'warning' ? 'bg-yellow-50' : 'bg-red-50'
              }`}>
                {taxaConversaoStatus === 'success' ? 
                  <TrendingUp className="w-6 h-6 text-green-500" /> :
                  <TrendingDown className="w-6 h-6 text-red-500" />
                }
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">Pedidos aprovados/exportados</p>
          </CardContent>
        </Card>

        {/* Alertas Críticos */}
        <Card className={`border-l-4 ${
          analytics?.pedidos_criticos > 0 ? 'border-l-red-500 bg-red-50/30' : 'border-l-green-500'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Pedidos Críticos</p>
                <p className={`text-3xl font-bold ${
                  analytics?.pedidos_criticos > 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {analytics?.pedidos_criticos || 0}
                </p>
              </div>
              <div className={`p-3 rounded-full ${
                analytics?.pedidos_criticos > 0 ? 'bg-red-100' : 'bg-green-50'
              }`}>
                {analytics?.pedidos_criticos > 0 ? 
                  <AlertTriangle className="w-6 h-6 text-red-500" /> :
                  <CheckCircle className="w-6 h-6 text-green-500" />
                }
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              {analytics?.pedidos_criticos > 0 ? 'Parados há mais de 48h!' : 'Nenhum alerta'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos Principais */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Funil de Matrículas */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <ArrowRight className="w-5 h-5 text-[#004587]" />
              Funil de Matrículas
            </CardTitle>
            <p className="text-sm text-gray-500">Visualize onde o processo está travando</p>
          </CardHeader>
          <CardContent>
            {analytics?.funil && analytics.funil.some(f => f.total > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={analytics.funil}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                  <XAxis type="number" />
                  <YAxis dataKey="label" type="category" width={90} tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value) => [value, 'Pedidos']}
                    contentStyle={{ borderRadius: '8px' }}
                  />
                  <Bar dataKey="total" radius={[0, 4, 4, 0]}>
                    {analytics.funil.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={FUNNEL_COLORS[entry.status] || COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-[300px] text-gray-400">
                <FileText className="w-12 h-12 mb-2" />
                <p>Nenhum pedido cadastrado ainda</p>
                <Button
                  variant="link"
                  onClick={() => navigate('/admin/novo-pedido')}
                  className="mt-2"
                >
                  Criar primeiro pedido
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Empresas */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Users className="w-5 h-5 text-[#004587]" />
              Top 5 Empresas
            </CardTitle>
            <p className="text-sm text-gray-500">Empresas com mais matrículas</p>
          </CardHeader>
          <CardContent>
            {analytics?.top_empresas && analytics.top_empresas.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={analytics.top_empresas}
                  margin={{ top: 5, right: 30, left: 20, bottom: 60 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis 
                    dataKey="nome" 
                    angle={-45} 
                    textAnchor="end" 
                    height={60}
                    tick={{ fontSize: 11 }}
                    interval={0}
                  />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [value, 'Matrículas']}
                    contentStyle={{ borderRadius: '8px' }}
                  />
                  <Bar dataKey="total" fill="#004587" radius={[4, 4, 0, 0]}>
                    {analytics.top_empresas.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-[300px] text-gray-400">
                <Users className="w-12 h-12 mb-2" />
                <p>Nenhuma empresa vinculada ainda</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Segunda Linha de Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Matrículas por Mês */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[#004587]" />
              Evolução Mensal
            </CardTitle>
            <p className="text-sm text-gray-500">Matrículas nos últimos 6 meses</p>
          </CardHeader>
          <CardContent>
            {analytics?.matriculas_por_mes && analytics.matriculas_por_mes.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart
                  data={analytics.matriculas_por_mes}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [value, 'Matrículas']}
                    contentStyle={{ borderRadius: '8px' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="total" 
                    stroke="#004587" 
                    strokeWidth={3}
                    dot={{ fill: '#004587', strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-[250px] text-gray-400">
                <TrendingUp className="w-12 h-12 mb-2" />
                <p>Sem dados históricos ainda</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Projetos */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="w-5 h-5 text-[#004587]" />
              Matrículas por Projeto
            </CardTitle>
            <p className="text-sm text-gray-500">Distribuição entre projetos</p>
          </CardHeader>
          <CardContent>
            {analytics?.top_projetos && analytics.top_projetos.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={analytics.top_projetos}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ nome, percent }) => `${nome.substring(0,15)}${nome.length > 15 ? '...' : ''} (${(percent * 100).toFixed(0)}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="total"
                  >
                    {analytics.top_projetos.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value, name, props) => [value, props.payload.nome]}
                    contentStyle={{ borderRadius: '8px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-[250px] text-gray-400">
                <FileText className="w-12 h-12 mb-2" />
                <p>Nenhum projeto vinculado ainda</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Ações Rápidas */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Ações Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
              variant="outline"
              className="h-auto py-4 flex flex-col items-center gap-2 hover:bg-blue-50 hover:border-[#004587]"
              onClick={() => navigate('/admin/novo-pedido')}
            >
              <Plus className="w-6 h-6 text-[#004587]" />
              <span className="text-sm">Nova Matrícula</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex flex-col items-center gap-2 hover:bg-blue-50 hover:border-[#004587]"
              onClick={() => navigate('/admin/pedidos')}
            >
              <FileText className="w-6 h-6 text-[#004587]" />
              <span className="text-sm">Ver Pedidos</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex flex-col items-center gap-2 hover:bg-blue-50 hover:border-[#004587]"
              onClick={() => navigate('/admin/usuarios')}
            >
              <Users className="w-6 h-6 text-[#004587]" />
              <span className="text-sm">Usuários</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex flex-col items-center gap-2 hover:bg-green-50 hover:border-green-600"
              onClick={async () => {
                try {
                  const token = localStorage.getItem('token');
                  const apiUrl = process.env.REACT_APP_BACKEND_URL;
                  const response = await fetch(`${apiUrl}/api/pedidos/exportar/totvs?formato=xlsx`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                  });
                  if (!response.ok) throw new Error('Erro ao exportar');
                  const blob = await response.blob();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `exportacao_totvs_${new Date().toISOString().split('T')[0]}.xlsx`;
                  document.body.appendChild(a);
                  a.click();
                  window.URL.revokeObjectURL(url);
                  a.remove();
                } catch (error) {
                  console.error('Erro ao exportar:', error);
                  alert('Erro ao exportar. Verifique se há pedidos realizados.');
                }
              }}
            >
              <Download className="w-6 h-6 text-green-600" />
              <span className="text-sm">Exportar TOTVS</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Resumo de Alunos */}
      <Card className="bg-gradient-to-r from-[#004587] to-[#0066cc] text-white">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100">Total de Alunos Matriculados</p>
              <p className="text-4xl font-bold mt-1">{analytics?.total_alunos || 0}</p>
              <p className="text-blue-200 text-sm mt-2">
                Em {analytics?.total_pedidos || 0} pedidos de matrícula
              </p>
            </div>
            <div className="bg-white/10 p-4 rounded-full">
              <Users className="w-12 h-12" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard;
