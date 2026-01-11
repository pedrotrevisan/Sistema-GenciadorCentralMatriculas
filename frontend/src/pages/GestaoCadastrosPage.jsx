import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { cursosAPI, projetosAPI, empresasAPI } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import {
  GraduationCap,
  Building2,
  FolderKanban,
  Plus,
  Pencil,
  Trash2,
  ArrowLeft,
  Save,
  X,
  LayoutDashboard
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
  
  // Form states
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({ nome: '', descricao: '', cnpj: '' });

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/');
      return;
    }
    loadData();
  }, [user, navigate]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cursosRes, projetosRes, empresasRes] = await Promise.all([
        cursosAPI.listar(),
        projetosAPI.listar(),
        empresasAPI.listar()
      ]);
      setCursos(cursosRes.data);
      setProjetos(projetosRes.data);
      setEmpresas(empresasRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
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

  const getAPI = () => {
    switch (activeTab) {
      case 'cursos': return cursosAPI;
      case 'projetos': return projetosAPI;
      case 'empresas': return empresasAPI;
      default: return null;
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    setFormData({ nome: '', descricao: '', cnpj: '' });
    setShowForm(true);
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({ 
      nome: item.nome, 
      descricao: item.descricao || '', 
      cnpj: item.cnpj || '' 
    });
    setShowForm(true);
  };

  const handleDelete = async (item) => {
    if (!window.confirm(`Deseja desativar "${item.nome}"?`)) return;
    
    try {
      await getAPI().deletar(item.id);
      toast.success('Item desativado com sucesso');
      loadData();
    } catch (error) {
      toast.error('Erro ao desativar item');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.nome.trim()) {
      toast.error('Nome é obrigatório');
      return;
    }

    try {
      const api = getAPI();
      const data = { nome: formData.nome };
      
      if (activeTab === 'empresas') {
        data.cnpj = formData.cnpj || null;
      } else {
        data.descricao = formData.descricao || null;
      }

      if (editingItem) {
        await api.atualizar(editingItem.id, data);
        toast.success('Item atualizado com sucesso');
      } else {
        await api.criar(data);
        toast.success('Item criado com sucesso');
      }
      
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
    { id: 'cursos', label: 'Cursos', icon: GraduationCap, count: cursos.filter(c => c.ativo).length },
    { id: 'projetos', label: 'Projetos', icon: FolderKanban, count: projetos.filter(p => p.ativo).length },
    { id: 'empresas', label: 'Empresas', icon: Building2, count: empresas.filter(e => e.ativo).length },
  ];

  const getTitle = () => {
    switch (activeTab) {
      case 'cursos': return 'Cursos';
      case 'projetos': return 'Projetos';
      case 'empresas': return 'Empresas';
      default: return '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-[#004587] text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/admin')}
                className="text-white hover:bg-white/10"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar
              </Button>
              <h1 className="text-xl font-bold">Gestão de Cadastros</h1>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/admin')}
              className="text-white hover:bg-white/10"
            >
              <LayoutDashboard className="w-4 h-4 mr-2" />
              Dashboard
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-[#004587] text-white shadow-md'
                    : 'bg-white text-gray-600 hover:bg-gray-100 border'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
                <span className={`px-2 py-0.5 rounded-full text-xs ${
                  activeTab === tab.id ? 'bg-white/20' : 'bg-gray-100'
                }`}>
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Content Card */}
        <div className="bg-white rounded-xl shadow-sm border">
          {/* Card Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-800">
              {getTitle()} Cadastrados
            </h2>
            <Button onClick={handleAdd} className="bg-[#E30613] hover:bg-[#c00510]">
              <Plus className="w-4 h-4 mr-2" />
              Novo {getTitle().slice(0, -1)}
            </Button>
          </div>

          {/* Form */}
          {showForm && (
            <div className="p-6 bg-gray-50 border-b">
              <form onSubmit={handleSubmit} className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome *
                  </label>
                  <Input
                    value={formData.nome}
                    onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                    placeholder={`Nome do ${getTitle().slice(0, -1).toLowerCase()}`}
                    className="w-full"
                    autoFocus
                  />
                </div>
                
                {activeTab === 'empresas' ? (
                  <div className="w-48">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      CNPJ
                    </label>
                    <Input
                      value={formData.cnpj}
                      onChange={(e) => setFormData({ ...formData, cnpj: e.target.value })}
                      placeholder="00.000.000/0000-00"
                    />
                  </div>
                ) : (
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Descrição
                    </label>
                    <Input
                      value={formData.descricao}
                      onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                      placeholder="Descrição (opcional)"
                    />
                  </div>
                )}

                <div className="flex gap-2">
                  <Button type="submit" className="bg-[#004587] hover:bg-[#003366]">
                    <Save className="w-4 h-4 mr-2" />
                    {editingItem ? 'Atualizar' : 'Salvar'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowForm(false)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </form>
            </div>
          )}

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nome
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {activeTab === 'empresas' ? 'CNPJ' : 'Descrição'}
                  </th>
                  <th className="text-center px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {loading ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                      Carregando...
                    </td>
                  </tr>
                ) : getActiveData().length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                      Nenhum registro encontrado
                    </td>
                  </tr>
                ) : (
                  getActiveData().map((item) => (
                    <tr key={item.id} className={`hover:bg-gray-50 ${!item.ativo ? 'opacity-50' : ''}`}>
                      <td className="px-6 py-4">
                        <span className="font-medium text-gray-900">{item.nome}</span>
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {activeTab === 'empresas' ? (item.cnpj || '-') : (item.descricao || '-')}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          item.ativo 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {item.ativo ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(item)}
                            disabled={!item.ativo}
                            className="text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(item)}
                            disabled={!item.ativo}
                            className="text-red-600 hover:text-red-800 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GestaoCadastrosPage;
