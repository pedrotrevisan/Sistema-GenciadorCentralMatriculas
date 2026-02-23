import { useState, useEffect } from 'react';
import { contatosAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from './ui/collapsible';
import { toast } from 'sonner';
import {
  Phone,
  MessageCircle,
  Mail,
  User,
  MessageSquare,
  MoreHorizontal,
  Plus,
  ChevronDown,
  ChevronUp,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Calendar,
  RefreshCw
} from 'lucide-react';

// Ícones por tipo de contato
const tipoIcons = {
  ligacao: Phone,
  whatsapp: MessageCircle,
  email: Mail,
  presencial: User,
  sms: MessageSquare,
  outro: MoreHorizontal
};

// Cores por resultado
const resultadoColors = {
  sucesso: 'bg-green-100 text-green-800 border-green-200',
  nao_atendeu: 'bg-red-100 text-red-800 border-red-200',
  caixa_postal: 'bg-orange-100 text-orange-800 border-orange-200',
  numero_errado: 'bg-red-100 text-red-800 border-red-200',
  sem_resposta: 'bg-amber-100 text-amber-800 border-amber-200',
  pendente: 'bg-blue-100 text-blue-800 border-blue-200',
  agendado: 'bg-purple-100 text-purple-800 border-purple-200'
};

// Cores por tipo
const tipoColors = {
  ligacao: 'bg-blue-50 border-blue-200',
  whatsapp: 'bg-green-50 border-green-200',
  email: 'bg-purple-50 border-purple-200',
  presencial: 'bg-orange-50 border-orange-200',
  sms: 'bg-cyan-50 border-cyan-200',
  outro: 'bg-gray-50 border-gray-200'
};

const LogContatos = ({ pedidoId }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [isOpen, setIsOpen] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  
  // Options para selects
  const [tipos, setTipos] = useState([]);
  const [resultados, setResultados] = useState([]);
  const [motivos, setMotivos] = useState([]);
  
  // Form state
  const [formData, setFormData] = useState({
    tipo: '',
    resultado: '',
    motivo: '',
    descricao: '',
    contato_nome: '',
    contato_telefone: '',
    contato_email: '',
    data_retorno: ''
  });

  const loadData = async () => {
    try {
      const response = await contatosAPI.listarPorPedido(pedidoId);
      setData(response.data);
    } catch (error) {
      console.error('Erro ao carregar contatos:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadOptions = async () => {
    try {
      const [tiposRes, resultadosRes, motivosRes] = await Promise.all([
        contatosAPI.getTipos(),
        contatosAPI.getResultados(),
        contatosAPI.getMotivos()
      ]);
      setTipos(tiposRes.data);
      setResultados(resultadosRes.data);
      setMotivos(motivosRes.data);
    } catch (error) {
      console.error('Erro ao carregar opções:', error);
    }
  };

  useEffect(() => {
    loadData();
    loadOptions();
  }, [pedidoId]);

  const handleSubmit = async () => {
    if (!formData.tipo || !formData.resultado || !formData.motivo || !formData.descricao) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    if (formData.descricao.length < 5) {
      toast.error('A descrição deve ter pelo menos 5 caracteres');
      return;
    }

    setSaving(true);
    try {
      await contatosAPI.registrar({
        pedido_id: pedidoId,
        tipo: formData.tipo,
        resultado: formData.resultado,
        motivo: formData.motivo,
        descricao: formData.descricao,
        contato_nome: formData.contato_nome || null,
        contato_telefone: formData.contato_telefone || null,
        contato_email: formData.contato_email || null,
        data_retorno: formData.data_retorno ? new Date(formData.data_retorno).toISOString() : null
      });
      
      toast.success('Contato registrado com sucesso!');
      setShowModal(false);
      setFormData({
        tipo: '',
        resultado: '',
        motivo: '',
        descricao: '',
        contato_nome: '',
        contato_telefone: '',
        contato_email: '',
        data_retorno: ''
      });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao registrar contato');
    } finally {
      setSaving(false);
    }
  };

  const handleMarcarRetorno = async (contatoId) => {
    try {
      await contatosAPI.marcarRetorno(contatoId);
      toast.success('Retorno marcado como realizado');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao marcar retorno');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDateShort = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-200 rounded w-1/4"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const TipoIcon = ({ tipo }) => {
    const Icon = tipoIcons[tipo] || MoreHorizontal;
    return <Icon className="h-4 w-4" />;
  };

  return (
    <>
      <Card data-testid="log-contatos-section">
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CardHeader className="cursor-pointer" onClick={() => setIsOpen(!isOpen)}>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Phone className="h-4 w-4" />
                Log de Contatos
                {data?.resumo && (
                  <Badge variant="outline" className="ml-2">
                    {data.resumo.total_contatos} contato{data.resumo.total_contatos !== 1 ? 's' : ''}
                  </Badge>
                )}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowModal(true);
                  }}
                  className="bg-[#004587] hover:bg-[#003366]"
                  data-testid="add-contato-btn"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Registrar Contato
                </Button>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm">
                    {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </Button>
                </CollapsibleTrigger>
              </div>
            </div>
          </CardHeader>
          
          <CollapsibleContent>
            <CardContent className="pt-0">
              {/* Resumo */}
              {data?.resumo && data.resumo.total_contatos > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{data.resumo.total_contatos}</p>
                    <p className="text-xs text-gray-500">Total</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">{data.resumo.contatos_sucesso}</p>
                    <p className="text-xs text-gray-500">Sucesso</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">{data.resumo.taxa_sucesso}%</p>
                    <p className="text-xs text-gray-500">Taxa</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-amber-600">{data.resumo.retornos_pendentes}</p>
                    <p className="text-xs text-gray-500">Retornos</p>
                  </div>
                </div>
              )}

              {/* Lista de Contatos */}
              {data?.contatos && data.contatos.length > 0 ? (
                <div className="space-y-3">
                  {data.contatos.map((contato) => (
                    <div
                      key={contato.id}
                      className={`p-3 rounded-lg border ${tipoColors[contato.tipo] || 'bg-gray-50 border-gray-200'}`}
                      data-testid={`contato-item-${contato.id}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-3 flex-1">
                          <div className="mt-1">
                            <TipoIcon tipo={contato.tipo} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap mb-1">
                              <span className="font-medium text-sm">{contato.tipo_label}</span>
                              <Badge 
                                variant="outline" 
                                className={`text-xs ${resultadoColors[contato.resultado] || ''}`}
                              >
                                {contato.resultado_label}
                              </Badge>
                              <Badge variant="outline" className="text-xs">
                                {contato.motivo_label}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-700 mb-1">{contato.descricao}</p>
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              <span>{formatDateShort(contato.criado_em)}</span>
                              <span>por {contato.usuario_nome}</span>
                              {contato.contato_telefone && (
                                <span className="flex items-center gap-1">
                                  <Phone className="h-3 w-3" />
                                  {contato.contato_telefone}
                                </span>
                              )}
                            </div>
                            {contato.precisa_retorno && (
                              <div className="mt-2 flex items-center gap-2">
                                <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                                  <Calendar className="h-3 w-3 mr-1" />
                                  Retorno: {formatDateShort(contato.data_retorno)}
                                </Badge>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-6 text-xs"
                                  onClick={() => handleMarcarRetorno(contato.id)}
                                >
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  Marcar Realizado
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <MessageCircle className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                  <p>Nenhum contato registrado ainda</p>
                  <p className="text-sm">Clique em "Registrar Contato" para adicionar</p>
                </div>
              )}
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>

      {/* Modal de Novo Contato */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Registrar Contato</DialogTitle>
            <DialogDescription>
              Registre uma interação com o aluno
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tipo de Contato *</Label>
                <Select 
                  value={formData.tipo} 
                  onValueChange={(v) => setFormData({...formData, tipo: v})}
                >
                  <SelectTrigger data-testid="contato-tipo-select">
                    <SelectValue placeholder="Selecione..." />
                  </SelectTrigger>
                  <SelectContent>
                    {tipos.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Resultado *</Label>
                <Select 
                  value={formData.resultado} 
                  onValueChange={(v) => setFormData({...formData, resultado: v})}
                >
                  <SelectTrigger data-testid="contato-resultado-select">
                    <SelectValue placeholder="Selecione..." />
                  </SelectTrigger>
                  <SelectContent>
                    {resultados.map((r) => (
                      <SelectItem key={r.value} value={r.value}>
                        {r.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Motivo/Assunto *</Label>
              <Select 
                value={formData.motivo} 
                onValueChange={(v) => setFormData({...formData, motivo: v})}
              >
                <SelectTrigger data-testid="contato-motivo-select">
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  {motivos.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Descrição do Contato *</Label>
              <Textarea
                placeholder="Descreva o que foi conversado, acordado ou informado..."
                value={formData.descricao}
                onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                rows={3}
                data-testid="contato-descricao"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Telefone Utilizado</Label>
                <Input
                  placeholder="(00) 00000-0000"
                  value={formData.contato_telefone}
                  onChange={(e) => setFormData({...formData, contato_telefone: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Quem Atendeu</Label>
                <Input
                  placeholder="Nome da pessoa"
                  value={formData.contato_nome}
                  onChange={(e) => setFormData({...formData, contato_nome: e.target.value})}
                />
              </div>
            </div>

            {(formData.resultado === 'agendado' || formData.resultado === 'pendente') && (
              <div className="space-y-2">
                <Label>Data do Retorno</Label>
                <Input
                  type="datetime-local"
                  value={formData.data_retorno}
                  onChange={(e) => setFormData({...formData, data_retorno: e.target.value})}
                  data-testid="contato-data-retorno"
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowModal(false)}>
              Cancelar
            </Button>
            <Button 
              className="bg-[#004587] hover:bg-[#003366]"
              onClick={handleSubmit}
              disabled={saving}
              data-testid="save-contato-btn"
            >
              {saving ? 'Salvando...' : 'Registrar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default LogContatos;
