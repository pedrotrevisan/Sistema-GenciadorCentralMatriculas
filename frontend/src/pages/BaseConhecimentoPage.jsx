import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Search, BookOpen, FileText, HelpCircle, Lightbulb, Phone, File,
  Plus, Eye, ChevronLeft, Star, Clock, User, Tag, X, Edit, Trash2
} from 'lucide-react';

const CATEGORIAS = [
  { value: 'procedimento', label: 'Procedimento', icone: FileText, cor: 'bg-blue-100 text-blue-800' },
  { value: 'faq', label: 'Perguntas Frequentes', icone: HelpCircle, cor: 'bg-purple-100 text-purple-800' },
  { value: 'documento', label: 'Documento', icone: File, cor: 'bg-green-100 text-green-800' },
  { value: 'dica', label: 'Dica Rápida', icone: Lightbulb, cor: 'bg-amber-100 text-amber-800' },
  { value: 'contato', label: 'Informação de Contato', icone: Phone, cor: 'bg-red-100 text-red-800' },
];

const BaseConhecimentoPage = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [artigos, setArtigos] = useState([]);
  const [artigoSelecionado, setArtigoSelecionado] = useState(null);
  const [busca, setBusca] = useState('');
  const [categoriaFiltro, setCategoriaFiltro] = useState('');
  const [showEditor, setShowEditor] = useState(false);
  const [editando, setEditando] = useState(null);
  const [formArtigo, setFormArtigo] = useState({
    titulo: '',
    conteudo: '',
    resumo: '',
    categoria: 'procedimento',
    tags: '',
    destaque: false
  });

  useEffect(() => {
    carregarArtigos();
  }, [busca, categoriaFiltro]);

  const carregarArtigos = async () => {
    try {
      const params = {};
      if (busca) params.busca = busca;
      if (categoriaFiltro) params.categoria = categoriaFiltro;
      
      const response = await api.get('/apoio/conhecimento', { params });
      setArtigos(response.data);
    } catch (error) {
      toast.error('Erro ao carregar artigos');
    } finally {
      setLoading(false);
    }
  };

  const abrirArtigo = async (artigoId) => {
    try {
      const response = await api.get(`/apoio/conhecimento/${artigoId}`);
      setArtigoSelecionado(response.data);
    } catch (error) {
      toast.error('Erro ao carregar artigo');
    }
  };

  const salvarArtigo = async () => {
    if (!formArtigo.titulo.trim() || !formArtigo.conteudo.trim()) {
      toast.error('Título e conteúdo são obrigatórios');
      return;
    }

    try {
      if (editando) {
        await api.put(`/apoio/conhecimento/${editando}`, formArtigo);
        toast.success('Artigo atualizado!');
      } else {
        await api.post('/apoio/conhecimento', formArtigo);
        toast.success('Artigo criado!');
      }
      setShowEditor(false);
      setEditando(null);
      resetForm();
      carregarArtigos();
    } catch (error) {
      toast.error('Erro ao salvar artigo');
    }
  };

  const editarArtigo = (artigo) => {
    setEditando(artigo.id);
    setFormArtigo({
      titulo: artigo.titulo,
      conteudo: artigo.conteudo,
      resumo: artigo.resumo || '',
      categoria: artigo.categoria,
      tags: artigo.tags?.join(',') || '',
      destaque: artigo.destaque
    });
    setArtigoSelecionado(null);
    setShowEditor(true);
  };

  const deletarArtigo = async (artigoId) => {
    if (!window.confirm('Deseja remover este artigo?')) return;
    
    try {
      await api.delete(`/apoio/conhecimento/${artigoId}`);
      toast.success('Artigo removido');
      setArtigoSelecionado(null);
      carregarArtigos();
    } catch (error) {
      toast.error('Erro ao remover artigo');
    }
  };

  const resetForm = () => {
    setFormArtigo({
      titulo: '',
      conteudo: '',
      resumo: '',
      categoria: 'procedimento',
      tags: '',
      destaque: false
    });
  };

  const getCategoriaInfo = (cat) => {
    return CATEGORIAS.find(c => c.value === cat) || CATEGORIAS[0];
  };

  const artigosDestaque = artigos.filter(a => a.destaque);
  const artigosLista = artigos.filter(a => !a.destaque || busca || categoriaFiltro);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004587] mx-auto"></div>
          <p className="mt-4 text-slate-500">Carregando base de conhecimento...</p>
        </div>
      </div>
    );
  }

  // Visualização de artigo
  if (artigoSelecionado) {
    const catInfo = getCategoriaInfo(artigoSelecionado.categoria);
    const CatIcon = catInfo.icone;
    
    return (
      <div className="min-h-screen bg-slate-50 p-6">
        <div className="max-w-4xl mx-auto">
          <Button 
            variant="ghost" 
            onClick={() => setArtigoSelecionado(null)}
            className="mb-4"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>
          
          <Card className="bg-white">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <Badge className={catInfo.cor + " mb-3"}>
                    <CatIcon className="w-3 h-3 mr-1" />
                    {catInfo.label}
                  </Badge>
                  <CardTitle className="text-2xl">{artigoSelecionado.titulo}</CardTitle>
                </div>
                {user?.role === 'admin' && (
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => editarArtigo(artigoSelecionado)}>
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button variant="outline" size="sm" className="text-red-600" onClick={() => deletarArtigo(artigoSelecionado.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-4 text-sm text-slate-500 mt-2">
                {artigoSelecionado.criado_por && (
                  <span className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    {artigoSelecionado.criado_por}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Eye className="w-4 h-4" />
                  {artigoSelecionado.visualizacoes} visualizações
                </span>
                {artigoSelecionado.updated_at && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    Atualizado em {new Date(artigoSelecionado.updated_at).toLocaleDateString('pt-BR')}
                  </span>
                )}
              </div>
            </CardHeader>
            
            <CardContent>
              {/* Conteúdo renderizado como markdown simples */}
              <div className="prose prose-slate max-w-none">
                {artigoSelecionado.conteudo.split('\n').map((linha, i) => {
                  if (linha.startsWith('# ')) {
                    return <h1 key={i} className="text-2xl font-bold mt-6 mb-4">{linha.slice(2)}</h1>;
                  }
                  if (linha.startsWith('## ')) {
                    return <h2 key={i} className="text-xl font-semibold mt-5 mb-3">{linha.slice(3)}</h2>;
                  }
                  if (linha.startsWith('### ')) {
                    return <h3 key={i} className="text-lg font-medium mt-4 mb-2">{linha.slice(4)}</h3>;
                  }
                  if (linha.startsWith('- ')) {
                    return <li key={i} className="ml-4">{linha.slice(2)}</li>;
                  }
                  if (linha.startsWith('**') && linha.endsWith('**')) {
                    return <p key={i} className="font-bold">{linha.slice(2, -2)}</p>;
                  }
                  if (linha.trim() === '') {
                    return <br key={i} />;
                  }
                  return <p key={i} className="mb-2">{linha}</p>;
                })}
              </div>
              
              {/* Tags */}
              {artigoSelecionado.tags?.length > 0 && (
                <div className="mt-8 pt-4 border-t">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Tag className="w-4 h-4 text-slate-400" />
                    {artigoSelecionado.tags.map((tag, i) => (
                      <Badge key={i} variant="outline" className="text-slate-600">
                        {tag.trim()}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-['Chivo'] flex items-center gap-2">
            <BookOpen className="w-7 h-7 text-[#004587]" />
            Base de Conhecimento
          </h1>
          <p className="text-slate-500">
            Procedimentos, dicas e informações úteis
          </p>
        </div>
        {user?.role === 'admin' && (
          <Button onClick={() => { resetForm(); setEditando(null); setShowEditor(true); }} className="bg-[#004587]">
            <Plus className="w-4 h-4 mr-2" />
            Novo Artigo
          </Button>
        )}
      </div>

      {/* Busca e Filtros */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Buscar artigos, procedimentos, dicas..."
                className="pl-10"
              />
            </div>
            <Select value={categoriaFiltro || "all"} onValueChange={(v) => setCategoriaFiltro(v === "all" ? "" : v)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Todas categorias" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas categorias</SelectItem>
                {CATEGORIAS.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Artigos em Destaque */}
      {!busca && !categoriaFiltro && artigosDestaque.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Star className="w-5 h-5 text-amber-500" />
            Em Destaque
          </h2>
          <div className="grid md:grid-cols-3 gap-4">
            {artigosDestaque.map((artigo) => {
              const catInfo = getCategoriaInfo(artigo.categoria);
              const CatIcon = catInfo.icone;
              return (
                <Card 
                  key={artigo.id} 
                  className="bg-gradient-to-br from-white to-amber-50 cursor-pointer hover:shadow-lg transition-shadow border-amber-200"
                  onClick={() => abrirArtigo(artigo.id)}
                >
                  <CardContent className="p-5">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                        <CatIcon className="w-5 h-5 text-amber-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-800 mb-1">{artigo.titulo}</h3>
                        {artigo.resumo && (
                          <p className="text-sm text-slate-600 line-clamp-2">{artigo.resumo}</p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Lista de Artigos */}
      <div>
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          {busca || categoriaFiltro ? `Resultados (${artigosLista.length})` : 'Todos os Artigos'}
        </h2>
        
        {artigosLista.length === 0 ? (
          <Card className="bg-white">
            <CardContent className="p-12 text-center">
              <BookOpen className="w-16 h-16 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">Nenhum artigo encontrado</p>
              {busca && (
                <Button variant="link" onClick={() => setBusca('')}>
                  Limpar busca
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {artigosLista.map((artigo) => {
              const catInfo = getCategoriaInfo(artigo.categoria);
              const CatIcon = catInfo.icone;
              return (
                <Card 
                  key={artigo.id} 
                  className="bg-white cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => abrirArtigo(artigo.id)}
                >
                  <CardContent className="p-5">
                    <Badge className={catInfo.cor + " mb-3"}>
                      <CatIcon className="w-3 h-3 mr-1" />
                      {catInfo.label}
                    </Badge>
                    <h3 className="font-semibold text-slate-800 mb-2">{artigo.titulo}</h3>
                    {artigo.resumo && (
                      <p className="text-sm text-slate-600 line-clamp-2 mb-3">{artigo.resumo}</p>
                    )}
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {artigo.visualizacoes}
                      </span>
                      {artigo.tags?.length > 0 && (
                        <span>{artigo.tags.slice(0, 2).join(', ')}</span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal Editor de Artigo */}
      <Dialog open={showEditor} onOpenChange={setShowEditor}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-[#004587]" />
              {editando ? 'Editar Artigo' : 'Novo Artigo'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Título *</Label>
              <Input
                value={formArtigo.titulo}
                onChange={(e) => setFormArtigo({ ...formArtigo, titulo: e.target.value })}
                placeholder="Título do artigo"
              />
            </div>
            
            <div>
              <Label>Resumo (opcional)</Label>
              <Input
                value={formArtigo.resumo}
                onChange={(e) => setFormArtigo({ ...formArtigo, resumo: e.target.value })}
                placeholder="Breve descrição para listagem"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Categoria</Label>
                <Select 
                  value={formArtigo.categoria} 
                  onValueChange={(v) => setFormArtigo({ ...formArtigo, categoria: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIAS.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Tags (separadas por vírgula)</Label>
                <Input
                  value={formArtigo.tags}
                  onChange={(e) => setFormArtigo({ ...formArtigo, tags: e.target.value })}
                  placeholder="matrícula, documentos, processo"
                />
              </div>
            </div>
            
            <div>
              <Label>Conteúdo *</Label>
              <p className="text-xs text-slate-500 mb-1">
                Use # para título, ## para subtítulo, - para listas
              </p>
              <Textarea
                value={formArtigo.conteudo}
                onChange={(e) => setFormArtigo({ ...formArtigo, conteudo: e.target.value })}
                placeholder="Escreva o conteúdo do artigo..."
                rows={12}
                className="font-mono text-sm"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="destaque"
                checked={formArtigo.destaque}
                onChange={(e) => setFormArtigo({ ...formArtigo, destaque: e.target.checked })}
                className="rounded border-slate-300"
              />
              <Label htmlFor="destaque" className="text-sm cursor-pointer">
                Exibir em destaque na página inicial
              </Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditor(false)}>
              Cancelar
            </Button>
            <Button onClick={salvarArtigo} className="bg-[#004587]">
              {editando ? 'Salvar Alterações' : 'Criar Artigo'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BaseConhecimentoPage;
