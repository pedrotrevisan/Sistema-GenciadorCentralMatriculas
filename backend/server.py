"""FastAPI Backend - Sistema Central de Matrículas SENAI CIMATEC (PostgreSQL)"""
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
from contextlib import asynccontextmanager
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

# Infrastructure imports - PostgreSQL
from src.infrastructure.persistence.database import engine, async_session, init_db, Base
from src.infrastructure.persistence.repositories import PedidoRepository, UsuarioRepository, AuditoriaRepository
from src.infrastructure.persistence.models import CursoModel, ProjetoModel, EmpresaModel
from src.infrastructure.security import JWTAuthenticator

# Application imports
from src.application.dtos.request import (
    CriarPedidoDTO, AtualizarStatusDTO, 
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

# JWT Authenticator
jwt_auth = JWTAuthenticator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    logger.info("Initializing PostgreSQL database...")
    await init_db()
    
    # Create default users and seed data
    async with async_session() as session:
        usuario_repo = UsuarioRepository(session)
        
        # Admin
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
        
        # Consultor
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
        
        # Assistente
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
        
        # Seed Cursos
        from sqlalchemy import select, func
        cursos_count = await session.execute(select(func.count(CursoModel.id)))
        if cursos_count.scalar() == 0:
            cursos_iniciais = [
                "Técnico em Mecatrônica",
                "Técnico em Automação Industrial",
                "Técnico em Eletrotécnica",
                "Técnico em Desenvolvimento de Sistemas",
                "Técnico em Redes de Computadores",
                "Técnico em Segurança do Trabalho",
                "Engenharia de Produção",
                "Engenharia Mecânica"
            ]
            for nome in cursos_iniciais:
                session.add(CursoModel(id=str(uuid.uuid4()), nome=nome))
            await session.commit()
            logger.info(f"{len(cursos_iniciais)} cursos criados")
        
        # Seed Projetos
        projetos_count = await session.execute(select(func.count(ProjetoModel.id)))
        if projetos_count.scalar() == 0:
            projetos_iniciais = [
                "Projeto SENAI de Inovação",
                "Projeto Capacitação Industrial 4.0",
                "Projeto Jovem Aprendiz",
                "Projeto Qualifica Bahia"
            ]
            for nome in projetos_iniciais:
                session.add(ProjetoModel(id=str(uuid.uuid4()), nome=nome))
            await session.commit()
            logger.info(f"{len(projetos_iniciais)} projetos criados")
        
        # Seed Empresas
        empresas_count = await session.execute(select(func.count(EmpresaModel.id)))
        if empresas_count.scalar() == 0:
            empresas_iniciais = [
                "Petrobras",
                "Ford Brasil",
                "BYD Energy",
                "Braskem",
                "Suzano Papel e Celulose"
            ]
            for nome in empresas_iniciais:
                session.add(EmpresaModel(id=str(uuid.uuid4()), nome=nome))
            await session.commit()
            logger.info(f"{len(empresas_iniciais)} empresas criadas")
    
    logger.info("Database initialized successfully!")
    
    yield
    
    # Shutdown
    await engine.dispose()
    logger.info("Database connection closed.")


# Create the main app
app = FastAPI(
    title="Sistema Central de Matrículas - SENAI CIMATEC",
    description="API para gerenciamento de matrículas (PostgreSQL)",
    version="1.2.0",
    lifespan=lifespan
)

# CORS middleware - MUST be added right after app creation
cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins == '*':
    origins = ["*"]
else:
    origins = [origin.strip() for origin in cors_origins.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router
api_router = APIRouter(prefix="/api")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ==================== DEPENDENCY INJECTION ====================

async def get_db_session():
    """Get database session"""
    async with async_session() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
) -> Usuario:
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
        
        usuario_repo = UsuarioRepository(session)
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


def require_permission(permission: str):
    """Dependency factory para verificar permissão"""
    async def check_permission(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_db_session)
    ):
        user = await get_current_user(token, session)
        if not user.tem_permissao(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{permission}' necessária"
            )
        return user, session
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
async def login(request: LoginRequest, session: AsyncSession = Depends(get_db_session)):
    """Realiza login e retorna token JWT"""
    usuario_repo = UsuarioRepository(session)
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
async def register(request: RegisterRequest, session: AsyncSession = Depends(get_db_session)):
    """Registra um novo usuário"""
    usuario_repo = UsuarioRepository(session)
    
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
async def get_me(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna dados do usuário autenticado"""
    usuario = await get_current_user(token, session)
    return UsuarioResponseDTO(**usuario.to_dict())


# ==================== PEDIDOS ROUTES ====================

@api_router.post("/pedidos", response_model=PedidoResponseDTO, tags=["Pedidos"])
async def criar_pedido(
    request: CriarPedidoDTO,
    deps: tuple = Depends(require_permission("pedido:criar"))
):
    """Cria um novo pedido de matrícula"""
    usuario, session = deps
    pedido_repo = PedidoRepository(session)
    auditoria_repo = AuditoriaRepository(session)
    
    criar_pedido_uc = CriarPedidoMatriculaUseCase(pedido_repo, auditoria_repo)
    pedido = await criar_pedido_uc.executar(request, usuario)
    return PedidoResponseDTO(**pedido.to_dict())


@api_router.get("/pedidos", response_model=ListaPedidosResponseDTO, tags=["Pedidos"])
async def listar_pedidos(
    status_filter: Optional[str] = Query(None, alias="status"),
    consultor_id: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Lista pedidos com filtros"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    
    consultar_pedidos_uc = ConsultarPedidosUseCase(pedido_repo)
    
    filtros = FiltrosPedidoDTO(
        status=status_filter,
        consultor_id=consultor_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=pagina,
        por_pagina=por_pagina
    )
    return await consultar_pedidos_uc.listar(filtros, usuario)


@api_router.get("/pedidos/dashboard", tags=["Pedidos"])
async def get_dashboard(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna dados do dashboard"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    
    consultar_pedidos_uc = ConsultarPedidosUseCase(pedido_repo)
    contagem = await consultar_pedidos_uc.contar_por_status(usuario)
    
    # Busca pedidos recentes
    filtros = FiltrosPedidoDTO(pagina=1, por_pagina=5)
    resultado = await consultar_pedidos_uc.listar(filtros, usuario)
    
    return {
        "contagem_status": contagem,
        "pedidos_recentes": [p.model_dump() for p in resultado.pedidos]
    }


@api_router.get("/pedidos/analytics", tags=["Pedidos"])
async def get_analytics(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna dados analíticos avançados para o Dashboard 2.0"""
    from sqlalchemy import select, func, case, text
    from src.infrastructure.persistence.models import PedidoModel, AlunoModel
    
    usuario = await get_current_user(token, session)
    
    # 1. Funil de Matrículas - Contagem por status em ordem do fluxo
    funil_query = select(
        PedidoModel.status,
        func.count(PedidoModel.id).label('total')
    ).group_by(PedidoModel.status)
    
    # Filtrar por consultor se não for admin/assistente
    if usuario.role.value == 'consultor':
        funil_query = funil_query.where(PedidoModel.consultor_id == usuario.id)
    
    funil_result = await session.execute(funil_query)
    funil_data = {row.status: row.total for row in funil_result}
    
    # Ordenar funil na sequência lógica
    funil_ordem = ['pendente', 'em_analise', 'documentacao_pendente', 'aprovado', 'realizado', 'exportado']
    funil = [
        {"status": s, "label": s.replace('_', ' ').title(), "total": funil_data.get(s, 0)}
        for s in funil_ordem
    ]
    
    # 2. Tempo Médio de Matrícula (em dias)
    tempo_query = select(
        func.avg(
            func.julianday(PedidoModel.updated_at) - func.julianday(PedidoModel.created_at)
        ).label('tempo_medio')
    ).where(PedidoModel.status.in_(['realizado', 'exportado']))
    
    if usuario.role.value == 'consultor':
        tempo_query = tempo_query.where(PedidoModel.consultor_id == usuario.id)
    
    tempo_result = await session.execute(tempo_query)
    tempo_medio = tempo_result.scalar() or 0
    
    # 3. Top 5 Empresas
    empresas_query = select(
        PedidoModel.empresa_nome,
        func.count(PedidoModel.id).label('total')
    ).where(
        PedidoModel.empresa_nome.isnot(None)
    ).group_by(PedidoModel.empresa_nome).order_by(
        func.count(PedidoModel.id).desc()
    ).limit(5)
    
    if usuario.role.value == 'consultor':
        empresas_query = empresas_query.where(PedidoModel.consultor_id == usuario.id)
    
    empresas_result = await session.execute(empresas_query)
    top_empresas = [{"nome": row.empresa_nome or "Sem empresa", "total": row.total} for row in empresas_result]
    
    # 4. Top 5 Projetos
    projetos_query = select(
        PedidoModel.projeto_nome,
        func.count(PedidoModel.id).label('total')
    ).where(
        PedidoModel.projeto_nome.isnot(None)
    ).group_by(PedidoModel.projeto_nome).order_by(
        func.count(PedidoModel.id).desc()
    ).limit(5)
    
    if usuario.role.value == 'consultor':
        projetos_query = projetos_query.where(PedidoModel.consultor_id == usuario.id)
    
    projetos_result = await session.execute(projetos_query)
    top_projetos = [{"nome": row.projeto_nome or "Sem projeto", "total": row.total} for row in projetos_result]
    
    # 5. Pedidos Críticos (parados há mais de 48h)
    from datetime import timedelta
    limite_48h = datetime.now(timezone.utc) - timedelta(hours=48)
    
    criticos_query = select(func.count(PedidoModel.id)).where(
        PedidoModel.updated_at < limite_48h,
        PedidoModel.status.in_(['pendente', 'em_analise', 'documentacao_pendente'])
    )
    
    if usuario.role.value == 'consultor':
        criticos_query = criticos_query.where(PedidoModel.consultor_id == usuario.id)
    
    criticos_result = await session.execute(criticos_query)
    pedidos_criticos = criticos_result.scalar() or 0
    
    # 6. Total de Alunos Matriculados
    alunos_query = select(func.count(AlunoModel.id))
    alunos_result = await session.execute(alunos_query)
    total_alunos = alunos_result.scalar() or 0
    
    # 7. Matrículas por Mês (últimos 6 meses)
    from datetime import timedelta
    seis_meses_atras = datetime.now(timezone.utc) - timedelta(days=180)
    
    # Query simplificada para SQLite
    matriculas_mes_query = select(
        func.strftime('%Y-%m', PedidoModel.created_at).label('mes'),
        func.count(PedidoModel.id).label('total')
    ).where(
        PedidoModel.created_at >= seis_meses_atras
    ).group_by(
        func.strftime('%Y-%m', PedidoModel.created_at)
    ).order_by(
        func.strftime('%Y-%m', PedidoModel.created_at)
    )
    
    if usuario.role.value == 'consultor':
        matriculas_mes_query = matriculas_mes_query.where(PedidoModel.consultor_id == usuario.id)
    
    matriculas_mes_result = await session.execute(matriculas_mes_query)
    matriculas_por_mes = [{"mes": row.mes, "total": row.total} for row in matriculas_mes_result]
    
    # 8. Taxa de Conversão (aprovados / total)
    total_query = select(func.count(PedidoModel.id))
    if usuario.role.value == 'consultor':
        total_query = total_query.where(PedidoModel.consultor_id == usuario.id)
    total_result = await session.execute(total_query)
    total_pedidos = total_result.scalar() or 0
    
    aprovados_query = select(func.count(PedidoModel.id)).where(
        PedidoModel.status.in_(['aprovado', 'realizado', 'exportado'])
    )
    if usuario.role.value == 'consultor':
        aprovados_query = aprovados_query.where(PedidoModel.consultor_id == usuario.id)
    aprovados_result = await session.execute(aprovados_query)
    total_aprovados = aprovados_result.scalar() or 0
    
    taxa_conversao = (total_aprovados / total_pedidos * 100) if total_pedidos > 0 else 0
    
    return {
        "funil": funil,
        "tempo_medio_dias": round(tempo_medio, 1),
        "top_empresas": top_empresas,
        "top_projetos": top_projetos,
        "pedidos_criticos": pedidos_criticos,
        "total_alunos": total_alunos,
        "matriculas_por_mes": matriculas_por_mes,
        "taxa_conversao": round(taxa_conversao, 1),
        "total_pedidos": total_pedidos
    }


@api_router.get("/pedidos/{pedido_id}", response_model=PedidoResponseDTO, tags=["Pedidos"])
async def buscar_pedido(
    pedido_id: str,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Busca pedido por ID"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    
    consultar_pedidos_uc = ConsultarPedidosUseCase(pedido_repo)
    return await consultar_pedidos_uc.buscar_por_id(pedido_id, usuario)


@api_router.patch("/pedidos/{pedido_id}/status", response_model=PedidoResponseDTO, tags=["Pedidos"])
async def atualizar_status(
    pedido_id: str,
    request: AtualizarStatusDTO,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Atualiza status do pedido"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    auditoria_repo = AuditoriaRepository(session)
    
    atualizar_status_uc = AtualizarStatusPedidoUseCase(pedido_repo, auditoria_repo)
    pedido = await atualizar_status_uc.executar(pedido_id, request, usuario)
    return PedidoResponseDTO(**pedido.to_dict())


@api_router.get("/pedidos/exportar/totvs", tags=["Pedidos"])
async def exportar_totvs(
    formato: str = Query(default="xlsx", pattern="^(xlsx|csv)$"),
    deps: tuple = Depends(require_permission("pedido:exportar"))
):
    """Exporta pedidos realizados para formato TOTVS"""
    usuario, session = deps
    pedido_repo = PedidoRepository(session)
    auditoria_repo = AuditoriaRepository(session)
    
    gerar_exportacao_uc = GerarExportacaoTOTVSUseCase(pedido_repo, auditoria_repo)
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
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Lista todos os usuários"""
    usuario, session = deps
    usuario_repo = UsuarioRepository(session)
    
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
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Busca usuário por ID"""
    current_user, session = deps
    usuario_repo = UsuarioRepository(session)
    
    usuario = await usuario_repo.buscar_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UsuarioResponseDTO(**usuario.to_dict())


@api_router.patch("/usuarios/{usuario_id}", response_model=UsuarioResponseDTO, tags=["Usuarios"])
async def atualizar_usuario(
    usuario_id: str,
    request: AtualizarUsuarioDTO,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Atualiza dados do usuário"""
    current_user, session = deps
    usuario_repo = UsuarioRepository(session)
    
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
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Deleta um usuário"""
    current_user, session = deps
    
    if usuario_id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível deletar o próprio usuário")
    
    usuario_repo = UsuarioRepository(session)
    sucesso = await usuario_repo.deletar(usuario_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {"message": "Usuário deletado com sucesso"}


# ==================== CRUD CURSOS ====================

class CursoRequest(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200)
    descricao: Optional[str] = None

class CursoResponse(BaseModel):
    id: str
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

@api_router.get("/cursos", tags=["Cursos"])
async def listar_cursos(
    ativo: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Lista todos os cursos"""
    from sqlalchemy import select
    query = select(CursoModel)
    if ativo is not None:
        query = query.where(CursoModel.ativo == ativo)
    query = query.order_by(CursoModel.nome)
    result = await session.execute(query)
    cursos = result.scalars().all()
    return [{"id": c.id, "nome": c.nome, "descricao": c.descricao, "ativo": c.ativo} for c in cursos]

@api_router.post("/cursos", response_model=CursoResponse, status_code=201, tags=["Cursos"])
async def criar_curso(
    request: CursoRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Cria um novo curso (Admin)"""
    usuario, session = deps
    from sqlalchemy import select
    
    # Verifica duplicidade
    result = await session.execute(select(CursoModel).where(CursoModel.nome == request.nome))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Curso já existe")
    
    curso = CursoModel(
        id=str(uuid.uuid4()),
        nome=request.nome,
        descricao=request.descricao
    )
    session.add(curso)
    await session.commit()
    return {"id": curso.id, "nome": curso.nome, "descricao": curso.descricao, "ativo": curso.ativo}

@api_router.put("/cursos/{curso_id}", response_model=CursoResponse, tags=["Cursos"])
async def atualizar_curso(
    curso_id: str,
    request: CursoRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Atualiza um curso (Admin)"""
    usuario, session = deps
    from sqlalchemy import select
    
    result = await session.execute(select(CursoModel).where(CursoModel.id == curso_id))
    curso = result.scalar_one_or_none()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    curso.nome = request.nome
    curso.descricao = request.descricao
    curso.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"id": curso.id, "nome": curso.nome, "descricao": curso.descricao, "ativo": curso.ativo}

@api_router.delete("/cursos/{curso_id}", tags=["Cursos"])
async def deletar_curso(
    curso_id: str,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Desativa um curso (Admin)"""
    usuario, session = deps
    from sqlalchemy import select
    
    result = await session.execute(select(CursoModel).where(CursoModel.id == curso_id))
    curso = result.scalar_one_or_none()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    curso.ativo = False
    curso.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"message": "Curso desativado com sucesso"}


# ==================== CRUD PROJETOS ====================

class ProjetoRequest(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200)
    descricao: Optional[str] = None

class ProjetoResponse(BaseModel):
    id: str
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

@api_router.get("/projetos", tags=["Projetos"])
async def listar_projetos(
    ativo: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Lista todos os projetos"""
    from sqlalchemy import select
    query = select(ProjetoModel)
    if ativo is not None:
        query = query.where(ProjetoModel.ativo == ativo)
    query = query.order_by(ProjetoModel.nome)
    result = await session.execute(query)
    projetos = result.scalars().all()
    return [{"id": p.id, "nome": p.nome, "descricao": p.descricao, "ativo": p.ativo} for p in projetos]

@api_router.post("/projetos", response_model=ProjetoResponse, status_code=201, tags=["Projetos"])
async def criar_projeto(
    request: ProjetoRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Cria um novo projeto (Admin)"""
    usuario, session = deps
    from sqlalchemy import select
    
    result = await session.execute(select(ProjetoModel).where(ProjetoModel.nome == request.nome))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Projeto já existe")
    
    projeto = ProjetoModel(
        id=str(uuid.uuid4()),
        nome=request.nome,
        descricao=request.descricao
    )
    session.add(projeto)
    await session.commit()
    return {"id": projeto.id, "nome": projeto.nome, "descricao": projeto.descricao, "ativo": projeto.ativo}

@api_router.put("/projetos/{projeto_id}", response_model=ProjetoResponse, tags=["Projetos"])
async def atualizar_projeto(
    projeto_id: str,
    request: ProjetoRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Atualiza um projeto (Admin)"""
    usuario, session = deps
    from sqlalchemy import select
    
    result = await session.execute(select(ProjetoModel).where(ProjetoModel.id == projeto_id))
    projeto = result.scalar_one_or_none()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    projeto.nome = request.nome
    projeto.descricao = request.descricao
    projeto.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"id": projeto.id, "nome": projeto.nome, "descricao": projeto.descricao, "ativo": projeto.ativo}

@api_router.delete("/projetos/{projeto_id}", tags=["Projetos"])
async def deletar_projeto(
    projeto_id: str,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Desativa um projeto (Admin)"""
    usuario, session = deps
    from sqlalchemy import select
    
    result = await session.execute(select(ProjetoModel).where(ProjetoModel.id == projeto_id))
    projeto = result.scalar_one_or_none()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    projeto.ativo = False
    projeto.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"message": "Projeto desativado com sucesso"}


# ==================== CRUD EMPRESAS ====================

class EmpresaRequest(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200)
    cnpj: Optional[str] = None

class EmpresaResponse(BaseModel):
    id: str
    nome: str
    cnpj: Optional[str] = None
    ativo: bool = True

@api_router.get("/empresas", tags=["Empresas"])
async def listar_empresas(
    ativo: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Lista todas as empresas"""
    from sqlalchemy import select
    query = select(EmpresaModel)
    if ativo is not None:
        query = query.where(EmpresaModel.ativo == ativo)
    query = query.order_by(EmpresaModel.nome)
    result = await session.execute(query)
    empresas = result.scalars().all()
    return [{"id": e.id, "nome": e.nome, "cnpj": e.cnpj, "ativo": e.ativo} for e in empresas]

@api_router.post("/empresas", response_model=EmpresaResponse, status_code=201, tags=["Empresas"])
async def criar_empresa(
    request: EmpresaRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Cria uma nova empresa (Admin)"""
    usuario, session = deps
    from sqlalchemy import select
    
    result = await session.execute(select(EmpresaModel).where(EmpresaModel.nome == request.nome))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Empresa já existe")
    
    empresa = EmpresaModel(
        id=str(uuid.uuid4()),
        nome=request.nome,
        cnpj=request.cnpj
    )
    session.add(empresa)
    await session.commit()
    return {"id": empresa.id, "nome": empresa.nome, "cnpj": empresa.cnpj, "ativo": empresa.ativo}

@api_router.put("/empresas/{empresa_id}", response_model=EmpresaResponse, tags=["Empresas"])
async def atualizar_empresa(
    empresa_id: str,
    request: EmpresaRequest,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Atualiza uma empresa (Admin)"""
    usuario, session = deps
    from sqlalchemy import select
    
    result = await session.execute(select(EmpresaModel).where(EmpresaModel.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    empresa.nome = request.nome
    empresa.cnpj = request.cnpj
    empresa.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"id": empresa.id, "nome": empresa.nome, "cnpj": empresa.cnpj, "ativo": empresa.ativo}

@api_router.delete("/empresas/{empresa_id}", tags=["Empresas"])
async def deletar_empresa(
    empresa_id: str,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Desativa uma empresa (Admin)"""
    usuario, session = deps
    from sqlalchemy import select
    
    result = await session.execute(select(EmpresaModel).where(EmpresaModel.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    empresa.ativo = False
    empresa.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {"message": "Empresa desativada com sucesso"}


# ==================== DADOS AUXILIARES ====================

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
    return {"message": "Sistema Central de Matrículas - SENAI CIMATEC", "version": "1.2.0", "database": "PostgreSQL"}


@api_router.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "database": "PostgreSQL", "timestamp": datetime.now(timezone.utc).isoformat()}


# Include router
app.include_router(api_router)
