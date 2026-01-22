import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "./contexts/AuthContext";

// Components
import ProtectedRoute from "./components/ProtectedRoute";
import DashboardLayout from "./components/DashboardLayout";

// Pages
import LoginPage from "./pages/LoginPage";
import ConsultorDashboard from "./pages/ConsultorDashboard";
import AssistenteDashboard from "./pages/AssistenteDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import AdminPedidosPage from "./pages/AdminPedidosPage";
import GestaoUsuariosPage from "./pages/GestaoUsuariosPage";
import GestaoCadastrosPage from "./pages/GestaoCadastrosPage";
import NovaMatriculaPage from "./pages/NovaMatriculaPage";
import PedidoDetalhePage from "./pages/PedidoDetalhePage";
import ImportacaoLotePage from "./pages/ImportacaoLotePage";
import CentralPendenciasPage from "./pages/CentralPendenciasPage";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Consultor Routes */}
          <Route element={<ProtectedRoute allowedRoles={['consultor', 'assistente', 'admin']} />}>
            <Route element={<DashboardLayout />}>
              {/* Consultor specific routes */}
              <Route path="/consultor" element={<ConsultorDashboard />} />
              <Route path="/consultor/novo-pedido" element={<NovaMatriculaPage />} />
              <Route path="/consultor/pedido/:id" element={<PedidoDetalhePage />} />
            </Route>
          </Route>

          {/* Assistente Routes */}
          <Route element={<ProtectedRoute allowedRoles={['assistente', 'admin']} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/assistente" element={<AssistenteDashboard />} />
              <Route path="/assistente/novo-pedido" element={<NovaMatriculaPage />} />
              <Route path="/assistente/pedido/:id" element={<PedidoDetalhePage />} />
            </Route>
          </Route>

          {/* Admin Routes */}
          <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/pedidos" element={<AdminPedidosPage />} />
              <Route path="/admin/pedido/:id" element={<PedidoDetalhePage />} />
              <Route path="/admin/usuarios" element={<GestaoUsuariosPage />} />
              <Route path="/admin/cadastros" element={<GestaoCadastrosPage />} />
              <Route path="/admin/novo-pedido" element={<NovaMatriculaPage />} />
              <Route path="/admin/importacao" element={<ImportacaoLotePage />} />
              <Route path="/admin/pendencias" element={<CentralPendenciasPage />} />
            </Route>
          </Route>

          {/* Central de Pendências - Assistentes e Admin */}
          <Route element={<ProtectedRoute allowedRoles={['assistente', 'admin']} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/pendencias" element={<CentralPendenciasPage />} />
            </Route>
          </Route>

          {/* Importação em Lote - Todos os perfis */}
          <Route element={<ProtectedRoute allowedRoles={['consultor', 'assistente', 'admin']} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/importacao" element={<ImportacaoLotePage />} />
            </Route>
          </Route>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
        
        {/* Toast notifications - moved inside BrowserRouter */}
        <Toaster 
          position="top-right"
          richColors
          toastOptions={{
            style: {
              fontFamily: 'Manrope, sans-serif',
            },
          }}
        />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
