"""Router de Autenticação"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from src.domain.entities import Usuario, RoleUsuario
from src.domain.value_objects import Email
from src.infrastructure.persistence.repositories import UsuarioRepository
from src.application.dtos.response import UsuarioResponseDTO, LoginResponseDTO

from .dependencies import (
    get_db_session, get_current_user, jwt_auth, oauth2_scheme
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ==================== DTOs ====================

class AlterarSenhaRequest(BaseModel):
    senha_atual: str = Field(..., min_length=1)
    nova_senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)


class AtualizarPerfilRequest(BaseModel):
    nome: Optional[str] = Field(None, min_length=3)
    email: Optional[str] = None
    telefone: Optional[str] = None
    cargo: Optional[str] = None
    setor: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    senha: str


class RegisterRequest(BaseModel):
    nome: str = Field(..., min_length=3)
    email: str
    senha: str = Field(..., min_length=6)
    role: str = Field(default="consultor")


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
    
    # Registra acesso
    usuario.registrar_acesso()
    await usuario_repo.salvar(usuario)
    
    # Gera token
    token = jwt_auth.criar_token(usuario)
    
    return LoginResponseDTO(
        token=token,
        usuario=UsuarioResponseDTO(**usuario.to_dict())
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
