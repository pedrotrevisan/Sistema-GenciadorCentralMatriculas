import { useEffect, useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Badge } from './ui/badge';
import { Keyboard } from 'lucide-react';

// Definição dos atalhos
const SHORTCUTS = [
  { keys: ['g', 'd'], action: 'dashboard', label: 'Ir para Dashboard', path: '/admin' },
  { keys: ['g', 'k'], action: 'kanban', label: 'Ir para Kanban', path: '/kanban' },
  { keys: ['g', 'b'], action: 'bi', label: 'Ir para Dashboard BI', path: '/bi' },
  { keys: ['g', 'p'], action: 'pedidos', label: 'Ir para Pedidos', path: '/admin/pedidos' },
  { keys: ['g', 'n'], action: 'novo', label: 'Nova Solicitação', path: '/admin/novo-pedido' },
  { keys: ['g', 'e'], action: 'pendencias', label: 'Ir para Pendências', path: '/pendencias' },
  { keys: ['g', 'r'], action: 'reembolsos', label: 'Ir para Reembolsos', path: '/reembolsos' },
  { keys: ['?'], action: 'help', label: 'Mostrar atalhos', path: null },
  { keys: ['Escape'], action: 'close', label: 'Fechar modal/menu', path: null },
];

/**
 * Hook para gerenciar atalhos de teclado
 */
export const useKeyboardShortcuts = () => {
  const navigate = useNavigate();
  const [showHelp, setShowHelp] = useState(false);
  const [keySequence, setKeySequence] = useState([]);

  const handleKeyDown = useCallback((event) => {
    // Ignorar se estiver digitando em input/textarea
    const target = event.target;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      return;
    }

    const key = event.key.toLowerCase();

    // Atalho de ajuda
    if (key === '?' || (event.shiftKey && key === '/')) {
      event.preventDefault();
      setShowHelp(true);
      return;
    }

    // Escape fecha modais
    if (key === 'escape') {
      setShowHelp(false);
      setKeySequence([]);
      return;
    }

    // Adicionar tecla à sequência
    const newSequence = [...keySequence, key].slice(-2);
    setKeySequence(newSequence);

    // Verificar atalhos
    const matchedShortcut = SHORTCUTS.find(shortcut => {
      if (shortcut.keys.length === 1) {
        return shortcut.keys[0] === key;
      }
      return (
        shortcut.keys.length === newSequence.length &&
        shortcut.keys.every((k, i) => k === newSequence[i])
      );
    });

    if (matchedShortcut && matchedShortcut.path) {
      event.preventDefault();
      navigate(matchedShortcut.path);
      setKeySequence([]);
    }

    // Limpar sequência após timeout
    setTimeout(() => {
      setKeySequence([]);
    }, 1000);
  }, [keySequence, navigate]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return { showHelp, setShowHelp, keySequence };
};

/**
 * Modal de ajuda com atalhos
 */
export const KeyboardShortcutsModal = ({ open, onClose }) => {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Atalhos de Teclado
          </DialogTitle>
          <DialogDescription>
            Use estes atalhos para navegar rapidamente
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
              Navegação
            </h4>
            <p className="text-xs text-gray-400 mb-2">
              Pressione <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">g</kbd> seguido da tecla
            </p>
          </div>

          <div className="space-y-2">
            {SHORTCUTS.filter(s => s.path).map((shortcut) => (
              <div
                key={shortcut.action}
                className="flex items-center justify-between py-2 px-3 rounded bg-gray-50"
              >
                <span className="text-sm text-gray-700">{shortcut.label}</span>
                <div className="flex items-center gap-1">
                  {shortcut.keys.map((key, i) => (
                    <span key={i} className="flex items-center gap-1">
                      <Badge variant="outline" className="font-mono text-xs px-2">
                        {key.toUpperCase()}
                      </Badge>
                      {i < shortcut.keys.length - 1 && (
                        <span className="text-gray-400 text-xs">+</span>
                      )}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t">
            <div className="flex items-center justify-between py-2 px-3 rounded bg-gray-50">
              <span className="text-sm text-gray-700">Mostrar esta ajuda</span>
              <Badge variant="outline" className="font-mono text-xs px-2">?</Badge>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

/**
 * Componente wrapper que adiciona atalhos à aplicação
 */
const KeyboardShortcuts = ({ children }) => {
  const { showHelp, setShowHelp } = useKeyboardShortcuts();

  return (
    <>
      {children}
      <KeyboardShortcutsModal open={showHelp} onClose={() => setShowHelp(false)} />
    </>
  );
};

export default KeyboardShortcuts;
