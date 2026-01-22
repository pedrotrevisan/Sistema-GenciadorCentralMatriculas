"""FastAPI Backend - Sistema Central de Matrículas SENAI CIMATEC (PostgreSQL)"""
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query, Response, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List
from contextlib import asynccontextmanager
import os
import logging
import uuid
from datetime import datetime, timezone
import io
import re

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
from src.infrastructure.persistence.models import CursoModel, ProjetoModel, EmpresaModel, AlunoModel, TipoDocumentoModel, PendenciaModel, HistoricoContatoModel, ReembolsoModel
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
        
        # Seed Tipos de Documento para Pendências
        from src.infrastructure.persistence.models import TipoDocumentoModel
        tipos_doc_count = await session.execute(select(func.count(TipoDocumentoModel.id)))
        if tipos_doc_count.scalar() == 0:
            tipos_documentos = [
                {"codigo": "94", "nome": "Comprovante de Residência", "obrigatorio": True, "observacoes": "PDF ou JPG – Máx. 10MB"},
                {"codigo": "96", "nome": "Solicitação Desconto (Sindicato/CIEB/Ex-Aluno/Col. Sistema FIEB)", "obrigatorio": False, "observacoes": "Se aplicável"},
                {"codigo": "97", "nome": "CPF/RG Responsável Legal (menor de 18 anos)", "obrigatorio": False, "observacoes": "Se aplicável"},
                {"codigo": "131", "nome": "RG – Frente", "obrigatorio": True, "observacoes": "PDF ou JPG – Máx. 10MB"},
                {"codigo": "132", "nome": "RG – Verso", "obrigatorio": True, "observacoes": "PDF ou JPG – Máx. 10MB"},
                {"codigo": "136", "nome": "Comprovante de Escolaridade – Frente", "obrigatorio": True, "observacoes": "Histórico ou Atestado - PDF ou JPG – Máx. 10MB"},
                {"codigo": "137", "nome": "Comprovante de Escolaridade – Verso", "obrigatorio": True, "observacoes": "Histórico ou Atestado - PDF ou JPG – Máx. 10MB"},
                {"codigo": "205", "nome": "CPF", "obrigatorio": False, "observacoes": "PDF ou JPG – Máx. 10MB"},
            ]
            for tipo in tipos_documentos:
                session.add(TipoDocumentoModel(
                    id=str(uuid.uuid4()),
                    codigo=tipo["codigo"],
                    nome=tipo["nome"],
                    obrigatorio=tipo["obrigatorio"],
                    observacoes=tipo.get("observacoes")
                ))
            await session.commit()
            logger.info(f"{len(tipos_documentos)} tipos de documento criados")
    
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


