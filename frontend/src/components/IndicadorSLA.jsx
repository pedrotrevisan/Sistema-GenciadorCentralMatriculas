import { Badge } from './ui/badge';
import { Clock, AlertTriangle, CheckCircle, Zap } from 'lucide-react';

/**
 * Indicador de SLA - mostra o tempo desde a criação do pedido
 * e indica se está dentro do prazo esperado
 */
const IndicadorSLA = ({ createdAt, status, compact = false }) => {
  if (!createdAt) return null;

  const created = new Date(createdAt);
  const now = new Date();
  const diffMs = now - created;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  // Definir SLAs por status (em horas)
  const SLA_CONFIG = {
    pendente: { limit: 24, warning: 12 },           // 24h para sair de pendente
    em_analise: { limit: 48, warning: 24 },         // 48h para analisar
    documentacao_pendente: { limit: 72, warning: 48 }, // 72h esperando docs
    aprovado: { limit: 24, warning: 12 },           // 24h para realizar
    realizado: { limit: 24, warning: 12 },          // 24h para exportar
    exportado: { limit: null, warning: null },      // Finalizado
    cancelado: { limit: null, warning: null }       // Finalizado
  };

  const sla = SLA_CONFIG[status] || { limit: 48, warning: 24 };
  
  // Determinar estado do SLA
  let slaStatus = 'ok';
  let color = 'text-green-600';
  let bgColor = 'bg-green-50';
  let borderColor = 'border-green-200';
  let Icon = CheckCircle;

  if (sla.limit) {
    if (diffHours > sla.limit) {
      slaStatus = 'critical';
      color = 'text-red-600';
      bgColor = 'bg-red-50';
      borderColor = 'border-red-200';
      Icon = AlertTriangle;
    } else if (diffHours > sla.warning) {
      slaStatus = 'warning';
      color = 'text-amber-600';
      bgColor = 'bg-amber-50';
      borderColor = 'border-amber-200';
      Icon = Clock;
    } else if (diffHours < 2) {
      slaStatus = 'fast';
      color = 'text-blue-600';
      bgColor = 'bg-blue-50';
      borderColor = 'border-blue-200';
      Icon = Zap;
    }
  }

  // Formatar tempo
  const formatTime = () => {
    if (diffDays > 0) {
      return `${diffDays}d ${diffHours % 24}h`;
    }
    if (diffHours > 0) {
      return `${diffHours}h`;
    }
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    return `${diffMinutes}min`;
  };

  // Versão compacta (para cards)
  if (compact) {
    return (
      <span 
        className={`inline-flex items-center gap-1 text-xs ${color}`}
        title={`Criado há ${formatTime()} - SLA: ${sla.limit ? sla.limit + 'h' : 'N/A'}`}
      >
        <Icon className="h-3 w-3" />
        {formatTime()}
      </span>
    );
  }

  // Versão completa (para detalhes)
  return (
    <Badge 
      variant="outline" 
      className={`${bgColor} ${color} ${borderColor} flex items-center gap-1`}
      data-testid="sla-indicator"
    >
      <Icon className="h-3 w-3" />
      <span>{formatTime()}</span>
      {sla.limit && (
        <span className="text-xs opacity-70">
          / {sla.limit}h
        </span>
      )}
    </Badge>
  );
};

/**
 * Barra de progresso do SLA
 */
export const SLAProgressBar = ({ createdAt, status }) => {
  if (!createdAt) return null;

  const created = new Date(createdAt);
  const now = new Date();
  const diffHours = (now - created) / (1000 * 60 * 60);

  const SLA_LIMITS = {
    pendente: 24,
    em_analise: 48,
    documentacao_pendente: 72,
    aprovado: 24,
    realizado: 24
  };

  const limit = SLA_LIMITS[status];
  if (!limit) return null;

  const progress = Math.min((diffHours / limit) * 100, 100);
  
  let barColor = 'bg-green-500';
  if (progress > 100) {
    barColor = 'bg-red-500';
  } else if (progress > 75) {
    barColor = 'bg-amber-500';
  } else if (progress > 50) {
    barColor = 'bg-yellow-500';
  }

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>SLA</span>
        <span>{Math.round(progress)}%</span>
      </div>
      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`h-full ${barColor} transition-all duration-300`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
    </div>
  );
};

export default IndicadorSLA;
