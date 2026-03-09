import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { documentosAPI, contatosAPI } from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
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
  Legend,
  AreaChart,
  Area,
  RadialBarChart,
  RadialBar
} from 'recharts';
import {
  TrendingUp,
  Users,
  FileText,
  CheckCircle,
  Clock,
  AlertTriangle,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
  Target,
  Wallet,
  FileWarning,
  Phone,
  MessageCircle
} from 'lucide-react';

const COLORS = {
  primary: '#004587',
  secondary: '#E30613',
  success: '#10B981',
  warning: '#F59E0B',
  purple: '#8B5CF6',
  pink: '#EC4899',
  gray: '#6B7280'
};

const CHART_COLORS = ['#004587', '#10B981', '#F59E0B', '#E30613', '#8B5CF6', '#EC4899'];

const BIDashboardPage = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [contatosData, setContatosData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('visao-geral');

  const loadData = async () => {
    try {
      const [biResponse, contatosResponse] = await Promise.all([
        documentosAPI.getBICompleto(),
        contatosAPI.getStats()
      ]);
      setData(biResponse.data);
      setContatosData(contatosResponse.data);
    } catch (error) {
      console.error('Erro ao carregar dados do BI:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004587] mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando dados do Business Intelligence...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto" />
          <p className="mt-4 text-gray-600">Erro ao carregar dados. Tente novamente.</p>
          <Button onClick={loadData} className="mt-4">Tentar novamente</Button>
        </div>
      </div>
    );
  }

  const { matriculas, evolucao_mensal, reembolsos, pendencias, resumo } = data;

  // Dados para o gráfico de funil
  const funnelData = [
    { name: 'Pendentes', value: matriculas.pendentes, fill: COLORS.warning },
    { name: 'Em Análise', value: matriculas.em_analise, fill: COLORS.primary },
    { name: 'Aprovados', value: matriculas.aprovados, fill: COLORS.success },
    { name: 'Realizados', value: matriculas.realizados, fill: COLORS.purple },
    { name: 'Exportados', value: matriculas.exportados, fill: COLORS.pink }
  ].filter(d => d.value > 0);

  // Dados para o gráfico de pizza de status
  const statusPieData = Object.entries(matriculas.por_status || {}).map(([key, value]) => ({
    name: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value,
    fill: CHART_COLORS[Object.keys(matriculas.por_status).indexOf(key) % CHART_COLORS.length]
  })).filter(d => d.value > 0);

  // Dados para KPI de taxa de conversão
  const taxaConversaoData = [
    { name: 'Taxa', value: matriculas.taxa_conversao, fill: COLORS.success }
  ];

  return (
    <div className="space-y-6" data-testid="bi-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="h-7 w-7 text-[#004587]" />
            Dashboard de Inteligência
          </h1>
          <p className="text-gray-600 mt-1">
            Análise de dados operacionais e KPIs do sistema
          </p>
        </div>
        <Button 
          variant="outline" 
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Atualizar
        </Button>
      </div>

      {/* Cards de KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card 
          className="bg-gradient-to-br from-blue-50 to-white border-blue-200 cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
          onClick={() => navigate('/admin/pedidos')}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Total Matrículas</p>
                <p className="text-3xl font-bold text-blue-900">{resumo.total_matriculas}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-2 flex items-center text-sm">
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                {resumo.matriculas_mes} este mês
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card 
          className="bg-gradient-to-br from-green-50 to-white border-green-200 cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
          onClick={() => navigate('/sla')}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Taxa de Conversão</p>
                <p className="text-3xl font-bold text-green-900">{resumo.taxa_conversao}%</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                <Target className="h-6 w-6 text-green-600" />
              </div>
            </div>
            <div className="mt-2 flex items-center text-sm text-green-600">
              {resumo.taxa_conversao > 50 ? (
                <>
                  <ArrowUpRight className="h-4 w-4 mr-1" />
                  Acima da meta
                </>
              ) : (
                <>
                  <ArrowDownRight className="h-4 w-4 mr-1" />
                  Abaixo da meta
                </>
              )}
            </div>
          </CardContent>
        </Card>

        <Card 
          className="bg-gradient-to-br from-amber-50 to-white border-amber-200 cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
          onClick={() => navigate('/pendencias')}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-amber-600">Pendências Abertas</p>
                <p className="text-3xl font-bold text-amber-900">{resumo.pendencias_abertas}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-amber-100 flex items-center justify-center">
                <FileWarning className="h-6 w-6 text-amber-600" />
              </div>
            </div>
            <div className="mt-2">
              <span className="text-amber-700 text-sm">Ver pendências →</span>
            </div>
          </CardContent>
        </Card>

        <Card 
          className="bg-gradient-to-br from-purple-50 to-white border-purple-200 cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
          onClick={() => navigate('/reembolsos')}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Reembolsos Pendentes</p>
                <p className="text-3xl font-bold text-purple-900">{resumo.reembolsos_pendentes}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
                <Wallet className="h-6 w-6 text-purple-600" />
              </div>
            </div>
            <div className="mt-2">
              <span className="text-purple-700 text-sm">Ver reembolsos →</span>
            </div>
          </CardContent>
        </Card>

        <Card 
          className="bg-gradient-to-br from-pink-50 to-white border-pink-200 cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
          onClick={() => navigate('/pendencias')}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-pink-600">Aprovação Docs</p>
                <p className="text-3xl font-bold text-pink-900">{pendencias.taxa_aprovacao}%</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-pink-100 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-pink-600" />
              </div>
            </div>
            <div className="mt-2 text-sm text-pink-600">
              {pendencias.aprovados} de {pendencias.total} documentos
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs de Análise */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
          <TabsTrigger value="visao-geral" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            <span className="hidden sm:inline">Visão Geral</span>
          </TabsTrigger>
          <TabsTrigger value="matriculas" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">Matrículas</span>
          </TabsTrigger>
          <TabsTrigger value="contatos" className="flex items-center gap-2">
            <Phone className="h-4 w-4" />
            <span className="hidden sm:inline">Contatos</span>
          </TabsTrigger>
          <TabsTrigger value="documentos" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            <span className="hidden sm:inline">Documentos</span>
          </TabsTrigger>
          <TabsTrigger value="financeiro" className="flex items-center gap-2">
            <Wallet className="h-4 w-4" />
            <span className="hidden sm:inline">Financeiro</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab Visão Geral */}
        <TabsContent value="visao-geral" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Evolução Mensal */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-[#004587]" />
                  Evolução de Matrículas
                </CardTitle>
                <CardDescription>Últimos 6 meses</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={evolucao_mensal}>
                      <defs>
                        <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#004587" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#004587" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorConvertidos" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="mes_label" tick={{ fill: '#6B7280', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#6B7280', fontSize: 12 }} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #E5E7EB',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                      />
                      <Legend />
                      <Area 
                        type="monotone" 
                        dataKey="total" 
                        name="Total" 
                        stroke="#004587" 
                        fillOpacity={1} 
                        fill="url(#colorTotal)" 
                        strokeWidth={2}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="convertidos" 
                        name="Convertidos" 
                        stroke="#10B981" 
                        fillOpacity={1} 
                        fill="url(#colorConvertidos)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Distribuição por Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChartIcon className="h-5 w-5 text-[#004587]" />
                  Distribuição por Status
                </CardTitle>
                <CardDescription>Matrículas por situação atual</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={statusPieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {statusPieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value, name) => [value, name]}
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #E5E7EB',
                          borderRadius: '8px'
                        }}
                      />
                      <Legend 
                        verticalAlign="bottom" 
                        height={36}
                        formatter={(value) => <span className="text-sm text-gray-600">{value}</span>}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Resumo de Módulos */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-gray-600">Matrículas</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Total</span>
                    <span className="font-semibold">{matriculas.total_pedidos}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Pendentes</span>
                    <Badge variant="outline" className="bg-amber-50">{matriculas.pendentes}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Aprovados</span>
                    <Badge variant="outline" className="bg-green-50">{matriculas.aprovados}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Realizados</span>
                    <Badge variant="outline" className="bg-blue-50">{matriculas.realizados}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-gray-600">Pendências Documentais</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Total</span>
                    <span className="font-semibold">{pendencias.total}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Em Aberto</span>
                    <Badge variant="outline" className="bg-amber-50">{pendencias.em_aberto}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Aprovados</span>
                    <Badge variant="outline" className="bg-green-50">{pendencias.aprovados}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Taxa Aprovação</span>
                    <Badge variant="outline" className="bg-blue-50">{pendencias.taxa_aprovacao}%</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-gray-600">Reembolsos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Total</span>
                    <span className="font-semibold">{reembolsos.total}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Abertos</span>
                    <Badge variant="outline" className="bg-amber-50">{reembolsos.abertos}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">No Financeiro</span>
                    <Badge variant="outline" className="bg-purple-50">{reembolsos.no_financeiro}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Pagos</span>
                    <Badge variant="outline" className="bg-green-50">{reembolsos.pagos}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab Matrículas */}
        <TabsContent value="matriculas" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Funil de Conversão */}
            <Card>
              <CardHeader>
                <CardTitle>Funil de Conversão</CardTitle>
                <CardDescription>Jornada da matrícula</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={funnelData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis type="number" tick={{ fill: '#6B7280', fontSize: 12 }} />
                      <YAxis 
                        dataKey="name" 
                        type="category" 
                        width={100}
                        tick={{ fill: '#6B7280', fontSize: 12 }}
                      />
                      <Tooltip />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {funnelData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Taxa de Conversão Radial */}
            <Card>
              <CardHeader>
                <CardTitle>Taxa de Conversão</CardTitle>
                <CardDescription>Meta: 70%</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart
                      cx="50%"
                      cy="50%"
                      innerRadius="60%"
                      outerRadius="90%"
                      barSize={20}
                      data={[{ name: 'Taxa', value: matriculas.taxa_conversao, fill: matriculas.taxa_conversao >= 70 ? COLORS.success : COLORS.warning }]}
                      startAngle={180}
                      endAngle={0}
                    >
                      <RadialBar
                        background
                        dataKey="value"
                        cornerRadius={10}
                      />
                      <text
                        x="50%"
                        y="50%"
                        textAnchor="middle"
                        dominantBaseline="middle"
                        className="text-3xl font-bold"
                        fill="#1F2937"
                      >
                        {matriculas.taxa_conversao}%
                      </text>
                    </RadialBarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detalhamento por Status */}
          <Card>
            <CardHeader>
              <CardTitle>Detalhamento por Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {Object.entries(matriculas.por_status || {}).map(([status, count], index) => (
                  <div 
                    key={status}
                    className="p-4 rounded-lg border bg-gray-50 text-center"
                  >
                    <div 
                      className="w-3 h-3 rounded-full mx-auto mb-2"
                      style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
                    />
                    <p className="text-2xl font-bold text-gray-900">{count}</p>
                    <p className="text-xs text-gray-500 capitalize">{status.replace('_', ' ')}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Contatos */}
        <TabsContent value="contatos" className="space-y-6">
          {contatosData ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6 text-center">
                    <Phone className="h-8 w-8 mx-auto text-gray-400 mb-2" />
                    <p className="text-3xl font-bold text-gray-900">{contatosData.total}</p>
                    <p className="text-sm text-gray-500">Total de Contatos</p>
                  </CardContent>
                </Card>
                <Card className="border-green-200 bg-green-50/50">
                  <CardContent className="pt-6 text-center">
                    <CheckCircle className="h-8 w-8 mx-auto text-green-500 mb-2" />
                    <p className="text-3xl font-bold text-green-700">{contatosData.sucesso}</p>
                    <p className="text-sm text-green-600">Com Sucesso</p>
                  </CardContent>
                </Card>
                <Card className="border-amber-200 bg-amber-50/50">
                  <CardContent className="pt-6 text-center">
                    <Clock className="h-8 w-8 mx-auto text-amber-500 mb-2" />
                    <p className="text-3xl font-bold text-amber-700">{contatosData.retornos_pendentes}</p>
                    <p className="text-sm text-amber-600">Retornos Pendentes</p>
                  </CardContent>
                </Card>
                <Card className="border-blue-200 bg-blue-50/50">
                  <CardContent className="pt-6 text-center">
                    <Activity className="h-8 w-8 mx-auto text-blue-500 mb-2" />
                    <p className="text-3xl font-bold text-blue-700">{contatosData.contatos_hoje}</p>
                    <p className="text-sm text-blue-600">Contatos Hoje</p>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Gráfico por Tipo de Contato */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <PieChartIcon className="h-5 w-5 text-[#004587]" />
                      Contatos por Tipo
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={Object.entries(contatosData.por_tipo || {}).map(([tipo, count], index) => ({
                              name: tipo === 'ligacao' ? 'Ligação' : 
                                    tipo === 'whatsapp' ? 'WhatsApp' :
                                    tipo === 'email' ? 'E-mail' :
                                    tipo === 'presencial' ? 'Presencial' :
                                    tipo === 'sms' ? 'SMS' : 'Outro',
                              value: count,
                              fill: CHART_COLORS[index % CHART_COLORS.length]
                            }))}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={80}
                            paddingAngle={2}
                            dataKey="value"
                          >
                            {Object.entries(contatosData.por_tipo || {}).map((_, index) => (
                              <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Gráfico por Resultado */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-[#004587]" />
                      Contatos por Resultado
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={Object.entries(contatosData.por_resultado || {}).map(([resultado, count]) => ({
                            name: resultado === 'sucesso' ? 'Sucesso' :
                                  resultado === 'nao_atendeu' ? 'Não Atendeu' :
                                  resultado === 'sem_resposta' ? 'Sem Resposta' :
                                  resultado === 'agendado' ? 'Agendado' :
                                  resultado === 'caixa_postal' ? 'Caixa Postal' :
                                  resultado === 'numero_errado' ? 'Nº Errado' : resultado,
                            value: count,
                            fill: resultado === 'sucesso' ? COLORS.success :
                                  resultado === 'agendado' ? COLORS.purple :
                                  resultado === 'sem_resposta' ? COLORS.warning : COLORS.secondary
                          }))}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                          <XAxis dataKey="name" tick={{ fill: '#6B7280', fontSize: 11 }} />
                          <YAxis tick={{ fill: '#6B7280', fontSize: 12 }} />
                          <Tooltip />
                          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                            {Object.entries(contatosData.por_resultado || {}).map(([resultado], index) => (
                              <Cell 
                                key={`cell-${index}`} 
                                fill={resultado === 'sucesso' ? COLORS.success :
                                      resultado === 'agendado' ? COLORS.purple :
                                      resultado === 'sem_resposta' ? COLORS.warning : COLORS.secondary}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Taxa de Sucesso */}
              <Card>
                <CardHeader>
                  <CardTitle>Taxa de Sucesso nos Contatos</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="relative pt-1">
                    <div className="flex mb-2 items-center justify-between">
                      <div>
                        <span className={`text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full ${
                          contatosData.taxa_sucesso >= 50 ? 'text-green-600 bg-green-200' : 'text-amber-600 bg-amber-200'
                        }`}>
                          {contatosData.taxa_sucesso}% Sucesso
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-semibold inline-block text-gray-600">
                          {contatosData.sucesso} de {contatosData.total} contatos
                        </span>
                      </div>
                    </div>
                    <div className="overflow-hidden h-4 text-xs flex rounded-full bg-gray-200">
                      <div 
                        style={{ width: `${contatosData.taxa_sucesso}%` }}
                        className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center transition-all duration-500 ${
                          contatosData.taxa_sucesso >= 50 ? 'bg-green-500' : 'bg-amber-500'
                        }`}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="pt-6 text-center">
                <MessageCircle className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">Nenhum dado de contatos disponível</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab Documentos */}
        <TabsContent value="documentos" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6 text-center">
                <FileText className="h-8 w-8 mx-auto text-gray-400 mb-2" />
                <p className="text-3xl font-bold text-gray-900">{pendencias.total}</p>
                <p className="text-sm text-gray-500">Total de Documentos</p>
              </CardContent>
            </Card>
            <Card className="border-amber-200 bg-amber-50/50">
              <CardContent className="pt-6 text-center">
                <Clock className="h-8 w-8 mx-auto text-amber-500 mb-2" />
                <p className="text-3xl font-bold text-amber-700">{pendencias.pendentes}</p>
                <p className="text-sm text-amber-600">Pendentes</p>
              </CardContent>
            </Card>
            <Card className="border-blue-200 bg-blue-50/50">
              <CardContent className="pt-6 text-center">
                <Activity className="h-8 w-8 mx-auto text-blue-500 mb-2" />
                <p className="text-3xl font-bold text-blue-700">{pendencias.em_analise}</p>
                <p className="text-sm text-blue-600">Em Análise</p>
              </CardContent>
            </Card>
            <Card className="border-green-200 bg-green-50/50">
              <CardContent className="pt-6 text-center">
                <CheckCircle className="h-8 w-8 mx-auto text-green-500 mb-2" />
                <p className="text-3xl font-bold text-green-700">{pendencias.aprovados}</p>
                <p className="text-sm text-green-600">Aprovados</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Taxa de Aprovação de Documentos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative pt-1">
                <div className="flex mb-2 items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-green-600 bg-green-200">
                      {pendencias.taxa_aprovacao}% Aprovação
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold inline-block text-gray-600">
                      {pendencias.aprovados} / {pendencias.total}
                    </span>
                  </div>
                </div>
                <div className="overflow-hidden h-4 text-xs flex rounded-full bg-gray-200">
                  <div 
                    style={{ width: `${pendencias.taxa_aprovacao}%` }}
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-green-500 transition-all duration-500"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Financeiro */}
        <TabsContent value="financeiro" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6 text-center">
                <Wallet className="h-8 w-8 mx-auto text-gray-400 mb-2" />
                <p className="text-3xl font-bold text-gray-900">{reembolsos.total}</p>
                <p className="text-sm text-gray-500">Total de Reembolsos</p>
              </CardContent>
            </Card>
            <Card className="border-amber-200 bg-amber-50/50">
              <CardContent className="pt-6 text-center">
                <Clock className="h-8 w-8 mx-auto text-amber-500 mb-2" />
                <p className="text-3xl font-bold text-amber-700">{reembolsos.abertos}</p>
                <p className="text-sm text-amber-600">Abertos</p>
              </CardContent>
            </Card>
            <Card className="border-purple-200 bg-purple-50/50">
              <CardContent className="pt-6 text-center">
                <Activity className="h-8 w-8 mx-auto text-purple-500 mb-2" />
                <p className="text-3xl font-bold text-purple-700">{reembolsos.no_financeiro}</p>
                <p className="text-sm text-purple-600">No Financeiro</p>
              </CardContent>
            </Card>
            <Card className="border-green-200 bg-green-50/50">
              <CardContent className="pt-6 text-center">
                <CheckCircle className="h-8 w-8 mx-auto text-green-500 mb-2" />
                <p className="text-3xl font-bold text-green-700">{reembolsos.pagos}</p>
                <p className="text-sm text-green-600">Pagos</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Fluxo de Reembolsos</CardTitle>
              <CardDescription>Status do pipeline de reembolsos</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={[
                      { name: 'Abertos', value: reembolsos.abertos, fill: COLORS.warning },
                      { name: 'Aguardando Dados', value: reembolsos.aguardando, fill: COLORS.primary },
                      { name: 'No Financeiro', value: reembolsos.no_financeiro, fill: COLORS.purple },
                      { name: 'Pagos', value: reembolsos.pagos, fill: COLORS.success },
                      { name: 'Cancelados', value: reembolsos.cancelados, fill: COLORS.gray }
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="name" tick={{ fill: '#6B7280', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#6B7280', fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {[
                        { fill: COLORS.warning },
                        { fill: COLORS.primary },
                        { fill: COLORS.purple },
                        { fill: COLORS.success },
                        { fill: COLORS.gray }
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {reembolsos.com_retencao > 0 && (
            <Card className="border-red-200 bg-red-50/30">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-6 w-6 text-red-500" />
                  <div>
                    <p className="font-semibold text-red-800">
                      {reembolsos.com_retencao} reembolsos com retenção de 10%
                    </p>
                    <p className="text-sm text-red-600">
                      Casos de desistência do aluno
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BIDashboardPage;
