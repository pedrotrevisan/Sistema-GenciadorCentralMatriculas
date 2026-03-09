import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { pedidosAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import TimelineAuditoria from '../components/TimelineAuditoria';
import LogContatos from '../components/LogContatos';
import CobrarZap from '../components/CobrarZap';
import IndicadorSLA from '../components/IndicadorSLA';
import BotaoFavorito from '../components/BotaoFavorito';
import TemplatesMensagem from '../components/TemplatesMensagem';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import { 
  ChevronLeft, 
  FileText, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  User,
  Edit,
  ClipboardList
} from 'lucide-react';

const statusConfig = {
  pendente: { icon: Clock, color: 'badge-pendente', label: 'Pendente' },
  em_analise: { icon: AlertCircle, color: 'badge-em_analise', label: 'Em Análise' },
  documentacao_pendente: { icon: FileText, color: 'badge-documentacao_pendente', label: 'Doc. Pendente' },
  aprovado: { icon: CheckCircle, color: 'badge-aprovado', label: 'Aprovado' },
  rejeitado: { icon: XCircle, color: 'badge-rejeitado', label: 'Rejeitado' },
  realizado: { icon: CheckCircle, color: 'badge-realizado', label: 'Realizado' },
  cancelado: { icon: XCircle, color: 'badge-cancelado', label: 'Cancelado' },
  exportado: { icon: CheckCircle, color: 'badge-exportado', label: 'Exportado' },
};

const statusOptions = [
  { value: 'pendente', label: 'Pendente' },
  { value: 'em_analise', label: 'Em Análise' },
  { value: 'documentacao_pendente', label: 'Documentação Pendente' },
  { value: 'aprovado', label: 'Aprovado' },
  { value: 'rejeitado', label: 'Rejeitado' },
  { value: 'realizado', label: 'Realizado' },
  { value: 'cancelado', label: 'Cancelado' },
];

const PedidoDetalhePage = () => {
  const { id } = useParams();
  const { user, hasPermission } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [pedido, setPedido] = useState(null);
  
  // Status change modal
  const [statusModal, setStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [motivo, setMotivo] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const fetchPedido = async () => {
    setLoading(true);
    try {
      const response = await pedidosAPI.buscarPorId(id);
      setPedido(response.data);
    } catch (error) {
      toast.error('Erro ao carregar pedido');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPedido();
  }, [id]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleStatusChange = async () => {
    if (!newStatus) {
      toast.error('Selecione um status');
      return;
    }
    
    setUpdatingStatus(true);
    try {
      await pedidosAPI.atualizarStatus(id, {
        status: newStatus,
        motivo: motivo || undefined
      });
      toast.success('Status atualizado com sucesso');
      setStatusModal(false);
      setNewStatus('');
      setMotivo('');
      fetchPedido();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Erro ao atualizar status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const StatusBadge = ({ status }) => {
    const config = statusConfig[status] || statusConfig.pendente;
    const Icon = config.icon;
    return (
      <Badge variant="outline" className={`${config.color} flex items-center gap-1 px-3 py-1`}>
        <Icon className="h-4 w-4" />
        {config.label}
      </Badge>
    );
  };

  const getBasePath = () => {
    if (user?.role === 'consultor') return '/consultor';
    if (user?.role === 'assistente') return '/assistente';
    return '/admin/pedidos';
  };

  if (loading) {
    return (
      <div className="space-y-6" data-testid="pedido-loading">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!pedido) {
    return null;
  }

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="pedido-detalhe-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Button
            variant="ghost"
            onClick={() => navigate(getBasePath())}
            className="mb-2 -ml-4"
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
            {pedido.numero_protocolo ? (
              <span className="text-[#004587]">{pedido.numero_protocolo}</span>
            ) : (
              'Detalhes do Pedido'
            )}
          </h1>
          <p className="text-slate-500 text-sm">
            {pedido.numero_protocolo && 'Detalhes do Pedido • '}ID: {pedido.id.slice(0, 8)}...
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <IndicadorSLA createdAt={pedido.created_at} status={pedido.status} />
          <StatusBadge status={pedido.status} />
          <BotaoFavorito 
            pedidoId={pedido.id} 
            pedidoInfo={{ 
              protocolo: pedido.numero_protocolo,
              aluno: pedido.alunos?.[0]?.nome 
            }}
          />
          <CobrarZap pedido={pedido} variant="icon" />
          {/* Botão Assistente TOTVS - para assistente e admin */}
          {(user?.role === 'assistente' || user?.role === 'admin') && (
            <Button
              variant="outline"
              onClick={() => navigate(`/assistente-totvs/${pedido.id}`)}
              className="border-blue-300 text-blue-600 hover:bg-blue-50"
              data-testid="assistente-totvs-btn"
            >
              <ClipboardList className="h-4 w-4 mr-2" />
              Assistente TOTVS
            </Button>
          )}
          {hasPermission('pedido:editar_status') && pedido.pode_editar && (
            <Button
              variant="outline"
              onClick={() => setStatusModal(true)}
              data-testid="edit-status-btn"
            >
              <Edit className="h-4 w-4 mr-2" />
              Alterar Status
            </Button>
          )}
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Informações do Pedido
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {pedido.numero_protocolo && (
              <div>
                <p className="text-sm text-slate-500">Número do Protocolo</p>
                <p className="font-mono text-lg font-bold text-[#004587]">{pedido.numero_protocolo}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-slate-500">Curso</p>
              <p className="font-medium">{pedido.curso_nome}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">
                {pedido.projeto_nome ? 'Projeto' : 'Empresa'}
              </p>
              <p className="font-medium">{pedido.projeto_nome || pedido.empresa_nome}</p>
            </div>
            {pedido.observacoes && (
              <div>
                <p className="text-sm text-slate-500">Observações</p>
                <p className="font-medium">{pedido.observacoes}</p>
              </div>
            )}
            {pedido.motivo_rejeicao && (
              <div className="p-3 bg-red-50 rounded-lg">
                <p className="text-sm text-red-600 font-medium">Motivo da Rejeição</p>
                <p className="text-red-700">{pedido.motivo_rejeicao}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <User className="h-4 w-4" />
              Informações do Consultor
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm text-slate-500">Consultor</p>
              <p className="font-medium">{pedido.consultor_nome}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Data de Criação</p>
              <p className="font-medium">{formatDate(pedido.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Última Atualização</p>
              <p className="font-medium">{formatDate(pedido.updated_at)}</p>
            </div>
            {pedido.data_exportacao && (
              <div>
                <p className="text-sm text-slate-500">Data de Exportação</p>
                <p className="font-medium">{formatDate(pedido.data_exportacao)}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Alunos Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Alunos ({pedido.total_alunos})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {pedido.alunos.map((aluno, index) => (
              <Card key={aluno.id || index} className="border border-slate-200">
                <CardContent className="p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-slate-500">Nome</p>
                      <p className="font-medium">{aluno.nome}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">CPF</p>
                      <p className="font-medium">{aluno.cpf_formatado || aluno.cpf}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Email</p>
                      <p className="font-medium">{aluno.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Telefone</p>
                      <p className="font-medium">{aluno.telefone_formatado || aluno.telefone}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Data de Nascimento</p>
                      <p className="font-medium">{aluno.data_nascimento_formatada || aluno.data_nascimento}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">RG</p>
                      <p className="font-medium">{aluno.rg} - {aluno.rg_orgao_emissor}/{aluno.rg_uf}</p>
                    </div>
                    {aluno.rg_data_emissao && (
                      <div>
                        <p className="text-sm text-slate-500">Emissão RG</p>
                        <p className="font-medium">{aluno.rg_data_emissao}</p>
                      </div>
                    )}
                    {(aluno.naturalidade || aluno.naturalidade_uf) && (
                      <div>
                        <p className="text-sm text-slate-500">Naturalidade</p>
                        <p className="font-medium">{aluno.naturalidade}{aluno.naturalidade_uf ? `/${aluno.naturalidade_uf}` : ''}</p>
                      </div>
                    )}
                    {aluno.sexo && (
                      <div>
                        <p className="text-sm text-slate-500">Sexo</p>
                        <p className="font-medium">{aluno.sexo === 'M' ? 'Masculino' : 'Feminino'}</p>
                      </div>
                    )}
                    {aluno.cor_raca && (
                      <div>
                        <p className="text-sm text-slate-500">Cor/Raça</p>
                        <p className="font-medium">{aluno.cor_raca}</p>
                      </div>
                    )}
                    {aluno.grau_instrucao && (
                      <div>
                        <p className="text-sm text-slate-500">Grau de Instrução</p>
                        <p className="font-medium">{aluno.grau_instrucao}</p>
                      </div>
                    )}
                    {aluno.nome_pai && (
                      <div>
                        <p className="text-sm text-slate-500">Nome do Pai</p>
                        <p className="font-medium">{aluno.nome_pai}</p>
                      </div>
                    )}
                    {aluno.nome_mae && (
                      <div>
                        <p className="text-sm text-slate-500">Nome da Mãe</p>
                        <p className="font-medium">{aluno.nome_mae}</p>
                      </div>
                    )}
                    <div className="md:col-span-2 lg:col-span-3">
                      <p className="text-sm text-slate-500">Endereço</p>
                      <p className="font-medium">
                        {aluno.endereco_logradouro}, {aluno.endereco_numero}
                        {aluno.endereco_complemento ? ` - ${aluno.endereco_complemento}` : ''}, {aluno.endereco_bairro}, {aluno.endereco_cidade}/{aluno.endereco_uf} - CEP: {aluno.endereco_cep}
                      </p>
                    </div>
                    {/* Botão Assistente TOTVS por aluno */}
                    {(user?.role === 'assistente' || user?.role === 'admin') && (
                      <div className="md:col-span-2 lg:col-span-3 pt-2 border-t border-slate-100">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(`/assistente-totvs/${pedido.id}/${index}`)}
                          className="border-blue-200 text-blue-600 hover:bg-blue-50"
                          data-testid={`assistente-totvs-aluno-${index}-btn`}
                        >
                          <ClipboardList className="h-4 w-4 mr-2" />
                          Preencher TOTVS para {aluno.nome?.split(' ')[0]}
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Log de Contatos */}
      <LogContatos pedidoId={id} />

      {/* Templates de Mensagem */}
      {pedido && pedido.alunos?.[0] && (
        <TemplatesMensagem 
          pedido={pedido} 
          aluno={pedido.alunos[0]}
          documentosFaltantes={[]}
        />
      )}

      {/* Timeline de Auditoria */}
      <TimelineAuditoria pedidoId={id} />

      {/* Status Change Modal */}
      <Dialog open={statusModal} onOpenChange={setStatusModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Alterar Status do Pedido</DialogTitle>
            <DialogDescription>
              Selecione o novo status para o pedido
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Novo Status</label>
              <Select value={newStatus} onValueChange={setNewStatus}>
                <SelectTrigger data-testid="new-status-select">
                  <SelectValue placeholder="Selecione o status" />
                </SelectTrigger>
                <SelectContent>
                  {statusOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {newStatus === 'rejeitado' && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Motivo da Rejeição</label>
                <Textarea
                  placeholder="Informe o motivo..."
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  data-testid="rejection-reason"
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusModal(false)}>
              Cancelar
            </Button>
            <Button 
              className="bg-[#E30613] hover:bg-[#b9050f]"
              onClick={handleStatusChange}
              disabled={updatingStatus}
              data-testid="confirm-status-change"
            >
              {updatingStatus ? 'Salvando...' : 'Confirmar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PedidoDetalhePage;
