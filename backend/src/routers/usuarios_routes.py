"""
Router de Usuários Refatorado
Contém todas as rotas de CRUD de usuários (admin)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timezone

from src.domain.entities import Usuario, RoleUsuario
from src.infrastructure.persistence.repositories import UsuarioRepository
from src.application.dtos.request import AtualizarUsuarioDTO
from src.application.dtos.response import UsuarioResponseDTO

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

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
    from src.infrastructure.security import JWTAuthenticator
    from src.domain.exceptions import AuthenticationException
    
    jwt_auth = JWTAuthenticator()
    
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


# ==================== USUARIOS ROUTES ====================

@router.get("")
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


@router.get("/{usuario_id}", response_model=UsuarioResponseDTO)
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


@router.patch("/{usuario_id}", response_model=UsuarioResponseDTO)
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


@router.delete("/{usuario_id}")
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


@router.post("/{usuario_id}/resetar-senha")
async def resetar_senha_usuario(
    usuario_id: str,
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Reseta a senha de um usuário para a senha padrão"""
    from src.infrastructure.security import JWTAuthenticator
    from src.infrastructure.persistence.models import UsuarioModel
    from sqlalchemy import select
    
    current_user, session = deps
    usuario_repo = UsuarioRepository(session)
    jwt_auth = JWTAuthenticator()
    
    usuario = await usuario_repo.buscar_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Resetar para senha padrão
    SENHA_PADRAO = "Senai@2026"
    usuario.senha_hash = jwt_auth.hash_senha(SENHA_PADRAO)
    await usuario_repo.salvar(usuario)
    
    # Marcar como primeiro acesso
    result = await session.execute(
        select(UsuarioModel).where(UsuarioModel.id == usuario_id)
    )
    usuario_model = result.scalar_one_or_none()
    if usuario_model:
        usuario_model.primeiro_acesso = True
        await session.commit()
    
    return {"message": f"Senha resetada com sucesso para {usuario.nome}"}


@router.post("/resetar-todas-senhas")
async def resetar_todas_senhas(
    deps: tuple = Depends(require_permission("usuario:gerenciar"))
):
    """Reseta a senha de TODOS os usuários para a senha padrão (apenas admin)"""
    from src.infrastructure.security import JWTAuthenticator
    from src.infrastructure.persistence.models import UsuarioModel
    from sqlalchemy import select, update
    
    current_user, session = deps
    
    # Verificar se é admin
    if current_user.role.value != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem resetar todas as senhas")
    
    jwt_auth = JWTAuthenticator()
    SENHA_PADRAO = "Senai@2026"
    hash_padrao = jwt_auth.hash_senha(SENHA_PADRAO)
    
    # Atualizar todas as senhas
    await session.execute(
        update(UsuarioModel).values(
            senha_hash=hash_padrao,
            primeiro_acesso=True
        )
    )
    await session.commit()
    
    return {"message": "Todas as senhas foram resetadas com sucesso"}
