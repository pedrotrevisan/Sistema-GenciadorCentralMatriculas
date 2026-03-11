import { useState, useEffect } from 'react';
import { usuariosAPI, authAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { 
  Users, 
  Plus, 
  Edit, 
  Trash2, 
  RefreshCw,
  Search,
  Shield,
  CheckCircle,
  XCircle,
  KeyRound,
  RotateCcw
} from 'lucide-react';

const roleConfig = {
  admin: { color: 'bg-purple-100 text-purple-700', label: 'Admin' },
  assistente: { color: 'bg-blue-100 text-blue-700', label: 'Assistente' },
  consultor: { color: 'bg-slate-100 text-slate-700', label: 'Consultor' },
};

const GestaoUsuariosPage = () => {
  const [loading, setLoading] = useState(true);
  const [usuarios, setUsuarios] = useState([]);
  const [paginacao, setPaginacao] = useState({ total: 0, pagina: 1, por_pagina: 10 });
  const [searchTerm, setSearchTerm] = useState('');
  
  // Create/Edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' or 'edit'
  const [selectedUser, setSelectedUser] = useState(null);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    senha: '',
    role: 'consultor',
    ativo: true
  });
  const [submitting, setSubmitting] = useState(false);

  // Delete modal
  const [deleteModal, setDeleteModal] = useState({ open: false, user: null });
  const [deleting, setDeleting] = useState(false);

  // Reset senha modal
  const [resetSenhaModal, setResetSenhaModal] = useState({ open: false, user: null });
  const [resettingSenha, setResettingSenha] = useState(false);
  const [resetAllModal, setResetAllModal] = useState(false);
  const [resettingAll, setResettingAll] = useState(false);

  const fetchUsuarios = async () => {
    setLoading(true);
    try {
      const response = await usuariosAPI.listar({
        pagina: paginacao.pagina,
        por_pagina: paginacao.por_pagina
      });
      setUsuarios(response.data.usuarios);
      setPaginacao(prev => ({
        ...prev,
        total: response.data.total
      }));
    } catch (error) {
      toast.error('Erro ao carregar usuários');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsuarios();
  }, [paginacao.pagina]);

  const openCreateModal = () => {
    setModalMode('create');
    setFormData({
      nome: '',
      email: '',
      senha: '',
      role: 'consultor',
      ativo: true
    });
    setSelectedUser(null);
    setModalOpen(true);
  };

  const openEditModal = (user) => {
    setModalMode('edit');
    setFormData({
      nome: user.nome,
      email: user.email,
      senha: '',
      role: user.role,
      ativo: user.ativo
    });
    setSelectedUser(user);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    if (!formData.nome || !formData.email) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    if (modalMode === 'create' && !formData.senha) {
      toast.error('Senha é obrigatória para novo usuário');
      return;
    }

    setSubmitting(true);
    try {
      if (modalMode === 'create') {
        await authAPI.register({
          nome: formData.nome,
          email: formData.email,
          senha: formData.senha,
          role: formData.role
        });
        toast.success('Usuário criado com sucesso');
      } else {
        await usuariosAPI.atualizar(selectedUser.id, {
          nome: formData.nome,
          role: formData.role,
          ativo: formData.ativo
        });
        toast.success('Usuário atualizado com sucesso');
      }
      setModalOpen(false);
      fetchUsuarios();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar usuário');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await usuariosAPI.deletar(deleteModal.user.id);
      toast.success('Usuário deletado com sucesso');
      setDeleteModal({ open: false, user: null });
      fetchUsuarios();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao deletar usuário');
    } finally {
      setDeleting(false);
    }
  };

  const handleResetSenha = async () => {
    setResettingSenha(true);
    try {
      await usuariosAPI.resetarSenha(resetSenhaModal.user.id);
      toast.success(`Senha de ${resetSenhaModal.user.nome} resetada para: Senai@2026`);
      setResetSenhaModal({ open: false, user: null });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao resetar senha');
    } finally {
      setResettingSenha(false);
    }
  };

  const handleResetAll = async () => {
    setResettingAll(true);
    try {
      await usuariosAPI.resetarTodasSenhas();
      toast.success('Senhas de todos os usuários resetadas para: Senai@2026');
      setResetAllModal(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao resetar senhas');
    } finally {
      setResettingAll(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const RoleBadge = ({ role }) => {
    const config = roleConfig[role] || roleConfig.consultor;
    return (
      <Badge className={`${config.color} border-0`}>
        {config.label}
      </Badge>
    );
  };

  if (loading && !usuarios.length) {
    return (
      <div className="space-y-6" data-testid="usuarios-loading">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="gestao-usuarios-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
            Gestão de Usuários
          </h1>
          <p className="text-slate-500">
            Gerencie os usuários do sistema
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchUsuarios}
            data-testid="refresh-btn"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Atualizar
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setResetAllModal(true)}
            className="text-amber-600 border-amber-300 hover:bg-amber-50"
            data-testid="reset-all-btn"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Resetar Todas Senhas
          </Button>
          <Button
            className="bg-[#E30613] hover:bg-[#b9050f]"
            onClick={openCreateModal}
            data-testid="new-user-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Novo Usuário
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Buscar usuário..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
          data-testid="search-input"
        />
      </div>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Users className="h-5 w-5" />
            Usuários ({paginacao.total})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Perfil</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Último Acesso</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usuarios
                  .filter(u => 
                    u.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    u.email.toLowerCase().includes(searchTerm.toLowerCase())
                  )
                  .map((usuario) => (
                  <TableRow key={usuario.id} className="table-row-hover">
                    <TableCell className="font-medium">{usuario.nome}</TableCell>
                    <TableCell>{usuario.email}</TableCell>
                    <TableCell>
                      <RoleBadge role={usuario.role} />
                    </TableCell>
                    <TableCell>
                      {usuario.ativo ? (
                        <Badge className="bg-emerald-100 text-emerald-700 border-0">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Ativo
                        </Badge>
                      ) : (
                        <Badge className="bg-red-100 text-red-700 border-0">
                          <XCircle className="h-3 w-3 mr-1" />
                          Inativo
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>{formatDate(usuario.ultimo_acesso)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setResetSenhaModal({ open: true, user: usuario })}
                          className="text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                          title="Resetar senha"
                          data-testid={`reset-senha-${usuario.id}`}
                        >
                          <KeyRound className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditModal(usuario)}
                          data-testid={`edit-user-${usuario.id}`}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteModal({ open: true, user: usuario })}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          data-testid={`delete-user-${usuario.id}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {modalMode === 'create' ? 'Novo Usuário' : 'Editar Usuário'}
            </DialogTitle>
            <DialogDescription>
              {modalMode === 'create' 
                ? 'Preencha os dados para criar um novo usuário'
                : 'Atualize os dados do usuário'
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Nome *</Label>
              <Input
                value={formData.nome}
                onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                placeholder="Nome completo"
                data-testid="user-nome-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Email *</Label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                placeholder="email@exemplo.com"
                disabled={modalMode === 'edit'}
                data-testid="user-email-input"
              />
            </div>
            
            {modalMode === 'create' && (
              <div className="space-y-2">
                <Label>Senha *</Label>
                <Input
                  type="password"
                  value={formData.senha}
                  onChange={(e) => setFormData(prev => ({ ...prev, senha: e.target.value }))}
                  placeholder="••••••••"
                  data-testid="user-senha-input"
                />
              </div>
            )}
            
            <div className="space-y-2">
              <Label>Perfil *</Label>
              <Select 
                value={formData.role} 
                onValueChange={(v) => setFormData(prev => ({ ...prev, role: v }))}
              >
                <SelectTrigger data-testid="user-role-select">
                  <SelectValue placeholder="Selecione o perfil" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="consultor">Consultor</SelectItem>
                  <SelectItem value="assistente">Assistente</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {modalMode === 'edit' && (
              <div className="flex items-center justify-between">
                <Label>Usuário Ativo</Label>
                <Switch
                  checked={formData.ativo}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, ativo: checked }))}
                  data-testid="user-ativo-switch"
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setModalOpen(false)}>
              Cancelar
            </Button>
            <Button 
              className="bg-[#E30613] hover:bg-[#b9050f]"
              onClick={handleSubmit}
              disabled={submitting}
              data-testid="save-user-btn"
            >
              {submitting ? 'Salvando...' : 'Salvar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <Dialog open={deleteModal.open} onOpenChange={(open) => setDeleteModal({ open, user: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar Exclusão</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir o usuário "{deleteModal.user?.nome}"?
              Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteModal({ open: false, user: null })}>
              Cancelar
            </Button>
            <Button 
              variant="destructive"
              onClick={handleDelete}
              disabled={deleting}
              data-testid="confirm-delete-btn"
            >
              {deleting ? 'Excluindo...' : 'Excluir'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reset Senha Individual Modal */}
      <Dialog open={resetSenhaModal.open} onOpenChange={(open) => setResetSenhaModal({ open, user: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-amber-600" />
              Resetar Senha
            </DialogTitle>
            <DialogDescription>
              A senha do usuário <strong>{resetSenhaModal.user?.nome}</strong> será resetada para a senha padrão: <code className="bg-slate-100 px-2 py-1 rounded">Senai@2026</code>
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button variant="outline" onClick={() => setResetSenhaModal({ open: false, user: null })}>
              Cancelar
            </Button>
            <Button 
              className="bg-amber-500 hover:bg-amber-600"
              onClick={handleResetSenha}
              disabled={resettingSenha}
            >
              {resettingSenha ? 'Resetando...' : 'Confirmar Reset'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reset Todas Senhas Modal */}
      <Dialog open={resetAllModal} onOpenChange={setResetAllModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <RotateCcw className="h-5 w-5" />
              Resetar TODAS as Senhas
            </DialogTitle>
            <DialogDescription>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-2">
                <p className="text-red-800 font-medium mb-2">⚠️ Atenção!</p>
                <p className="text-red-700 text-sm">
                  Esta ação irá resetar a senha de <strong>TODOS</strong> os usuários para a senha padrão: <code className="bg-red-100 px-2 py-0.5 rounded">Senai@2026</code>
                </p>
                <p className="text-red-700 text-sm mt-2">
                  Todos os usuários precisarão trocar a senha no próximo login.
                </p>
              </div>
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button variant="outline" onClick={() => setResetAllModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="destructive"
              onClick={handleResetAll}
              disabled={resettingAll}
            >
              {resettingAll ? 'Resetando...' : 'Confirmar Reset de Todas'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GestaoUsuariosPage;
