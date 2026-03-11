"""Router de Usuários - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime, timezone

from src.domain.entities import Usuario, RoleUsuario
from src.domain.value_objects import Email
from src.infrastructure.persistence.mongodb import db
from src.infrastructure.security import JWTAuthenticator
from src.application.dtos.request import AtualizarUsuarioDTO
from src.application.dtos.response import UsuarioResponseDTO
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _doc_to_usuario(doc) -> Usuario:
    return Usuario(
        id=doc["id"], nome=doc["nome"], email=Email(doc["email"]),
        senha_hash=doc["senha_hash"], role=RoleUsuario.from_string(doc["role"]),
        ativo=doc.get("ativo", True), created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"), ultimo_acesso=doc.get("ultimo_acesso")
    )


@router.get("")
async def listar_usuarios(
    ativo: Optional[bool] = None,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role.value not in ("admin",):
        raise HTTPException(status_code=403, detail="Permissão necessária")

    query = {}
    if ativo is not None:
        query["ativo"] = ativo

    total = await db.usuarios.count_documents(query)
    offset = (pagina - 1) * por_pagina
    cursor = db.usuarios.find(query, {"_id": 0}).sort("nome", 1).skip(offset).limit(por_pagina)
    docs = await cursor.to_list(length=por_pagina)

    usuarios = [UsuarioResponseDTO(**_doc_to_usuario(d).to_dict()).model_dump() for d in docs]

    return {"usuarios": usuarios, "total": total, "pagina": pagina, "por_pagina": por_pagina}


@router.get("/{usuario_id}", response_model=UsuarioResponseDTO)
async def buscar_usuario(usuario_id: str, current_user: Usuario = Depends(get_current_user)):
    if current_user.role.value not in ("admin",):
        raise HTTPException(status_code=403, detail="Permissão necessária")

    doc = await db.usuarios.find_one({"id": usuario_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UsuarioResponseDTO(**_doc_to_usuario(doc).to_dict())


@router.patch("/{usuario_id}", response_model=UsuarioResponseDTO)
async def atualizar_usuario(
    usuario_id: str, request: AtualizarUsuarioDTO,
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role.value not in ("admin",):
        raise HTTPException(status_code=403, detail="Permissão necessária")

    doc = await db.usuarios.find_one({"id": usuario_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if request.nome:
        updates["nome"] = request.nome
    if request.role:
        updates["role"] = request.role
    if request.ativo is not None:
        updates["ativo"] = request.ativo

    await db.usuarios.update_one({"id": usuario_id}, {"$set": updates})
    doc = await db.usuarios.find_one({"id": usuario_id})
    return UsuarioResponseDTO(**_doc_to_usuario(doc).to_dict())


@router.delete("/{usuario_id}")
async def deletar_usuario(usuario_id: str, current_user: Usuario = Depends(get_current_user)):
    if current_user.role.value not in ("admin",):
        raise HTTPException(status_code=403, detail="Permissão necessária")
    if usuario_id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível deletar o próprio usuário")

    result = await db.usuarios.delete_one({"id": usuario_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"message": "Usuário deletado com sucesso"}


@router.post("/{usuario_id}/resetar-senha")
async def resetar_senha_usuario(usuario_id: str, current_user: Usuario = Depends(get_current_user)):
    if current_user.role.value not in ("admin",):
        raise HTTPException(status_code=403, detail="Permissão necessária")

    jwt_auth = JWTAuthenticator()
    doc = await db.usuarios.find_one({"id": usuario_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    await db.usuarios.update_one({"id": usuario_id}, {"$set": {
        "senha_hash": jwt_auth.hash_senha("Senai@2026"),
        "primeiro_acesso": True,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }})
    return {"message": f"Senha resetada com sucesso para {doc['nome']}"}


@router.post("/resetar-todas-senhas")
async def resetar_todas_senhas(current_user: Usuario = Depends(get_current_user)):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem resetar todas as senhas")

    jwt_auth = JWTAuthenticator()
    hash_padrao = jwt_auth.hash_senha("Senai@2026")

    await db.usuarios.update_many({}, {"$set": {
        "senha_hash": hash_padrao, "primeiro_acesso": True
    }})
    return {"message": "Todas as senhas foram resetadas com sucesso"}
