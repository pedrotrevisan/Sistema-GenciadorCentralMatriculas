import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Separator } from '../components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell
} from 'recharts';
import { toast } from 'sonner';
import api from '../services/api';
import {
  Activity, AlertTriangle, CheckCircle, Clock, Users, FileText,
  TrendingUp, TrendingDown, RefreshCw, Target, Award, BarChart2,
  Calendar, Timer, XCircle, Loader2
} from 'lucide-react';

const CORES = ['#004587', '#E30613', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899'];

const DashboardSLAPage = () => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tiposPS, setTiposPS] = useState([]);

  useEffect(() => {
    carregarDashboard();
    carregarTiposPS();
  }, []);

  const carregarDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/sla/dashboard');
      setDashboard(response.data);
    } catch (err) {
      setError('Erro ao carregar dashboard de SLA');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const carregarTiposPS = async () => {
    try {
      const response = await api.get('/sla/tipos-processo-seletivo');
      setTiposPS(response.data.tipos);
    } catch (err) {
      console.error('Erro ao carregar tipos PS:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-12 h-12 animate-spin text-[#004587]" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Erro</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
        <Button variant="outline" onClick={carregarDashboard} className="mt-2">
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      </Alert>
    );
  }

  const { resumo_geral, metricas_por_status, produtividade_atendentes, sla_por_tipo_ps, evolucao_semanal, alertas_sla } = dashboard || {};

  return (
    <div className="space-y-6" data-testid="dashboard-sla">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Target className="w-7 h-7 text-[#004587]" />
            Dashboard de SLA
          </h1>
          <p className="text-slate-500">Métricas e indicadores de desempenho da CAC</p>
        </div>
        <Button onClick={carregarDashboard} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Atualizar
        </Button>
      </div>

      {/* KPIs Resumo */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <FileText className="w-8 h-8 opacity-80" />
              <div className="text-right">
                <p className="text-3xl font-bold">{resumo_geral?.total_pedidos || 0}</p>
                <p className="text-xs opacity-80">Total Pedidos</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <TrendingUp className="w-8 h-8 opacity-80" />
              <div className="text-right">
                <p className="text-3xl font-bold">{resumo_geral?.pedidos_mes || 0}</p>
                <p className="text-xs opacity-80">Este Mês</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <Clock className="w-8 h-8 opacity-80" />
              <div className="text-right">
                <p className="text-3xl font-bold">{resumo_geral?.pedidos_abertos || 0}</p>
                <p className="text-xs opacity-80">Em Aberto</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <CheckCircle className="w-8 h-8 opacity-80" />
              <div className="text-right">
                <p className="text-3xl font-bold">{resumo_geral?.pedidos_concluidos || 0}</p>
                <p className="text-xs opacity-80">Concluídos</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <Award className="w-8 h-8 opacity-80" />
              <div className="text-right">
                <p className="text-3xl font-bold">{resumo_geral?.taxa_conclusao || 0}%</p>
                <p className="text-xs opacity-80">Taxa Conclusão</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <AlertTriangle className="w-8 h-8 opacity-80" />
              <div className="text-right">
                <p className="text-3xl font-bold">{resumo_geral?.pendencias_ativas || 0}</p>
                <p className="text-xs opacity-80">Pendências</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <XCircle className="w-8 h-8 opacity-80" />
              <div className="text-right">
                <p className="text-3xl font-bold">{resumo_geral?.reembolsos_pendentes || 0}</p>
                <p className="text-xs opacity-80">Reembolsos</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs com conteúdo detalhado */}
      <Tabs defaultValue="visao-geral" className="space-y-4">
        <TabsList>
          <TabsTrigger value="visao-geral">Visão Geral</TabsTrigger>
          <TabsTrigger value="produtividade">Produtividade</TabsTrigger>
          <TabsTrigger value="alertas">Alertas SLA</TabsTrigger>
          <TabsTrigger value="tipos-ps">Por Tipo PS</TabsTrigger>
        </TabsList>

        {/* Tab Visão Geral */}
        <TabsContent value="visao-geral" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Gráfico de Evolução */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-[#004587]" />
                  Evolução Semanal
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={evolucao_semanal || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="semana" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="criados" stroke="#004587" name="Criados" strokeWidth={2} />
                    <Line type="monotone" dataKey="concluidos" stroke="#10b981" name="Concluídos" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Métricas por Status */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <BarChart2 className="w-5 h-5 text-[#004587]" />
                  Por Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={metricas_por_status || []} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="status" type="category" width={120} />
                    <Tooltip />
                    <Bar dataKey="quantidade" fill="#004587" name="Quantidade" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Métricas de SLA por Status */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Timer className="w-5 h-5 text-[#004587]" />
                SLA por Etapa
              </CardTitle>
              <CardDescription>
                Tempo médio em cada status vs SLA configurado
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {metricas_por_status?.map((metrica, index) => (
                  <div key={metrica.status} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium capitalize">
                        {metrica.status.replace(/_/g, ' ')}
                      </span>
                      <div className="flex items-center gap-2">
                        <Badge variant={metrica.dentro_sla ? "default" : "destructive"}>
                          {metrica.tempo_medio_horas}h / {metrica.sla_horas}h
                        </Badge>
                        <span className="text-sm text-slate-500">
                          ({metrica.quantidade} pedidos)
                        </span>
                      </div>
                    </div>
                    <Progress 
                      value={Math.min(metrica.percentual_sla, 100)} 
                      className={`h-2 ${metrica.dentro_sla ? '' : '[&>div]:bg-red-500'}`}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Produtividade */}
        <TabsContent value="produtividade" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="w-5 h-5 text-[#004587]" />
                Ranking de Produtividade (Mês Atual)
              </CardTitle>
              <CardDescription>
                Desempenho dos atendentes por número de pedidos processados
              </CardDescription>
            </CardHeader>
            <CardContent>
              {produtividade_atendentes?.length > 0 ? (
                <div className="space-y-4">
                  {produtividade_atendentes.map((atendente, index) => (
                    <div 
                      key={atendente.responsavel_id || index}
                      className="flex items-center gap-4 p-4 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                    >
                      {/* Posição */}
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                        index === 0 ? 'bg-yellow-500' :
                        index === 1 ? 'bg-slate-400' :
                        index === 2 ? 'bg-amber-600' :
                        'bg-slate-300'
                      }`}>
                        {index + 1}
                      </div>
                      
                      {/* Info */}
                      <div className="flex-1">
                        <p className="font-medium text-slate-800">
                          {atendente.responsavel_nome}
                        </p>
                        <div className="flex gap-4 mt-1 text-sm text-slate-500">
                          <span>{atendente.total_atribuidos} atribuídos</span>
                          <span className="text-green-600">{atendente.concluidos} concluídos</span>
                          <span className="text-orange-600">{atendente.pendentes} pendentes</span>
                          <span className="text-blue-600">{atendente.em_analise} em análise</span>
                        </div>
                      </div>
                      
                      {/* Taxa de Conclusão */}
                      <div className="text-right">
                        <p className="text-2xl font-bold text-[#004587]">
                          {atendente.taxa_conclusao}%
                        </p>
                        <p className="text-xs text-slate-500">taxa conclusão</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Users className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p>Nenhum dado de produtividade disponível</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Alertas */}
        <TabsContent value="alertas" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                Alertas de SLA
              </CardTitle>
              <CardDescription>
                Pedidos e pendências com prazo crítico ou estourado
              </CardDescription>
            </CardHeader>
            <CardContent>
              {alertas_sla?.length > 0 ? (
                <div className="space-y-3">
                  {alertas_sla.map((alerta, index) => (
                    <Alert 
                      key={index}
                      variant={alerta.nivel === 'critico' ? 'destructive' : 'default'}
                      className={alerta.nivel === 'alerta' ? 'border-orange-300 bg-orange-50' : ''}
                    >
                      <AlertTriangle className="h-4 w-4" />
                      <AlertTitle className="flex items-center justify-between">
                        <span>
                          {alerta.tipo === 'analise_atrasada' ? 'Análise Atrasada' : 'Pendência Expirando'}
                        </span>
                        <Badge variant={alerta.nivel === 'critico' ? 'destructive' : 'outline'}>
                          {alerta.nivel.toUpperCase()}
                        </Badge>
                      </AlertTitle>
                      <AlertDescription>
                        <p>{alerta.mensagem}</p>
                        {alerta.protocolo && (
                          <p className="text-sm mt-1">Protocolo: {alerta.protocolo}</p>
                        )}
                        {alerta.responsavel && (
                          <p className="text-sm">Responsável: {alerta.responsavel}</p>
                        )}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
                  <p className="font-medium text-green-600">Nenhum alerta de SLA no momento!</p>
                  <p className="text-sm">Todos os prazos estão sendo cumpridos.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Por Tipo PS */}
        <TabsContent value="tipos-ps" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Gráfico Pizza */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Distribuição por Tipo de PS</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={sla_por_tipo_ps || []}
                      dataKey="quantidade"
                      nameKey="label"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={({ label, percent }) => `${label}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {sla_por_tipo_ps?.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CORES[index % CORES.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Detalhes por Tipo */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Métricas por Processo Seletivo</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {sla_por_tipo_ps?.map((tipo, index) => (
                    <div 
                      key={tipo.tipo_ps}
                      className="p-4 rounded-lg border"
                      style={{ borderLeftColor: CORES[index % CORES.length], borderLeftWidth: '4px' }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{tipo.label}</span>
                        <Badge variant="outline">{tipo.quantidade} pedidos</Badge>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div>
                          <p className="text-slate-500">Concluídos</p>
                          <p className="font-medium text-green-600">{tipo.concluidos}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Cancelados</p>
                          <p className="font-medium text-red-600">{tipo.cancelados}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Conversão</p>
                          <p className="font-medium text-[#004587]">{tipo.taxa_conversao}%</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Lista de Tipos de PS */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Tipos de Processo Seletivo Disponíveis</CardTitle>
              <CardDescription>
                Códigos oficiais do SENAI conforme manual CAC
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tiposPS.map((tipo) => (
                  <div 
                    key={tipo.value}
                    className="p-4 rounded-lg border hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Badge 
                        style={{ 
                          backgroundColor: tipo.cor === 'blue' ? '#004587' :
                                          tipo.cor === 'green' ? '#10b981' :
                                          tipo.cor === 'purple' ? '#8b5cf6' :
                                          tipo.cor === 'orange' ? '#f59e0b' :
                                          tipo.cor === 'teal' ? '#14b8a6' :
                                          '#6b7280'
                        }}
                      >
                        {tipo.label}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-600">{tipo.descricao}</p>
                    {tipo.requer_contrato && (
                      <p className="text-xs text-slate-400 mt-2">Requer contrato</p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DashboardSLAPage;
