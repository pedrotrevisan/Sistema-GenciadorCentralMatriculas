"""Router de Documentos/Pendências Documentais - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/documentos", tags=["Documentos"])

STATUS_DOC = ["pendente", "recebido", "validado", "rejeitado"]

class CriarPendenciaDocDTO(BaseModel):
    pedido_id: str
    aluno_id: str
    tipo_documento_id: Optional[str] = None
    tipo: str
    descricao: Optional[str] = None

class AtualizarStatusDocDTO(BaseModel):
    status: str
    observacoes: Optional[str] = None


@router.get("/tipos")
async def listar_tipos_documento(usuario: Usuario = Depends(get_current_user)):
    tipos = await db.tipos_documento.find({}, {"_id": 0}).sort("nome", 1).to_list(100)
    return {"tipos": tipos, "total": len(tipos)}


@router.post("/pendencias", status_code=201)
async def criar_pendencia_doc(dto: CriarPendenciaDocDTO, usuario: Usuario = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()), "pedido_id": dto.pedido_id, "aluno_id": dto.aluno_id,
        "tipo_documento_id": dto.tipo_documento_id, "tipo": dto.tipo,
        "descricao": dto.descricao, "status": "pendente",
        "criado_por_id": usuario.id, "criado_por_nome": usuario.nome,
        "created_at": now, "updated_at": now
    }
    await db.pendencias_doc.insert_one(doc)
    return doc


@router.get("/pendencias")
async def listar_pendencias_doc(
    pedido_id: Optional[str] = None, aluno_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    usuario: Usuario = Depends(get_current_user)
):
    query = {}
    if pedido_id:
        query["pedido_id"] = pedido_id
    if aluno_id:
        query["aluno_id"] = aluno_id
    if status_filter:
        query["status"] = status_filter
    docs = await db.pendencias_doc.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"pendencias": docs, "total": len(docs)}


@router.patch("/pendencias/{pendencia_id}/status")
async def atualizar_status_doc(pendencia_id: str, dto: AtualizarStatusDocDTO, usuario: Usuario = Depends(get_current_user)):
    if dto.status not in STATUS_DOC:
        raise HTTPException(400, f"Status inválido. Use: {', '.join(STATUS_DOC)}")
    result = await db.pendencias_doc.update_one({"id": pendencia_id}, {"$set": {
        "status": dto.status, "observacoes": dto.observacoes,
        "atualizado_por_id": usuario.id, "atualizado_por_nome": usuario.nome,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }})
    if result.matched_count == 0:
        raise HTTPException(404, "Pendência não encontrada")
    return {"message": "Status atualizado", "status": dto.status}


@router.get("/pendencias/pedido/{pedido_id}/resumo")
async def resumo_pendencias_pedido(pedido_id: str, usuario: Usuario = Depends(get_current_user)):
    pipeline = [
        {"$match": {"pedido_id": pedido_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    result = await db.pendencias_doc.aggregate(pipeline).to_list(10)
    por_status = {r["_id"]: r["count"] for r in result}
    total = sum(por_status.values())
    return {"pedido_id": pedido_id, "total": total, "por_status": por_status,
            "todas_resolvidas": total > 0 and por_status.get("pendente", 0) == 0}
