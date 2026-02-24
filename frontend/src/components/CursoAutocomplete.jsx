import { useState, useEffect, useRef, useCallback } from 'react';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Search, X, GraduationCap, Loader2, ChevronDown } from 'lucide-react';
import { cn } from '../lib/utils';

/**
 * Componente de Autocomplete inteligente para seleção de cursos
 * Com 4489+ cursos, este componente oferece:
 * - Busca em tempo real com debounce
 * - Filtro local instantâneo
 * - Destaque dos termos buscados
 * - Exibição de tipo/modalidade do curso
 * - Navegação por teclado
 */
const CursoAutocomplete = ({ 
  cursos = [], 
  value, 
  onChange, 
  placeholder = "Digite para buscar curso...",
  disabled = false 
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [filteredCursos, setFilteredCursos] = useState([]);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [isSearching, setIsSearching] = useState(false);
  
  const inputRef = useRef(null);
  const listRef = useRef(null);
  const containerRef = useRef(null);

  // Encontrar curso selecionado
  const selectedCurso = cursos.find(c => c.id === value);

  // Atualizar input quando value muda externamente
  useEffect(() => {
    if (selectedCurso && !isOpen) {
      setInputValue(selectedCurso.nome);
    }
  }, [selectedCurso, isOpen]);

  // Debounce da busca
  const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  };

  // Função para remover acentos
  const removeAccents = (str) => {
    return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  };

  // Função de filtro otimizada
  const filterCursos = useCallback((searchTerm) => {
    if (!searchTerm || searchTerm.length < 2) {
      setFilteredCursos([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    
    const termo = removeAccents(searchTerm.toLowerCase().trim());
    const termos = termo.split(' ').filter(t => t.length > 0);
    
    const resultados = cursos
      .filter(curso => {
        const nome = removeAccents(curso.nome.toLowerCase());
        // Todos os termos devem estar presentes
        return termos.every(t => nome.includes(t));
      })
      .slice(0, 50); // Limitar a 50 resultados para performance

    setFilteredCursos(resultados);
    setHighlightedIndex(-1);
    setIsSearching(false);
  }, [cursos]);

  // Debounced filter
  const debouncedFilter = useCallback(
    debounce((term) => filterCursos(term), 150),
    [filterCursos]
  );

  // Handle input change
  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setIsOpen(true);
    debouncedFilter(newValue);
  };

  // Handle selection
  const handleSelect = (curso) => {
    setInputValue(curso.nome);
    onChange(curso.id, curso);
    setIsOpen(false);
    setFilteredCursos([]);
    inputRef.current?.blur();
  };

  // Handle clear
  const handleClear = (e) => {
    e.stopPropagation();
    setInputValue('');
    onChange('', null);
    setFilteredCursos([]);
    inputRef.current?.focus();
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        if (inputValue.length >= 2) {
          filterCursos(inputValue);
        }
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev < filteredCursos.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && filteredCursos[highlightedIndex]) {
          handleSelect(filteredCursos[highlightedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setFilteredCursos([]);
        break;
      default:
        break;
    }
  };

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const item = listRef.current.children[highlightedIndex];
      if (item) {
        item.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex]);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
        if (selectedCurso) {
          setInputValue(selectedCurso.nome);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [selectedCurso]);

  // Highlight matching text
  const highlightMatch = (text, search) => {
    if (!search || search.length < 2) return text;
    
    const termos = search.toLowerCase().split(' ').filter(t => t.length > 0);
    let result = text;
    
    termos.forEach(termo => {
      const regex = new RegExp(`(${termo})`, 'gi');
      result = result.replace(regex, '<mark class="bg-yellow-200 rounded px-0.5">$1</mark>');
    });
    
    return <span dangerouslySetInnerHTML={{ __html: result }} />;
  };

  // Get tipo badge color
  const getTipoBadgeColor = (tipo) => {
    switch (tipo) {
      case 'tecnico': return 'bg-blue-100 text-blue-700';
      case 'graduacao': return 'bg-purple-100 text-purple-700';
      case 'pos_graduacao': return 'bg-indigo-100 text-indigo-700';
      case 'livre': return 'bg-green-100 text-green-700';
      case 'capacitacao': return 'bg-orange-100 text-orange-700';
      default: return 'bg-slate-100 text-slate-600';
    }
  };

  return (
    <div ref={containerRef} className="relative w-full" data-testid="curso-autocomplete">
      {/* Input Field */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => {
            setIsOpen(true);
            if (inputValue.length >= 2) {
              filterCursos(inputValue);
            }
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "pl-10 pr-20",
            selectedCurso && "border-green-500 bg-green-50/50"
          )}
          data-testid="curso-search-input"
        />
        
        {/* Right side icons */}
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isSearching && (
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
          )}
          {value && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 hover:bg-slate-100 rounded"
              data-testid="clear-curso-btn"
            >
              <X className="h-4 w-4 text-slate-400 hover:text-slate-600" />
            </button>
          )}
          <ChevronDown className={cn(
            "h-4 w-4 text-slate-400 transition-transform",
            isOpen && "transform rotate-180"
          )} />
        </div>
      </div>

      {/* Selected Course Badge */}
      {selectedCurso && !isOpen && (
        <div className="mt-2 flex items-center gap-2">
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <GraduationCap className="h-3 w-3 mr-1" />
            Selecionado
          </Badge>
          {selectedCurso.tipo_label && (
            <Badge variant="outline" className={getTipoBadgeColor(selectedCurso.tipo)}>
              {selectedCurso.tipo_label}
            </Badge>
          )}
          {selectedCurso.modalidade_label && (
            <Badge variant="outline" className="bg-slate-100 text-slate-600">
              {selectedCurso.modalidade_label}
            </Badge>
          )}
        </div>
      )}

      {/* Dropdown Results */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-80 overflow-hidden">
          {/* Search hint */}
          {inputValue.length < 2 && (
            <div className="p-4 text-center text-slate-500">
              <Search className="h-8 w-8 mx-auto mb-2 text-slate-300" />
              <p className="text-sm">Digite pelo menos 2 caracteres para buscar</p>
              <p className="text-xs text-slate-400 mt-1">
                {cursos.length.toLocaleString()} cursos disponíveis
              </p>
            </div>
          )}

          {/* Loading state */}
          {isSearching && inputValue.length >= 2 && (
            <div className="p-4 text-center">
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-blue-500" />
              <p className="text-sm text-slate-500 mt-2">Buscando...</p>
            </div>
          )}

          {/* Results list */}
          {!isSearching && inputValue.length >= 2 && filteredCursos.length > 0 && (
            <>
              <div className="px-3 py-2 bg-slate-50 border-b text-xs text-slate-500">
                {filteredCursos.length} {filteredCursos.length === 1 ? 'resultado' : 'resultados'} encontrado{filteredCursos.length > 1 ? 's' : ''}
                {filteredCursos.length === 50 && ' (mostrando primeiros 50)'}
              </div>
              <ul 
                ref={listRef} 
                className="overflow-y-auto max-h-64"
                data-testid="curso-results-list"
              >
                {filteredCursos.map((curso, index) => (
                  <li
                    key={curso.id}
                    onClick={() => handleSelect(curso)}
                    className={cn(
                      "px-4 py-3 cursor-pointer border-b border-slate-100 last:border-0 transition-colors",
                      highlightedIndex === index ? "bg-blue-50" : "hover:bg-slate-50",
                      curso.id === value && "bg-green-50"
                    )}
                    data-testid={`curso-option-${index}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-800 truncate">
                          {highlightMatch(curso.nome, inputValue)}
                        </p>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          {curso.tipo_label && (
                            <span className={cn(
                              "text-xs px-2 py-0.5 rounded-full",
                              getTipoBadgeColor(curso.tipo)
                            )}>
                              {curso.tipo_label}
                            </span>
                          )}
                          {curso.modalidade_label && (
                            <span className="text-xs text-slate-500">
                              {curso.modalidade_label}
                            </span>
                          )}
                          {curso.carga_horaria && (
                            <span className="text-xs text-slate-400">
                              {curso.carga_horaria}
                            </span>
                          )}
                        </div>
                      </div>
                      {curso.id === value && (
                        <Badge className="bg-green-500 text-white shrink-0">
                          ✓
                        </Badge>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* No results */}
          {!isSearching && inputValue.length >= 2 && filteredCursos.length === 0 && (
            <div className="p-4 text-center text-slate-500">
              <GraduationCap className="h-8 w-8 mx-auto mb-2 text-slate-300" />
              <p className="text-sm">Nenhum curso encontrado</p>
              <p className="text-xs text-slate-400 mt-1">
                Tente usar termos diferentes
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CursoAutocomplete;
