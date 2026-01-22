import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  FileText,
  Download,
  RefreshCw,
  Plus,
  AlertCircle,
  History
} from 'lucide-react';
import { pedidosAPI } from '../services/api';

const iconMap = {
  plus: Plus,
  check: CheckCircle,
  'check-circle': CheckCircle,
  x: XCircle,
  file: FileText,
  download: Download,
  refresh: RefreshCw,
  circle: Clock,
  alert: AlertCircle,
};

const colorMap = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  yellow: 'bg-yellow-500',
  orange: 'bg-orange-500',
  red: 'bg-red-500',
  gray: 'bg-gray-400',
};

const TimelineAuditoria = ({ pedidoId }) => {
  const [loading, setLoading] = useState(true);
  const [timeline, setTimeline] = useState([]);
  const [totalEventos, setTotalEventos] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTimeline = async () => {
      if (!pedidoId) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await pedidosAPI.buscarTimeline(pedidoId);
        setTimeline(response.data.timeline || []);
        setTotalEventos(response.data.total_eventos || 0);
      } catch (err) {
        console.error('Erro ao carregar timeline:', err);
        setError('Erro ao carregar histórico');
      } finally {
        setLoading(false);
      }
    };

    fetchTimeline();
  }, [pedidoId]);

  const formatDateTime = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatRelativeTime = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'agora';
    if (diffMins < 60) return `há ${diffMins} min`;
    if (diffHours < 24) return `há ${diffHours}h`;
    if (diffDays < 7) return `há ${diffDays} dias`;
    return '';
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <History className="h-4 w-4" />
            Timeline de Auditoria
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-4">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <History className="h-4 w-4" />
            Timeline de Auditoria
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-slate-500">
            <AlertCircle className="h-8 w-8 mx-auto mb-2 text-red-400" />
            <p>{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (timeline.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <History className="h-4 w-4" />
            Timeline de Auditoria
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-slate-500">
            <Clock className="h-8 w-8 mx-auto mb-2 text-slate-300" />
            <p>Nenhum evento registrado</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="timeline-auditoria">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-[#004587]" />
            Timeline de Auditoria
          </div>
          <Badge variant="secondary" className="font-normal">
            {totalEventos} {totalEventos === 1 ? 'evento' : 'eventos'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Linha vertical conectando os eventos */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-200" />
          
          <div className="space-y-6">
            {timeline.map((evento, index) => {
              const IconComponent = iconMap[evento.icon] || Clock;
              const bgColor = colorMap[evento.color] || colorMap.gray;
              const isFirst = index === 0;
              const isLast = index === timeline.length - 1;

              return (
                <div 
                  key={evento.id} 
                  className="relative flex gap-4"
                  data-testid={`timeline-evento-${index}`}
                >
                  {/* Ícone do evento */}
                  <div 
                    className={`
                      relative z-10 flex items-center justify-center 
                      w-8 h-8 rounded-full text-white shadow-md
                      ${bgColor}
                      ${isLast ? 'ring-4 ring-offset-2 ring-slate-100' : ''}
                    `}
                  >
                    <IconComponent className="h-4 w-4" />
                  </div>

                  {/* Conteúdo do evento */}
                  <div className={`flex-1 pb-2 ${!isLast ? 'border-b border-slate-100' : ''}`}>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                      <h4 className="font-semibold text-slate-900 text-sm">
                        {evento.acao_label}
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span>{formatDateTime(evento.timestamp)}</span>
                        {formatRelativeTime(evento.timestamp) && (
                          <Badge variant="outline" className="text-xs px-1.5 py-0">
                            {formatRelativeTime(evento.timestamp)}
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    <p className="text-sm text-slate-600 mt-1">
                      por <span className="font-medium text-[#004587]">{evento.usuario_nome}</span>
                    </p>
                    
                    {evento.detalhes && (
                      <p className="text-sm text-slate-500 mt-1 bg-slate-50 px-2 py-1 rounded">
                        {evento.detalhes}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TimelineAuditoria;
