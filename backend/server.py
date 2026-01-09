"""FastAPI Backend - Sistema Central de Matrículas SENAI CIMATEC"""
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging
import uuid
from datetime import datetime, timezone

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Domain imports
from src.domain.entities import Usuario, RoleUsuario
from src.domain.value_objects import Email, StatusPedido
from src.domain.exceptions import (
    DomainException, ValidationException, BusinessRuleException,
    NotFoundException, AuthenticationException, AuthorizationException,
    DuplicidadeException
)

# Infrastructure imports
from src.infrastructure.persistence.repositories import (
    PedidoRepositoryMongo, UsuarioRepositoryMongo, AuditoriaRepositoryMongo
)
from src.infrastructure.security import JWTAuthenticator

# Application imports
from src.application.dtos.request import (
    CriarPedidoDTO, AtualizarStatusDTO, LoginDTO, 
    CriarUsuarioDTO, AtualizarUsuarioDTO, FiltrosPedidoDTO
)
from src.application.dtos.response import (
    PedidoResponseDTO, ListaPedidosResponseDTO, UsuarioResponseDTO,
    LoginResponseDTO, ContadorStatusDTO, DashboardDTO, ErrorResponseDTO
)
from src.application.use_cases import (
    CriarPedidoMatriculaUseCase, AtualizarStatusPedidoUseCase,
    GerarExportacaoTOTVSUseCase, ConsultarPedidosUseCase
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(
    title="Sistema Central de Matrículas - SENAI CIMATEC",
    description="API para gerenciamento de matrículas",
    version="1.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# Initialize services
jwt_auth = JWTAuthenticator()

# Initialize repositories
pedido_repo = PedidoRepositoryMongo(db)
usuario_repo = UsuarioRepositoryMongo(db)
auditoria_repo = AuditoriaRepositoryMongo(db)

# Initialize use cases
criar_pedido_uc = CriarPedidoMatriculaUseCase(pedido_repo, auditoria_repo)
atualizar_status_uc = AtualizarStatusPedidoUseCase(pedido_repo, auditoria_repo)
gerar_exportacao_uc = GerarExportacaoTOTVSUseCase(pedido_repo, auditoria_repo)
consultar_pedidos_uc = ConsultarPedidosUseCase(pedido_repo)


# ==================== DEPENDENCY INJECTION ====================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Usuario:
    """Dependency para obter usuário autenticado"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt_auth.verificar_token(token)
        usuario_id = payload.get("sub")
        
        usuario = await usuario_repo.buscar_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado"
            )
        
        if not usuario.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )
        
        return usuario
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message)
        )


async def get_optional_user(token: str = Depends(oauth2_scheme)) -> Optional[Usuario]:
    """Dependency para obter usuário opcionalmente"""
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


def require_permission(permission: str):
    """Dependency factory para verificar permissão"""
    async def check_permission(user: Usuario = Depends(get_current_user)):
        if not user.tem_permissao(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{permission}' necessária"
            )
        return user
    return check_permission


# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(ValidationException)
async def validation_exception_handler(request, exc: ValidationException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code=exc.code,
            field=exc.field
        ).model_dump_json(),
        status_code=400,
        media_type="application/json"
    )


@app.exception_handler(BusinessRuleException)
async def business_rule_exception_handler(request, exc: BusinessRuleException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code=exc.code
        ).model_dump_json(),
        status_code=422,
        media_type="application/json"
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request, exc: NotFoundException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code=exc.code
        ).model_dump_json(),
        status_code=404,
        media_type="application/json"
    )


@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(request, exc: AuthorizationException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code=exc.code
        ).model_dump_json(),
        status_code=403,
        media_type="application/json"
    )


@app.exception_handler(DuplicidadeException)
async def duplicidade_exception_handler(request, exc: DuplicidadeException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code="DUPLICIDADE"
        ).model_dump_json(),
        status_code=409,
        media_type="application/json"
    )


# ==================== AUTH ROUTES ====================

class LoginRequest(BaseModel):
    email: str
    senha: str

class RegisterRequest(BaseModel):
    nome: str = Field(..., min_length=3)
    email: str
    senha: str = Field(..., min_length=6)
    role: str = Field(default="consultor")


@api_router.post("/auth/login", response_model=LoginResponseDTO, tags=["Auth"])
async def login(request: LoginRequest):
    """Realiza login e retorna token JWT"""
    usuario = await usuario_repo.buscar_por_email(request.email)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos"
        )
    
    if not jwt_auth.verificar_senha(request.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos"
        )
    
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    # Registra acesso
    usuario.registrar_acesso()
    await usuario_repo.salvar(usuario)
    
    # Gera token
    token = jwt_auth.criar_token(usuario)
    
    return LoginResponseDTO(
        token=token,
        usuario=UsuarioResponseDTO(**usuario.to_dict())
    )


@api_router.post("/auth/register", response_model=UsuarioResponseDTO, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(request: RegisterRequest):
    """Registra um novo usuário"""
    # Verifica se email já existe
    existente = await usuario_repo.buscar_por_email(request.email)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado"
        )
    
    # Cria usuário
    usuario = Usuario(
        id=str(uuid.uuid4()),
        nome=request.nome,
        email=Email(request.email),
        senha_hash=jwt_auth.hash_senha(request.senha),
        role=RoleUsuario.from_string(request.role)
    )
    
    await usuario_repo.salvar(usuario)
    
    return UsuarioResponseDTO(**usuario.to_dict())


@api_router.get("/auth/me", response_model=UsuarioResponseDTO, tags=["Auth"])
async def get_me(usuario: Usuario = Depends(get_current_user)):
    """Retorna dados do usuário autenticado"""
    return UsuarioResponseDTO(**usuario.to_dict())


# ==================== PEDIDOS ROUTES ====================

@api_router.post("/pedidos", response_model=PedidoResponseDTO, tags=["Pedidos"])
async def criar_pedido(
    request: CriarPedidoDTO,
    usuario: Usuario = Depends(require_permission("pedido:criar"))
):
    """Cria um novo pedido de matrícula"""
    pedido = await criar_pedido_uc.executar(request, usuario)
    return PedidoResponseDTO(**pedido.to_dict())


@api_router.get("/pedidos", response_model=ListaPedidosResponseDTO, tags=["Pedidos"])
async def listar_pedidos(
    status: Optional[str] = None,
    consultor_id: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista pedidos com filtros"""
    filtros = FiltrosPedidoDTO(
        status=status,
        consultor_id=consultor_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=pagina,
        por_pagina=por_pagina
    )
    return await consultar_pedidos_uc.listar(filtros, usuario)


@api_router.get("/pedidos/dashboard", tags=["Pedidos"])
async def get_dashboard(usuario: Usuario = Depends(get_current_user)):
    """Retorna dados do dashboard"""
    contagem = await consultar_pedidos_uc.contar_por_status(usuario)
    
    # Busca pedidos recentes
    filtros = FiltrosPedidoDTO(pagina=1, por_pagina=5)
    resultado = await consultar_pedidos_uc.listar(filtros, usuario)
    
    return {
        "contagem_status": contagem,
        "pedidos_recentes": [p.model_dump() for p in resultado.pedidos]
    }


@api_router.get("/pedidos/{pedido_id}", response_model=PedidoResponseDTO, tags=["Pedidos"])
async def buscar_pedido(
    pedido_id: str,
    usuario: Usuario = Depends(get_current_user)
):
    """Busca pedido por ID"""
    return await consultar_pedidos_uc.buscar_por_id(pedido_id, usuario)


@api_router.patch("/pedidos/{pedido_id}/status", response_model=PedidoResponseDTO, tags=["Pedidos"])
async def atualizar_status(
    pedido_id: str,
    request: AtualizarStatusDTO,
    usuario: Usuario = Depends(get_current_user)
):
    """Atualiza status do pedido"""
    pedido = await atualizar_status_uc.executar(pedido_id, request, usuario)
    return PedidoResponseDTO(**pedido.to_dict())


@api_router.get("/pedidos/exportar/totvs", tags=["Pedidos"])
async def exportar_totvs(
    formato: str = Query(default="xlsx", regex="^(xlsx|csv)$"),
    usuario: Usuario = Depends(require_permission("pedido:exportar"))
):
    """Exporta pedidos realizados para formato TOTVS"""
    arquivo, content_type, nome_arquivo = await gerar_exportacao_uc.executar(usuario, formato)
    
    return StreamingResponse(
        arquivo,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={nome_arquivo}"
        }
    )


# ==================== USUARIOS ROUTES ====================

@api_router.get("/usuarios", tags=["Usuarios"])
async def listar_usuarios(
    ativo: Optional[bool] = None,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    usuario: Usuario = Depends(require_permission("usuario:gerenciar"))
):
    """Lista todos os usuários"""
    usuarios, total = await usuario_repo.listar_todos(
        ativo=ativo,
        pagina=pagina,
        por_pagina=por_pagina
    )
    
    return {
        "usuarios": [UsuarioResponseDTO(**u.to_dict()).model_dump() for u in usuarios],
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina
    }


@api_router.get("/usuarios/{usuario_id}", response_model=UsuarioResponseDTO, tags=["Usuarios"])
async def buscar_usuario(
    usuario_id: str,
    current_user: Usuario = Depends(require_permission("usuario:gerenciar"))
):
    """Busca usuário por ID"""
    usuario = await usuario_repo.buscar_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UsuarioResponseDTO(**usuario.to_dict())


@api_router.patch("/usuarios/{usuario_id}", response_model=UsuarioResponseDTO, tags=["Usuarios"])
async def atualizar_usuario(
    usuario_id: str,
    request: AtualizarUsuarioDTO,
    current_user: Usuario = Depends(require_permission("usuario:gerenciar"))
):
    """Atualiza dados do usuário"""
    usuario = await usuario_repo.buscar_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if request.nome:
        usuario.nome = request.nome
    if request.role:
        usuario.role = RoleUsuario.from_string(request.role)
    if request.ativo is not None:
        usuario.ativo = request.ativo
    
    usuario.updated_at = datetime.now(timezone.utc)
    await usuario_repo.salvar(usuario)
    
    return UsuarioResponseDTO(**usuario.to_dict())


@api_router.delete("/usuarios/{usuario_id}", tags=["Usuarios"])
async def deletar_usuario(
    usuario_id: str,
    current_user: Usuario = Depends(require_permission("usuario:gerenciar"))
):
    """Deleta um usuário"""
    if usuario_id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível deletar o próprio usuário")
    
    sucesso = await usuario_repo.deletar(usuario_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {"message": "Usuário deletado com sucesso"}


# ==================== DADOS AUXILIARES ====================

@api_router.get("/cursos", tags=["Auxiliares"])
async def listar_cursos():
    """Lista cursos disponíveis (dados mock)"""
    return [
        {"id": "1", "nome": "Técnico em Mecatrônica"},
        {"id": "2", "nome": "Técnico em Automação Industrial"},
        {"id": "3", "nome": "Técnico em Eletrotécnica"},
        {"id": "4", "nome": "Técnico em Desenvolvimento de Sistemas"},
        {"id": "5", "nome": "Técnico em Redes de Computadores"},
        {"id": "6", "nome": "Técnico em Segurança do Trabalho"},
        {"id": "7", "nome": "Engenharia de Produção"},
        {"id": "8", "nome": "Engenharia Mecânica"}
    ]


@api_router.get("/projetos", tags=["Auxiliares"])
async def listar_projetos():
    """Lista projetos disponíveis (dados mock)"""
    return [
        {"id": "1", "nome": "Projeto SENAI de Inovação"},
        {"id": "2", "nome": "Projeto Capacitação Industrial 4.0"},
        {"id": "3", "nome": "Projeto Jovem Aprendiz"},
        {"id": "4", "nome": "Projeto Qualifica Bahia"}
    ]


@api_router.get("/empresas", tags=["Auxiliares"])
async def listar_empresas():
    """Lista empresas parceiras (dados mock)"""
    return [
        {"id": "1", "nome": "Petrobras"},
        {"id": "2", "nome": "Ford Brasil"},
        {"id": "3", "nome": "BYD Energy"},
        {"id": "4", "nome": "Braskem"},
        {"id": "5", "nome": "Suzano Papel e Celulose"}
    ]


@api_router.get("/status-pedido", tags=["Auxiliares"])
async def listar_status():
    """Lista status disponíveis"""
    return [
        {"value": s.value, "label": s.label}
        for s in StatusPedido
    ]


# ==================== ROOT & HEALTH ====================

@api_router.get("/", tags=["Health"])
async def root():
    return {"message": "Sistema Central de Matrículas - SENAI CIMATEC", "version": "1.0.0"}


@api_router.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Cria usuário admin padrão se não existir"""
    admin = await usuario_repo.buscar_por_email("admin@senai.br")
    if not admin:
        admin_user = Usuario(
            id=str(uuid.uuid4()),
            nome="Administrador",
            email=Email("admin@senai.br"),
            senha_hash=jwt_auth.hash_senha("admin123"),
            role=RoleUsuario.ADMIN
        )
        await usuario_repo.salvar(admin_user)
        logger.info("Usuário admin criado: admin@senai.br / admin123")
    
    # Cria usuário consultor de exemplo
    consultor = await usuario_repo.buscar_por_email("consultor@senai.br")
    if not consultor:
        consultor_user = Usuario(
            id=str(uuid.uuid4()),
            nome="Consultor Exemplo",
            email=Email("consultor@senai.br"),
            senha_hash=jwt_auth.hash_senha("consultor123"),
            role=RoleUsuario.CONSULTOR
        )
        await usuario_repo.salvar(consultor_user)
        logger.info("Usuário consultor criado: consultor@senai.br / consultor123")
    
    # Cria usuário assistente de exemplo
    assistente = await usuario_repo.buscar_por_email("assistente@senai.br")
    if not assistente:
        assistente_user = Usuario(
            id=str(uuid.uuid4()),
            nome="Assistente Exemplo",
            email=Email("assistente@senai.br"),
            senha_hash=jwt_auth.hash_senha("assistente123"),
            role=RoleUsuario.ASSISTENTE
        )
        await usuario_repo.salvar(assistente_user)
        logger.info("Usuário assistente criado: assistente@senai.br / assistente123")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
