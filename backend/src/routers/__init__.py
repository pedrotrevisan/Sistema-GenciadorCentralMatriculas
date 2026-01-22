# Routers do Sistema Central de Matrículas
from .auth import router as auth_router
from .usuarios import router as usuarios_router
from .pedidos import router as pedidos_router
from .cadastros import router as cadastros_router
from .pendencias import router as pendencias_router
from .reembolsos import router as reembolsos_router

__all__ = [
    "auth_router",
    "usuarios_router", 
    "pedidos_router",
    "cadastros_router",
    "pendencias_router",
    "reembolsos_router"
]
