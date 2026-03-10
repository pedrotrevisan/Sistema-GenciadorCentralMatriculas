import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from './ui/popover';
import {
  Bell,
  AlertTriangle,
  Clock,
  DollarSign,
  GraduationCap,
  ChevronRight,
  RefreshCw,
  CheckCircle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Ícones por tipo de alerta
const tipoIcons = {
  critico: AlertTriangle,
  sla_risco: Clock,
  reembolso: DollarSign,
  vagas: GraduationCap
};

// Cores por tipo
const tipoCores = {
  critico: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', badge: 'bg-red-500' },
  sla_risco: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', badge: 'bg-amber-500' },
  reembolso: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', badge: 'bg-orange-500' },
  vagas: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', badge: 'bg-purple-500' }
};

// Labels por tipo
const tipoLabels = {
  critico: 'Crítico',
  sla_risco: 'SLA em Risco',
  reembolso: 'Reembolso',
  vagas: 'Vagas'
};

const CentralAlertas = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  const loadAlertas = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/alertas/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('Erro ao carregar alertas:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlertas();
    // Atualizar a cada 3 minutos
    const interval = setInterval(loadAlertas, 3 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleNavigate = (url) => {
    setIsOpen(false);
    navigate(url);
  };

  const totalAlertas = data?.estatisticas?.total || 0;
  const criticos = data?.estatisticas?.criticos || 0;

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm" 
          className="relative text-white hover:bg-white/10"
          data-testid="central-alertas-trigger"
        >
          <Bell className={`h-5 w-5 ${criticos > 0 ? 'text-red-400 animate-pulse' : ''}`} />
          {totalAlertas > 0 && (
            <span className={`absolute -top-1 -right-1 h-5 w-5 rounded-full text-xs flex items-center justify-center text-white ${
              criticos > 0 ? 'bg-red-500' : 'bg-amber-500'
            }`}>
              {totalAlertas > 9 ? '9+' : totalAlertas}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[420px] p-0" align="end">
        {/* Header */}
        <div className="p-3 border-b bg-gradient-to-r from-[#004587] to-[#0066cc] text-white rounded-t-lg">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm flex items-center gap-2">
              <Bell className="h-4 w-4" />
              Central de Alertas
            </h3>
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-7 w-7 p-0 hover:bg-white/20"
              onClick={loadAlertas}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
          
          {/* Stats */}
          {data?.estatisticas && (
            <div className="flex gap-3 mt-2 text-xs">
              {data.estatisticas.criticos > 0 && (
                <span className="flex items-center gap-1 bg-red-500/30 px-2 py-0.5 rounded">
                  <AlertTriangle className="h-3 w-3" />
                  {data.estatisticas.criticos} crítico(s)
                </span>
              )}
              {data.estatisticas.sla_risco > 0 && (
                <span className="flex items-center gap-1 bg-amber-500/30 px-2 py-0.5 rounded">
                  <Clock className="h-3 w-3" />
                  {data.estatisticas.sla_risco} em risco
                </span>
              )}
              {data.estatisticas.reembolsos > 0 && (
                <span className="flex items-center gap-1 bg-orange-500/30 px-2 py-0.5 rounded">
                  <DollarSign className="h-3 w-3" />
                  {data.estatisticas.reembolsos} reembolso(s)
                </span>
              )}
            </div>
          )}
        </div>
        
        {/* Lista de Alertas */}
        <div className="max-h-[400px] overflow-y-auto">
          {loading && !data ? (
            <div className="p-6 text-center text-gray-500">
              <RefreshCw className="h-6 w-6 mx-auto animate-spin mb-2" />
              <p className="text-sm">Carregando alertas...</p>
            </div>
          ) : totalAlertas === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <CheckCircle className="h-10 w-10 mx-auto text-green-500 mb-2" />
              <p className="text-sm font-medium">Tudo em dia!</p>
              <p className="text-xs text-gray-400 mt-1">Nenhum alerta ativo no momento</p>
            </div>
          ) : (
            <div className="p-2 space-y-2">
              {data?.alertas?.map((alerta) => {
                const Icon = tipoIcons[alerta.tipo] || AlertTriangle;
                const cores = tipoCores[alerta.tipo] || tipoCores.critico;
                
                return (
                  <div 
                    key={alerta.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md ${cores.bg} ${cores.border}`}
                    onClick={() => handleNavigate(alerta.acao?.url || '/admin')}
                    data-testid={`alerta-item-${alerta.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-1.5 rounded-full ${cores.badge} bg-opacity-20`}>
                        <Icon className={`h-4 w-4 ${cores.text}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={`${cores.badge} text-white text-[10px] px-1.5 py-0`}>
                            {tipoLabels[alerta.tipo]}
                          </Badge>
                          {alerta.prioridade === 'alta' && (
                            <span className="text-[10px] text-red-600 font-semibold">URGENTE</span>
                          )}
                        </div>
                        <p className={`text-sm font-medium ${cores.text}`}>
                          {alerta.titulo}
                        </p>
                        <p className="text-xs text-gray-600 truncate">
                          {alerta.descricao}
                        </p>
                      </div>
                      <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0 mt-1" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-2 border-t bg-gray-50 rounded-b-lg">
          <Button 
            variant="ghost" 
            className="w-full text-sm text-[#004587] hover:text-[#003366] hover:bg-[#004587]/5"
            onClick={() => handleNavigate('/sla')}
          >
            Ver Dashboard SLA Completo
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
};

export default CentralAlertas;