@api_router.get("/pedidos/buscar/protocolo/{numero_protocolo}", response_model=PedidoResponseDTO, tags=["Pedidos"])
async def buscar_por_protocolo(
    numero_protocolo: str,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Busca pedido por número de protocolo (ex: CM-2026-0001)"""
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    
    pedido = await pedido_repo.buscar_por_protocolo(numero_protocolo)
    if not pedido:
        raise HTTPException(404, f"Pedido com protocolo {numero_protocolo} não encontrado")
    
    # Verificar permissão (consultor só vê os próprios)
    if usuario.role == "consultor" and pedido.consultor_id != usuario.id:
        raise HTTPException(403, "Sem permissão para visualizar este pedido")
    
    return PedidoResponseDTO(**pedido.to_dict())


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


# ==================== IMPORTAÇÃO EM LOTE ====================

from src.domain.value_objects import CPF, Telefone
from src.utils.text_formatters import formatar_nome_proprio, formatar_texto_titulo

class ImportacaoResultado(BaseModel):
    sucesso: bool
    total_linhas: int
    linhas_validas: int
    linhas_com_erro: int
    pedidos_criados: int = 0
    erros: List[dict] = []
    preview: List[dict] = []


def validar_cpf(cpf: str) -> tuple[bool, str]:
    """Valida formato do CPF"""
    if not cpf:
        return False, "CPF é obrigatório"
    cpf_limpo = re.sub(r'\D', '', str(cpf))
    if len(cpf_limpo) != 11:
        return False, f"CPF deve ter 11 dígitos (encontrado: {len(cpf_limpo)})"
    return True, cpf_limpo


def validar_email(email: str) -> tuple[bool, str]:
    """Valida formato do email"""
    if not email:
        return False, "Email é obrigatório"
    if '@' not in str(email) or '.' not in str(email):
        return False, "Email inválido"
    return True, str(email).strip().lower()


def validar_telefone(telefone: str) -> tuple[bool, str]:
    """Valida formato do telefone"""
    if not telefone:
        return False, "Telefone é obrigatório"
    tel_limpo = re.sub(r'\D', '', str(telefone))
    if len(tel_limpo) < 10 or len(tel_limpo) > 11:
        return False, f"Telefone deve ter 10 ou 11 dígitos"
    return True, tel_limpo


@api_router.post("/importacao/validar", response_model=ImportacaoResultado, tags=["Importação"])
async def validar_importacao(
    file: UploadFile = File(...),
    curso_id: str = Query(...),
    projeto_id: Optional[str] = Query(None),
    empresa_id: Optional[str] = Query(None),
    deps: tuple = Depends(require_permission("pedido:criar"))
):
    """Valida arquivo de importação e retorna preview com erros"""
    import pandas as pd
    
    usuario, session = deps
    
    # Validar extensão
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(400, "Formato inválido. Use .xlsx, .xls ou .csv")
    
    # Ler arquivo
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(contents), dtype=str)
    except Exception as e:
        raise HTTPException(400, f"Erro ao ler arquivo: {str(e)}")
    
    # Normalizar nomes das colunas
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Colunas obrigatórias
    colunas_obrigatorias = ['nome', 'cpf', 'email', 'telefone', 'data_nascimento', 'rg', 'cep', 'logradouro', 'numero', 'bairro', 'cidade', 'uf']
    colunas_faltantes = [c for c in colunas_obrigatorias if c not in df.columns]
    
    if colunas_faltantes:
        raise HTTPException(400, f"Colunas obrigatórias faltantes: {', '.join(colunas_faltantes)}")
    
    # Buscar dados auxiliares
    from sqlalchemy import select
    curso_result = await session.execute(select(CursoModel).where(CursoModel.id == curso_id))
    curso = curso_result.scalar_one_or_none()
    if not curso:
        raise HTTPException(404, "Curso não encontrado")
    
    # Buscar CPFs já cadastrados
    pedido_repo = PedidoRepository(session)
    
    # Validar cada linha
    erros = []
    preview = []
    linhas_validas = 0
    
    for idx, row in df.iterrows():
        linha_num = idx + 2  # +2 porque Excel começa em 1 e tem header
        linha_erros = []
        
        # Validar nome
        nome = str(row.get('nome', '')).strip()
        if not nome or len(nome) < 3:
            linha_erros.append("Nome deve ter pelo menos 3 caracteres")
        
        # Validar CPF
        cpf_valido, cpf_result = validar_cpf(row.get('cpf', ''))
        if not cpf_valido:
            linha_erros.append(cpf_result)
        else:
            # Verificar duplicidade no sistema
            aluno_existente = await pedido_repo.buscar_aluno_por_cpf(cpf_result)
            if aluno_existente:
                linha_erros.append(f"CPF já cadastrado ({aluno_existente['nome']})")
        
        # Validar email
        email_valido, email_result = validar_email(row.get('email', ''))
        if not email_valido:
            linha_erros.append(email_result)
        
        # Validar telefone
        tel_valido, tel_result = validar_telefone(row.get('telefone', ''))
        if not tel_valido:
            linha_erros.append(tel_result)
        
        # Validar data de nascimento
        data_nasc = str(row.get('data_nascimento', '')).strip()
        if not data_nasc:
            linha_erros.append("Data de nascimento é obrigatória")
        
        # Validar RG
        rg = str(row.get('rg', '')).strip()
        if not rg:
            linha_erros.append("RG é obrigatório")
        
        # Validar endereço
        if not str(row.get('cep', '')).strip():
            linha_erros.append("CEP é obrigatório")
        if not str(row.get('logradouro', '')).strip():
            linha_erros.append("Logradouro é obrigatório")
        if not str(row.get('numero', '')).strip():
            linha_erros.append("Número é obrigatório")
        if not str(row.get('bairro', '')).strip():
            linha_erros.append("Bairro é obrigatório")
        if not str(row.get('cidade', '')).strip():
            linha_erros.append("Cidade é obrigatória")
        
        uf = str(row.get('uf', '')).strip().upper()
        if not uf or len(uf) != 2:
            linha_erros.append("UF inválida (deve ter 2 caracteres)")
        
        # Montar preview
        preview_item = {
            "linha": linha_num,
            "nome": formatar_nome_proprio(nome) if nome else "",
            "cpf": cpf_result if cpf_valido else str(row.get('cpf', '')),
            "email": email_result if email_valido else str(row.get('email', '')),
            "telefone": tel_result if tel_valido else str(row.get('telefone', '')),
            "valido": len(linha_erros) == 0,
            "erros": linha_erros
        }
        preview.append(preview_item)
        
        if linha_erros:
            erros.append({
                "linha": linha_num,
                "erros": linha_erros
            })
        else:
            linhas_validas += 1
    
    return ImportacaoResultado(
        sucesso=len(erros) == 0,
        total_linhas=len(df),
        linhas_validas=linhas_validas,
        linhas_com_erro=len(erros),
        erros=erros,
        preview=preview[:50]  # Limitar preview a 50 linhas
    )


@api_router.post("/importacao/executar", tags=["Importação"])
async def executar_importacao(
    file: UploadFile = File(...),
    curso_id: str = Query(...),
    curso_nome: str = Query(...),
    projeto_id: Optional[str] = Query(None),
    projeto_nome: Optional[str] = Query(None),
    empresa_id: Optional[str] = Query(None),
    empresa_nome: Optional[str] = Query(None),
    deps: tuple = Depends(require_permission("pedido:criar"))
):
    """Executa a importação em lote criando os pedidos"""
    import pandas as pd
    
    usuario, session = deps
    
    # Validar extensão
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(400, "Formato inválido. Use .xlsx, .xls ou .csv")
    
    # Ler arquivo
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(contents), dtype=str)
    except Exception as e:
        raise HTTPException(400, f"Erro ao ler arquivo: {str(e)}")
    
    # Normalizar nomes das colunas
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    pedido_repo = PedidoRepository(session)
    auditoria_repo = AuditoriaRepository(session)
    
    pedidos_criados = 0
    erros = []
    
    for idx, row in df.iterrows():
        linha_num = idx + 2
        
        try:
            # Validar CPF
            cpf_valido, cpf_result = validar_cpf(row.get('cpf', ''))
            if not cpf_valido:
                erros.append({"linha": linha_num, "erro": cpf_result})
                continue
            
            # Verificar duplicidade
            aluno_existente = await pedido_repo.buscar_aluno_por_cpf(cpf_result)
            if aluno_existente:
                erros.append({"linha": linha_num, "erro": f"CPF já cadastrado"})
                continue
            
            # Preparar dados do aluno
            from src.application.dtos.request import CriarPedidoDTO, AlunoCreateDTO
            
            # Formatar data de nascimento
            data_nasc_str = str(row.get('data_nascimento', '')).strip()
            try:
                # Tentar diferentes formatos
                if '/' in data_nasc_str:
                    parts = data_nasc_str.split('/')
                    if len(parts[2]) == 2:
                        data_nasc_str = f"20{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                    else:
                        data_nasc_str = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                elif '-' in data_nasc_str and len(data_nasc_str) == 10:
                    pass  # Já está no formato correto
            except:
                erros.append({"linha": linha_num, "erro": "Data de nascimento inválida"})
                continue
            
            aluno_dto = AlunoCreateDTO(
                nome=formatar_nome_proprio(str(row.get('nome', '')).strip()),
                cpf=cpf_result,
                email=str(row.get('email', '')).strip().lower(),
                telefone=re.sub(r'\D', '', str(row.get('telefone', ''))),
                data_nascimento=data_nasc_str,
                rg=str(row.get('rg', '')).strip(),
                rg_orgao_emissor=str(row.get('orgao_emissor', 'SSP')).strip().upper(),
                rg_uf=str(row.get('rg_uf', row.get('uf', ''))).strip().upper(),
                rg_data_emissao=str(row.get('rg_data_emissao', '')).strip() if row.get('rg_data_emissao') else None,
                naturalidade=formatar_texto_titulo(str(row.get('naturalidade', '')).strip()) if row.get('naturalidade') else None,
                naturalidade_uf=str(row.get('naturalidade_uf', '')).strip().upper() if row.get('naturalidade_uf') else None,
                sexo=str(row.get('sexo', '')).strip().upper()[:1] if row.get('sexo') else None,
                cor_raca=str(row.get('cor_raca', '')).strip() if row.get('cor_raca') else None,
                grau_instrucao=str(row.get('grau_instrucao', '')).strip() if row.get('grau_instrucao') else None,
                nome_pai=formatar_nome_proprio(str(row.get('nome_pai', '')).strip()) if row.get('nome_pai') else None,
                nome_mae=formatar_nome_proprio(str(row.get('nome_mae', '')).strip()) if row.get('nome_mae') else None,
                endereco_cep=re.sub(r'\D', '', str(row.get('cep', ''))),
                endereco_logradouro=formatar_texto_titulo(str(row.get('logradouro', '')).strip()),
                endereco_numero=str(row.get('numero', '')).strip(),
                endereco_complemento=str(row.get('complemento', '')).strip() if row.get('complemento') else None,
                endereco_bairro=formatar_texto_titulo(str(row.get('bairro', '')).strip()),
                endereco_cidade=formatar_texto_titulo(str(row.get('cidade', '')).strip()),
                endereco_uf=str(row.get('uf', '')).strip().upper()
            )
            
            pedido_dto = CriarPedidoDTO(
                curso_id=curso_id,
                curso_nome=curso_nome,
                projeto_id=projeto_id,
                projeto_nome=projeto_nome,
                empresa_id=empresa_id,
                empresa_nome=empresa_nome,
                observacoes=f"Importado em lote - Linha {linha_num}",
                alunos=[aluno_dto]
            )
            
            # Criar pedido usando use case
            criar_pedido_uc = CriarPedidoMatriculaUseCase(pedido_repo, auditoria_repo)
            await criar_pedido_uc.executar(pedido_dto, usuario)
            pedidos_criados += 1
            
        except DuplicidadeException as e:
            erros.append({"linha": linha_num, "erro": str(e.message)})
        except ValidationException as e:
            erros.append({"linha": linha_num, "erro": str(e.message)})
        except Exception as e:
            erros.append({"linha": linha_num, "erro": str(e)})
    
    return {
        "sucesso": pedidos_criados > 0,
        "pedidos_criados": pedidos_criados,
        "total_linhas": len(df),
        "erros": erros
    }


@api_router.get("/importacao/template", tags=["Importação"])
async def download_template():
    """Gera template Excel para importação - Formato compatível com TOTVS"""
    import pandas as pd
    
    # Criar DataFrame com exemplo - NA ORDEM DO TOTVS
    data = {
        'cpf': ['123.456.789-00', '987.654.321-00'],
        'rg': ['12345678', '87654321'],
        'rg_data_emissao': ['10/05/2015', '15/08/2018'],
        'orgao_emissor': ['SSP', 'SSP'],
        'nome': ['JOÃO CARLOS DA SILVA', 'MARIA EDUARDA DOS SANTOS'],
        'naturalidade_uf': ['BA', 'BA'],
        'naturalidade': ['Salvador', 'Feira de Santana'],
        'data_nascimento': ['15/03/1995', '22/07/1998'],
        'sexo': ['M', 'F'],
        'cor_raca': ['Branca', 'Parda'],
        'grau_instrucao': ['Ensino Médio Completo', 'Ensino Superior Incompleto'],
        'logradouro': ['Rua das Flores', 'Avenida Sete de Setembro'],
        'numero': ['123', '456'],
        'complemento': ['Apto 101', ''],
        'bairro': ['Pituba', 'Centro'],
        'cidade': ['Salvador', 'Salvador'],
        'cep': ['41820-000', '40000-000'],
        'uf': ['BA', 'BA'],
        'telefone': ['(71) 99999-8888', '(71) 98888-7777'],
        'email': ['joao.silva@email.com', 'maria.santos@email.com'],
        'nome_pai': ['José Carlos da Silva', 'Pedro Santos'],
        'nome_mae': ['Maria Aparecida da Silva', 'Ana Paula dos Santos']
    }
    
    df = pd.DataFrame(data)
    
    # Criar arquivo Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Alunos')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=template_importacao_alunos.xlsx"
        }
    )


# ==================== CENTRAL DE PENDÊNCIAS ====================

# DTOs para Pendências
class CriarPendenciaDTO(BaseModel):
    aluno_id: str
    pedido_id: str
    documento_codigo: str
    observacoes: Optional[str] = None

class AtualizarPendenciaDTO(BaseModel):
    status: str  # pendente, aguardando_aluno, em_analise, aprovado, rejeitado, reenvio_necessario
    observacoes: Optional[str] = None
    motivo_rejeicao: Optional[str] = None

class RegistrarContatoDTO(BaseModel):
    tipo_contato: str  # telefone, whatsapp, email, presencial
    descricao: str
    resultado: Optional[str] = None  # atendeu, nao_atendeu, retornou, sem_resposta


@api_router.get("/pendencias/tipos-documento", tags=["Pendências"])
async def listar_tipos_documento(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todos os tipos de documento disponíveis"""
    from sqlalchemy import select
    
    result = await session.execute(
        select(TipoDocumentoModel).where(TipoDocumentoModel.ativo == True).order_by(TipoDocumentoModel.codigo)
    )
    tipos = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "codigo": t.codigo,
            "nome": t.nome,
            "obrigatorio": t.obrigatorio,
            "observacoes": t.observacoes
        }
        for t in tipos
    ]


