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

CANAIS_CONTATO = ["ligacao", "whatsapp", "email", "presencial", "sms", "outro"]
TIPOS_CONTATO = ["primeiro_contato", "retorno", "cobranca_documento", "informacao", "cancelamento", "outros"]

TIPOS_CONTATO_OPCOES = [
    {"value": "ligacao", "label": "Ligação Telefônica"},
    {"value": "whatsapp", "label": "WhatsApp"},
    {"value": "email", "label": "E-mail"},
    {"value": "presencial", "label": "Presencial"},
    {"value": "sms", "label": "SMS"},
    {"value": "outro", "label": "Outro"},
]

RESULTADOS_CONTATO_OPCOES = [
    {"value": "sucesso", "label": "Contato realizado com sucesso"},
    {"value": "nao_atendeu", "label": "Não atendeu"},
    {"value": "sem_resposta", "label": "Sem resposta"},
    {"value": "caixa_postal", "label": "Caiu na caixa postal"},
    {"value": "numero_errado", "label": "Número errado/inválido"},
    {"value": "agendado", "label": "Retorno agendado"},
    {"value": "pendente", "label": "Pendente de retorno"},
]

MOTIVOS_CONTATO_OPCOES = [
    {"value": "cobranca_documentos", "label": "Cobrança de Documentos"},
    {"value": "informacao_matricula", "label": "Informação sobre Matrícula"},
    {"value": "retorno_pendencia", "label": "Retorno de Pendência"},
    {"value": "confirmacao_vaga", "label": "Confirmação de Vaga"},
    {"value": "orientacao_acesso", "label": "Orientação de Acesso ao Sistema"},
    {"value": "cancelamento", "label": "Cancelamento de Matrícula"},
    {"value": "reagendamento", "label": "Reagendamento"},
    {"value": "reembolso", "label": "Reembolso"},
    {"value": "outro", "label": "Outro"},
]

class RegistrarContatoDTO(BaseModel):
    pedido_id: Optional[str] = None
    aluno_id: Optional[str] = None
    aluno_nome: Optional[str] = None
    canal: Optional[str] = None      # legado
    tipo: str                         # canal de contato (ligacao, whatsapp, etc.)
    resultado: Optional[str] = None
    motivo: Optional[str] = None
    descricao: str
    contato_nome: Optional[str] = None
    contato_telefone: Optional[str] = None
    contato_email: Optional[str] = None
    data_retorno: Optional[str] = None

class FiltroContatosDTO(BaseModel):
    pedido_id: Optional[str] = None
    aluno_id: Optional[str] = None
    canal: Optional[str] = None
    tipo: Optional[str] = None


@router.get("/canais")
async def listar_canais():
    return {"canais": CANAIS_CONTATO, "tipos": TIPOS_CONTATO}

@router.get("/tipos")
async def listar_tipos():
    return TIPOS_CONTATO_OPCOES

@router.get("/resultados")
async def listar_resultados():
    return RESULTADOS_CONTATO_OPCOES

@router.get("/motivos")
async def listar_motivos():
    return MOTIVOS_CONTATO_OPCOES

@router.post("")
async def registrar_contato(dto: RegistrarContatoDTO, usuario: Usuario = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()), "pedido_id": dto.pedido_id, "aluno_id": dto.aluno_id,
        "aluno_nome": dto.aluno_nome or "", "canal": dto.tipo,  # tipo = canal de contato
        "tipo": dto.tipo, "resultado": dto.resultado, "motivo": dto.motivo,
        "descricao": dto.descricao,
        "contato_nome": dto.contato_nome, "contato_telefone": dto.contato_telefone,
        "contato_email": dto.contato_email, "data_retorno": dto.data_retorno,
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
