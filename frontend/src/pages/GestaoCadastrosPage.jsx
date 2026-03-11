import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { cursosAPI, projetosAPI, empresasAPI } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import {
  GraduationCap,
  Building2,
  FolderKanban,
  Plus,
  Pencil,
  Trash2,
  Save,
  X,
  Search,
  Filter,
  Clock,
  Monitor,
  MapPin,
  RotateCcw,
  CheckCircle
} from 'lucide-react';

const GestaoCadastrosPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('cursos');
  const [loading, setLoading] = useState(false);
  
  // Data states
  const [cursos, setCursos] = useState([]);
  const [projetos, setProjetos] = useState([]);
  const [empresas, setEmpresas] = useState([]);
  const [opcoesCursos, setOpcoesCursos] = useState({ tipos: [], modalidades: [], areas: [] });
  const [estatisticasCursos, setEstatisticasCursos] = useState(null);
  
  // Filtros
  const [filtros, setFiltros] = useState({
    busca: '',
    tipo: '',
    modalidade: '',
    area: '',
    ativo: true
  });
  
  // Form states
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({ 
    nome: '', 
    descricao: '', 
    cnpj: '',
    tipo: '',
    modalidade: '',
    area: '',
    carga_horaria: '',
    duracao: ''
  });

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/');
      return;
    }
    loadData();
    loadOpcoesCursos();
  }, [user, navigate]);

  useEffect(() => {
    if (activeTab === 'cursos') {
      loadCursos();
    }
  }, [filtros, activeTab]);

  const loadOpcoesCursos = async () => {
    try {
      const response = await cursosAPI.getOpcoes();
      setOpcoesCursos(response.data);
    } catch (error) {
      console.error('Erro ao carregar opções de cursos');
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [cursosRes, projetosRes, empresasRes, statsRes] = await Promise.all([
        cursosAPI.listar({ ativo: filtros.ativo }),
        projetosAPI.listar(),
        empresasAPI.listar(),
        cursosAPI.getEstatisticas()
      ]);
      setCursos(cursosRes.data);
      setProjetos(projetosRes.data);
      setEmpresas(empresasRes.data);
      setEstatisticasCursos(statsRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const loadCursos = async () => {
    try {
      const params = {};
      if (filtros.busca) params.busca = filtros.busca;
      if (filtros.tipo) params.tipo = filtros.tipo;
      if (filtros.modalidade) params.modalidade = filtros.modalidade;
      if (filtros.area) params.area = filtros.area;
      if (filtros.ativo !== null) params.ativo = filtros.ativo;
      
      const response = await cursosAPI.listar(params);
      setCursos(response.data);
    } catch (error) {
      toast.error('Erro ao carregar cursos');
    }
  };

  const getActiveData = () => {
    switch (activeTab) {
      case 'cursos': return cursos;
      case 'projetos': return projetos;
      case 'empresas': return empresas;
      default: return [];
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    setFormData({ 
      nome: '', 
      descricao: '', 
      cnpj: '',
      tipo: '',
      modalidade: '',
      area: '',
      carga_horaria: '',
      duracao: ''
    });
    setShowForm(true);
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({ 
      nome: item.nome, 
      descricao: item.descricao || '', 
      cnpj: item.cnpj || '',
      tipo: item.tipo || '',
      modalidade: item.modalidade || '',
      area: item.area || '',
      carga_horaria: item.carga_horaria || '',
      duracao: item.duracao || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (item) => {
    if (!window.confirm(`Deseja desativar "${item.nome}"?`)) return;
    
    try {
      if (activeTab === 'cursos') {
        await cursosAPI.deletar(item.id);
      } else if (activeTab === 'projetos') {
        await projetosAPI.deletar(item.id);
      } else {
        await empresasAPI.deletar(item.id);
      }
      toast.success('Item desativado com sucesso');
      loadData();
    } catch (error) {
      toast.error('Erro ao desativar item');
    }
  };

  const handleAtivar = async (item) => {
    try {
      await cursosAPI.ativar(item.id);
      toast.success('Curso reativado com sucesso');
      loadData();
    } catch (error) {
      toast.error('Erro ao reativar curso');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.nome.trim()) {
      toast.error('Nome é obrigatório');
      return;
    }

    try {
      let data = { nome: formData.nome };
      
      if (activeTab === 'cursos') {
        data = {
          ...data,
          descricao: formData.descricao || null,
          tipo: formData.tipo || null,
          modalidade: formData.modalidade || null,
          area: formData.area || null,
          carga_horaria: formData.carga_horaria || null,
          duracao: formData.duracao || null
        };
        
        if (editingItem) {
          await cursosAPI.atualizar(editingItem.id, data);
        } else {
          await cursosAPI.criar(data);
        }
      } else if (activeTab === 'projetos') {
        data.descricao = formData.descricao || null;
        if (editingItem) {
          await projetosAPI.atualizar(editingItem.id, data);
        } else {
          await projetosAPI.criar(data);
        }
      } else {
        data.cnpj = formData.cnpj || null;
        if (editingItem) {
          await empresasAPI.atualizar(editingItem.id, data);
        } else {
          await empresasAPI.criar(data);
        }
      }
      
      toast.success(editingItem ? 'Item atualizado com sucesso' : 'Item criado com sucesso');
      setShowForm(false);
      loadData();
    } catch (error) {
      if (error.response?.status === 409) {
        toast.error('Este item já existe');
      } else {
        toast.error('Erro ao salvar item');
      }
    }
  };

  const tabs = [
    { id: 'cursos', label: 'Cursos', icon: GraduationCap, count: cursos.length },
    { id: 'projetos', label: 'Projetos', icon: FolderKanban, count: projetos.filter(p => p.ativo).length },
    { id: 'empresas', label: 'Empresas', icon: Building2, count: empresas.filter(e => e.ativo).length },
  ];

  const getTipoColor = (tipo) => {
    const colors = {
      tecnico: 'bg-blue-100 text-blue-800',
      graduacao: 'bg-green-100 text-green-800',
      pos_graduacao: 'bg-purple-100 text-purple-800',
      qualificacao: 'bg-cyan-100 text-cyan-800',
      aperfeicoamento: 'bg-amber-100 text-amber-800',
      livre: 'bg-orange-100 text-orange-800',
    };
    return colors[tipo] || 'bg-gray-100 text-gray-800';
  };

  const getTipoEmoji = (tipo) => {
    const emojis = {
      tecnico: '🎓',
      graduacao: '🏛️',
      pos_graduacao: '📚',
      qualificacao: '📝',
      aperfeicoamento: '🔧',
      livre: '📖',
    };
    return emojis[tipo] || '📌';
  };

  const getModalidadeIcon = (modalidade) => {
    if (modalidade === 'ead') return <Monitor className="w-3 h-3" />;
    if (modalidade === 'presencial') return <MapPin className="w-3 h-3" />;
    return null;
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
          Gestão de Cadastros
        </h1>
        <p className="text-slate-500">
          Gerencie cursos, projetos e empresas parceiras
        </p>
      </div>

      {/* Estatísticas de Cursos */}
      {activeTab === 'cursos' && estatisticasCursos && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <Card 
            className="bg-slate-50 border-slate-200 cursor-pointer hover:shadow-lg transition-all"
            onClick={() => setFiltros({ ...filtros, tipo: '' })}
          >
            <CardContent className="p-4 text-center">
              <GraduationCap className="w-8 h-8 mx-auto text-slate-600 mb-2" />
              <p className="text-2xl font-bold text-slate-700">{estatisticasCursos.total}</p>
              <p className="text-xs text-slate-600">Total</p>
            </CardContent>
          </Card>
          <Card 
            className="bg-blue-50 border-blue-200 cursor-pointer hover:shadow-lg transition-all"
            onClick={() => setFiltros({ ...filtros, tipo: 'tecnico' })}
          >
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-blue-700">{estatisticasCursos.por_tipo?.tecnico || 0}</p>
              <p className="text-xs text-blue-600">🎓 Técnico</p>
            </CardContent>
          </Card>
          <Card 
            className="bg-green-50 border-green-200 cursor-pointer hover:shadow-lg transition-all"
            onClick={() => setFiltros({ ...filtros, tipo: 'graduacao' })}
          >
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-green-700">{estatisticasCursos.por_tipo?.graduacao || 0}</p>
              <p className="text-xs text-green-600">🏛️ Graduação</p>
            </CardContent>
          </Card>
          <Card 
            className="bg-purple-50 border-purple-200 cursor-pointer hover:shadow-lg transition-all"
            onClick={() => setFiltros({ ...filtros, tipo: 'pos_graduacao' })}
          >
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-purple-700">{estatisticasCursos.por_tipo?.pos_graduacao || 0}</p>
              <p className="text-xs text-purple-600">📚 Pós-Grad</p>
            </CardContent>
          </Card>
          <Card 
            className="bg-cyan-50 border-cyan-200 cursor-pointer hover:shadow-lg transition-all"
            onClick={() => setFiltros({ ...filtros, tipo: 'qualificacao' })}
          >
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-cyan-700">{estatisticasCursos.por_tipo?.qualificacao || 0}</p>
              <p className="text-xs text-cyan-600">📝 Qualificação</p>
            </CardContent>
          </Card>
          <Card 
            className="bg-amber-50 border-amber-200 cursor-pointer hover:shadow-lg transition-all"
            onClick={() => setFiltros({ ...filtros, tipo: 'aperfeicoamento' })}
          >
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-amber-700">{estatisticasCursos.por_tipo?.aperfeicoamento || 0}</p>
              <p className="text-xs text-amber-600">🔧 Aperfeiç.</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-200 pb-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? 'default' : 'outline'}
              onClick={() => setActiveTab(tab.id)}
              className={activeTab === tab.id ? 'bg-[#004587]' : ''}
            >
              <Icon className="w-4 h-4 mr-2" />
              {tab.label}
              <Badge variant="secondary" className="ml-2">{tab.count}</Badge>
            </Button>
          );
        })}
      </div>

      {/* Filtros para Cursos */}
      {activeTab === 'cursos' && (
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex-1 min-w-[200px]">
                <Label>Buscar</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    value={filtros.busca}
                    onChange={(e) => setFiltros({ ...filtros, busca: e.target.value })}
                    placeholder="Nome do curso..."
                    className="pl-10"
                  />
                </div>
              </div>
              
              <div className="w-[180px]">
                <Label>Tipo</Label>
                <Select value={filtros.tipo || "all"} onValueChange={(v) => setFiltros({ ...filtros, tipo: v === "all" ? "" : v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Todos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    {opcoesCursos.tipos.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="w-[150px]">
                <Label>Modalidade</Label>
                <Select value={filtros.modalidade || "all"} onValueChange={(v) => setFiltros({ ...filtros, modalidade: v === "all" ? "" : v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Todas" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas</SelectItem>
                    {opcoesCursos.modalidades.map((m) => (
                      <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="w-[180px]">
                <Label>Área</Label>
                <Select value={filtros.area || "all"} onValueChange={(v) => setFiltros({ ...filtros, area: v === "all" ? "" : v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Todas" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas</SelectItem>
                    {opcoesCursos.areas.map((a) => (
                      <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="w-[130px]">
                <Label>Status</Label>
                <Select 
                  value={filtros.ativo === null ? 'todos' : filtros.ativo ? 'ativos' : 'inativos'} 
                  onValueChange={(v) => setFiltros({ ...filtros, ativo: v === 'todos' ? null : v === 'ativos' })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todos">Todos</SelectItem>
                    <SelectItem value="ativos">Ativos</SelectItem>
                    <SelectItem value="inativos">Inativos</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Button onClick={loadCursos} className="bg-[#004587]">
                <Filter className="w-4 h-4 mr-2" />
                Filtrar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Botão Adicionar e Lista */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {activeTab === 'cursos' && <GraduationCap className="w-5 h-5" />}
            {activeTab === 'projetos' && <FolderKanban className="w-5 h-5" />}
            {activeTab === 'empresas' && <Building2 className="w-5 h-5" />}
            {activeTab === 'cursos' ? 'Cursos Cadastrados' : activeTab === 'projetos' ? 'Projetos' : 'Empresas'}
          </CardTitle>
          <Button onClick={handleAdd} className="bg-green-600 hover:bg-green-700">
            <Plus className="w-4 h-4 mr-2" />
            Adicionar
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004587] mx-auto"></div>
              <p className="mt-4 text-slate-500">Carregando...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-100">
                  <tr>
                    <th className="text-left p-3 font-semibold text-slate-700">Nome</th>
                    {activeTab === 'cursos' && (
                      <>
                        <th className="text-left p-3 font-semibold text-slate-700">Tipo</th>
                        <th className="text-left p-3 font-semibold text-slate-700">Modalidade</th>
                        <th className="text-left p-3 font-semibold text-slate-700">Área</th>
                        <th className="text-left p-3 font-semibold text-slate-700">Carga Horária</th>
                      </>
                    )}
                    {activeTab === 'empresas' && (
                      <th className="text-left p-3 font-semibold text-slate-700">CNPJ</th>
                    )}
                    {activeTab !== 'empresas' && activeTab !== 'cursos' && (
                      <th className="text-left p-3 font-semibold text-slate-700">Descrição</th>
                    )}
                    <th className="text-left p-3 font-semibold text-slate-700">Status</th>
                    <th className="text-right p-3 font-semibold text-slate-700">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {getActiveData().map((item) => (
                    <tr key={item.id} className={`border-b hover:bg-slate-50 ${!item.ativo ? 'opacity-50' : ''}`}>
                      <td className="p-3">
                        <div>
                          <p className="font-medium text-slate-900">{item.nome}</p>
                          {activeTab === 'cursos' && item.descricao && (
                            <p className="text-xs text-slate-500 mt-1 line-clamp-1">{item.descricao}</p>
                          )}
                        </div>
                      </td>
                      {activeTab === 'cursos' && (
                        <>
                          <td className="p-3">
                            {item.tipo_label && (
                              <Badge className={getTipoColor(item.tipo)}>
                                {item.tipo_label}
                              </Badge>
                            )}
                          </td>
                          <td className="p-3">
                            {item.modalidade_label && (
                              <div className="flex items-center gap-1 text-sm text-slate-600">
                                {getModalidadeIcon(item.modalidade)}
                                {item.modalidade_label}
                              </div>
                            )}
                          </td>
                          <td className="p-3 text-sm text-slate-600">
                            {item.area_label || '-'}
                          </td>
                          <td className="p-3">
                            {item.carga_horaria && (
                              <div className="flex items-center gap-1 text-sm text-slate-600">
                                <Clock className="w-3 h-3" />
                                {item.carga_horaria}
                              </div>
                            )}
                          </td>
                        </>
                      )}
                      {activeTab === 'empresas' && (
                        <td className="p-3 text-sm text-slate-600 font-mono">{item.cnpj || '-'}</td>
                      )}
                      {activeTab !== 'empresas' && activeTab !== 'cursos' && (
                        <td className="p-3 text-sm text-slate-600 max-w-[200px] truncate">{item.descricao || '-'}</td>
                      )}
                      <td className="p-3">
                        <Badge className={item.ativo ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {item.ativo ? 'Ativo' : 'Inativo'}
                        </Badge>
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex gap-2 justify-end">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEdit(item)}
                            className="text-blue-600"
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          {item.ativo ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDelete(item)}
                              className="text-red-600"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          ) : activeTab === 'cursos' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleAtivar(item)}
                              className="text-green-600"
                            >
                              <RotateCcw className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {getActiveData().length === 0 && (
                    <tr>
                      <td colSpan={activeTab === 'cursos' ? 7 : 4} className="p-8 text-center text-slate-500">
                        Nenhum registro encontrado
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal de Formulário */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {activeTab === 'cursos' && <GraduationCap className="w-5 h-5 text-[#004587]" />}
              {activeTab === 'projetos' && <FolderKanban className="w-5 h-5 text-[#004587]" />}
              {activeTab === 'empresas' && <Building2 className="w-5 h-5 text-[#004587]" />}
              {editingItem ? 'Editar' : 'Novo'} {activeTab === 'cursos' ? 'Curso' : activeTab === 'projetos' ? 'Projeto' : 'Empresa'}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Nome *</Label>
              <Input
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                placeholder={`Nome do ${activeTab.slice(0, -1)}`}
              />
            </div>
            
            {activeTab === 'cursos' && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Tipo de Curso</Label>
                    <Select value={formData.tipo} onValueChange={(v) => setFormData({ ...formData, tipo: v })}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        {opcoesCursos.tipos.map((t) => (
                          <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Modalidade</Label>
                    <Select value={formData.modalidade} onValueChange={(v) => setFormData({ ...formData, modalidade: v })}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        {opcoesCursos.modalidades.map((m) => (
                          <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <Label>Área</Label>
                  <Select value={formData.area} onValueChange={(v) => setFormData({ ...formData, area: v })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione a área" />
                    </SelectTrigger>
                    <SelectContent>
                      {opcoesCursos.areas.map((a) => (
                        <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Carga Horária</Label>
                    <Input
                      value={formData.carga_horaria}
                      onChange={(e) => setFormData({ ...formData, carga_horaria: e.target.value })}
                      placeholder="Ex: 800h"
                    />
                  </div>
                  <div>
                    <Label>Duração</Label>
                    <Input
                      value={formData.duracao}
                      onChange={(e) => setFormData({ ...formData, duracao: e.target.value })}
                      placeholder="Ex: 2 anos"
                    />
                  </div>
                </div>
                
                <div>
                  <Label>Descrição</Label>
                  <Textarea
                    value={formData.descricao}
                    onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                    placeholder="Descrição do curso..."
                    rows={3}
                  />
                </div>
              </>
            )}
            
            {activeTab === 'projetos' && (
              <div>
                <Label>Descrição</Label>
                <Textarea
                  value={formData.descricao}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                  placeholder="Descrição do projeto..."
                  rows={3}
                />
              </div>
            )}
            
            {activeTab === 'empresas' && (
              <div>
                <Label>CNPJ</Label>
                <Input
                  value={formData.cnpj}
                  onChange={(e) => setFormData({ ...formData, cnpj: e.target.value })}
                  placeholder="00.000.000/0000-00"
                />
              </div>
            )}
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                <X className="w-4 h-4 mr-2" />
                Cancelar
              </Button>
              <Button type="submit" className="bg-[#004587]">
                <Save className="w-4 h-4 mr-2" />
                Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GestaoCadastrosPage;
