# Routers do Sistema SYNAPSE - Hub de Inteligência Operacional
# Refatorado para Clean Architecture modular

from .auth_routes import router as auth_router
from .usuarios_routes import router as usuarios_router
from .pedidos_routes import router as pedidos_router
from .cadastros import router as cadastros_router
from .pendencias import router as pendencias_router
from .reembolsos import router as reembolsos_router
from .auxiliares import router as auxiliares_router

__all__ = [
    "auth_router",
    "usuarios_router", 
    "pedidos_router",
    "cadastros_router",
    "pendencias_router",
    "reembolsos_router",
    "auxiliares_router"
]
