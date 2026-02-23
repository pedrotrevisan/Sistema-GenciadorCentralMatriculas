import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { contatosAPI } from '../services/api';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from './ui/alert';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from './ui/popover';
import {
  Bell,
  Phone,
  MessageCircle,
  Mail,
  User,
  Clock,
  AlertTriangle,
  CheckCircle,
  X,
  ChevronRight
} from 'lucide-react';

// Ícones por tipo de contato
const tipoIcons = {
  ligacao: Phone,
  whatsapp: MessageCircle,
  email: Mail,
  presencial: User,
  sms: Phone,
  outro: Phone
};

const AlertaRetornos = ({ variant = 'popover' }) => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState([]);

  const loadRetornos = async () => {
    try {
      const response = await contatosAPI.getRetornos(20);
      setData(response.data);
    } catch (error) {
      console.error('Erro ao carregar retornos:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRetornos();
    // Atualizar a cada 5 minutos
    const interval = setInterval(loadRetornos, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleDismiss = (id) => {
    setDismissed([...dismissed, id]);
  };

  const handleMarcarRetorno = async (contatoId, e) => {
    e.stopPropagation();
    try {
      await contatosAPI.marcarRetorno(contatoId);
      loadRetornos();
    } catch (error) {
      console.error('Erro ao marcar retorno:', error);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = date - now;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMs < 0) {
      // Atrasado
      const atrasoHoras = Math.abs(diffHours);
      if (atrasoHoras < 24) {
        return `Atrasado ${atrasoHoras}h`;
      }
      return `Atrasado ${Math.abs(diffDays)} dia(s)`;
    } else if (diffHours < 1) {
      return 'Em breve';
    } else if (diffHours < 24) {
      return `Em ${diffHours}h`;
    } else {
      return `Em ${diffDays} dia(s)`;
    }
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading || !data) return null;

  const atrasados = (data.atrasados || []).filter(c => !dismissed.includes(c.id));
  const pendentes = (data.pendentes || []).filter(c => !dismissed.includes(c.id));
  const totalAlertas = atrasados.length + pendentes.length;

  if (totalAlertas === 0) return null;

  // Versão Banner para o topo do dashboard
  if (variant === 'banner' && atrasados.length > 0) {
    return (
      <Alert variant="destructive" className="mb-4 border-red-300 bg-red-50" data-testid="alerta-retornos-banner">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle className="flex items-center justify-between">
          <span>Retornos Atrasados</span>
          <Badge variant="destructive">{atrasados.length}</Badge>
        </AlertTitle>
        <AlertDescription>
          <div className="mt-2 space-y-2">
            {atrasados.slice(0, 3).map((contato) => {
              const TipoIcon = tipoIcons[contato.tipo] || Phone;
              return (
                <div 
                  key={contato.id}
                  className="flex items-center justify-between p-2 bg-white rounded border border-red-200 cursor-pointer hover:bg-red-50"
                  onClick={() => navigate(`/admin/pedido/${contato.pedido_id}`)}
                >
                  <div className="flex items-center gap-2">
                    <TipoIcon className="h-4 w-4 text-red-500" />
                    <div>
                      <p className="text-sm font-medium text-red-800">{contato.tipo_label}</p>
                      <p className="text-xs text-red-600">{contato.descricao?.slice(0, 50)}...</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-red-100 text-red-700 border-red-300">
                      {formatDate(contato.data_retorno)}
                    </Badge>
                    <Button 
                      size="sm" 
                      variant="ghost"
                      className="h-7 text-xs text-green-600 hover:text-green-700 hover:bg-green-50"
                      onClick={(e) => handleMarcarRetorno(contato.id, e)}
                    >
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Feito
                    </Button>
                  </div>
                </div>
              );
            })}
            {atrasados.length > 3 && (
              <p className="text-xs text-red-600 text-center">
                +{atrasados.length - 3} retorno(s) atrasado(s)
              </p>
            )}
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Versão Popover para o header
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm" 
          className="relative"
          data-testid="alerta-retornos-trigger"
        >
          <Bell className={`h-5 w-5 ${atrasados.length > 0 ? 'text-red-500' : 'text-gray-600'}`} />
          {totalAlertas > 0 && (
            <span className={`absolute -top-1 -right-1 h-5 w-5 rounded-full text-xs flex items-center justify-center text-white ${
              atrasados.length > 0 ? 'bg-red-500' : 'bg-amber-500'
            }`}>
              {totalAlertas > 9 ? '9+' : totalAlertas}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96 p-0" align="end">
        <div className="p-3 border-b bg-gray-50">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Retornos Pendentes
          </h3>
        </div>
        
        <div className="max-h-80 overflow-y-auto">
          {/* Atrasados */}
          {atrasados.length > 0 && (
            <div className="p-2">
              <p className="text-xs font-semibold text-red-600 mb-2 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                ATRASADOS ({atrasados.length})
              </p>
              {atrasados.map((contato) => {
                const TipoIcon = tipoIcons[contato.tipo] || Phone;
                return (
                  <div 
                    key={contato.id}
                    className="p-2 rounded bg-red-50 border border-red-100 mb-2 cursor-pointer hover:bg-red-100 transition-colors"
                    onClick={() => navigate(`/admin/pedido/${contato.pedido_id}`)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2 flex-1 min-w-0">
                        <TipoIcon className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-red-800 truncate">
                            {contato.tipo_label} - {contato.motivo_label}
                          </p>
                          <p className="text-xs text-red-600 truncate">{contato.descricao?.slice(0, 40)}...</p>
                          <p className="text-xs text-red-500 mt-1">
                            Previsto: {formatDateTime(contato.data_retorno)}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1 flex-shrink-0">
                        <Badge variant="destructive" className="text-xs">
                          {formatDate(contato.data_retorno)}
                        </Badge>
                        <Button 
                          size="sm" 
                          variant="ghost"
                          className="h-6 text-xs text-green-600 hover:text-green-700 hover:bg-green-50 px-2"
                          onClick={(e) => handleMarcarRetorno(contato.id, e)}
                        >
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Feito
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Pendentes (próximos) */}
          {pendentes.length > 0 && (
            <div className="p-2 border-t">
              <p className="text-xs font-semibold text-amber-600 mb-2 flex items-center gap-1">
                <Clock className="h-3 w-3" />
                PRÓXIMOS ({pendentes.length})
              </p>
              {pendentes.slice(0, 5).map((contato) => {
                const TipoIcon = tipoIcons[contato.tipo] || Phone;
                return (
                  <div 
                    key={contato.id}
                    className="p-2 rounded bg-amber-50 border border-amber-100 mb-2 cursor-pointer hover:bg-amber-100 transition-colors"
                    onClick={() => navigate(`/admin/pedido/${contato.pedido_id}`)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2 flex-1 min-w-0">
                        <TipoIcon className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-amber-800 truncate">
                            {contato.tipo_label} - {contato.motivo_label}
                          </p>
                          <p className="text-xs text-amber-600 truncate">{contato.descricao?.slice(0, 40)}...</p>
                        </div>
                      </div>
                      <Badge variant="outline" className="bg-amber-100 text-amber-700 border-amber-300 text-xs flex-shrink-0">
                        {formatDate(contato.data_retorno)}
                      </Badge>
                    </div>
                  </div>
                );
              })}
              {pendentes.length > 5 && (
                <p className="text-xs text-amber-600 text-center">
                  +{pendentes.length - 5} retorno(s) pendente(s)
                </p>
              )}
            </div>
          )}

          {/* Empty state */}
          {atrasados.length === 0 && pendentes.length === 0 && (
            <div className="p-6 text-center text-gray-500">
              <CheckCircle className="h-8 w-8 mx-auto text-green-500 mb-2" />
              <p className="text-sm">Nenhum retorno pendente!</p>
            </div>
          )}
        </div>

        <div className="p-2 border-t bg-gray-50">
          <Button 
            variant="ghost" 
            className="w-full text-sm text-gray-600 hover:text-gray-800"
            onClick={() => navigate('/bi')}
          >
            Ver Dashboard Completo
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
};

export default AlertaRetornos;
