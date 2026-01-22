"""Router de Gestão de Usuários"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Usuario, RoleUsuario
from src.infrastructure.persistence.repositories import UsuarioRepository
from src.application.dtos.request import AtualizarUsuarioDTO
from src.application.dtos.response import UsuarioResponseDTO

from .dependencies import get_db_session, require_permission

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


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
