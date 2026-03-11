"""Shared Dependencies for all routers - MongoDB version"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.infrastructure.persistence.mongodb import db
from src.infrastructure.security import JWTAuthenticator
from src.domain.entities import Usuario, RoleUsuario
from src.domain.value_objects import Email
from src.domain.exceptions import AuthenticationException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
jwt_auth = JWTAuthenticator()


async def get_db_session():
    """Returns MongoDB database instance (kept name for compatibility)"""
    return db


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> Usuario:
    """Dependency para obter usuário autenticado via MongoDB"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        payload = jwt_auth.verificar_token(token)
        usuario_id = payload.get("sub")

        doc = await db.usuarios.find_one({"id": usuario_id})
        if not doc:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        usuario = Usuario(
            id=doc["id"],
            nome=doc["nome"],
            email=Email(doc["email"]),
            senha_hash=doc["senha_hash"],
            role=RoleUsuario.from_string(doc["role"]),
            ativo=doc.get("ativo", True),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
            ultimo_acesso=doc.get("ultimo_acesso")
        )

        if not usuario.ativo:
            raise HTTPException(status_code=403, detail="Usuário inativo")

        return usuario
    except AuthenticationException as e:
        raise HTTPException(status_code=401, detail=str(e.message))


def require_role(*roles):
    """Dependency factory to require specific roles"""
    async def check_role(
        current_user: Usuario = Depends(get_current_user)
    ) -> Usuario:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso restrito a: {', '.join(roles)}"
            )
        return current_user
    return check_role
