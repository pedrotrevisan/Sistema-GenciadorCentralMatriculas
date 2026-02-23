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
from src.infrastructure.persistence.models import CursoModel, ProjetoModel, EmpresaModel, AlunoModel, TipoDocumentoModel, PendenciaModel, HistoricoContatoModel, ReembolsoModel, AuditoriaModel, UsuarioModel, PedidoModel
from sqlalchemy import select, desc
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


# ==================== PAINEL DE CONTA ====================

class AlterarSenhaRequest(BaseModel):
    senha_atual: str = Field(..., min_length=1)
    nova_senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)


class AtualizarPerfilRequest(BaseModel):
    nome: Optional[str] = Field(None, min_length=3)
    email: Optional[str] = None


@api_router.put("/auth/me/senha", tags=["Auth"])
async def alterar_senha(
    request: AlterarSenhaRequest,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Altera a senha do usuário autenticado"""
    usuario = await get_current_user(token, session)
    usuario_repo = UsuarioRepository(session)
    
    # Verifica senha atual
    if not jwt_auth.verificar_senha(request.senha_atual, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Verifica confirmação
    if request.nova_senha != request.confirmar_senha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nova senha e confirmação não conferem"
        )
    
    # Verifica se nova senha é diferente da atual
    if request.senha_atual == request.nova_senha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nova senha deve ser diferente da atual"
        )
    
    # Atualiza senha
    usuario.senha_hash = jwt_auth.hash_senha(request.nova_senha)
    await usuario_repo.salvar(usuario)
    
    return {"message": "Senha alterada com sucesso"}


@api_router.put("/auth/me/perfil", response_model=UsuarioResponseDTO, tags=["Auth"])
async def atualizar_perfil(
    request: AtualizarPerfilRequest,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Atualiza dados do perfil do usuário autenticado"""
    usuario = await get_current_user(token, session)
    usuario_repo = UsuarioRepository(session)
    
    # Atualiza campos permitidos
    if request.nome:
        usuario.nome = request.nome
    
    if request.email:
        # Verifica se email já existe
        email_obj = Email(request.email)
        existente = await usuario_repo.buscar_por_email(request.email)
        if existente and existente.id != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este email já está em uso"
            )
        usuario.email = email_obj
    
    await usuario_repo.salvar(usuario)
    
    return UsuarioResponseDTO(**usuario.to_dict())


