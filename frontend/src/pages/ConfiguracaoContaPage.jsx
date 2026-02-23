import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Separator } from '../components/ui/separator';
import { toast } from 'sonner';
import api from '../services/api';
import {
  User, Lock, Bell, History, Shield, Mail, Phone, Building,
  Eye, EyeOff, Save, RefreshCw, CheckCircle, AlertTriangle
} from 'lucide-react';

const ConfiguracaoContaPage = () => {
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [atividades, setAtividades] = useState(null);
  
  // Form states
  const [perfil, setPerfil] = useState({
    nome: '',
    email: ''
  });
  
  const [senha, setSenha] = useState({
    senha_atual: '',
    nova_senha: '',
    confirmar_senha: ''
  });
  
  const [showSenha, setShowSenha] = useState({
    atual: false,
    nova: false,
    confirmar: false
  });

  useEffect(() => {
    if (user) {
      setPerfil({
        nome: user.nome || '',
        email: user.email || ''
      });
    }
    carregarAtividades();
  }, [user]);

  const carregarAtividades = async () => {
    try {
      const response = await api.get('/auth/me/atividades');
      setAtividades(response.data);
    } catch (error) {
      console.error('Erro ao carregar atividades:', error);
    }
  };

  const salvarPerfil = async () => {
    if (!perfil.nome.trim()) {
      toast.error('Nome é obrigatório');
      return;
    }

    setLoading(true);
    try {
      await api.put('/auth/me/perfil', perfil);
      toast.success('Perfil atualizado com sucesso!');
      if (refreshUser) refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar perfil');
    } finally {
      setLoading(false);
    }
  };

  const alterarSenha = async () => {
    if (!senha.senha_atual || !senha.nova_senha || !senha.confirmar_senha) {
      toast.error('Preencha todos os campos de senha');
      return;
    }

    if (senha.nova_senha !== senha.confirmar_senha) {
      toast.error('Nova senha e confirmação não conferem');
      return;
    }

    if (senha.nova_senha.length < 6) {
      toast.error('A nova senha deve ter pelo menos 6 caracteres');
      return;
    }

    setLoading(true);
    try {
      await api.put('/auth/me/senha', senha);
      toast.success('Senha alterada com sucesso!');
      setSenha({ senha_atual: '', nova_senha: '', confirmar_senha: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  const getRoleBadge = (role) => {
    const roles = {
      admin: { label: 'Administrador', color: 'bg-red-100 text-red-800' },
      assistente: { label: 'Assistente', color: 'bg-blue-100 text-blue-800' },
      consultor: { label: 'Consultor', color: 'bg-green-100 text-green-800' }
    };
    return roles[role] || { label: role, color: 'bg-gray-100 text-gray-800' };
  };

  const roleInfo = getRoleBadge(user?.role);

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900 font-['Chivo'] flex items-center gap-2">
            <User className="w-7 h-7 text-[#004587]" />
            Minha Conta
          </h1>
          <p className="text-slate-500">Gerencie suas informações pessoais e configurações</p>
        </div>

        {/* Card do Usuário */}
        <Card className="mb-6 bg-gradient-to-r from-[#004587] to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center">
                <User className="w-8 h-8" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">{user?.nome}</h2>
                <p className="text-blue-100">{user?.email}</p>
                <Badge className={`mt-2 ${roleInfo.color}`}>
                  <Shield className="w-3 h-3 mr-1" />
                  {roleInfo.label}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs defaultValue="perfil" className="space-y-4">
          <TabsList className="grid grid-cols-3 w-full max-w-md">
            <TabsTrigger value="perfil" className="flex items-center gap-2">
              <User className="w-4 h-4" />
              Perfil
            </TabsTrigger>
            <TabsTrigger value="seguranca" className="flex items-center gap-2">
              <Lock className="w-4 h-4" />
              Segurança
            </TabsTrigger>
            <TabsTrigger value="atividades" className="flex items-center gap-2">
              <History className="w-4 h-4" />
              Atividades
            </TabsTrigger>
          </TabsList>

          {/* Tab Perfil */}
          <TabsContent value="perfil">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Informações Pessoais</CardTitle>
                <CardDescription>Atualize suas informações de perfil</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label>Nome Completo</Label>
                    <Input
                      value={perfil.nome}
                      onChange={(e) => setPerfil({ ...perfil, nome: e.target.value })}
                      placeholder="Seu nome"
                      data-testid="input-nome"
                    />
                  </div>
                  <div>
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={perfil.email}
                      onChange={(e) => setPerfil({ ...perfil, email: e.target.value })}
                      placeholder="seu@email.com"
                      data-testid="input-email"
                    />
                  </div>
                </div>

                <Separator />

                <div className="flex justify-end">
                  <Button 
                    onClick={salvarPerfil} 
                    disabled={loading}
                    className="bg-[#004587]"
                    data-testid="btn-salvar-perfil"
                  >
                    {loading ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4 mr-2" />
                    )}
                    Salvar Alterações
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tab Segurança */}
          <TabsContent value="seguranca">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Lock className="w-5 h-5 text-[#004587]" />
                  Alterar Senha
                </CardTitle>
                <CardDescription>
                  Mantenha sua conta segura com uma senha forte
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Senha Atual</Label>
                  <div className="relative">
                    <Input
                      type={showSenha.atual ? 'text' : 'password'}
                      value={senha.senha_atual}
                      onChange={(e) => setSenha({ ...senha, senha_atual: e.target.value })}
                      placeholder="Digite sua senha atual"
                      data-testid="input-senha-atual"
                    />
                    <button
                      type="button"
                      onClick={() => setShowSenha({ ...showSenha, atual: !showSenha.atual })}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {showSenha.atual ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label>Nova Senha</Label>
                    <div className="relative">
                      <Input
                        type={showSenha.nova ? 'text' : 'password'}
                        value={senha.nova_senha}
                        onChange={(e) => setSenha({ ...senha, nova_senha: e.target.value })}
                        placeholder="Mínimo 6 caracteres"
                        data-testid="input-nova-senha"
                      />
                      <button
                        type="button"
                        onClick={() => setShowSenha({ ...showSenha, nova: !showSenha.nova })}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      >
                        {showSenha.nova ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <Label>Confirmar Nova Senha</Label>
                    <div className="relative">
                      <Input
                        type={showSenha.confirmar ? 'text' : 'password'}
                        value={senha.confirmar_senha}
                        onChange={(e) => setSenha({ ...senha, confirmar_senha: e.target.value })}
                        placeholder="Repita a nova senha"
                        data-testid="input-confirmar-senha"
                      />
                      <button
                        type="button"
                        onClick={() => setShowSenha({ ...showSenha, confirmar: !showSenha.confirmar })}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      >
                        {showSenha.confirmar ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                {senha.nova_senha && senha.confirmar_senha && (
                  <div className={`flex items-center gap-2 text-sm ${
                    senha.nova_senha === senha.confirmar_senha ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {senha.nova_senha === senha.confirmar_senha ? (
                      <>
                        <CheckCircle className="w-4 h-4" />
                        Senhas conferem
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-4 h-4" />
                        Senhas não conferem
                      </>
                    )}
                  </div>
                )}

                <Separator />

                <div className="flex justify-end">
                  <Button 
                    onClick={alterarSenha} 
                    disabled={loading || !senha.senha_atual || !senha.nova_senha || senha.nova_senha !== senha.confirmar_senha}
                    className="bg-[#004587]"
                    data-testid="btn-alterar-senha"
                  >
                    {loading ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Lock className="w-4 h-4 mr-2" />
                    )}
                    Alterar Senha
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tab Atividades */}
          <TabsContent value="atividades">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <History className="w-5 h-5 text-[#004587]" />
                  Atividades Recentes
                </CardTitle>
                <CardDescription>
                  Histórico das suas últimas ações no sistema
                </CardDescription>
              </CardHeader>
              <CardContent>
                {atividades?.pedidos_recentes?.length > 0 ? (
                  <div className="space-y-4">
                    <h4 className="font-medium text-slate-700">Últimas Solicitações</h4>
                    <div className="space-y-2">
                      {atividades.pedidos_recentes.map((pedido) => (
                        <div 
                          key={pedido.id}
                          className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                        >
                          <div>
                            <p className="font-medium text-slate-800">
                              {pedido.protocolo || 'Sem protocolo'}
                            </p>
                            <p className="text-sm text-slate-500">{pedido.curso}</p>
                          </div>
                          <div className="text-right">
                            <Badge variant="outline">{pedido.status}</Badge>
                            <p className="text-xs text-slate-400 mt-1">
                              {pedido.created_at ? new Date(pedido.created_at).toLocaleDateString('pt-BR') : '-'}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <History className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>Nenhuma atividade recente</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default ConfiguracaoContaPage;