@api_router.get("/pendencias/dashboard", tags=["Pendências"])
async def dashboard_pendencias(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Dashboard da Central de Pendências"""
    from sqlalchemy import select, func
    
    # Contagem por status
    status_query = await session.execute(
        select(PendenciaModel.status, func.count(PendenciaModel.id))
        .group_by(PendenciaModel.status)
    )
    contagem_status = {row[0]: row[1] for row in status_query.fetchall()}
    
    # Contagem por tipo de documento
    doc_query = await session.execute(
        select(PendenciaModel.documento_nome, func.count(PendenciaModel.id))
        .where(PendenciaModel.status.in_(['pendente', 'aguardando_aluno', 'reenvio_necessario']))
        .group_by(PendenciaModel.documento_nome)
    )
    por_documento = [{"documento": row[0], "total": row[1]} for row in doc_query.fetchall()]
    
    # Total de pendências abertas (não resolvidas)
    abertas_query = await session.execute(
        select(func.count(PendenciaModel.id))
        .where(PendenciaModel.status.in_(['pendente', 'aguardando_aluno', 'em_analise', 'reenvio_necessario']))
    )
    total_abertas = abertas_query.scalar() or 0
    
    # Pendências críticas (mais de 7 dias sem resolução)
    from datetime import timedelta
    data_limite = datetime.now(timezone.utc) - timedelta(days=7)
    criticas_query = await session.execute(
        select(func.count(PendenciaModel.id))
        .where(
            PendenciaModel.status.in_(['pendente', 'aguardando_aluno', 'reenvio_necessario']),
            PendenciaModel.created_at < data_limite
        )
    )
    total_criticas = criticas_query.scalar() or 0
    
    return {
        "contagem_status": contagem_status,
        "por_documento": por_documento,
        "total_abertas": total_abertas,
        "total_criticas": total_criticas,
        "total_pendente": contagem_status.get('pendente', 0),
        "total_aguardando": contagem_status.get('aguardando_aluno', 0),
        "total_em_analise": contagem_status.get('em_analise', 0),
        "total_aprovado": contagem_status.get('aprovado', 0),
        "total_rejeitado": contagem_status.get('rejeitado', 0),
        "total_reenvio": contagem_status.get('reenvio_necessario', 0)
    }


@api_router.get("/pendencias", tags=["Pendências"])
async def listar_pendencias(
    status: Optional[str] = None,
    documento_codigo: Optional[str] = None,
    aluno_nome: Optional[str] = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todas as pendências com filtros"""
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload
    
    query = select(PendenciaModel).options(
        selectinload(PendenciaModel.aluno),
        selectinload(PendenciaModel.pedido),
        selectinload(PendenciaModel.historico_contatos)
    )
    
    # Filtros
    if status:
        query = query.where(PendenciaModel.status == status)
    if documento_codigo:
        query = query.where(PendenciaModel.documento_codigo == documento_codigo)
    
    # Ordenação: pendentes primeiro, depois por data
    query = query.order_by(
        PendenciaModel.status.desc(),
        PendenciaModel.created_at.desc()
    )
    
    # Contagem total
    count_query = select(func.count(PendenciaModel.id))
    if status:
        count_query = count_query.where(PendenciaModel.status == status)
    if documento_codigo:
        count_query = count_query.where(PendenciaModel.documento_codigo == documento_codigo)
    
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginação
    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)
    
    result = await session.execute(query)
    pendencias = result.scalars().all()
    
    # Filtro por nome do aluno (em memória por simplicidade)
    pendencias_list = []
    for p in pendencias:
        if aluno_nome and aluno_nome.lower() not in p.aluno.nome.lower():
            continue
        
        pendencias_list.append({
            "id": p.id,
            "aluno_id": p.aluno_id,
            "aluno_nome": p.aluno.nome,
            "aluno_cpf": p.aluno.cpf,
            "aluno_email": p.aluno.email,
            "aluno_telefone": p.aluno.telefone,
            "pedido_id": p.pedido_id,
            "pedido_protocolo": p.pedido.numero_protocolo,
            "curso_nome": p.pedido.curso_nome,
            "documento_codigo": p.documento_codigo,
            "documento_nome": p.documento_nome,
            "status": p.status,
            "observacoes": p.observacoes,
            "motivo_rejeicao": p.motivo_rejeicao,
            "total_contatos": len(p.historico_contatos),
            "ultimo_contato": max([c.data_contato for c in p.historico_contatos], default=None),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "resolved_at": p.resolved_at.isoformat() if p.resolved_at else None
        })
    
    return {
        "pendencias": pendencias_list,
        "paginacao": {
            "pagina_atual": pagina,
            "por_pagina": por_pagina,
            "total_itens": total,
            "total_paginas": (total + por_pagina - 1) // por_pagina
        }
    }


