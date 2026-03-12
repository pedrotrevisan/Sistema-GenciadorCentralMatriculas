"""Router Status Matrícula - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from src.domain.entities import Usuario
from src.domain.status_matricula import StatusMatriculaEnum, STATUS_LABELS, STATUS_COLORS
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/status", tags=["Máquina de Estados"])

class TransicionarStatusDTO(BaseModel):
    status_novo: str
    motivo: Optional[str] = None
    observacoes: Optional[str] = None


@router.get("/enums")
async def listar_status_enums():
    return {"status": [{"valor": s.value, "label": STATUS_LABELS[s], "cor": STATUS_COLORS[s]} for s in StatusMatriculaEnum]}


@router.get("/pedidos/{pedido_id}/proximos")
async def obter_proximos_status(pedido_id: str, usuario: Usuario = Depends(get_current_user)):
    pedido = await db.pedidos.find_one({"id": pedido_id})
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")

    from src.domain.status_matricula import TRANSICOES_VALIDAS
    status_atual = pedido.get("status", "inscrito")
    try:
        status_enum = StatusMatriculaEnum(status_atual)
    except ValueError:
        status_enum = StatusMatriculaEnum.INSCRITO

    proximos = TRANSICOES_VALIDAS.get(status_enum, [])
    return {
        "status_atual": {"valor": status_enum.value, "label": STATUS_LABELS.get(status_enum, status_atual), "cor": STATUS_COLORS.get(status_enum, "gray")},
        "proximos_status": [{"valor": s.value, "label": STATUS_LABELS[s], "cor": STATUS_COLORS[s]} for s in proximos]
    }


@router.post("/pedidos/{pedido_id}/transicionar", status_code=201)
async def transicionar_status(pedido_id: str, dto: TransicionarStatusDTO, usuario: Usuario = Depends(get_current_user)):
    pedido = await db.pedidos.find_one({"id": pedido_id})
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")

    try:
        status_novo = StatusMatriculaEnum(dto.status_novo)
    except ValueError:
        raise HTTPException(400, f"Status inválido: {dto.status_novo}")

    status_anterior = pedido.get("status", "pendente")
    now = datetime.now(timezone.utc).isoformat()
    transicao_id = str(uuid.uuid4())

    await db.pedidos.update_one({"id": pedido_id}, {"$set": {"status": dto.status_novo, "updated_at": now}})
    await db.transicoes_status.insert_one({
        "id": transicao_id, "pedido_id": pedido_id, "status_anterior": status_anterior,
        "status_novo": dto.status_novo, "tipo_transicao": "manual",
        "data_transicao": now, "motivo": dto.motivo, "observacoes": dto.observacoes,
        "usuario_id": usuario.id, "usuario_nome": usuario.nome, "usuario_email": str(usuario.email)
    })
    await db.auditoria.insert_one({
        "id": str(uuid.uuid4()), "pedido_id": pedido_id, "usuario_id": usuario.id,
        "acao": "ATUALIZACAO_STATUS",
        "detalhes": {"status_anterior": status_anterior, "status_novo": dto.status_novo, "motivo": dto.motivo},
        "timestamp": now
    })

    return {"id": transicao_id, "pedido_id": pedido_id, "status_anterior": status_anterior,
            "status_novo": dto.status_novo, "tipo_transicao": "manual", "data_transicao": now,
            "motivo": dto.motivo, "observacoes": dto.observacoes,
            "usuario_id": usuario.id, "usuario_nome": usuario.nome, "usuario_email": str(usuario.email)}


@router.get("/pedidos/{pedido_id}/historico")
async def consultar_historico(pedido_id: str, limite: int = 50, usuario: Usuario = Depends(get_current_user)):
    transicoes = await db.transicoes_status.find({"pedido_id": pedido_id}, {"_id": 0}).sort("data_transicao", -1).limit(limite).to_list(limite)
    return {"total": len(transicoes), "transicoes": transicoes}
