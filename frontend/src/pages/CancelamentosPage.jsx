import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import api from '../services/api';
import {
  XCircle, Clock, ArrowRight, CheckCircle2, AlertTriangle,
  User, Building, Phone, FileText, RefreshCw, Search,
  Timer, RotateCcw, Ban, Send
} from 'lucide-react';
import { cn } from '../lib/utils';

const CancelamentosPage = () => {
  const [loading, setLoading] = useState(true);
  const [tipos, setTipos] = useState([]);
  const [responsabilidades, setResponsabilidades] = useState(null);
  const [pedidoBusca, setPedidoBusca] = useState('');
  const [pedidoSelecionado, setPedidoSelecionado] = useState(null);
  const [prazoNRM, setPrazoNRM] = useState(null);
  const [showSolicitarModal, setShowSolicitarModal] = useState(false);
  const [showRespostaNRMModal, setShowRespostaNRMModal] = useState(false);
  
  // Form states
  const [tipoSelecionado, setTipoSelecionado] = useState('');
  const [motivo, setMotivo] = useState('');
  const [observacoesNRM, setObservacoesNRM] = useState('');
  const [processando, setProcessando] = useState(false);

  useEffect(() => {
    carregarDados();
  }, []);

  const carregarDados = async () => {
    setLoading(true);
    try {
      const [tiposRes, respRes] = await Promise.all([
        api.get('/cancelamento/tipos'),
        api.get('/cancelamento/responsabilidades')
      ]);
      setTipos(tiposRes.data.tipos || []);
      setResponsabilidades(respRes.data);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar dados de cancelamento');
    } finally {
      setLoading(false);
    }
  };

  const buscarPedido = async () => {
    if (!pedidoBusca.trim()) {
      toast.error('Digite o ID ou protocolo do pedido');
      return;
    }
    
    setProcessando(true);
    try {
      // Buscar pedido
      const response = await api.get(`/pedidos/${pedidoBusca.trim()}`);
      setPedidoSelecionado(response.data);
      
      // Verificar prazo NRM se houver cancelamento pendente
      try {
        const prazoRes = await api.get(`/cancelamento/verificar-prazo/${pedidoBusca.trim()}`);
        setPrazoNRM(prazoRes.data);
      } catch {
        setPrazoNRM(null);
      }
      
      toast.success('Pedido encontrado!');
    } catch (error) {
      toast.error('Pedido não encontrado');
      setPedidoSelecionado(null);
      setPrazoNRM(null);
    } finally {
      setProcessando(false);
    }
  };

  const solicitarCancelamento = async () => {
    if (!tipoSelecionado || !motivo.trim()) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    setProcessando(true);
    try {
      const response = await api.post('/cancelamento/solicitar', {
        pedido_id: pedidoSelecionado.id,
        tipo: tipoSelecionado,
        motivo: motivo.trim(),
        solicitante_id: 'current_user',
        solicitante_nome: 'Usuário Atual'
      });
      
      toast.success('Solicitação de cancelamento registrada!');
      setShowSolicitarModal(false);
      setTipoSelecionado('');
      setMotivo('');
      
      // Recarregar dados do pedido
      buscarPedido();
    } catch (error) {
      toast.error('Erro ao solicitar cancelamento: ' + (error.response?.data?.detail || error.message));
    } finally {
      setProcessando(false);
    }
  };

  const registrarRespostaNRM = async (revertido) => {
    setProcessando(true);
    try {
      const response = await api.post('/cancelamento/resposta-nrm', {
        pedido_id: pedidoSelecionado.id,
        revertido,
        observacoes: observacoesNRM
      });
      
      toast.success(revertido ? 'Cancelamento revertido!' : 'Cancelamento confirmado');
      setShowRespostaNRMModal(false);
      setObservacoesNRM('');
      
      // Recarregar dados
      buscarPedido();
    } catch (error) {
      toast.error('Erro ao registrar resposta: ' + (error.response?.data?.detail || error.message));
    } finally {
      setProcessando(false);
    }
  };

  const calcularProgressoPrazo = () => {
    if (!prazoNRM || prazoNRM.status === 'nao_aplicavel') return null;
    const horasTotal = responsabilidades?.prazo_nrm_horas || 48;
    const horasRestantes = prazoNRM.horas_restantes || 0;
    const progresso = Math.max(0, Math.min(100, ((horasTotal - horasRestantes) / horasTotal) * 100));
    return { progresso, horasRestantes, expirado: prazoNRM.expirado };
  };

  const getStatusBadge = (status) => {
    const badges = {
      'inscricao': { color: 'bg-blue-100 text-blue-700', icon: FileText },
      'pre_analise': { color: 'bg-slate-100 text-slate-700', icon: Clock },
      'analise_documental': { color: 'bg-amber-100 text-amber-700', icon: FileText },
      'matriculado': { color: 'bg-green-100 text-green-700', icon: CheckCircle2 },
      'cancelado': { color: 'bg-red-100 text-red-700', icon: XCircle },
    };
    const config = badges[status] || badges.inscricao;
    const Icon = config.icon;
    return (
      <Badge className={config.color}>
        <Icon className="w-3 h-3 mr-1" />
        {status?.replace(/_/g, ' ').toUpperCase()}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const prazoInfo = calcularProgressoPrazo();

  return (
    <div className="space-y-6" data-testid="cancelamentos-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Fluxo de Cancelamento</h1>
        <p className="text-slate-500">
          Gerencie solicitações de cancelamento de matrícula conforme procedimento CAC
        </p>
      </div>

      {/* Cards de Responsabilidades */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <User className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-slate-700">Solicitado pelo Candidato</p>
                <p className="text-sm text-slate-500">
                  Encaminha para NRM (48h para reverter)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Clock className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="font-medium text-slate-700">Pré-Análise / Análise</p>
                <p className="text-sm text-slate-500">
                  CAC: dados bancários + chamado financeiro
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Building className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="font-medium text-slate-700">Matriculado</p>
                <p className="text-sm text-slate-500">
                  CAA: orientar Portal do Aluno
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Busca de Pedido */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5 text-slate-600" />
            Buscar Pedido
          </CardTitle>
          <CardDescription>
            Digite o ID ou número de protocolo do pedido
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input
              placeholder="ID ou protocolo (ex: CM-2026-0001)"
              value={pedidoBusca}
              onChange={(e) => setPedidoBusca(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && buscarPedido()}
              className="flex-1"
              data-testid="input-busca-pedido"
            />
            <Button onClick={buscarPedido} disabled={processando}>
              {processando ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              <span className="ml-2">Buscar</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Detalhes do Pedido */}
      {pedidoSelecionado && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Pedido: {pedidoSelecionado.numero_protocolo || pedidoSelecionado.id?.substring(0, 8)}
              </CardTitle>
              {getStatusBadge(pedidoSelecionado.status)}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Info do Aluno */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
              <div>
                <p className="text-sm text-slate-500">Aluno</p>
                <p className="font-medium">{pedidoSelecionado.aluno?.nome || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">CPF</p>
                <p className="font-medium">{pedidoSelecionado.aluno?.cpf || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Curso</p>
                <p className="font-medium">{pedidoSelecionado.curso_nome || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Empresa</p>
                <p className="font-medium">{pedidoSelecionado.empresa_nome || 'N/A'}</p>
              </div>
            </div>

            {/* Prazo NRM (se aplicável) */}
            {prazoInfo && !prazoInfo.expirado && prazoNRM?.status !== 'nao_aplicavel' && (
              <Alert className={cn(
                "border-l-4",
                prazoInfo.horasRestantes < 12 ? "border-l-red-500 bg-red-50" : 
                prazoInfo.horasRestantes < 24 ? "border-l-amber-500 bg-amber-50" :
                "border-l-blue-500 bg-blue-50"
              )}>
                <Timer className={cn(
                  "w-4 h-4",
                  prazoInfo.horasRestantes < 12 ? "text-red-600" : 
                  prazoInfo.horasRestantes < 24 ? "text-amber-600" : "text-blue-600"
                )} />
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-medium">
                      Aguardando NRM - {prazoInfo.horasRestantes.toFixed(1)}h restantes
                    </p>
                    <Progress 
                      value={prazoInfo.progresso} 
                      className="h-2"
                    />
                    <p className="text-sm">
                      O NRM tem 48h para tentar reverter o cancelamento
                    </p>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Prazo Expirado */}
            {prazoInfo?.expirado && (
              <Alert className="border-l-4 border-l-red-500 bg-red-50">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <AlertDescription className="text-red-700">
                  <strong>Prazo NRM expirado!</strong> O cancelamento pode prosseguir.
                </AlertDescription>
              </Alert>
            )}

            {/* Motivo de Cancelamento (se houver) */}
            {pedidoSelecionado.motivo_cancelamento && (
              <Alert className="bg-slate-50">
                <XCircle className="w-4 h-4 text-slate-600" />
                <AlertDescription>
                  <strong>Motivo do cancelamento:</strong> {pedidoSelecionado.motivo_cancelamento}
                </AlertDescription>
              </Alert>
            )}

            {/* Ações */}
            <div className="flex gap-3 pt-4 border-t">
              {/* Solicitar Cancelamento */}
              {pedidoSelecionado.status !== 'cancelado' && (
                <Button 
                  variant="destructive"
                  onClick={() => setShowSolicitarModal(true)}
                  data-testid="btn-solicitar-cancelamento"
                >
                  <Ban className="w-4 h-4 mr-2" />
                  Solicitar Cancelamento
                </Button>
              )}

              {/* Resposta NRM (se aguardando) */}
              {prazoNRM && prazoNRM.status !== 'nao_aplicavel' && !prazoNRM.nrm_respondeu && (
                <Button 
                  variant="outline"
                  onClick={() => setShowRespostaNRMModal(true)}
                  data-testid="btn-resposta-nrm"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Registrar Resposta NRM
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Fluxo Visual */}
      <Card>
        <CardHeader>
          <CardTitle>Fluxo de Cancelamento</CardTitle>
          <CardDescription>Conforme procedimento PG-SENAI.EP 003</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center justify-center gap-2 p-4">
            <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <User className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium">Candidato solicita</span>
            </div>
            <ArrowRight className="w-5 h-5 text-slate-400" />
            <div className="flex items-center gap-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
              <Building className="w-5 h-5 text-amber-600" />
              <span className="text-sm font-medium">CAC recebe</span>
            </div>
            <ArrowRight className="w-5 h-5 text-slate-400" />
            <div className="flex items-center gap-2 p-3 bg-purple-50 rounded-lg border border-purple-200">
              <Timer className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium">NRM (48h)</span>
            </div>
            <ArrowRight className="w-5 h-5 text-slate-400" />
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 p-2 bg-green-50 rounded-lg border border-green-200">
                <RotateCcw className="w-4 h-4 text-green-600" />
                <span className="text-xs font-medium">Revertido</span>
              </div>
              <div className="flex items-center gap-2 p-2 bg-red-50 rounded-lg border border-red-200">
                <XCircle className="w-4 h-4 text-red-600" />
                <span className="text-xs font-medium">Confirmado</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Modal Solicitar Cancelamento */}
      <Dialog open={showSolicitarModal} onOpenChange={setShowSolicitarModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Solicitar Cancelamento</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Tipo de Cancelamento *</Label>
              <Select value={tipoSelecionado} onValueChange={setTipoSelecionado}>
                <SelectTrigger data-testid="select-tipo-cancelamento">
                  <SelectValue placeholder="Selecione o tipo" />
                </SelectTrigger>
                <SelectContent>
                  {tipos.map((tipo) => (
                    <SelectItem key={tipo.value} value={tipo.value}>
                      {tipo.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Motivo *</Label>
              <Textarea
                placeholder="Descreva o motivo do cancelamento..."
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                rows={4}
                data-testid="textarea-motivo"
              />
            </div>

            {tipoSelecionado === 'solicitado_candidato' && (
              <Alert className="bg-amber-50 border-amber-200">
                <Clock className="w-4 h-4 text-amber-600" />
                <AlertDescription className="text-amber-700">
                  Este tipo de cancelamento será encaminhado para o NRM, 
                  que terá 48h para tentar reverter a decisão do candidato.
                </AlertDescription>
              </Alert>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSolicitarModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="destructive" 
              onClick={solicitarCancelamento}
              disabled={processando}
            >
              {processando ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Send className="w-4 h-4 mr-2" />
              )}
              Confirmar Solicitação
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Resposta NRM */}
      <Dialog open={showRespostaNRMModal} onOpenChange={setShowRespostaNRMModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resposta do NRM</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-slate-600">
              O NRM tentou reverter o cancelamento?
            </p>
            
            <div className="space-y-2">
              <Label>Observações (opcional)</Label>
              <Textarea
                placeholder="Detalhes sobre a tentativa de reversão..."
                value={observacoesNRM}
                onChange={(e) => setObservacoesNRM(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={() => setShowRespostaNRMModal(false)}
            >
              Fechar
            </Button>
            <Button 
              className="bg-green-600 hover:bg-green-700"
              onClick={() => registrarRespostaNRM(true)}
              disabled={processando}
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Revertido
            </Button>
            <Button 
              variant="destructive"
              onClick={() => registrarRespostaNRM(false)}
              disabled={processando}
            >
              <XCircle className="w-4 h-4 mr-2" />
              Não Revertido
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CancelamentosPage;
