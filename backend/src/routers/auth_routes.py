"""
Router de Autenticação Refatorado
Contém todas as rotas de auth, login, registro, primeiro acesso e painel de conta
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
import uuid
import logging
from datetime import datetime, timezone

from src.domain.entities import Usuario, RoleUsuario
from src.domain.value_objects import Email
from src.domain.exceptions import AuthenticationException
from src.infrastructure.persistence.repositories import UsuarioRepository, AuditoriaRepository
from src.infrastructure.persistence.models import UsuarioModel, AuditoriaModel, PedidoModel
from src.infrastructure.security import JWTAuthenticator
from src.application.dtos.response import UsuarioResponseDTO, LoginResponseDTO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

# JWT Authenticator
jwt_auth = JWTAuthenticator()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ==================== DEPENDENCY INJECTION ====================

async def get_db_session():
    """Get database session"""
    from src.infrastructure.persistence.database import async_session
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


# ==================== DTOs ====================

class LoginRequest(BaseModel):
    email: str
    senha: str


class RegisterRequest(BaseModel):
    nome: str = Field(..., min_length=3)
    email: str
    senha: str = Field(..., min_length=6)
    role: str = Field(default="consultor")


class AlterarSenhaRequest(BaseModel):
    senha_atual: str = Field(..., min_length=1)
    nova_senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)


class AtualizarPerfilRequest(BaseModel):
    nome: Optional[str] = Field(None, min_length=3)
    email: Optional[str] = None


class TrocarSenhaPrimeiroAcessoRequest(BaseModel):
    """Request para troca de senha no primeiro acesso"""
    nova_senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)


# ==================== AUTH ROUTES ====================

@router.post("/login", response_model=LoginResponseDTO)
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
    
    # Buscar o modelo para verificar primeiro_acesso
    result = await session.execute(
        select(UsuarioModel).where(UsuarioModel.email == request.email)
    )
    usuario_model = result.scalar_one_or_none()
    primeiro_acesso = usuario_model.primeiro_acesso if usuario_model else False
    
    # Registra acesso
    usuario.registrar_acesso()
    await usuario_repo.salvar(usuario)
    
    # Registrar atividade de login
    from src.services.atividade_service import registrar_atividade
    try:
        await registrar_atividade(
            session=session,
            usuario_id=usuario.id,
            usuario_nome=usuario.nome,
            tipo="login",
            descricao="Fez login no sistema"
        )
    except Exception as e:
        logger.warning(f"Erro ao registrar atividade de login: {e}")
    
    # Gera token
    token = jwt_auth.criar_token(usuario)
    
    # Preparar resposta com primeiro_acesso
    usuario_dict = usuario.to_dict()
    usuario_dict["primeiro_acesso"] = primeiro_acesso
    
    return LoginResponseDTO(
        token=token,
        usuario=UsuarioResponseDTO(**usuario_dict)
    )


@router.post("/register", response_model=UsuarioResponseDTO, status_code=status.HTTP_201_CREATED)
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


@router.get("/me", response_model=UsuarioResponseDTO)
async def get_me(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna dados do usuário autenticado"""
    usuario = await get_current_user(token, session)
    return UsuarioResponseDTO(**usuario.to_dict())


# ==================== PAINEL DE CONTA ====================

