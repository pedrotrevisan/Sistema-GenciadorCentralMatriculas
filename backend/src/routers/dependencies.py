"""Dependências compartilhadas entre os routers"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from src.domain.entities import Usuario
from src.infrastructure.persistence.database import async_session
from src.infrastructure.persistence.repositories import UsuarioRepository
from src.infrastructure.security import JWTAuthenticator

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# JWT Authenticator
jwt_auth = JWTAuthenticator()


async def get_db_session() -> AsyncSession:
    """Dependency para obter sessão do banco de dados"""
    async with async_session() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
) -> Usuario:
    """Dependency para obter usuário atual autenticado"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt_auth.verificar_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        usuario_repo = UsuarioRepository(session)
        usuario = await usuario_repo.buscar_por_id(user_id)
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return usuario
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
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


def require_role(*roles: str):
    """Dependency factory para verificar role"""
    async def check_role(
        usuario: Usuario = Depends(get_current_user)
    ):
        if usuario.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso restrito para roles: {', '.join(roles)}"
            )
        return usuario
    return check_role
