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
