import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';
import { toast } from 'sonner';
import api from '../services/api';
import { Loader2, Eye, EyeOff, Lock, ShieldCheck, AlertTriangle } from 'lucide-react';

const TrocarSenhaPrimeiroAcessoPage = () => {
  const [novaSenha, setNovaSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();

  // Validações
  const senhaMinLength = novaSenha.length >= 6;
  const senhaTemNumero = /\d/.test(novaSenha);
  const senhaTemLetra = /[a-zA-Z]/.test(novaSenha);
  const senhasConferem = novaSenha === confirmarSenha && confirmarSenha.length > 0;
  const senhaValida = senhaMinLength && senhaTemNumero && senhaTemLetra && senhasConferem;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!senhaValida) {
      toast.error('Verifique os requisitos da senha');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/trocar-senha-primeiro-acesso', {
        nova_senha: novaSenha,
        confirmar_senha: confirmarSenha
      });
      
      toast.success('Senha definida com sucesso! Bem-vindo ao SYNAPSE.');
      
      // Atualizar dados do usuário
      if (refreshUser) {
        await refreshUser();
      }
      
      // Redirecionar baseado no role
      if (user?.role === 'consultor') {
        navigate('/consultor');
      } else if (user?.role === 'assistente') {
        navigate('/assistente');
      } else {
        navigate('/admin');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao definir senha');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center login-bg p-4"
      data-testid="trocar-senha-primeiro-acesso-page"
    >
      <Card className="w-full max-w-md shadow-2xl animate-fadeIn">
        <CardHeader className="space-y-4 pb-4 text-center">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <ShieldCheck className="w-8 h-8 text-blue-600" />
          </div>
          <div>
            <CardTitle className="text-xl">Bem-vindo ao SYNAPSE!</CardTitle>
            <CardDescription className="mt-2">
              Por segurança, defina uma nova senha para continuar.
            </CardDescription>
          </div>
        </CardHeader>
        
        <CardContent>
          <Alert className="mb-6 bg-amber-50 border-amber-200">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-700 text-sm">
              Este é seu primeiro acesso. A senha padrão precisa ser alterada.
            </AlertDescription>
          </Alert>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="nova-senha" className="text-sm font-medium">
                Nova Senha
              </Label>
              <div className="relative">
                <Input
                  id="nova-senha"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Digite sua nova senha"
                  value={novaSenha}
                  onChange={(e) => setNovaSenha(e.target.value)}
                  required
                  className="h-11 pr-10"
                  data-testid="nova-senha-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmar-senha" className="text-sm font-medium">
                Confirmar Senha
              </Label>
              <div className="relative">
                <Input
                  id="confirmar-senha"
                  type={showConfirm ? 'text' : 'password'}
                  placeholder="Confirme sua nova senha"
                  value={confirmarSenha}
                  onChange={(e) => setConfirmarSenha(e.target.value)}
                  required
                  className="h-11 pr-10"
                  data-testid="confirmar-senha-input"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Requisitos da senha */}
            <div className="p-3 bg-slate-50 rounded-lg space-y-2">
              <p className="text-xs font-semibold text-slate-600 uppercase">Requisitos da senha:</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className={`flex items-center gap-1.5 ${senhaMinLength ? 'text-green-600' : 'text-slate-400'}`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${senhaMinLength ? 'bg-green-500' : 'bg-slate-300'}`} />
                  Mínimo 6 caracteres
                </div>
                <div className={`flex items-center gap-1.5 ${senhaTemLetra ? 'text-green-600' : 'text-slate-400'}`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${senhaTemLetra ? 'bg-green-500' : 'bg-slate-300'}`} />
                  Pelo menos 1 letra
                </div>
                <div className={`flex items-center gap-1.5 ${senhaTemNumero ? 'text-green-600' : 'text-slate-400'}`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${senhaTemNumero ? 'bg-green-500' : 'bg-slate-300'}`} />
                  Pelo menos 1 número
                </div>
                <div className={`flex items-center gap-1.5 ${senhasConferem ? 'text-green-600' : 'text-slate-400'}`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${senhasConferem ? 'bg-green-500' : 'bg-slate-300'}`} />
                  Senhas conferem
                </div>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading || !senhaValida}
              className="w-full h-11 bg-[#004587] hover:bg-[#003366] text-white font-medium"
              data-testid="definir-senha-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Salvando...
                </>
              ) : (
                <>
                  <Lock className="mr-2 h-4 w-4" />
                  Definir Nova Senha
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-200 text-center">
            <p className="text-xs text-slate-400">
              SYNAPSE — Hub de Inteligência Operacional
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TrocarSenhaPrimeiroAcessoPage;