@router.post("/trocar-senha-primeiro-acesso")
async def trocar_senha_primeiro_acesso(
    request: TrocarSenhaPrimeiroAcessoRequest,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Troca a senha no primeiro acesso (obrigatório)"""
    usuario = await get_current_user(token, session)
    usuario_repo = UsuarioRepository(session)
    
    # Verifica se é primeiro acesso
    result = await session.execute(
        select(UsuarioModel).where(UsuarioModel.id == usuario.id)
    )
    usuario_model = result.scalar_one_or_none()
    
    if not usuario_model or not usuario_model.primeiro_acesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta função é apenas para primeiro acesso"
        )
    
    # Verifica confirmação
    if request.nova_senha != request.confirmar_senha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nova senha e confirmação não conferem"
        )
    
    # Atualiza senha e marca primeiro_acesso como False
    usuario.senha_hash = jwt_auth.hash_senha(request.nova_senha)
    await usuario_repo.salvar(usuario)
    
    usuario_model.primeiro_acesso = False
    await session.commit()
    
    # Registrar atividade
    from src.services.atividade_service import registrar_atividade
    try:
        await registrar_atividade(
            session=session,
            usuario_id=usuario.id,
            usuario_nome=usuario.nome,
            tipo="primeiro_acesso",
            descricao="Definiu nova senha no primeiro acesso"
        )
    except Exception as e:
        logger.warning(f"Erro ao registrar atividade: {e}")
    
    return {"message": "Senha definida com sucesso! Bem-vindo ao SYNAPSE."}


@router.put("/me/senha")
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
    
    # Registrar atividade
    from src.services.atividade_service import registrar_atividade
    try:
        await registrar_atividade(
            session=session,
            usuario_id=usuario.id,
            usuario_nome=usuario.nome,
            tipo="alterar_senha",
            descricao="Alterou a senha de acesso"
        )
    except Exception as e:
        logger.warning(f"Erro ao registrar atividade: {e}")
    
    return {"message": "Senha alterada com sucesso"}


@router.put("/me/perfil", response_model=UsuarioResponseDTO)
async def atualizar_perfil(
    request: AtualizarPerfilRequest,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Atualiza dados do perfil do usuário autenticado"""
    usuario = await get_current_user(token, session)
    usuario_repo = UsuarioRepository(session)
    
    campos_alterados = []
    
    # Atualiza campos permitidos
    if request.nome:
        campos_alterados.append("nome")
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
        campos_alterados.append("email")
        usuario.email = email_obj
    
    await usuario_repo.salvar(usuario)
    
    # Registrar atividade
    if campos_alterados:
        from src.services.atividade_service import registrar_atividade
        try:
            await registrar_atividade(
                session=session,
                usuario_id=usuario.id,
                usuario_nome=usuario.nome,
                tipo="alterar_perfil",
                descricao=f"Atualizou o perfil: {', '.join(campos_alterados)}",
                detalhes={"campos_alterados": campos_alterados}
            )
        except Exception as e:
            logger.warning(f"Erro ao registrar atividade: {e}")
    
    return UsuarioResponseDTO(**usuario.to_dict())


@router.get("/me/atividades")
async def minhas_atividades(
    limite: int = Query(default=50, ge=1, le=100),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de atividade"),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna atividades recentes do usuário - Log de Auditoria Completo"""
    from src.infrastructure.persistence.models import AtividadeUsuarioModel
    from src.services.atividade_service import listar_atividades_usuario, get_tipos_atividade
    
    usuario = await get_current_user(token, session)
    
    # Buscar atividades do novo sistema
    tipos_filtro = [tipo] if tipo else None
    atividades = await listar_atividades_usuario(session, usuario.id, limite, tipos_filtro)
    
    # Buscar também auditorias antigas (para retrocompatibilidade)
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
    
    # Mapear ações de auditoria para ícones e cores
    ACOES_MAPEADAS = {
        "CRIACAO": {"icone": "file-plus", "cor": "blue", "descricao": "Criou solicitação"},
        "PEDIDO_CRIADO": {"icone": "file-plus", "cor": "blue", "descricao": "Criou solicitação"},
        "STATUS_ATUALIZADO": {"icone": "refresh-cw", "cor": "yellow", "descricao": "Alterou status"},
        "ATUALIZACAO_STATUS": {"icone": "refresh-cw", "cor": "yellow", "descricao": "Alterou status"},
        "PEDIDO_EXPORTADO": {"icone": "download", "cor": "green", "descricao": "Exportou TOTVS"},
        "EXPORTACAO": {"icone": "download", "cor": "green", "descricao": "Exportou TOTVS"},
        "PEDIDO_APROVADO": {"icone": "check-circle", "cor": "green", "descricao": "Aprovação"},
        "PEDIDO_REALIZADO": {"icone": "check-circle", "cor": "green", "descricao": "Matrícula realizada"},
        "PEDIDO_CANCELADO": {"icone": "x-circle", "cor": "red", "descricao": "Cancelamento"},
    }
    
    # Converter auditorias antigas para formato unificado
    auditorias_formatadas = []
    for a in auditorias:
        info = ACOES_MAPEADAS.get(a.acao, {"icone": "activity", "cor": "gray", "descricao": a.acao})
        
        # Extrair descrição dos detalhes
        descricao = info["descricao"]
        if a.detalhes:
            if "status_anterior" in a.detalhes and "status_novo" in a.detalhes:
                status_ant = a.detalhes.get("status_anterior", "").replace("_", " ").title()
                status_novo = a.detalhes.get("status_novo", "").replace("_", " ").title()
                descricao = f"Alterou status de '{status_ant}' para '{status_novo}'"
        
        auditorias_formatadas.append({
            "id": a.id,
            "tipo": a.acao.lower(),
            "tipo_icone": info["icone"],
            "tipo_cor": info["cor"],
            "descricao": descricao,
            "entidade_tipo": "pedido",
            "entidade_id": a.pedido_id,
            "entidade_nome": None,
            "detalhes": a.detalhes,
            "created_at": a.timestamp.isoformat() if a.timestamp else None
        })
    
    return {
        "atividades": atividades,
        "auditorias": auditorias_formatadas,
        "pedidos_recentes": [
            {
                "id": p.id,
                "protocolo": p.numero_protocolo,
                "curso": p.curso_nome,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in pedidos
        ],
        "tipos_disponiveis": get_tipos_atividade()
    }
