"""Router de Autenticação - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import logging
from datetime import datetime, timezone

from src.domain.entities import Usuario, RoleUsuario
from src.domain.value_objects import Email
from src.infrastructure.persistence.mongodb import db
from src.infrastructure.security import JWTAuthenticator
from src.application.dtos.response import UsuarioResponseDTO, LoginResponseDTO
from src.routers.dependencies import oauth2_scheme, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])
jwt_auth = JWTAuthenticator()


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
    nova_senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)


# ==================== AUTH ROUTES ====================

@router.post("/login", response_model=LoginResponseDTO)
async def login(request: LoginRequest):
    doc = await db.usuarios.find_one({"email": request.email})
    if not doc:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    if not jwt_auth.verificar_senha(request.senha, doc["senha_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    if not doc.get("ativo", True):
        raise HTTPException(status_code=403, detail="Usuário inativo")

    primeiro_acesso = doc.get("primeiro_acesso", False)

    # Update ultimo_acesso
    now = datetime.now(timezone.utc).isoformat()
    await db.usuarios.update_one({"id": doc["id"]}, {"$set": {"ultimo_acesso": now, "updated_at": now}})

    # Log activity
    try:
        await db.atividades_usuario.insert_one({
            "id": str(uuid.uuid4()), "usuario_id": doc["id"], "usuario_nome": doc["nome"],
            "tipo": "login", "descricao": "Fez login no sistema", "created_at": now
        })
    except Exception as e:
        logger.warning(f"Erro ao registrar atividade de login: {e}")

    usuario = Usuario(
        id=doc["id"], nome=doc["nome"], email=Email(doc["email"]),
        senha_hash=doc["senha_hash"], role=RoleUsuario.from_string(doc["role"]),
        ativo=doc.get("ativo", True), created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"), ultimo_acesso=now
    )
    token = jwt_auth.criar_token(usuario)

    usuario_dict = usuario.to_dict()
    usuario_dict["primeiro_acesso"] = primeiro_acesso

    return LoginResponseDTO(token=token, usuario=UsuarioResponseDTO(**usuario_dict))


@router.post("/register", response_model=UsuarioResponseDTO, status_code=201)
async def register(request: RegisterRequest):
    existing = await db.usuarios.find_one({"email": request.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email já cadastrado")

    now = datetime.now(timezone.utc).isoformat()
    usuario_id = str(uuid.uuid4())
    doc = {
        "id": usuario_id, "nome": request.nome, "email": request.email,
        "senha_hash": jwt_auth.hash_senha(request.senha),
        "role": request.role, "ativo": True, "primeiro_acesso": True,
        "created_at": now, "updated_at": now, "ultimo_acesso": None
    }
    await db.usuarios.insert_one(doc)

    usuario = Usuario(
        id=usuario_id, nome=request.nome, email=Email(request.email),
        senha_hash=doc["senha_hash"], role=RoleUsuario.from_string(request.role),
        ativo=True, created_at=now, updated_at=now
    )
    return UsuarioResponseDTO(**usuario.to_dict())


@router.get("/me", response_model=UsuarioResponseDTO)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    return UsuarioResponseDTO(**current_user.to_dict())


@router.post("/trocar-senha-primeiro-acesso")
async def trocar_senha_primeiro_acesso(
    request: TrocarSenhaPrimeiroAcessoRequest,
    current_user: Usuario = Depends(get_current_user)
):
    doc = await db.usuarios.find_one({"id": current_user.id})
    if not doc or not doc.get("primeiro_acesso"):
        raise HTTPException(status_code=400, detail="Esta função é apenas para primeiro acesso")

    if request.nova_senha != request.confirmar_senha:
        raise HTTPException(status_code=400, detail="Nova senha e confirmação não conferem")

    now = datetime.now(timezone.utc).isoformat()
    await db.usuarios.update_one({"id": current_user.id}, {"$set": {
        "senha_hash": jwt_auth.hash_senha(request.nova_senha),
        "primeiro_acesso": False, "updated_at": now
    }})

    try:
        await db.atividades_usuario.insert_one({
            "id": str(uuid.uuid4()), "usuario_id": current_user.id,
            "usuario_nome": current_user.nome, "tipo": "primeiro_acesso",
            "descricao": "Definiu nova senha no primeiro acesso", "created_at": now
        })
    except Exception as e:
        logger.warning(f"Erro ao registrar atividade: {e}")

    return {"message": "Senha definida com sucesso! Bem-vindo ao SYNAPSE."}


@router.put("/me/senha")
async def alterar_senha(
    request: AlterarSenhaRequest,
    current_user: Usuario = Depends(get_current_user)
):
    if not jwt_auth.verificar_senha(request.senha_atual, current_user.senha_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    if request.nova_senha != request.confirmar_senha:
        raise HTTPException(status_code=400, detail="Nova senha e confirmação não conferem")

    if request.senha_atual == request.nova_senha:
        raise HTTPException(status_code=400, detail="Nova senha deve ser diferente da atual")

    now = datetime.now(timezone.utc).isoformat()
    await db.usuarios.update_one({"id": current_user.id}, {"$set": {
        "senha_hash": jwt_auth.hash_senha(request.nova_senha), "updated_at": now
    }})

    try:
        await db.atividades_usuario.insert_one({
            "id": str(uuid.uuid4()), "usuario_id": current_user.id,
            "usuario_nome": current_user.nome, "tipo": "alterar_senha",
            "descricao": "Alterou a senha de acesso", "created_at": now
        })
    except Exception as e:
        logger.warning(f"Erro ao registrar atividade: {e}")

    return {"message": "Senha alterada com sucesso"}


@router.put("/me/perfil", response_model=UsuarioResponseDTO)
async def atualizar_perfil(
    request: AtualizarPerfilRequest,
    current_user: Usuario = Depends(get_current_user)
):
    updates = {}
    campos_alterados = []

    if request.nome:
        updates["nome"] = request.nome
        campos_alterados.append("nome")

    if request.email:
        existing = await db.usuarios.find_one({"email": request.email, "id": {"$ne": current_user.id}})
        if existing:
            raise HTTPException(status_code=409, detail="Este email já está em uso")
        updates["email"] = request.email
        campos_alterados.append("email")

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.usuarios.update_one({"id": current_user.id}, {"$set": updates})

    if campos_alterados:
        try:
            await db.atividades_usuario.insert_one({
                "id": str(uuid.uuid4()), "usuario_id": current_user.id,
                "usuario_nome": current_user.nome, "tipo": "alterar_perfil",
                "descricao": f"Atualizou o perfil: {', '.join(campos_alterados)}",
                "detalhes": {"campos_alterados": campos_alterados},
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.warning(f"Erro ao registrar atividade: {e}")

    doc = await db.usuarios.find_one({"id": current_user.id})
    usuario = Usuario(
        id=doc["id"], nome=doc["nome"], email=Email(doc["email"]),
        senha_hash=doc["senha_hash"], role=RoleUsuario.from_string(doc["role"]),
        ativo=doc.get("ativo", True), created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"), ultimo_acesso=doc.get("ultimo_acesso")
    )
    return UsuarioResponseDTO(**usuario.to_dict())


@router.get("/me/atividades")
async def minhas_atividades(
    limite: int = Query(default=50, ge=1, le=100),
    tipo: Optional[str] = Query(None),
    current_user: Usuario = Depends(get_current_user)
):
    # Atividades
    query = {"usuario_id": current_user.id}
    if tipo:
        query["tipo"] = tipo
    atividades_cursor = db.atividades_usuario.find(query, {"_id": 0}).sort("created_at", -1).limit(limite)
    atividades = await atividades_cursor.to_list(length=limite)

    # Auditorias
    auditorias_cursor = db.auditoria.find({"usuario_id": current_user.id}, {"_id": 0}).sort("timestamp", -1).limit(limite)
    auditorias_raw = await auditorias_cursor.to_list(length=limite)

    ACOES_MAPEADAS = {
        "CRIACAO": {"icone": "file-plus", "cor": "blue", "descricao": "Criou solicitação"},
        "PEDIDO_CRIADO": {"icone": "file-plus", "cor": "blue", "descricao": "Criou solicitação"},
        "STATUS_ATUALIZADO": {"icone": "refresh-cw", "cor": "yellow", "descricao": "Alterou status"},
        "ATUALIZACAO_STATUS": {"icone": "refresh-cw", "cor": "yellow", "descricao": "Alterou status"},
        "PEDIDO_EXPORTADO": {"icone": "download", "cor": "green", "descricao": "Exportou TOTVS"},
        "EXPORTACAO": {"icone": "download", "cor": "green", "descricao": "Exportou TOTVS"},
    }

    auditorias_formatadas = []
    for a in auditorias_raw:
        info = ACOES_MAPEADAS.get(a.get("acao", ""), {"icone": "activity", "cor": "gray", "descricao": a.get("acao", "")})
        descricao = info["descricao"]
        detalhes = a.get("detalhes")
        if isinstance(detalhes, dict):
            if "status_anterior" in detalhes and "status_novo" in detalhes:
                descricao = f"Alterou status de '{detalhes['status_anterior']}' para '{detalhes['status_novo']}'"

        auditorias_formatadas.append({
            "id": a.get("id"), "tipo": a.get("acao", "").lower(),
            "tipo_icone": info["icone"], "tipo_cor": info["cor"],
            "descricao": descricao, "entidade_tipo": "pedido",
            "entidade_id": a.get("pedido_id"), "entidade_nome": None,
            "detalhes": detalhes,
            "created_at": a.get("timestamp")
        })

    # Pedidos recentes
    pedidos_cursor = db.pedidos.find({"consultor_id": current_user.id}, {"_id": 0}).sort("created_at", -1).limit(10)
    pedidos = await pedidos_cursor.to_list(length=10)

    tipos_disponiveis = [
        "login", "logout", "criar_pedido", "atualizar_pedido",
        "criar_pendencia", "atualizar_pendencia", "criar_reembolso",
        "atualizar_reembolso", "alterar_perfil", "alterar_senha",
        "exportar_totvs", "importar_lote", "primeiro_acesso"
    ]

    return {
        "atividades": atividades,
        "auditorias": auditorias_formatadas,
        "pedidos_recentes": [
            {"id": p["id"], "protocolo": p.get("numero_protocolo"), "curso": p.get("curso_nome"),
             "status": p.get("status"), "created_at": p.get("created_at")}
            for p in pedidos
        ],
        "tipos_disponiveis": tipos_disponiveis
    }