@api_router.post("/pendencias", tags=["Pendências"])
async def criar_pendencia(
    dto: CriarPendenciaDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Cria uma nova pendência documental para um aluno"""
    from sqlalchemy import select
    
    # Verificar se o aluno existe
    aluno_result = await session.execute(
        select(AlunoModel).where(AlunoModel.id == dto.aluno_id)
    )
    aluno = aluno_result.scalar_one_or_none()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    # Buscar tipo de documento
    tipo_doc_result = await session.execute(
        select(TipoDocumentoModel).where(TipoDocumentoModel.codigo == dto.documento_codigo)
    )
    tipo_doc = tipo_doc_result.scalar_one_or_none()
    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo de documento não encontrado")
    
    # Verificar se já existe pendência para este aluno/documento
    existing = await session.execute(
        select(PendenciaModel).where(
            PendenciaModel.aluno_id == dto.aluno_id,
            PendenciaModel.documento_codigo == dto.documento_codigo,
            PendenciaModel.status.in_(['pendente', 'aguardando_aluno', 'em_analise', 'reenvio_necessario'])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Já existe uma pendência ativa para este documento")
    
    # Criar pendência
    pendencia = PendenciaModel(
        id=str(uuid.uuid4()),
        aluno_id=dto.aluno_id,
        pedido_id=dto.pedido_id,
        tipo_documento_id=tipo_doc.id,
        documento_codigo=dto.documento_codigo,
        documento_nome=tipo_doc.nome,
        status="pendente",
        observacoes=dto.observacoes
    )
    
    session.add(pendencia)
    await session.commit()
    
    return {
        "id": pendencia.id,
        "mensagem": "Pendência criada com sucesso",
        "documento": tipo_doc.nome
    }


@api_router.post("/pendencias/lote", tags=["Pendências"])
async def criar_pendencias_lote(
    aluno_id: str,
    pedido_id: str,
    documentos_codigos: List[str],
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Cria múltiplas pendências de uma vez para um aluno"""
    from sqlalchemy import select
    
    # Verificar se o aluno existe
    aluno_result = await session.execute(
        select(AlunoModel).where(AlunoModel.id == aluno_id)
    )
    aluno = aluno_result.scalar_one_or_none()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    criadas = []
    erros = []
    
    for codigo in documentos_codigos:
        # Buscar tipo de documento
        tipo_doc_result = await session.execute(
            select(TipoDocumentoModel).where(TipoDocumentoModel.codigo == codigo)
        )
        tipo_doc = tipo_doc_result.scalar_one_or_none()
        if not tipo_doc:
            erros.append({"codigo": codigo, "erro": "Documento não encontrado"})
            continue
        
        # Verificar se já existe
        existing = await session.execute(
            select(PendenciaModel).where(
                PendenciaModel.aluno_id == aluno_id,
                PendenciaModel.documento_codigo == codigo,
                PendenciaModel.status.in_(['pendente', 'aguardando_aluno', 'em_analise', 'reenvio_necessario'])
            )
        )
        if existing.scalar_one_or_none():
            erros.append({"codigo": codigo, "erro": "Pendência já existe"})
            continue
        
        pendencia = PendenciaModel(
            id=str(uuid.uuid4()),
            aluno_id=aluno_id,
            pedido_id=pedido_id,
            tipo_documento_id=tipo_doc.id,
            documento_codigo=codigo,
            documento_nome=tipo_doc.nome,
            status="pendente"
        )
        session.add(pendencia)
        criadas.append({"codigo": codigo, "nome": tipo_doc.nome})
    
    await session.commit()
    
    return {
        "criadas": criadas,
        "erros": erros,
        "total_criadas": len(criadas)
    }


@api_router.get("/pendencias/{pendencia_id}", tags=["Pendências"])
async def buscar_pendencia(
    pendencia_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Busca detalhes de uma pendência específica"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await session.execute(
        select(PendenciaModel)
        .options(
            selectinload(PendenciaModel.aluno),
            selectinload(PendenciaModel.pedido),
            selectinload(PendenciaModel.historico_contatos)
        )
        .where(PendenciaModel.id == pendencia_id)
    )
    pendencia = result.scalar_one_or_none()
    
    if not pendencia:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    
    return {
        "id": pendencia.id,
        "aluno": {
            "id": pendencia.aluno.id,
            "nome": pendencia.aluno.nome,
            "cpf": pendencia.aluno.cpf,
            "email": pendencia.aluno.email,
            "telefone": pendencia.aluno.telefone
        },
        "pedido": {
            "id": pendencia.pedido.id,
            "protocolo": pendencia.pedido.numero_protocolo,
            "curso": pendencia.pedido.curso_nome,
            "projeto": pendencia.pedido.projeto_nome,
            "empresa": pendencia.pedido.empresa_nome
        },
        "documento_codigo": pendencia.documento_codigo,
        "documento_nome": pendencia.documento_nome,
        "status": pendencia.status,
        "observacoes": pendencia.observacoes,
        "motivo_rejeicao": pendencia.motivo_rejeicao,
        "created_at": pendencia.created_at.isoformat() if pendencia.created_at else None,
        "updated_at": pendencia.updated_at.isoformat() if pendencia.updated_at else None,
        "resolved_at": pendencia.resolved_at.isoformat() if pendencia.resolved_at else None,
        "historico_contatos": [
            {
                "id": c.id,
                "usuario_nome": c.usuario_nome,
                "tipo_contato": c.tipo_contato,
                "descricao": c.descricao,
                "resultado": c.resultado,
                "data_contato": c.data_contato.isoformat() if c.data_contato else None
            }
            for c in sorted(pendencia.historico_contatos, key=lambda x: x.data_contato, reverse=True)
        ]
    }


@api_router.put("/pendencias/{pendencia_id}", tags=["Pendências"])
async def atualizar_pendencia(
    pendencia_id: str,
    dto: AtualizarPendenciaDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Atualiza status de uma pendência"""
    from sqlalchemy import select
    
    result = await session.execute(
        select(PendenciaModel).where(PendenciaModel.id == pendencia_id)
    )
    pendencia = result.scalar_one_or_none()
    
    if not pendencia:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    
    status_validos = ['pendente', 'aguardando_aluno', 'em_analise', 'aprovado', 'rejeitado', 'reenvio_necessario']
    if dto.status not in status_validos:
        raise HTTPException(status_code=400, detail=f"Status inválido. Válidos: {status_validos}")
    
    pendencia.status = dto.status
    if dto.observacoes is not None:
        pendencia.observacoes = dto.observacoes
    if dto.motivo_rejeicao is not None:
        pendencia.motivo_rejeicao = dto.motivo_rejeicao
    
    # Se aprovado ou rejeitado, marcar data de resolução
    if dto.status in ['aprovado', 'rejeitado']:
        pendencia.resolved_at = datetime.now(timezone.utc)
    else:
        pendencia.resolved_at = None
    
    await session.commit()
    
    return {
        "id": pendencia.id,
        "status": pendencia.status,
        "mensagem": "Pendência atualizada com sucesso"
    }


@api_router.post("/pendencias/{pendencia_id}/contatos", tags=["Pendências"])
async def registrar_contato(
    pendencia_id: str,
    dto: RegistrarContatoDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Registra uma tentativa de contato com o aluno"""
    from sqlalchemy import select
    
    result = await session.execute(
        select(PendenciaModel).where(PendenciaModel.id == pendencia_id)
    )
    pendencia = result.scalar_one_or_none()
    
    if not pendencia:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    
    tipos_contato_validos = ['telefone', 'whatsapp', 'email', 'presencial']
    if dto.tipo_contato not in tipos_contato_validos:
        raise HTTPException(status_code=400, detail=f"Tipo de contato inválido. Válidos: {tipos_contato_validos}")
    
    contato = HistoricoContatoModel(
        id=str(uuid.uuid4()),
        pendencia_id=pendencia_id,
        usuario_id=usuario.id,
        usuario_nome=usuario.nome,
        tipo_contato=dto.tipo_contato,
        descricao=dto.descricao,
        resultado=dto.resultado
    )
    
    session.add(contato)
    
    # Atualizar status para "aguardando_aluno" se ainda estiver pendente
    if pendencia.status == 'pendente':
        pendencia.status = 'aguardando_aluno'
    
    await session.commit()
    
    return {
        "id": contato.id,
        "mensagem": "Contato registrado com sucesso",
        "novo_status": pendencia.status
    }


@api_router.get("/pendencias/aluno/{aluno_id}", tags=["Pendências"])
async def listar_pendencias_aluno(
    aluno_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Lista todas as pendências de um aluno específico"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await session.execute(
        select(PendenciaModel)
        .options(selectinload(PendenciaModel.historico_contatos))
        .where(PendenciaModel.aluno_id == aluno_id)
        .order_by(PendenciaModel.created_at.desc())
    )
    pendencias = result.scalars().all()
    
    return [
        {
            "id": p.id,
            "documento_codigo": p.documento_codigo,
            "documento_nome": p.documento_nome,
            "status": p.status,
            "observacoes": p.observacoes,
            "motivo_rejeicao": p.motivo_rejeicao,
            "total_contatos": len(p.historico_contatos),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "resolved_at": p.resolved_at.isoformat() if p.resolved_at else None
        }
        for p in pendencias
    ]


@api_router.delete("/pendencias/{pendencia_id}", tags=["Pendências"])
async def excluir_pendencia(
    pendencia_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """Exclui uma pendência (apenas admin)"""
    if usuario.role.value != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir pendências")
    
    from sqlalchemy import select
    
    result = await session.execute(
        select(PendenciaModel).where(PendenciaModel.id == pendencia_id)
    )
    pendencia = result.scalar_one_or_none()
    
    if not pendencia:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    
    await session.delete(pendencia)
    await session.commit()
    
    return {"mensagem": "Pendência excluída com sucesso"}


# ==================== ROOT & HEALTH ====================

@api_router.get("/", tags=["Health"])
async def root():
    return {"message": "Sistema Central de Matrículas - SENAI CIMATEC", "version": "1.2.0", "database": "PostgreSQL"}


@api_router.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "database": "PostgreSQL", "timestamp": datetime.now(timezone.utc).isoformat()}


# Include router
app.include_router(api_router)
