import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { pedidosAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { toast } from 'sonner';
import {
  Search,
  RefreshCw,
  GripVertical,
  User,
  Building,
  Calendar,
  Clock,
  FileText,
  ChevronRight,
  Filter,
  LayoutGrid
} from 'lucide-react';

// Configuração de status do Kanban
const KANBAN_COLUMNS = [
  { id: 'pendente', title: 'Pendente', color: 'bg-amber-500', bgColor: 'bg-amber-50', borderColor: 'border-amber-200' },
  { id: 'em_analise', title: 'Em Análise', color: 'bg-blue-500', bgColor: 'bg-blue-50', borderColor: 'border-blue-200' },
  { id: 'documentacao_pendente', title: 'Doc. Pendente', color: 'bg-orange-500', bgColor: 'bg-orange-50', borderColor: 'border-orange-200' },
  { id: 'aprovado', title: 'Aprovado', color: 'bg-green-500', bgColor: 'bg-green-50', borderColor: 'border-green-200' },
  { id: 'realizado', title: 'Realizado', color: 'bg-purple-500', bgColor: 'bg-purple-50', borderColor: 'border-purple-200' },
  { id: 'exportado', title: 'Exportado', color: 'bg-pink-500', bgColor: 'bg-pink-50', borderColor: 'border-pink-200' },
  { id: 'cancelado', title: 'Cancelado', color: 'bg-gray-500', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' }
];

// Componente do Card arrastável
const KanbanCard = ({ pedido, isDragging }) => {
  const navigate = useNavigate();
  
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: pedido.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit'
    });
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white rounded-lg border shadow-sm p-3 mb-2 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow ${
        isDragging ? 'shadow-lg ring-2 ring-blue-400' : ''
      }`}
      data-testid={`kanban-card-${pedido.id}`}
    >
      <div className="flex items-start gap-2">
        <button 
          {...attributes} 
          {...listeners}
          className="mt-1 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing"
        >
          <GripVertical className="h-4 w-4" />
        </button>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-xs font-mono text-blue-600 font-semibold">
              {pedido.protocolo}
            </span>
            <button
              onClick={() => navigate(`/admin/pedido/${pedido.id}`)}
              className="text-gray-400 hover:text-blue-600"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
          
          <p className="text-sm font-medium text-gray-900 truncate mb-1">
            {pedido.alunos?.[0]?.nome || 'Sem aluno'}
          </p>
          
          <p className="text-xs text-gray-600 truncate mb-2">
            {pedido.curso?.nome || pedido.curso_nome || '-'}
          </p>
          
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Building className="h-3 w-3" />
              {pedido.projeto?.nome || pedido.projeto_nome || '-'}
            </span>
          </div>
          
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <Calendar className="h-3 w-3" />
              {formatDate(pedido.created_at)}
            </span>
            {pedido.alunos?.length > 1 && (
              <Badge variant="outline" className="text-xs">
                +{pedido.alunos.length - 1} alunos
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Componente da Coluna do Kanban
const KanbanColumn = ({ column, pedidos, onCardClick }) => {
  const count = pedidos.length;

  return (
    <div 
      className={`flex-shrink-0 w-72 rounded-lg ${column.bgColor} border ${column.borderColor}`}
      data-testid={`kanban-column-${column.id}`}
    >
      <div className={`p-3 rounded-t-lg ${column.bgColor} border-b ${column.borderColor}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${column.color}`} />
            <h3 className="font-semibold text-gray-800 text-sm">{column.title}</h3>
          </div>
          <Badge variant="outline" className="bg-white">
            {count}
          </Badge>
        </div>
      </div>
      
      <div className="p-2 min-h-[400px] max-h-[calc(100vh-280px)] overflow-y-auto">
        <SortableContext
          items={pedidos.map(p => p.id)}
          strategy={verticalListSortingStrategy}
        >
          {pedidos.map((pedido) => (
            <KanbanCard 
              key={pedido.id} 
              pedido={pedido}
              onCardClick={onCardClick}
            />
          ))}
        </SortableContext>
        
        {pedidos.length === 0 && (
          <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
            Nenhuma matrícula
          </div>
        )}
      </div>
    </div>
  );
};

// Card overlay durante o drag
const DragOverlayCard = ({ pedido }) => {
  if (!pedido) return null;
  
  return (
    <div className="bg-white rounded-lg border-2 border-blue-400 shadow-xl p-3 w-72 cursor-grabbing">
      <div className="flex items-start gap-2">
        <GripVertical className="h-4 w-4 text-gray-400 mt-1" />
        <div className="flex-1">
          <span className="text-xs font-mono text-blue-600 font-semibold">
            {pedido.protocolo}
          </span>
          <p className="text-sm font-medium text-gray-900 truncate mt-1">
            {pedido.alunos?.[0]?.nome || 'Sem aluno'}
          </p>
          <p className="text-xs text-gray-600 truncate">
            {pedido.curso?.nome || pedido.curso_nome || '-'}
          </p>
        </div>
      </div>
    </div>
  );
};

const KanbanPage = () => {
  const navigate = useNavigate();
  const [pedidos, setPedidos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeId, setActiveId] = useState(null);
  const [updating, setUpdating] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const loadPedidos = async () => {
    try {
      // Carregar todos os pedidos (sem paginação para o kanban)
      const response = await pedidosAPI.listar({ por_pagina: 200 });
      setPedidos(response.data.pedidos || []);
    } catch (error) {
      console.error('Erro ao carregar pedidos:', error);
      toast.error('Erro ao carregar matrículas');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadPedidos();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadPedidos();
  };

  // Filtrar pedidos por busca
  const filteredPedidos = useMemo(() => {
    if (!searchTerm) return pedidos;
    
    const term = searchTerm.toLowerCase();
    return pedidos.filter(p => 
      p.protocolo?.toLowerCase().includes(term) ||
      p.alunos?.[0]?.nome?.toLowerCase().includes(term) ||
      p.curso_nome?.toLowerCase().includes(term) ||
      p.projeto_nome?.toLowerCase().includes(term)
    );
  }, [pedidos, searchTerm]);

  // Agrupar pedidos por status
  const pedidosByStatus = useMemo(() => {
    const grouped = {};
    KANBAN_COLUMNS.forEach(col => {
      grouped[col.id] = filteredPedidos.filter(p => p.status === col.id);
    });
    return grouped;
  }, [filteredPedidos]);

  // Encontrar pedido ativo durante drag
  const activePedido = useMemo(() => {
    if (!activeId) return null;
    return pedidos.find(p => p.id === activeId);
  }, [activeId, pedidos]);

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const pedidoId = active.id;
    const pedido = pedidos.find(p => p.id === pedidoId);
    
    if (!pedido) return;

    // Encontrar coluna de destino
    let newStatus = null;
    
    // Se soltou em cima de outro card, pegar o status desse card
    const overPedido = pedidos.find(p => p.id === over.id);
    if (overPedido) {
      newStatus = overPedido.status;
    } else {
      // Se soltou na coluna diretamente
      const column = KANBAN_COLUMNS.find(c => c.id === over.id);
      if (column) {
        newStatus = column.id;
      }
    }

    if (!newStatus || newStatus === pedido.status) return;

    // Atualizar status no backend
    setUpdating(true);
    try {
      await pedidosAPI.atualizarStatus(pedidoId, { status: newStatus });
      
      // Atualizar localmente
      setPedidos(prev => prev.map(p => 
        p.id === pedidoId ? { ...p, status: newStatus } : p
      ));
      
      toast.success(`Status alterado para "${KANBAN_COLUMNS.find(c => c.id === newStatus)?.title}"`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar status');
      // Recarregar para garantir consistência
      loadPedidos();
    } finally {
      setUpdating(false);
    }
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  if (loading) {
    return (
      <div className="space-y-6" data-testid="kanban-loading">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {[1, 2, 3, 4, 5].map(i => (
            <Skeleton key={i} className="h-96 w-72 flex-shrink-0" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="kanban-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <LayoutGrid className="h-6 w-6 text-[#004587]" />
            Kanban de Matrículas
          </h1>
          <p className="text-gray-600 mt-1">
            Arraste os cards para alterar o status das matrículas
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Buscar matrícula..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64"
              data-testid="kanban-search"
            />
          </div>
          <Button 
            variant="outline" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      {/* Estatísticas rápidas */}
      <div className="flex gap-4 flex-wrap">
        {KANBAN_COLUMNS.slice(0, 5).map(col => (
          <div key={col.id} className="flex items-center gap-2 text-sm">
            <div className={`w-3 h-3 rounded-full ${col.color}`} />
            <span className="text-gray-600">{col.title}:</span>
            <span className="font-semibold">{pedidosByStatus[col.id]?.length || 0}</span>
          </div>
        ))}
      </div>

      {/* Kanban Board */}
      <div className="relative">
        {updating && (
          <div className="absolute inset-0 bg-white/50 z-10 flex items-center justify-center">
            <div className="bg-white rounded-lg shadow-lg p-4 flex items-center gap-3">
              <RefreshCw className="h-5 w-5 animate-spin text-blue-600" />
              <span>Atualizando status...</span>
            </div>
          </div>
        )}
        
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
          <div className="flex gap-4 overflow-x-auto pb-4 -mx-4 px-4">
            {KANBAN_COLUMNS.map(column => (
              <KanbanColumn
                key={column.id}
                column={column}
                pedidos={pedidosByStatus[column.id] || []}
              />
            ))}
          </div>

          <DragOverlay>
            <DragOverlayCard pedido={activePedido} />
          </DragOverlay>
        </DndContext>
      </div>

      {/* Legenda */}
      <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
        <p className="text-sm text-gray-600 flex items-center gap-2">
          <GripVertical className="h-4 w-4" />
          <strong>Dica:</strong> Arraste um card pelo ícone de grip para movê-lo entre colunas
        </p>
      </div>
    </div>
  );
};

export default KanbanPage;
