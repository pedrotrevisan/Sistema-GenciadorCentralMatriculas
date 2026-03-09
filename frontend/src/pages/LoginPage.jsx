import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader } from '../components/ui/card';
import { toast } from 'sonner';
import { Loader2, Eye, EyeOff } from 'lucide-react';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const usuario = await login(email, senha);
      
      // Verificar se é primeiro acesso
      if (usuario.primeiro_acesso) {
        toast.info('Por segurança, defina uma nova senha.');
        navigate('/primeiro-acesso');
        return;
      }
      
      toast.success(`Bem-vindo, ${usuario.nome}!`);
      
      // Redirect based on role
      if (usuario.role === 'consultor') {
        navigate('/consultor');
      } else if (usuario.role === 'assistente') {
        navigate('/assistente');
      } else {
        navigate('/admin');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center login-bg p-4"
      data-testid="login-page"
    >
      <Card className="w-full max-w-md shadow-2xl animate-fadeIn">
        <CardHeader className="space-y-4 pb-4">
          {/* Logo SENAI CIMATEC */}
          <div className="text-center space-y-3">
            <img 
              src="https://customer-assets.emergentagent.com/job_matricula-hub/artifacts/p7o5gy77_logo_cimatec.jpg" 
              alt="SENAI CIMATEC"
              className="h-16 mx-auto object-contain"
            />
            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">
              Central de Matrículas
            </p>
          </div>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                E-MAIL
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="h-12 focus:ring-[#004587]"
                data-testid="login-email-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="senha" className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                SENHA
              </Label>
              <div className="relative">
                <Input
                  id="senha"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  required
                  className="h-12 pr-10 focus:ring-[#004587]"
                  data-testid="login-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-[#E30613] hover:bg-[#b9050f] text-white font-semibold uppercase tracking-wider"
              data-testid="login-submit-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                'ENTRAR'
              )}
            </Button>
          </form>

          {/* Footer institucional */}
          <div className="mt-6 pt-4 border-t border-slate-200 text-center">
            <p className="text-xs text-slate-400">
              SYNAPSE — Hub de Inteligência Operacional
            </p>
            <p className="text-xs text-slate-400 mt-1">
              SENAI CIMATEC © {new Date().getFullYear()}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;
