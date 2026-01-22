import { useState } from 'react';
import { NavLink, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { 
  LayoutDashboard, 
  FileText, 
  Users, 
  LogOut, 
  Menu, 
  X,
  Plus,
  Download,
  ChevronDown,
  User,
  Settings,
  Upload,
  AlertCircle,
  DollarSign
} from 'lucide-react';

const DashboardLayout = () => {
  const { user, logout, hasPermission } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleExportTOTVS = async () => {
    try {
      const token = localStorage.getItem('token');
      const apiUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${apiUrl}/api/pedidos/exportar/totvs?formato=xlsx`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Erro ao exportar');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `exportacao_totvs_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (error) {
      console.error('Erro ao exportar:', error);
      alert('Erro ao exportar dados. Verifique se há pedidos realizados.');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getNavItems = () => {
    const items = [];
    
    if (user?.role === 'consultor') {
      items.push(
        { to: '/consultor', icon: LayoutDashboard, label: 'Meus Pedidos' },
        { to: '/consultor/novo-pedido', icon: Plus, label: 'Nova Solicitação' },
        { to: '/importacao', icon: Upload, label: 'Importar Lote' }
      );
    } else if (user?.role === 'assistente') {
      items.push(
        { to: '/assistente', icon: LayoutDashboard, label: 'Painel de Gestão' },
        { to: '/assistente/novo-pedido', icon: Plus, label: 'Nova Solicitação' },
        { to: '/pendencias', icon: AlertCircle, label: 'Pendências' },
        { to: '/reembolsos', icon: DollarSign, label: 'Reembolsos' },
        { to: '/importacao', icon: Upload, label: 'Importar Lote' }
      );
    } else if (user?.role === 'admin') {
      items.push(
        { to: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
        { to: '/admin/pedidos', icon: FileText, label: 'Pedidos' },
        { to: '/pendencias', icon: AlertCircle, label: 'Pendências' },
        { to: '/reembolsos', icon: DollarSign, label: 'Reembolsos' },
        { to: '/admin/usuarios', icon: Users, label: 'Usuários' },
        { to: '/admin/cadastros', icon: Settings, label: 'Cadastros' },
        { to: '/admin/novo-pedido', icon: Plus, label: 'Nova Solicitação' },
        { to: '/importacao', icon: Upload, label: 'Importar Lote' }
      );
    }
    
    return items;
  };

  const navItems = getNavItems();

  return (
    <div className="min-h-screen bg-slate-50" data-testid="dashboard-layout">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-[#004587] shadow-md z-50">
        <div className="h-full px-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              className="lg:hidden text-white"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <div className="flex items-center gap-3">
              <img 
                src="https://customer-assets.emergentagent.com/job_matricula-hub/artifacts/p7o5gy77_logo_cimatec.jpg" 
                alt="SENAI CIMATEC"
                className="h-10 bg-white rounded px-2 py-1 object-contain"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="text-white hover:bg-white/10">
                  <User className="h-4 w-4 mr-2" />
                  <span className="hidden sm:inline">{user?.nome}</span>
                  <ChevronDown className="h-4 w-4 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div>
                    <p className="font-medium">{user?.nome}</p>
                    <p className="text-xs text-slate-500">{user?.email}</p>
                    <span className="inline-block mt-1 px-2 py-0.5 bg-[#004587]/10 text-[#004587] text-xs rounded-full capitalize">
                      {user?.role}
                    </span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600 cursor-pointer">
                  <LogOut className="h-4 w-4 mr-2" />
                  Sair
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside
        className={`
          fixed top-16 left-0 bottom-0 w-64 bg-white border-r border-slate-200 z-40
          transform transition-transform duration-200 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <nav className="p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/consultor' || item.to === '/assistente' || item.to === '/admin'}
              className={({ isActive }) =>
                `sidebar-item ${isActive ? 'active' : ''}`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Exportar TOTVS - só para assistente e admin */}
        {hasPermission('pedido:exportar') && (
          <div className="absolute bottom-4 left-4 right-4">
            <Button
              variant="outline"
              className="w-full justify-start gap-2"
              onClick={handleExportTOTVS}
              data-testid="export-totvs-btn"
            >
              <Download className="h-4 w-4" />
              Exportar TOTVS
            </Button>
          </div>
        )}
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <main className="pt-16 lg:pl-64">
        <div className="p-4 md:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
