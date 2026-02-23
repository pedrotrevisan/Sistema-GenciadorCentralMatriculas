import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import api from '../services/api';
import {
  Inbox, FileText, AlertCircle, DollarSign, RefreshCw, ChevronRight,
  Clock, Filter, CheckCircle, Circle, AlertTriangle, Zap
} from 'lucide-react';

const PRIORIDADE_CONFIG = {
  urgente: { label: 'Urgente', color: 'bg-red-100 text-red-800', icon: Zap },
  alta: { label: 'Alta', color: 'bg-orange-100 text-orange-800', icon: AlertTriangle },
  normal: { label: 'Normal', color: 'bg-blue-100 text-blue-800', icon: Circle },
  baixa: { label: 'Baixa', color: 'bg-gray-100 text-gray-800', icon: Circle }
};

const TIPO_CONFIG = {
  pedido: { label: 'Matrícula', color: 'bg-blue-100 text-blue-800', icon: FileText },
  pendencia: { label: 'Pendência', color: 'bg-orange-100 text-orange-800', icon: AlertCircle },
  reembolso: { label: 'Reembolso', color: 'bg-green-100 text-green-800', icon: DollarSign }
};

const CaixaEntradaPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [items, setItems] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [filtroTipo, setFiltroTipo] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('');

  useEffect(() => {
    carregarDados();
  }, [filtroTipo, filtroStatus]);

  const carregarDados = async () => {
    try {
      const params = {};
      if (filtroTipo) params.tipo = filtroTipo;
      if (filtroStatus) params.status = filtroStatus;

      const [caixaRes, resumoRes] = await Promise.all([
        api.get('/atribuicoes/minha-caixa', { params }),
        api.get('/atribuicoes/resumo')
      ]);

      setItems(caixaRes.data.items || []);
      setResumo(resumoRes.data);
    } catch (error) {
      toast.error('Erro ao carregar caixa de entrada');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    carregarDados();
  };

  const navigateToItem = (item) => {
    if (item.tipo === 'pedido') {
      navigate(`/pedidos/${item.id}`);
    } else if (item.tipo === 'pendencia') {
      navigate(`/pendencias`);
    } else if (item.tipo === 'reembolso') {
      navigate(`/reembolsos`);
    }
  };

  const getPrioridadeConfig = (prioridade) => {
    return PRIORIDADE_CONFIG[prioridade] || PRIORIDADE_CONFIG.normal;
  };

  const getTipoConfig = (tipo) => {
    return TIPO_CONFIG[tipo] || TIPO_CONFIG.pedido;
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      pendente: { label: 'Pendente', color: 'bg-amber-100 text-amber-800' },
      aberto: { label: 'Aberto', color: 'bg-amber-100 text-amber-800' },
      em_analise: { label: 'Em Análise', color: 'bg-blue-100 text-blue-800' },
      documentacao_pendente: { label: 'Doc. Pendente', color: 'bg-orange-100 text-orange-800' },
      aguardando_aluno: { label: 'Aguardando Aluno', color: 'bg-purple-100 text-purple-800' },
      aguardando_dados_bancarios: { label: 'Aguardando Dados', color: 'bg-purple-100 text-purple-800' },
      aprovado: { label: 'Aprovado', color: 'bg-green-100 text-green-800' },
      pago: { label: 'Pago', color: 'bg-green-100 text-green-800' }
    };
    return statusMap[status] || { label: status, color: 'bg-gray-100 text-gray-800' };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004587] mx-auto"></div>
          <p className="mt-4 text-slate-500">Carregando caixa de entrada...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-['Chivo'] flex items-center gap-2">
            <Inbox className="w-7 h-7 text-[#004587]" />
            Minha Caixa de Entrada
          </h1>
          <p className="text-slate-500">
            Demandas atribuídas a você
          </p>
        </div>
        <Button 
          variant="outline" 
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Atualizar
        </Button>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="bg-white">
          <CardContent className="p-4 text-center">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-2">
              <Inbox className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-slate-800">{resumo?.total || 0}</p>
            <p className="text-sm text-slate-500">Total</p>
          </CardContent>
        </Card>
        
        <Card className="bg-white">
          <CardContent className="p-4 text-center">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-2">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-slate-800">{resumo?.pedidos || 0}</p>
            <p className="text-sm text-slate-500">Matrículas</p>
          </CardContent>
        </Card>
        
        <Card className="bg-white">
          <CardContent className="p-4 text-center">
            <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-2">
              <AlertCircle className="w-5 h-5 text-orange-600" />
            </div>
            <p className="text-2xl font-bold text-slate-800">{resumo?.pendencias || 0}</p>
            <p className="text-sm text-slate-500">Pendências</p>
          </CardContent>
        </Card>
        
        <Card className="bg-white">
          <CardContent className="p-4 text-center">
            <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-2">
              <DollarSign className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-slate-800">{resumo?.reembolsos || 0}</p>
            <p className="text-sm text-slate-500">Reembolsos</p>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-slate-400" />
            <Select value={filtroTipo || "all"} onValueChange={(v) => setFiltroTipo(v === "all" ? "" : v)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Todos os tipos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os tipos</SelectItem>
                <SelectItem value="pedido">Matrículas</SelectItem>
                <SelectItem value="pendencia">Pendências</SelectItem>
                <SelectItem value="reembolso">Reembolsos</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={filtroStatus || "all"} onValueChange={(v) => setFiltroStatus(v === "all" ? "" : v)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Todos os status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os status</SelectItem>
                <SelectItem value="pendente">Pendentes</SelectItem>
                <SelectItem value="em_andamento">Em andamento</SelectItem>
                <SelectItem value="concluido">Concluídos</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Items */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Demandas ({items.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <div className="text-center py-12">
              <Inbox className="w-16 h-16 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500 text-lg">Nenhuma demanda atribuída</p>
              <p className="text-slate-400 text-sm">
                Quando alguém atribuir uma tarefa a você, ela aparecerá aqui
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((item) => {
                const tipoConfig = getTipoConfig(item.tipo);
                const TipoIcon = tipoConfig.icon;
                const prioridadeConfig = getPrioridadeConfig(item.prioridade);
                const statusConfig = getStatusBadge(item.status);
                
                return (
                  <div
                    key={`${item.tipo}-${item.id}`}
                    onClick={() => navigateToItem(item)}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all"
                    data-testid={`inbox-item-${item.id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-lg ${tipoConfig.color.replace('text-', 'bg-').replace('-800', '-100')} flex items-center justify-center`}>
                        <TipoIcon className={`w-5 h-5 ${tipoConfig.color.split(' ')[1]}`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-slate-800">{item.titulo}</p>
                          {item.prioridade === 'urgente' && (
                            <Zap className="w-4 h-4 text-red-500" />
                          )}
                        </div>
                        <p className="text-sm text-slate-500">{item.descricao}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Badge className={prioridadeConfig.color}>
                        {prioridadeConfig.label}
                      </Badge>
                      <Badge className={statusConfig.color}>
                        {statusConfig.label}
                      </Badge>
                      <div className="text-right">
                        <p className="text-xs text-slate-400">
                          {item.updated_at ? new Date(item.updated_at).toLocaleDateString('pt-BR') : '-'}
                        </p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-slate-400" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CaixaEntradaPage;
