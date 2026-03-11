import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import api from '../services/api';
import {
  GraduationCap,
  Users,
  TrendingUp,
  AlertTriangle,
  Plus,
  RefreshCw,
  Search,
  Sun,
  Moon,
  Clock,
  CheckCircle,
  BarChart3,
  Download,
  Calendar,
  Copy
} from 'lucide-react';

export default function PainelVagasPage() {
  const [dashboard, setDashboard] = useState(null);
  const [turmas, setTurmas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtroTurno, setFiltroTurno] = useState('');
  const [filtroPeriodo, setFiltroPeriodo] = useState('');
  const [periodos, setPeriodos] = useState([]);
  const [busca, setBusca] = useState('');
  const [showNovaTurma, setShowNovaTurma] = useState(false);
  const [showDuplicar, setShowDuplicar] = useState(false);
  const [duplicarDestino, setDuplicarDestino] = useState('');
  const [duplicarLoading, setDuplicarLoading] = useState(false);
  const [novaTurma, setNovaTurma] = useState({
    codigo_turma: '',
    nome_curso: '',
    turno: 'NOTURNO',
    vagas_totais: 40,
    vagas_ocupadas: 0,
    periodo_letivo: '2026.1',
    modalidade: 'CHP'
  });

  const carregarDados = async () => {
    try {
      setLoading(true);
      const params = {
        turno: filtroTurno || undefined,
        busca: busca || undefined,
        periodo: filtroPeriodo || undefined
      };
      const [dashRes, turmasRes] = await Promise.all([
        api.get('/painel-vagas/dashboard', { params: { periodo: filtroPeriodo || undefined } }),
        api.get('/painel-vagas/turmas', { params })
      ]);
      setDashboard(dashRes.data);
      setTurmas(turmasRes.data.turmas);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar dados do painel');
    } finally {
      setLoading(false);
    }
  };

  const carregarPeriodos = async () => {
    try {
      const res = await api.get('/painel-vagas/periodos');
      const lista = res.data.periodos || [];
      setPeriodos(lista);
      if (lista.length > 0 && !filtroPeriodo) {
        setFiltroPeriodo(lista[0]);
      }
    } catch (err) {
      console.error('Erro ao carregar períodos:', err);
    }
  };

  useEffect(() => {
    carregarPeriodos();
  }, []);

  useEffect(() => {
    if (filtroPeriodo || periodos.length === 0) {
      carregarDados();
    }
  }, [filtroTurno, filtroPeriodo]);

  const handleBusca = (e) => {
    e.preventDefault();
    carregarDados();
  };

  const importarCursos = async () => {
    try {
      const res = await api.post('/painel-vagas/importar-cimatec-2026');
      toast.success(res.data.message);
      carregarDados();
    } catch (error) {
      toast.error('Erro ao importar cursos');
    }
  };

  const criarTurma = async () => {
    try {
      if (!novaTurma.codigo_turma || !novaTurma.nome_curso) {
        toast.error('Código e nome do curso são obrigatórios');
        return;
      }
      await api.post('/painel-vagas/turmas', null, { params: novaTurma });
      toast.success('Turma criada com sucesso!');
      setShowNovaTurma(false);
      setNovaTurma({
        codigo_turma: '',
        nome_curso: '',
        turno: 'NOTURNO',
        vagas_totais: 40,
        vagas_ocupadas: 0,
        periodo_letivo: '2026.1',
        modalidade: 'CHP'
      });
      carregarDados();
    } catch (error) {
      toast.error('Erro ao criar turma');
    }
  };

  const atualizarOcupacao = async (turmaId, novaOcupacao) => {
    try {
      await api.put(`/painel-vagas/turmas/${turmaId}/ocupacao`, null, {
        params: { vagas_ocupadas: novaOcupacao }
      });
      toast.success('Ocupação atualizada!');
      carregarDados();
    } catch (error) {
      toast.error('Erro ao atualizar ocupação');
    }
  };

  const duplicarPeriodo = async () => {
    if (!duplicarDestino.trim()) {
      toast.error('Informe o período de destino');
      return;
    }
    if (!filtroPeriodo) {
      toast.error('Selecione um período de origem no filtro');
      return;
    }
    setDuplicarLoading(true);
    try {
      const res = await api.post('/painel-vagas/duplicar-periodo', null, {
        params: { periodo_origem: filtroPeriodo, periodo_destino: duplicarDestino.trim() }
      });
      toast.success(res.data.message);
      setShowDuplicar(false);
      setDuplicarDestino('');
      await carregarPeriodos();
      setFiltroPeriodo(duplicarDestino.trim());
    } catch (error) {
      const msg = error.response?.data?.detail || 'Erro ao duplicar período';
      toast.error(msg);
    } finally {
      setDuplicarLoading(false);
    }
  };

  const getCorOcupacao = (percentual) => {
    if (percentual >= 100) return 'bg-red-500';
    if (percentual >= 85) return 'bg-amber-500';
    if (percentual >= 50) return 'bg-blue-500';
    return 'bg-green-500';
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'lotado':
        return <Badge className="bg-red-500 text-white">LOTADO</Badge>;
      case 'lotando':
        return <Badge className="bg-amber-500 text-white">LOTANDO</Badge>;
      default:
        return <Badge className="bg-green-500 text-white">DISPONÍVEL</Badge>;
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="painel-vagas-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <GraduationCap className="h-7 w-7 text-blue-600" />
            Painel de Vagas
          </h1>
          <div className="text-slate-500 mt-1 flex items-center gap-2">
            Controle visual de ocupação por curso e turma
            {filtroPeriodo && <Badge variant="outline" className="text-[#004587] border-[#004587]">{filtroPeriodo}</Badge>}
          </div>
        </div>
        <div className="flex gap-2 flex-wrap items-center">
          <Select value={filtroPeriodo || "all"} onValueChange={(v) => setFiltroPeriodo(v === "all" ? "" : v)}>
            <SelectTrigger className="w-[180px]" data-testid="select-periodo">
              <Calendar className="h-4 w-4 mr-2 text-slate-500" />
              <SelectValue placeholder="Período Letivo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os Períodos</SelectItem>
              {periodos.map(p => (
                <SelectItem key={p} value={p}>{p}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={carregarDados} data-testid="btn-refresh">
            <RefreshCw className="h-4 w-4 mr-2" />
            Atualizar
          </Button>
          <Button onClick={() => setShowNovaTurma(true)} data-testid="btn-nova-turma">
            <Plus className="h-4 w-4 mr-2" />
            Nova Turma
          </Button>
          <Button variant="outline" onClick={() => setShowDuplicar(true)} data-testid="btn-duplicar-periodo">
            <Copy className="h-4 w-4 mr-2" />
            Novo Período
          </Button>
        </div>
      </div>

      {/* Dashboard Cards */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="p-4 text-center">
              <GraduationCap className="w-8 h-8 mx-auto opacity-80 mb-2" />
              <p className="text-3xl font-bold">{dashboard.resumo.total_turmas}</p>
              <p className="text-sm opacity-80">Turmas</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
            <CardContent className="p-4 text-center">
              <Users className="w-8 h-8 mx-auto opacity-80 mb-2" />
              <p className="text-3xl font-bold">{dashboard.resumo.total_vagas}</p>
              <p className="text-sm opacity-80">Total Vagas</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardContent className="p-4 text-center">
              <CheckCircle className="w-8 h-8 mx-auto opacity-80 mb-2" />
              <p className="text-3xl font-bold">{dashboard.resumo.total_ocupadas}</p>
              <p className="text-sm opacity-80">Ocupadas</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardContent className="p-4 text-center">
              <TrendingUp className="w-8 h-8 mx-auto opacity-80 mb-2" />
              <p className="text-3xl font-bold">{dashboard.resumo.vagas_disponiveis}</p>
              <p className="text-sm opacity-80">Disponíveis</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
            <CardContent className="p-4 text-center">
              <BarChart3 className="w-8 h-8 mx-auto opacity-80 mb-2" />
              <p className="text-3xl font-bold">{dashboard.resumo.percentual_ocupacao}%</p>
              <p className="text-sm opacity-80">Ocupação Geral</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white">
            <CardContent className="p-4 text-center">
              <AlertTriangle className="w-8 h-8 mx-auto opacity-80 mb-2" />
              <p className="text-3xl font-bold">{dashboard.resumo.turmas_lotando}</p>
              <p className="text-sm opacity-80">Lotando</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Ocupação por Curso - Visualização Principal */}
      {dashboard && dashboard.por_curso.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              Ocupação por Curso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboard.por_curso
                .sort((a, b) => b.percentual - a.percentual)
                .map((curso, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between items-center text-sm">
                      <span className="font-medium text-slate-700 truncate max-w-[60%]">
                        {curso.curso}
                      </span>
                      <span className="text-slate-500">
                        {curso.vagas_ocupadas}/{curso.vagas_totais} vagas 
                        <span className="ml-2 font-semibold text-slate-700">
                          ({curso.percentual}%)
                        </span>
                      </span>
                    </div>
                    <div className="h-6 bg-slate-100 rounded-full overflow-hidden relative">
                      <div
                        className={`h-full ${getCorOcupacao(curso.percentual)} transition-all duration-500`}
                        style={{ width: `${Math.min(curso.percentual, 100)}%` }}
                      />
                      <span className="absolute inset-0 flex items-center justify-center text-xs font-medium">
                        {curso.vagas_disponiveis > 0 
                          ? `${curso.vagas_disponiveis} disponíveis`
                          : 'LOTADO'}
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Ocupação por Turno */}
      {dashboard && dashboard.por_turno.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {dashboard.por_turno.map((turno, idx) => (
            <Card key={idx} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-full ${turno.turno === 'MATUTINO' ? 'bg-amber-100' : turno.turno === 'VESPERTINO' ? 'bg-orange-100' : 'bg-indigo-100'}`}>
                    {turno.turno === 'MATUTINO' ? (
                      <Sun className="h-6 w-6 text-amber-600" />
                    ) : turno.turno === 'VESPERTINO' ? (
                      <Clock className="h-6 w-6 text-orange-600" />
                    ) : (
                      <Moon className="h-6 w-6 text-indigo-600" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-slate-700">{turno.turno}</p>
                    <p className="text-sm text-slate-500">
                      {turno.vagas_ocupadas}/{turno.vagas_totais} vagas ocupadas
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-slate-700">{turno.percentual}%</p>
                    <Progress value={turno.percentual} className="w-24 h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Alertas */}
      {dashboard && dashboard.alertas.length > 0 && (
        <Card className="border-amber-200 bg-amber-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2 text-amber-700">
              <AlertTriangle className="h-5 w-5" />
              Alertas - Turmas Lotando
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dashboard.alertas.map((alerta, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-white rounded-lg border border-amber-200">
                  <div>
                    <p className="font-medium text-slate-700">{alerta.curso}</p>
                    <p className="text-sm text-slate-500">Turma: {alerta.codigo} | {alerta.turno}</p>
                  </div>
                  <div className="text-right">
                    <Badge className={alerta.status === 'lotado' ? 'bg-red-500' : 'bg-amber-500'}>
                      {alerta.percentual}%
                    </Badge>
                    <p className="text-xs text-slate-500 mt-1">
                      {alerta.vagas_disponiveis} vaga(s) restante(s)
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filtros e Lista de Turmas */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <CardTitle className="text-lg">Lista de Turmas</CardTitle>
            <div className="flex gap-2 flex-wrap">
              <form onSubmit={handleBusca} className="flex gap-2">
                <Input
                  placeholder="Buscar curso..."
                  value={busca}
                  onChange={(e) => setBusca(e.target.value)}
                  className="w-[200px]"
                />
                <Button type="submit" size="sm" variant="outline">
                  <Search className="h-4 w-4" />
                </Button>
              </form>
              <Select value={filtroTurno || "all"} onValueChange={(v) => setFiltroTurno(v === "all" ? "" : v)}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Turno" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos Turnos</SelectItem>
                  <SelectItem value="MATUTINO">Matutino</SelectItem>
                  <SelectItem value="VESPERTINO">Vespertino</SelectItem>
                  <SelectItem value="NOTURNO">Noturno</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b text-left text-sm text-slate-500">
                  <th className="pb-2 font-medium">Código</th>
                  <th className="pb-2 font-medium">Curso</th>
                  <th className="pb-2 font-medium">Turno</th>
                  <th className="pb-2 font-medium text-center">Vagas</th>
                  <th className="pb-2 font-medium text-center">Ocupadas</th>
                  <th className="pb-2 font-medium text-center">Disponíveis</th>
                  <th className="pb-2 font-medium">Ocupação</th>
                  <th className="pb-2 font-medium">Período</th>
                  <th className="pb-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {turmas.map((turma) => (
                  <tr key={turma.id} className="border-b hover:bg-slate-50 text-sm">
                    <td className="py-3 font-mono text-xs">{turma.codigo_turma}</td>
                    <td className="py-3 font-medium">{turma.nome_curso}</td>
                    <td className="py-3">
                      <Badge variant="outline" className="text-xs">
                        {turma.turno === 'MATUTINO' && <Sun className="h-3 w-3 mr-1" />}
                        {turma.turno === 'NOTURNO' && <Moon className="h-3 w-3 mr-1" />}
                        {turma.turno}
                      </Badge>
                    </td>
                    <td className="py-3 text-center font-semibold">{turma.vagas_totais}</td>
                    <td className="py-3 text-center">{turma.vagas_ocupadas}</td>
                    <td className="py-3 text-center font-semibold text-green-600">{turma.vagas_disponiveis}</td>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <Progress value={turma.percentual} className="w-20 h-2" />
                        <span className="text-xs font-medium">{turma.percentual}%</span>
                      </div>
                    </td>
                    <td className="py-3">
                      <Badge variant="outline" className="text-xs font-mono">{turma.periodo_letivo || '-'}</Badge>
                    </td>
                    <td className="py-3">{getStatusBadge(turma.status_ocupacao)}</td>
                  </tr>
                ))}
                {turmas.length === 0 && (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-slate-500">
                      Nenhuma turma encontrada. 
                      <Button variant="link" onClick={importarCursos} className="ml-2">
                        Importar cursos CIMATEC
                      </Button>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Modal Nova Turma */}
      <Dialog open={showNovaTurma} onOpenChange={setShowNovaTurma}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Nova Turma</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Código da Turma *</Label>
              <Input
                placeholder="Ex: B101622"
                value={novaTurma.codigo_turma}
                onChange={(e) => setNovaTurma({ ...novaTurma, codigo_turma: e.target.value })}
              />
            </div>
            <div>
              <Label>Nome do Curso *</Label>
              <Input
                placeholder="Ex: Técnico em Mecânica"
                value={novaTurma.nome_curso}
                onChange={(e) => setNovaTurma({ ...novaTurma, nome_curso: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Turno</Label>
                <Select
                  value={novaTurma.turno}
                  onValueChange={(v) => setNovaTurma({ ...novaTurma, turno: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MATUTINO">Matutino</SelectItem>
                    <SelectItem value="VESPERTINO">Vespertino</SelectItem>
                    <SelectItem value="NOTURNO">Noturno</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Modalidade</Label>
                <Select
                  value={novaTurma.modalidade}
                  onValueChange={(v) => setNovaTurma({ ...novaTurma, modalidade: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CHP">CHP - Cursos Técnicos</SelectItem>
                    <SelectItem value="CAI">CAI - Aprendizagem</SelectItem>
                    <SelectItem value="BMP">BMP - Brasil + Produtivo</SelectItem>
                    <SelectItem value="CQP">CQP - Qualificação</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Vagas Totais</Label>
                <Input
                  type="number"
                  value={novaTurma.vagas_totais}
                  onChange={(e) => setNovaTurma({ ...novaTurma, vagas_totais: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <Label>Já Ocupadas</Label>
                <Input
                  type="number"
                  value={novaTurma.vagas_ocupadas}
                  onChange={(e) => setNovaTurma({ ...novaTurma, vagas_ocupadas: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>
            <div>
              <Label>Período Letivo</Label>
              <Input
                placeholder="Ex: 2026.1"
                value={novaTurma.periodo_letivo}
                onChange={(e) => setNovaTurma({ ...novaTurma, periodo_letivo: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNovaTurma(false)}>Cancelar</Button>
            <Button onClick={criarTurma}>Criar Turma</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Duplicar Período */}
      <Dialog open={showDuplicar} onOpenChange={setShowDuplicar}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Copy className="h-5 w-5 text-[#004587]" />
              Duplicar Turmas para Novo Período
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
              Todas as turmas do período de origem serão copiadas para o novo período com <strong>vagas ocupadas zeradas</strong>.
            </div>
            <div>
              <Label>Período de Origem</Label>
              <Input
                value={filtroPeriodo || 'Nenhum selecionado'}
                disabled
                className="bg-slate-50"
                data-testid="duplicar-origem"
              />
              {!filtroPeriodo && (
                <p className="text-xs text-red-500 mt-1">Selecione um período no filtro principal primeiro</p>
              )}
            </div>
            <div>
              <Label>Novo Período de Destino *</Label>
              <Input
                placeholder="Ex: 2026.2"
                value={duplicarDestino}
                onChange={(e) => setDuplicarDestino(e.target.value)}
                data-testid="duplicar-destino"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDuplicar(false)}>Cancelar</Button>
            <Button
              onClick={duplicarPeriodo}
              disabled={duplicarLoading || !filtroPeriodo || !duplicarDestino.trim()}
              data-testid="btn-confirmar-duplicar"
            >
              {duplicarLoading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Copy className="h-4 w-4 mr-2" />}
              Duplicar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