@api_router.get("/auth/me/atividades", tags=["Auth"])
async def minhas_atividades(
    limite: int = Query(default=20, ge=1, le=100),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna atividades recentes do usuário"""
    usuario = await get_current_user(token, session)
    
    # Buscar atividades de auditoria
    result = await session.execute(
        select(AuditoriaModel)
        .where(AuditoriaModel.usuario_id == usuario.id)
        .order_by(desc(AuditoriaModel.timestamp))
        .limit(limite)
    )
    auditorias = result.scalars().all()
    
    # Buscar pedidos criados pelo usuário
    result = await session.execute(
        select(PedidoModel)
        .where(PedidoModel.consultor_id == usuario.id)
        .order_by(desc(PedidoModel.created_at))
        .limit(10)
    )
    pedidos = result.scalars().all()
    
    return {
        "auditorias": [
            {
                "id": a.id,
                "acao": a.acao,
                "pedido_id": a.pedido_id,
                "detalhes": a.detalhes,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None
            }
            for a in auditorias
        ],
        "pedidos_recentes": [
            {
                "id": p.id,
                "protocolo": p.numero_protocolo,
                "curso": p.curso_nome,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in pedidos
        ]
    }


# ==================== PEDIDOS ROUTES ====================

@api_router.post("/pedidos", response_model=dict, tags=["Pedidos"])
async def criar_pedido(
    request: CriarPedidoDTO,
    deps: tuple = Depends(require_permission("pedido:criar"))
):
    """
    Cria um novo pedido de matrícula COM reserva automática de vaga
    
    Se turma_id for fornecido, reserva vaga automaticamente.
    Retorna informações do pedido E da reserva.
    """
    usuario, session = deps
    pedido_repo = PedidoRepository(session)
    auditoria_repo = AuditoriaRepository(session)
    
    # Se turma_id fornecido, usar use case com reserva
    if request.turma_id:
        from src.infrastructure.persistence.repositories_turmas import TurmaRepository, ReservaVagaRepository
        from src.application.use_cases.criar_pedido_com_reserva_use_case import CriarPedidoComReservaUseCase
        
        turma_repo = TurmaRepository(session)
        reserva_repo = ReservaVagaRepository(session)
        
        criar_pedido_uc = CriarPedidoComReservaUseCase(
            pedido_repo, auditoria_repo, turma_repo, reserva_repo
        )
        
        resultado = await criar_pedido_uc.executar(request, usuario, request.turma_id)
        
        return {
            "pedido": PedidoResponseDTO(**resultado["pedido"].to_dict()).model_dump(),
            "reserva": {
                "id": resultado["reserva"].id if resultado["reserva"] else None,
                "turma_id": resultado["reserva"].turma_id if resultado["reserva"] else None,
                "status": resultado["reserva"].status.value if resultado["reserva"] else None,
                "data_expiracao": resultado["reserva"].data_expiracao.isoformat() if resultado["reserva"] and resultado["reserva"].data_expiracao else None
            } if resultado["reserva"] else None,
            "mensagem_reserva": resultado["mensagem_reserva"]
        }
    
    # Sem turma, usar use case padrão
    criar_pedido_uc = CriarPedidoMatriculaUseCase(pedido_repo, auditoria_repo)
    pedido = await criar_pedido_uc.executar(request, usuario)
    
    return {
        "pedido": PedidoResponseDTO(**pedido.to_dict()).model_dump(),
        "reserva": None,
        "mensagem_reserva": None
    }


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


@api_router.get("/pedidos/{pedido_id}/timeline", tags=["Pedidos"])
async def buscar_timeline_pedido(
    pedido_id: str,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna timeline de auditoria de um pedido"""
    from sqlalchemy import select
    
    usuario = await get_current_user(token, session)
    pedido_repo = PedidoRepository(session)
    
    # Verificar se pedido existe e se usuário tem acesso
    pedido = await pedido_repo.buscar_por_id(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Consultor só vê os próprios pedidos
    if usuario.role.value == 'consultor' and pedido.consultor_id != usuario.id:
        raise HTTPException(status_code=403, detail="Sem permissão para visualizar este pedido")
    
    # Buscar registros de auditoria
    result = await session.execute(
        select(AuditoriaModel)
        .where(AuditoriaModel.pedido_id == pedido_id)
        .order_by(AuditoriaModel.timestamp.asc())  # Ordem cronológica
    )
    auditorias = result.scalars().all()
    
    # Buscar nomes dos usuários
    usuario_ids = list(set(a.usuario_id for a in auditorias))
    usuario_repo = UsuarioRepository(session)
    usuarios_dict = {}
    for uid in usuario_ids:
        u = await usuario_repo.buscar_por_id(uid)
        if u:
            usuarios_dict[uid] = u.nome
    
    # Mapear ações para labels amigáveis
    ACOES_LABELS = {
        "CRIACAO": {"label": "Solicitação Criada", "icon": "plus", "color": "blue"},
        "PEDIDO_CRIADO": {"label": "Solicitação Criada", "icon": "plus", "color": "blue"},
        "STATUS_ATUALIZADO": {"label": "Status Alterado", "icon": "refresh", "color": "yellow"},
        "ATUALIZACAO_STATUS": {"label": "Status Alterado", "icon": "refresh", "color": "yellow"},
        "PEDIDO_EXPORTADO": {"label": "Exportado para TOTVS", "icon": "download", "color": "green"},
        "EXPORTACAO": {"label": "Exportado para TOTVS", "icon": "download", "color": "green"},
        "DOCUMENTACAO_SOLICITADA": {"label": "Documentação Solicitada", "icon": "file", "color": "orange"},
        "PEDIDO_APROVADO": {"label": "Solicitação Aprovada", "icon": "check", "color": "green"},
        "PEDIDO_REALIZADO": {"label": "Matrícula Realizada", "icon": "check-circle", "color": "green"},
        "PEDIDO_CANCELADO": {"label": "Solicitação Cancelada", "icon": "x", "color": "red"},
    }
    
    # Construir timeline
    timeline = []
    for audit in auditorias:
        acao_info = ACOES_LABELS.get(audit.acao, {"label": audit.acao, "icon": "circle", "color": "gray"})
        
        # Extrair detalhes relevantes
        detalhes_str = ""
        if audit.detalhes:
            if "status_anterior" in audit.detalhes and "status_novo" in audit.detalhes:
                status_ant = audit.detalhes.get("status_anterior", "").replace("_", " ").title()
                status_novo = audit.detalhes.get("status_novo", "").replace("_", " ").title()
                detalhes_str = f"De '{status_ant}' para '{status_novo}'"
            elif "motivo" in audit.detalhes:
                detalhes_str = audit.detalhes.get("motivo", "")
            elif "formato" in audit.detalhes:
                detalhes_str = f"Formato: {audit.detalhes.get('formato', '').upper()}"
        
        timeline.append({
            "id": audit.id,
            "acao": audit.acao,
            "acao_label": acao_info["label"],
            "icon": acao_info["icon"],
            "color": acao_info["color"],
            "usuario_id": audit.usuario_id,
            "usuario_nome": usuarios_dict.get(audit.usuario_id, "Usuário Desconhecido"),
            "detalhes": detalhes_str,
            "detalhes_raw": audit.detalhes,
            "timestamp": audit.timestamp.isoformat() if audit.timestamp else None
        })
    
    return {
        "pedido_id": pedido_id,
        "numero_protocolo": pedido.numero_protocolo,
        "total_eventos": len(timeline),
        "timeline": timeline
    }


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




# ==================== DADOS AUXILIARES ====================
# NOTA: CRUD de Cursos, Projetos e Empresas foi movido para src/routers/cadastros.py
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


# ==================== ROOT & HEALTH ====================

@api_router.get("/", tags=["Health"])
async def root():
    return {"message": "Sistema Central de Matrículas - SENAI CIMATEC", "version": "1.3.0", "database": "PostgreSQL"}


@api_router.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "database": "PostgreSQL", "timestamp": datetime.now(timezone.utc).isoformat()}


# Include modular routers first
from src.routers.reembolsos import router as reembolsos_router
from src.routers.pendencias import router as pendencias_router
from src.routers.turmas import router as turmas_router
from src.routers.ocr import router as ocr_router
from src.routers.status_matricula import router as status_router
from src.routers.documentos import router as documentos_router
from src.routers.contatos import router as contatos_router
from src.routers.cadastros import router as cadastros_router
from src.routers.apoio_cognitivo import router as apoio_router
from src.routers.atribuicoes import router as atribuicoes_router

api_router.include_router(reembolsos_router)
api_router.include_router(pendencias_router)
api_router.include_router(turmas_router)
api_router.include_router(ocr_router)
api_router.include_router(status_router)
api_router.include_router(documentos_router)
api_router.include_router(contatos_router)
api_router.include_router(cadastros_router)
api_router.include_router(apoio_router)
api_router.include_router(atribuicoes_router)

# Then include main router in app
app.include_router(api_router)
