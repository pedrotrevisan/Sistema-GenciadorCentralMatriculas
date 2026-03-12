"""Router de Contatos - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/contatos", tags=["Log de Contatos"])

CANAIS_CONTATO = ["telefone", "email", "whatsapp", "presencial", "sgc"]
TIPOS_CONTATO = ["primeiro_contato", "retorno", "cobranca_documento", "informacao", "cancelamento", "outros"]

class RegistrarContatoDTO(BaseModel):
    pedido_id: Optional[str] = None
    aluno_id: Optional[str] = None
    aluno_nome: str
    canal: str
    tipo: str
    descricao: str
    resultado: Optional[str] = None

class FiltroContatosDTO(BaseModel):
    pedido_id: Optional[str] = None
    aluno_id: Optional[str] = None
    canal: Optional[str] = None
    tipo: Optional[str] = None


@router.get("/canais")
async def listar_canais():
    return {"canais": CANAIS_CONTATO, "tipos": TIPOS_CONTATO}

@router.post("")
async def registrar_contato(dto: RegistrarContatoDTO, usuario: Usuario = Depends(get_current_user)):
    if dto.canal not in CANAIS_CONTATO:
        raise HTTPException(400, f"Canal inválido. Use: {', '.join(CANAIS_CONTATO)}")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()), "pedido_id": dto.pedido_id, "aluno_id": dto.aluno_id,
        "aluno_nome": dto.aluno_nome, "canal": dto.canal, "tipo": dto.tipo,
        "descricao": dto.descricao, "resultado": dto.resultado,
        "usuario_id": usuario.id, "usuario_nome": usuario.nome,
        "created_at": now
    }
    await db.contatos.insert_one(doc)
    doc.pop("_id", None)
    return doc

@router.get("")
async def listar_contatos(
    pedido_id: Optional[str] = None, aluno_id: Optional[str] = None,
    canal: Optional[str] = None, tipo: Optional[str] = None,
    limite: int = Query(50, ge=1, le=200),
    usuario: Usuario = Depends(get_current_user)
):
    query = {}
    if pedido_id:
        query["pedido_id"] = pedido_id
    if aluno_id:
        query["aluno_id"] = aluno_id
    if canal:
        query["canal"] = canal
    if tipo:
        query["tipo"] = tipo
    contatos = await db.contatos.find(query, {"_id": 0}).sort("created_at", -1).limit(limite).to_list(limite)
    return {"contatos": contatos, "total": len(contatos)}

@router.get("/retornos")
async def listar_retornos(
    limite: int = Query(20, ge=1, le=100),
    usuario: Usuario = Depends(get_current_user)
):
    """Retorna contatos com retorno agendado (atrasados e pendentes nas próximas 24h)"""
    from datetime import timedelta
    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.isoformat()
    amanha_str = (now_dt + timedelta(hours=24)).isoformat()

    # Atrasados: proximo_retorno < agora e não marcado
    atrasados_cursor = db.contatos.find(
        {"proximo_retorno": {"$lt": now_str, "$exists": True}, "retorno_realizado": {"$ne": True}},
        {"_id": 0}
    ).sort("proximo_retorno", 1).limit(limite)
    atrasados = await atrasados_cursor.to_list(limite)

    # Pendentes: proximo_retorno entre agora e amanhã
    pendentes_cursor = db.contatos.find(
        {"proximo_retorno": {"$gte": now_str, "$lte": amanha_str}, "retorno_realizado": {"$ne": True}},
        {"_id": 0}
    ).sort("proximo_retorno", 1).limit(limite)
    pendentes = await pendentes_cursor.to_list(limite)

    return {"atrasados": atrasados, "pendentes": pendentes,
            "total_atrasados": len(atrasados), "total_pendentes": len(pendentes)}


@router.post("/{contato_id}/marcar-retorno")
async def marcar_retorno(contato_id: str, usuario: Usuario = Depends(get_current_user)):
    """Marca um contato como retorno realizado"""
    now = datetime.now(timezone.utc).isoformat()
    result = await db.contatos.update_one(
        {"id": contato_id},
        {"$set": {"retorno_realizado": True, "retorno_em": now, "updated_at": now}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Contato não encontrado")
    return {"message": "Retorno marcado com sucesso"}


@router.get("/stats")
async def stats_contatos(usuario: Usuario = Depends(get_current_user)):
    """Estatísticas gerais de contatos para BI"""
    total = await db.contatos.count_documents({})
    retornos_pendentes = await db.contatos.count_documents(
        {"proximo_retorno": {"$exists": True}, "retorno_realizado": {"$ne": True}}
    )
    por_canal = {}
    pipeline = [{"$group": {"_id": "$canal", "count": {"$sum": 1}}}]
    async for r in db.contatos.aggregate(pipeline):
        por_canal[r["_id"]] = r["count"]
    return {"total_contatos": total, "retornos_pendentes": retornos_pendentes, "por_canal": por_canal}


    total = await db.contatos.count_documents({"pedido_id": pedido_id})
    pipeline = [
        {"$match": {"pedido_id": pedido_id}},
        {"$group": {"_id": "$canal", "count": {"$sum": 1}}}
    ]
    por_canal = {r["_id"]: r["count"] for r in await db.contatos.aggregate(pipeline).to_list(20)}
    ultimo = await db.contatos.find({"pedido_id": pedido_id}, {"_id": 0}).sort("created_at", -1).limit(1).to_list(1)
    return {"pedido_id": pedido_id, "total_contatos": total, "por_canal": por_canal,
            "ultimo_contato": ultimo[0] if ultimo else None}
