import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import api from '../services/api';
import { UserPlus, Zap, AlertTriangle, Circle, Loader2 } from 'lucide-react';

const PRIORIDADES = [
  { value: 'urgente', label: 'Urgente', color: 'bg-red-100 text-red-800', icon: Zap },
  { value: 'alta', label: 'Alta', color: 'bg-orange-100 text-orange-800', icon: AlertTriangle },
  { value: 'normal', label: 'Normal', color: 'bg-blue-100 text-blue-800', icon: Circle },
  { value: 'baixa', label: 'Baixa', color: 'bg-gray-100 text-gray-800', icon: Circle },
];

const AtribuirResponsavelModal = ({ 
  isOpen, 
  onClose, 
  tipo, // 'pedido', 'pendencia', 'reembolso'
  itemId,
  itemTitulo,
  responsavelAtual,
  onSuccess 
}) => {
  const [loading, setLoading] = useState(false);
  const [loadingResponsaveis, setLoadingResponsaveis] = useState(true);
  const [responsaveis, setResponsaveis] = useState([]);
  const [selectedResponsavel, setSelectedResponsavel] = useState('');
  const [prioridade, setPrioridade] = useState('normal');
  const [observacao, setObservacao] = useState('');

  useEffect(() => {
    if (isOpen) {
      carregarResponsaveis();
      setSelectedResponsavel(responsavelAtual || '');
      setPrioridade('normal');
      setObservacao('');
    }
  }, [isOpen, responsavelAtual]);

  const carregarResponsaveis = async () => {
    setLoadingResponsaveis(true);
    try {
      const response = await api.get('/atribuicoes/responsaveis');
      setResponsaveis(response.data);
    } catch (error) {
      toast.error('Erro ao carregar responsáveis');
    } finally {
      setLoadingResponsaveis(false);
    }
  };

  const handleAtribuir = async () => {
    if (!selectedResponsavel) {
      toast.error('Selecione um responsável');
      return;
    }

    setLoading(true);
    try {
      await api.post('/atribuicoes/atribuir', {
        tipo,
        item_id: itemId,
        responsavel_id: selectedResponsavel,
        prioridade,
        observacao: observacao || undefined
      });

      const responsavelNome = responsaveis.find(r => r.id === selectedResponsavel)?.nome;
      toast.success(`Atribuído a ${responsavelNome}`);
      
      if (onSuccess) {
        onSuccess({
          responsavel_id: selectedResponsavel,
          responsavel_nome: responsavelNome,
          prioridade
        });
      }
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atribuir');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoverAtribuicao = async () => {
    setLoading(true);
    try {
      await api.delete(`/atribuicoes/atribuir/${tipo}/${itemId}`);
      toast.success('Atribuição removida');
      
      if (onSuccess) {
        onSuccess({
          responsavel_id: null,
          responsavel_nome: null,
          prioridade: null
        });
      }
      onClose();
    } catch (error) {
      toast.error('Erro ao remover atribuição');
    } finally {
      setLoading(false);
    }
  };

  const tipoLabel = {
    pedido: 'Matrícula',
    pendencia: 'Pendência',
    reembolso: 'Reembolso'
  }[tipo] || tipo;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-[#004587]" />
            Atribuir Responsável
          </DialogTitle>
          <DialogDescription>
            {tipoLabel}: <strong>{itemTitulo}</strong>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Responsável */}
          <div className="space-y-2">
            <Label>Responsável</Label>
            {loadingResponsaveis ? (
              <div className="flex items-center gap-2 text-slate-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                Carregando...
              </div>
            ) : (
              <Select value={selectedResponsavel} onValueChange={setSelectedResponsavel}>
                <SelectTrigger data-testid="select-responsavel">
                  <SelectValue placeholder="Selecione um responsável" />
                </SelectTrigger>
                <SelectContent>
                  {responsaveis.map((resp) => (
                    <SelectItem key={resp.id} value={resp.id}>
                      <div className="flex items-center gap-2">
                        <span>{resp.nome}</span>
                        <Badge variant="outline" className="text-xs">
                          {resp.role}
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Prioridade */}
          <div className="space-y-2">
            <Label>Prioridade</Label>
            <Select value={prioridade} onValueChange={setPrioridade}>
              <SelectTrigger data-testid="select-prioridade">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PRIORIDADES.map((p) => {
                  const Icon = p.icon;
                  return (
                    <SelectItem key={p.value} value={p.value}>
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4" />
                        <span>{p.label}</span>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          {/* Observação */}
          <div className="space-y-2">
            <Label>Observação (opcional)</Label>
            <Textarea
              placeholder="Adicione uma nota para o responsável..."
              value={observacao}
              onChange={(e) => setObservacao(e.target.value)}
              rows={2}
              data-testid="textarea-observacao"
            />
          </div>
        </div>

        <DialogFooter className="flex gap-2">
          {responsavelAtual && (
            <Button
              variant="outline"
              onClick={handleRemoverAtribuicao}
              disabled={loading}
              className="text-red-600 hover:text-red-700"
            >
              Remover Atribuição
            </Button>
          )}
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button 
            onClick={handleAtribuir} 
            disabled={loading || !selectedResponsavel}
            className="bg-[#004587]"
            data-testid="btn-atribuir"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <UserPlus className="w-4 h-4 mr-2" />
            )}
            Atribuir
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AtribuirResponsavelModal;
