import React, { useState, useEffect } from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { 
  Clock, AlertTriangle, AlertCircle, CheckCircle, 
  Timer, Calendar, Bell, RefreshCw
} from 'lucide-react';
import api from '../services/api';

/**
 * Componente para exibir alerta visual de prazo de pendência
 * Integra com o endpoint /api/regras/prazos/pendencia
 */
export const AlertaPrazo = ({ 
  dataCriacao, 
  status,
  tamanho = 'normal', // 'compact', 'normal', 'full'
  showContador = true,
  onExpired 
}) => {
  const [prazoInfo, setPrazoInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (dataCriacao && status === 'documentacao_pendente') {
      calcularPrazo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataCriacao, status]);

  const calcularPrazo = async () => {
    setLoading(true);
    try {
      const response = await api.post('/regras/prazos/pendencia', {
        data_criacao: dataCriacao
      });
      setPrazoInfo(response.data);
      
      if (response.data.expirado && onExpired) {
        onExpired();
      }
    } catch (error) {
      console.error('Erro ao calcular prazo:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!prazoInfo || status !== 'documentacao_pendente') {
    return null;
  }

  const getCorClasse = () => {
    const cores = {
      'expirado': 'bg-red-100 text-red-800 border-red-300',
      'critico': 'bg-red-100 text-red-800 border-red-300 animate-pulse',
      'urgente': 'bg-orange-100 text-orange-800 border-orange-300',
      'normal': 'bg-yellow-100 text-yellow-800 border-yellow-300'
    };
    return cores[prazoInfo.nivel_alerta] || cores['normal'];
  };

  const getIcone = () => {
    const icones = {
      'expirado': <AlertCircle className="w-4 h-4" />,
      'critico': <AlertTriangle className="w-4 h-4" />,
      'urgente': <Clock className="w-4 h-4" />,
      'normal': <Timer className="w-4 h-4" />
    };
    return icones[prazoInfo.nivel_alerta] || icones['normal'];
  };

  if (tamanho === 'compact') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge className={`${getCorClasse()} cursor-help`} data-testid="alerta-prazo-badge">
              {getIcone()}
              <span className="ml-1">{prazoInfo.dias_restantes}d</span>
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>{prazoInfo.mensagem}</p>
            <p className="text-xs text-slate-500">Limite: {new Date(prazoInfo.data_limite).toLocaleDateString('pt-BR')}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  if (tamanho === 'full') {
    return (
      <Card className={`${getCorClasse()} border`} data-testid="alerta-prazo-card">
        <CardHeader className="py-3">
          <CardTitle className="text-sm flex items-center gap-2">
            {getIcone()}
            Prazo de Pendência Documental
          </CardTitle>
        </CardHeader>
        <CardContent className="py-2">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{prazoInfo.mensagem}</p>
              <p className="text-sm opacity-75">
                Limite: {new Date(prazoInfo.data_limite).toLocaleDateString('pt-BR', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric'
                })}
              </p>
            </div>
            {showContador && (
              <div className="text-center">
                <div className="text-3xl font-bold">{prazoInfo.dias_restantes}</div>
                <div className="text-xs">dias</div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Tamanho normal (padrão)
  return (
    <div 
      className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getCorClasse()}`}
      data-testid="alerta-prazo"
    >
      {getIcone()}
      <span className="text-sm font-medium">{prazoInfo.mensagem}</span>
      {showContador && prazoInfo.dias_restantes >= 0 && (
        <Badge variant="outline" className="ml-auto">
          {prazoInfo.dias_restantes}d restantes
        </Badge>
      )}
    </div>
  );
};

/**
 * Componente para exibir indicador de SLA
 */
export const IndicadorSLAv2 = ({ dataCriacao, statusAtual }) => {
  const [slaInfo, setSlaInfo] = useState(null);

  useEffect(() => {
    if (dataCriacao && statusAtual) {
      calcularSLA();
    }
  }, [dataCriacao, statusAtual]);

  const calcularSLA = async () => {
    try {
      const response = await api.get('/regras/prazos/sla', {
        params: {
          data_criacao: dataCriacao,
          status_atual: statusAtual
        }
      });
      setSlaInfo(response.data);
    } catch (error) {
      console.error('Erro ao calcular SLA:', error);
    }
  };

  if (!slaInfo) return null;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge 
            variant={slaInfo.dentro_sla ? "outline" : "destructive"}
            className={`cursor-help ${slaInfo.dentro_sla ? 'border-green-300 text-green-700' : ''}`}
            data-testid="indicador-sla"
          >
            {slaInfo.dentro_sla ? (
              <CheckCircle className="w-3 h-3 mr-1" />
            ) : (
              <AlertTriangle className="w-3 h-3 mr-1" />
            )}
            {slaInfo.dias_corridos}d
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p>{slaInfo.dentro_sla ? 'Dentro do SLA' : `Atrasado ${slaInfo.dias_atraso}d`}</p>
          <p className="text-xs">SLA: {slaInfo.sla_dias} dias - {slaInfo.sla_descricao}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

/**
 * Componente de contador regressivo visual
 */
export const ContadorRegressivo = ({ dataLimite, onExpire }) => {
  const [tempo, setTempo] = useState({ dias: 0, horas: 0, minutos: 0 });
  const [expirado, setExpirado] = useState(false);

  useEffect(() => {
    const calcular = () => {
      const agora = new Date();
      const limite = new Date(dataLimite);
      const diff = limite - agora;

      if (diff <= 0) {
        setExpirado(true);
        if (onExpire) onExpire();
        return;
      }

      const dias = Math.floor(diff / (1000 * 60 * 60 * 24));
      const horas = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutos = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

      setTempo({ dias, horas, minutos });
    };

    calcular();
    const interval = setInterval(calcular, 60000); // Atualiza a cada minuto

    return () => clearInterval(interval);
  }, [dataLimite, onExpire]);

  if (expirado) {
    return (
      <div className="flex items-center gap-2 text-red-600 animate-pulse" data-testid="contador-expirado">
        <AlertCircle className="w-5 h-5" />
        <span className="font-bold">PRAZO EXPIRADO</span>
      </div>
    );
  }

  const getCorTexto = () => {
    if (tempo.dias === 0) return 'text-red-600';
    if (tempo.dias <= 2) return 'text-orange-600';
    return 'text-yellow-600';
  };

  return (
    <div className={`flex items-center gap-3 ${getCorTexto()}`} data-testid="contador-regressivo">
      <div className="text-center">
        <div className="text-2xl font-bold">{tempo.dias}</div>
        <div className="text-xs uppercase">dias</div>
      </div>
      <div className="text-xl font-light">:</div>
      <div className="text-center">
        <div className="text-2xl font-bold">{String(tempo.horas).padStart(2, '0')}</div>
        <div className="text-xs uppercase">horas</div>
      </div>
      <div className="text-xl font-light">:</div>
      <div className="text-center">
        <div className="text-2xl font-bold">{String(tempo.minutos).padStart(2, '0')}</div>
        <div className="text-xs uppercase">min</div>
      </div>
    </div>
  );
};

export default AlertaPrazo;
