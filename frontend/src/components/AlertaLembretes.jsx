import { useState, useEffect, useCallback } from 'react';
import { Bell, X, Clock, CheckCircle } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AlertaLembretes = () => {
  const [lembretes, setLembretes] = useState([]);
  const [alertaAtivo, setAlertaAtivo] = useState(null);
  const [lembretesNotificados, setLembretesNotificados] = useState(new Set());

  const carregarLembretes = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${API_URL}/api/apoio/meu-dia`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setLembretes(data.lembretes || []);
      }
    } catch (error) {
      console.error('Erro ao carregar lembretes:', error);
    }
  }, []);

  // Carregar lembretes ao montar e a cada 1 minuto
  useEffect(() => {
    carregarLembretes();
    const interval = setInterval(carregarLembretes, 60000);
    return () => clearInterval(interval);
  }, [carregarLembretes]);

  // Verificar se algum lembrete chegou no horário
  useEffect(() => {
    const verificarHorarios = () => {
      const agora = new Date();
      const horaAtual = agora.toTimeString().slice(0, 5); // HH:MM

      lembretes.forEach(lembrete => {
        if (lembrete.horario && !lembretesNotificados.has(lembrete.id)) {
          // Verificar se o horário do lembrete é agora (com 1 minuto de tolerância)
          const [horaLembrete, minLembrete] = lembrete.horario.split(':').map(Number);
          const [horaAgora, minAgora] = horaAtual.split(':').map(Number);
          
          const minutosTotaisLembrete = horaLembrete * 60 + minLembrete;
          const minutosTotaisAgora = horaAgora * 60 + minAgora;
          
          // Se estamos no minuto do lembrete ou 1 minuto depois
          if (minutosTotaisAgora >= minutosTotaisLembrete && 
              minutosTotaisAgora <= minutosTotaisLembrete + 1) {
            // Disparar alerta!
            setAlertaAtivo(lembrete);
            setLembretesNotificados(prev => new Set([...prev, lembrete.id]));
            
            // Tocar som de notificação (se disponível)
            try {
              const audio = new Audio('/notification.mp3');
              audio.play().catch(() => {});
            } catch (e) {}
            
            // Também mostrar toast
            toast.info(`Lembrete: ${lembrete.titulo}`, {
              description: lembrete.descricao || `Horário: ${lembrete.horario}`,
              duration: 10000
            });
          }
        }
      });
    };

    verificarHorarios();
    const interval = setInterval(verificarHorarios, 30000); // Verificar a cada 30 segundos
    return () => clearInterval(interval);
  }, [lembretes, lembretesNotificados]);

  const fecharAlerta = () => {
    setAlertaAtivo(null);
  };

  const marcarConcluido = async (lembrete) => {
    try {
      const token = localStorage.getItem('token');
      const lembreteId = lembrete.id;
      
      // Determinar endpoint correto baseado na fonte do lembrete
      let endpoint;
      if (lembrete.fonte === 'tarefa') {
        endpoint = `/api/apoio/tarefas/${lembreteId}/concluir`;
      } else if (lembrete.fonte === 'lembrete') {
        endpoint = `/api/apoio/lembretes/${lembreteId}/concluir`;
      } else {
        // Alertas operacionais não são "concluíveis" - apenas fechamos o modal
        setAlertaAtivo(null);
        toast.info('Alerta fechado. Acesse a seção correspondente para mais ações.');
        return;
      }
      
      await fetch(`${API_URL}${endpoint}`, {
        method: 'PATCH',  // Corrigido de POST para PATCH
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setAlertaAtivo(null);
      carregarLembretes();
      toast.success('Marcado como concluído!');
    } catch (error) {
      console.error('Erro ao marcar como concluído:', error);
      toast.error('Erro ao marcar como concluído');
    }
  };

  if (!alertaAtivo) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 animate-in fade-in">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden animate-in zoom-in-95">
        {/* Header com animação */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-4 flex items-center gap-3">
          <div className="bg-white/20 p-2 rounded-full animate-pulse">
            <Bell className="h-6 w-6 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-white font-bold text-lg">Lembrete!</h3>
            <p className="text-white/80 text-sm flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {alertaAtivo.horario}
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/20"
            onClick={fecharAlerta}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Conteúdo */}
        <div className="p-6">
          <h4 className="text-xl font-semibold text-gray-800 mb-2">
            {alertaAtivo.titulo}
          </h4>
          {alertaAtivo.descricao && (
            <p className="text-gray-600 mb-4">
              {alertaAtivo.descricao}
            </p>
          )}
          
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
              {alertaAtivo.tipo || 'Lembrete'}
            </span>
            {alertaAtivo.fonte === 'tarefa' && (
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                Tarefa do dia
              </span>
            )}
          </div>

          {/* Botões de ação */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              className="flex-1"
              onClick={fecharAlerta}
            >
              Adiar (5 min)
            </Button>
            <Button
              className="flex-1 bg-green-600 hover:bg-green-700"
              onClick={() => marcarConcluido(alertaAtivo)}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Concluído
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertaLembretes;
