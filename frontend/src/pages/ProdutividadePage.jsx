import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import {
  Activity, Users, FileText, TrendingUp, Award,
  DollarSign, Clock, BarChart3, RefreshCw
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from 'recharts';
import api from '../services/api';

const PERIODOS = [
  { value: '7d', label: '7 dias' },
  { value: '15d', label: '15 dias' },
  { value: '30d', label: '30 dias' },
  { value: '90d', label: '90 dias' },
  { value: 'all', label: 'Todo período' }
];

export default function ProdutividadePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [periodo, setPeriodo] = useState('30d');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/produtividade/dashboard?periodo=${periodo}`);
      setData(res.data);
    } catch (err) {
      console.error('Erro ao carregar produtividade:', err);
    } finally {
      setLoading(false);
    }
  }, [periodo]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="produtividade-loading">
        <RefreshCw className="w-6 h-6 animate-spin text-[#004587]" />
        <span className="ml-2 text-slate-500">Carregando dados...</span>
      </div>
    );
  }

  if (!data) return null;

  const { kpis, membros, evolucao_diaria } = data;

  // Chart data for member ranking
  const rankingData = membros
    .filter(m => m.total_acoes > 0)
    .slice(0, 10)
    .map(m => ({
      nome: m.nome.split(' ').slice(0, 2).join(' '),
      pedidos: m.pedidos_criados,
      auditorias: m.total_auditorias,
      reembolsos: m.reembolsos_tratados,
      total: m.total_acoes
    }));

  return (
    <div className="space-y-6" data-testid="produtividade-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2" data-testid="produtividade-title">
            <Activity className="w-7 h-7 text-[#004587]" />
            Dashboard de Produtividade
          </h1>
          <p className="text-slate-500">Acompanhe o desempenho da equipe - {data.periodo}</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={periodo} onValueChange={setPeriodo}>
            <SelectTrigger className="w-[160px]" data-testid="periodo-select">
              <SelectValue placeholder="Período" />
            </SelectTrigger>
            <SelectContent>
              {PERIODOS.map(p => (
                <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={fetchData} data-testid="refresh-btn">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4" data-testid="kpi-cards">
        <Card className="border-l-4 border-l-[#004587]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <FileText className="w-4 h-4 text-[#004587]" />
              <span className="text-xs text-slate-500">Pedidos</span>
            </div>
            <p className="text-2xl font-bold text-slate-800" data-testid="kpi-pedidos">{kpis.total_pedidos}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span className="text-xs text-slate-500">Aprovados</span>
            </div>
            <p className="text-2xl font-bold text-slate-800" data-testid="kpi-aprovados">{kpis.total_aprovados}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-yellow-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="w-4 h-4 text-yellow-500" />
              <span className="text-xs text-slate-500">Reembolsos</span>
            </div>
            <p className="text-2xl font-bold text-slate-800" data-testid="kpi-reembolsos">{kpis.total_reembolsos}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <BarChart3 className="w-4 h-4 text-purple-500" />
              <span className="text-xs text-slate-500">Auditorias</span>
            </div>
            <p className="text-2xl font-bold text-slate-800" data-testid="kpi-auditorias">{kpis.total_auditorias}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-cyan-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-cyan-500" />
              <span className="text-xs text-slate-500">Média/Dia</span>
            </div>
            <p className="text-2xl font-bold text-slate-800" data-testid="kpi-media">{kpis.media_diaria_pedidos}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Users className="w-4 h-4 text-orange-500" />
              <span className="text-xs text-slate-500">Membros Ativos</span>
            </div>
            <p className="text-2xl font-bold text-slate-800" data-testid="kpi-membros">{kpis.membros_ativos}</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Ranking Chart */}
        {rankingData.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Award className="w-5 h-5 text-[#004587]" />
                Ranking de Atividade
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={rankingData} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="nome" type="category" width={100} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="pedidos" name="Pedidos" fill="#004587" stackId="a" />
                  <Bar dataKey="auditorias" name="Auditorias" fill="#22c55e" stackId="a" />
                  <Bar dataKey="reembolsos" name="Reembolsos" fill="#eab308" stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Daily Evolution */}
        {evolucao_diaria && evolucao_diaria.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                Evolução Diária
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={evolucao_diaria}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="data" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="pedidos" name="Pedidos" stroke="#004587" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="acoes" name="Ações" stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Members Table */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="w-5 h-5 text-[#004587]" />
            Detalhamento por Membro
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="membros-table">
              <thead>
                <tr className="border-b bg-slate-50">
                  <th className="text-left p-3 font-medium text-slate-600">#</th>
                  <th className="text-left p-3 font-medium text-slate-600">Membro</th>
                  <th className="text-left p-3 font-medium text-slate-600">Perfil</th>
                  <th className="text-center p-3 font-medium text-slate-600">Pedidos Criados</th>
                  <th className="text-center p-3 font-medium text-slate-600">Alt. Status</th>
                  <th className="text-center p-3 font-medium text-slate-600">Auditorias</th>
                  <th className="text-center p-3 font-medium text-slate-600">Reembolsos</th>
                  <th className="text-center p-3 font-medium text-slate-600">Total Ações</th>
                </tr>
              </thead>
              <tbody>
                {membros.filter(m => m.total_acoes > 0).length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center p-8 text-slate-400">
                      Nenhuma atividade registrada no período selecionado
                    </td>
                  </tr>
                ) : (
                  membros.filter(m => m.total_acoes > 0).map((m, i) => (
                    <tr key={m.usuario_id} className="border-b hover:bg-slate-50" data-testid={`membro-row-${i}`}>
                      <td className="p-3">
                        {i === 0 && <span className="text-yellow-500 font-bold">1</span>}
                        {i === 1 && <span className="text-slate-400 font-bold">2</span>}
                        {i === 2 && <span className="text-orange-400 font-bold">3</span>}
                        {i > 2 && <span className="text-slate-400">{i + 1}</span>}
                      </td>
                      <td className="p-3">
                        <div className="font-medium text-slate-800">{m.nome}</div>
                      </td>
                      <td className="p-3">
                        <Badge variant="outline" className={
                          m.role === 'admin' ? 'bg-red-50 text-red-700 border-red-200' :
                          m.role === 'assistente' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                          'bg-green-50 text-green-700 border-green-200'
                        }>
                          {m.role || 'N/A'}
                        </Badge>
                      </td>
                      <td className="p-3 text-center font-medium">{m.pedidos_criados}</td>
                      <td className="p-3 text-center">{m.alteracoes_status}</td>
                      <td className="p-3 text-center">{m.total_auditorias}</td>
                      <td className="p-3 text-center">{m.reembolsos_tratados}</td>
                      <td className="p-3 text-center">
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-[#004587]/10 text-[#004587] font-bold text-xs">
                          {m.total_acoes}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
