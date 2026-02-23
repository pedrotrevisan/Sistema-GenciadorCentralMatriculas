import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import api from '../services/api';
import {
  Sun, Moon, Coffee, CheckCircle2, Circle, Plus, Clock, Bell, 
  FileText, AlertTriangle, Calendar, Sparkles, BookOpen, 
  ChevronRight, Trash2, RotateCcw, Star, Zap
} from 'lucide-react';

const CATEGORIAS = [
  { value: 'rotina', label: 'Rotina Diária', cor: 'bg-blue-100 text-blue-800', icon: RotateCcw },
  { value: 'pendencia', label: 'Pendência', cor: 'bg-orange-100 text-orange-800', icon: AlertTriangle },
  { value: 'lembrete', label: 'Lembrete', cor: 'bg-purple-100 text-purple-800', icon: Bell },
  { value: 'reuniao', label: 'Reunião', cor: 'bg-green-100 text-green-800', icon: Calendar },
  { value: 'outro', label: 'Outro', cor: 'bg-gray-100 text-gray-800', icon: Circle },
];

const MeuDiaPage = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [meuDia, setMeuDia] = useState(null);
  const [showNovaTarefa, setShowNovaTarefa] = useState(false);
  const [novaTarefa, setNovaTarefa] = useState({
    titulo: '',
    descricao: '',
    categoria: 'outro',
    prioridade: 2,
    recorrente: false,
    horario_sugerido: ''
  });

  useEffect(() => {
    carregarMeuDia();
  }, []);

  const carregarMeuDia = async () => {
    try {
      const response = await api.get('/apoio/meu-dia');
      setMeuDia(response.data);
    } catch (error) {
      toast.error('Erro ao carregar dados do dia');
    } finally {
      setLoading(false);
    }
  };

  const toggleTarefa = async (tarefaId) => {
    try {
      await api.patch(`/apoio/tarefas/${tarefaId}/concluir`);
      carregarMeuDia();
    } catch (error) {
      toast.error('Erro ao atualizar tarefa');
    }
  };

  const criarTarefa = async () => {
    if (!novaTarefa.titulo.trim()) {
      toast.error('Informe o título da tarefa');
      return;
    }

    try {
      await api.post('/apoio/tarefas', {
        ...novaTarefa,
        data_tarefa: new Date().toISOString().split('T')[0]
      });
      toast.success('Tarefa adicionada!');
      setShowNovaTarefa(false);
      setNovaTarefa({
        titulo: '',
        descricao: '',
        categoria: 'outro',
        prioridade: 2,
        recorrente: false,
        horario_sugerido: ''
      });
      carregarMeuDia();
    } catch (error) {
      toast.error('Erro ao criar tarefa');
    }
  };

  const deletarTarefa = async (tarefaId) => {
    try {
      await api.delete(`/apoio/tarefas/${tarefaId}`);
      toast.success('Tarefa removida');
      carregarMeuDia();
    } catch (error) {
      toast.error('Erro ao remover tarefa');
    }
  };

  const getIconeSaudacao = () => {
    const hora = new Date().getHours();
    if (hora < 12) return <Coffee className="w-8 h-8 text-amber-500" />;
    if (hora < 18) return <Sun className="w-8 h-8 text-yellow-500" />;
    return <Moon className="w-8 h-8 text-indigo-500" />;
  };

  const getCategoriaInfo = (cat) => {
    return CATEGORIAS.find(c => c.value === cat) || CATEGORIAS[4];
  };

  const progresso = meuDia?.resumo ? 
    Math.round((meuDia.resumo.tarefas_concluidas / Math.max(meuDia.resumo.tarefas_total, 1)) * 100) : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004587] mx-auto"></div>
          <p className="mt-4 text-slate-500">Preparando seu dia...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      {/* Header com Saudação */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          {getIconeSaudacao()}
          <div>
            <h1 className="text-3xl font-bold text-slate-900 font-['Chivo']">
              {meuDia?.saudacao}, {user?.nome?.split(' ')[0]}!
            </h1>
            <p className="text-slate-500">
              {meuDia?.dia_semana}, {new Date().toLocaleDateString('pt-BR', { day: 'numeric', month: 'long' })}
            </p>
          </div>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card className="bg-white/80 backdrop-blur border-0 shadow-sm">
          <CardContent className="p-4 text-center">
            <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-2">
              <CheckCircle2 className="w-6 h-6 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-slate-800">
              {meuDia?.resumo?.tarefas_concluidas || 0}/{meuDia?.resumo?.tarefas_total || 0}
            </p>
            <p className="text-sm text-slate-500">Tarefas do dia</p>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur border-0 shadow-sm">
          <CardContent className="p-4 text-center">
            <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-2">
              <FileText className="w-6 h-6 text-orange-600" />
            </div>
            <p className="text-2xl font-bold text-slate-800">
              {meuDia?.resumo?.pendencias_abertas || 0}
            </p>
            <p className="text-sm text-slate-500">Pendências abertas</p>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur border-0 shadow-sm">
          <CardContent className="p-4 text-center">
            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-2">
              <Zap className="w-6 h-6 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-slate-800">
              {meuDia?.resumo?.pedidos_andamento || 0}
            </p>
            <p className="text-sm text-slate-500">Pedidos em andamento</p>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur border-0 shadow-sm">
          <CardContent className="p-4 text-center">
            <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-2">
              <Bell className="w-6 h-6 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-slate-800">
              {meuDia?.retornos_pendentes || 0}
            </p>
            <p className="text-sm text-slate-500">Retornos pendentes</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Checklist do Dia */}
        <div className="md:col-span-2">
          <Card className="bg-white/90 backdrop-blur border-0 shadow-md">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-500" />
                Minhas Tarefas de Hoje
              </CardTitle>
              <Button 
                onClick={() => setShowNovaTarefa(true)} 
                size="sm" 
                className="bg-[#004587]"
              >
                <Plus className="w-4 h-4 mr-1" />
                Nova
              </Button>
            </CardHeader>
            <CardContent>
              {/* Barra de Progresso */}
              <div className="mb-6">
                <div className="flex justify-between text-sm text-slate-600 mb-1">
                  <span>Progresso do dia</span>
                  <span>{progresso}%</span>
                </div>
                <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-[#004587] to-blue-400 transition-all duration-500"
                    style={{ width: `${progresso}%` }}
                  />
                </div>
              </div>

              {/* Lista de Tarefas */}
              <div className="space-y-3">
                {meuDia?.tarefas?.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>Nenhuma tarefa para hoje.</p>
                    <p className="text-sm">Adicione tarefas para organizar seu dia!</p>
                  </div>
                ) : (
                  meuDia?.tarefas?.map((tarefa) => {
                    const catInfo = getCategoriaInfo(tarefa.categoria);
                    const CatIcon = catInfo.icon;
                    return (
                      <div 
                        key={tarefa.id}
                        className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                          tarefa.concluida 
                            ? 'bg-green-50 border-green-200' 
                            : 'bg-white border-slate-200 hover:border-blue-300'
                        }`}
                      >
                        <button
                          onClick={() => toggleTarefa(tarefa.id)}
                          className="flex-shrink-0"
                        >
                          {tarefa.concluida ? (
                            <CheckCircle2 className="w-6 h-6 text-green-600" />
                          ) : (
                            <Circle className="w-6 h-6 text-slate-400 hover:text-blue-500" />
                          )}
                        </button>
                        
                        <div className="flex-1 min-w-0">
                          <p className={`font-medium ${tarefa.concluida ? 'text-slate-400 line-through' : 'text-slate-800'}`}>
                            {tarefa.titulo}
                          </p>
                          {tarefa.descricao && (
                            <p className="text-sm text-slate-500 truncate">{tarefa.descricao}</p>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2">
                          {tarefa.horario_sugerido && (
                            <span className="text-xs text-slate-500 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {tarefa.horario_sugerido}
                            </span>
                          )}
                          <Badge className={catInfo.cor}>
                            <CatIcon className="w-3 h-3 mr-1" />
                            {catInfo.label}
                          </Badge>
                          {tarefa.recorrente && (
                            <RotateCcw className="w-4 h-4 text-slate-400" title="Tarefa recorrente" />
                          )}
                          <button 
                            onClick={() => deletarTarefa(tarefa.id)}
                            className="text-slate-400 hover:text-red-500"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Lembretes */}
          <Card className="bg-white/90 backdrop-blur border-0 shadow-md">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Bell className="w-5 h-5 text-purple-500" />
                Lembretes de Hoje
              </CardTitle>
            </CardHeader>
            <CardContent>
              {meuDia?.lembretes?.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-4">
                  Nenhum lembrete para hoje
                </p>
              ) : (
                <div className="space-y-2">
                  {meuDia?.lembretes?.map((lembrete) => (
                    <div 
                      key={lembrete.id}
                      className="p-3 bg-purple-50 rounded-lg border border-purple-100"
                    >
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-purple-600" />
                        <span className="text-sm font-medium text-purple-700">
                          {lembrete.horario}
                        </span>
                      </div>
                      <p className="text-sm text-slate-700 mt-1">{lembrete.titulo}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Acesso Rápido */}
          <Card className="bg-white/90 backdrop-blur border-0 shadow-md">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Star className="w-5 h-5 text-amber-500" />
                Acesso Rápido
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <a 
                href="/pendencias" 
                className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <span className="text-sm font-medium text-slate-700">Central de Pendências</span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </a>
              <a 
                href="/kanban" 
                className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <span className="text-sm font-medium text-slate-700">Kanban de Matrículas</span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </a>
              <a 
                href="/base-conhecimento" 
                className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <span className="text-sm font-medium text-slate-700">Base de Conhecimento</span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </a>
            </CardContent>
          </Card>

          {/* Dica do Dia */}
          <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-0 shadow-md">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <BookOpen className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <p className="font-medium text-amber-800 mb-1">Dica do Dia</p>
                  <p className="text-sm text-amber-700">
                    Lembre-se de verificar os retornos de contato pendentes. 
                    Um acompanhamento rápido pode resolver pendências mais facilmente!
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Modal Nova Tarefa */}
      <Dialog open={showNovaTarefa} onOpenChange={setShowNovaTarefa}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5 text-[#004587]" />
              Nova Tarefa
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Título *</Label>
              <Input
                value={novaTarefa.titulo}
                onChange={(e) => setNovaTarefa({ ...novaTarefa, titulo: e.target.value })}
                placeholder="O que você precisa fazer?"
              />
            </div>
            
            <div>
              <Label>Descrição</Label>
              <Textarea
                value={novaTarefa.descricao}
                onChange={(e) => setNovaTarefa({ ...novaTarefa, descricao: e.target.value })}
                placeholder="Detalhes adicionais..."
                rows={2}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Categoria</Label>
                <Select 
                  value={novaTarefa.categoria} 
                  onValueChange={(v) => setNovaTarefa({ ...novaTarefa, categoria: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIAS.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Horário Sugerido</Label>
                <Input
                  type="time"
                  value={novaTarefa.horario_sugerido}
                  onChange={(e) => setNovaTarefa({ ...novaTarefa, horario_sugerido: e.target.value })}
                />
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Checkbox
                id="recorrente"
                checked={novaTarefa.recorrente}
                onCheckedChange={(checked) => setNovaTarefa({ ...novaTarefa, recorrente: checked })}
              />
              <Label htmlFor="recorrente" className="text-sm cursor-pointer">
                Repetir todos os dias (tarefa recorrente)
              </Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNovaTarefa(false)}>
              Cancelar
            </Button>
            <Button onClick={criarTarefa} className="bg-[#004587]">
              <Plus className="w-4 h-4 mr-2" />
              Adicionar Tarefa
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MeuDiaPage;
