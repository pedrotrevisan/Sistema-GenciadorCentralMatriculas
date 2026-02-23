import { useState, useEffect, createContext, useContext } from 'react';
import { Button } from './ui/button';
import { Star } from 'lucide-react';
import { toast } from 'sonner';

// Context para gerenciar favoritos globalmente
const FavoritosContext = createContext();

export const useFavoritos = () => {
  const context = useContext(FavoritosContext);
  if (!context) {
    throw new Error('useFavoritos must be used within FavoritosProvider');
  }
  return context;
};

export const FavoritosProvider = ({ children }) => {
  const [favoritos, setFavoritos] = useState(() => {
    // Carregar do localStorage
    const saved = localStorage.getItem('synapse_favoritos');
    return saved ? JSON.parse(saved) : [];
  });

  // Salvar no localStorage quando mudar
  useEffect(() => {
    localStorage.setItem('synapse_favoritos', JSON.stringify(favoritos));
  }, [favoritos]);

  const addFavorito = (pedidoId, pedidoInfo) => {
    setFavoritos(prev => {
      if (prev.find(f => f.id === pedidoId)) return prev;
      return [...prev, { 
        id: pedidoId, 
        protocolo: pedidoInfo?.protocolo,
        aluno: pedidoInfo?.aluno,
        addedAt: new Date().toISOString()
      }];
    });
    toast.success('Adicionado aos favoritos!');
  };

  const removeFavorito = (pedidoId) => {
    setFavoritos(prev => prev.filter(f => f.id !== pedidoId));
    toast.success('Removido dos favoritos');
  };

  const toggleFavorito = (pedidoId, pedidoInfo) => {
    if (isFavorito(pedidoId)) {
      removeFavorito(pedidoId);
    } else {
      addFavorito(pedidoId, pedidoInfo);
    }
  };

  const isFavorito = (pedidoId) => {
    return favoritos.some(f => f.id === pedidoId);
  };

  return (
    <FavoritosContext.Provider value={{
      favoritos,
      addFavorito,
      removeFavorito,
      toggleFavorito,
      isFavorito,
      count: favoritos.length
    }}>
      {children}
    </FavoritosContext.Provider>
  );
};

// Botão de favorito
const BotaoFavorito = ({ pedidoId, pedidoInfo, size = 'sm', showLabel = false }) => {
  const { toggleFavorito, isFavorito } = useFavoritos();
  const isFav = isFavorito(pedidoId);

  return (
    <Button
      variant="ghost"
      size={size}
      onClick={(e) => {
        e.stopPropagation();
        toggleFavorito(pedidoId, pedidoInfo);
      }}
      className={`${isFav ? 'text-yellow-500 hover:text-yellow-600' : 'text-gray-400 hover:text-yellow-500'}`}
      title={isFav ? 'Remover dos favoritos' : 'Adicionar aos favoritos'}
      data-testid="favorito-btn"
    >
      <Star className={`h-4 w-4 ${isFav ? 'fill-current' : ''}`} />
      {showLabel && (
        <span className="ml-1">{isFav ? 'Favoritado' : 'Favoritar'}</span>
      )}
    </Button>
  );
};

export default BotaoFavorito;
