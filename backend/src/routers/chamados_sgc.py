"""Router de Chamados SGC - MongoDB version"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/chamados-sgc", tags=["Chamados SGC"])

class ChamadoCreate(BaseModel):
    numero_ticket: str
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data_abertura: datetime
    data_previsao_inicio: Optional[datetime] = None
    data_previsao_fim: Optional[datetime] = None
    prioridade: int = 0
    critico: bool = False
    sla_horas: float = 32.0
    solicitante_nome: Optional[str] = None
    solicitante_telefone: Optional[str] = None
    solicitante_unidade: Optional[str] = None
    area: Optional[str] = None
    classificacao: Optional[str] = "Matrícula"
    produto: Optional[str] = "MATRÍCULA BMP"
    dono_produto: Optional[str] = None
    tecnico_responsavel: Optional[str] = None
    pedido_id: Optional[str] = None
    codigo_curso: Optional[str] = None
    nome_curso: Optional[str] = None
    turno: Optional[str] = None
    periodo_letivo: Optional[str] = None
    quantidade_vagas: Optional[int] = None
    modalidade: Optional[str] = None
    forma_pagamento: Optional[str] = None
    cont: Optional[str] = None
    requisito_acesso: Optional[str] = None
    empresa_nome: Optional[str] = None
    empresa_contato: Optional[str] = None
    empresa_email: Optional[str] = None
    empresa_telefone: Optional[str] = None
    data_inicio_curso: Optional[datetime] = None
    data_fim_curso: Optional[datetime] = None
    documentos_obrigatorios: Optional[str] = None

class ChamadoUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data_previsao_inicio: Optional[datetime] = None
    data_previsao_fim: Optional[datetime] = None
    data_fechamento: Optional[datetime] = None
    status: Optional[str] = None
    prioridade: Optional[int] = None
    critico: Optional[bool] = None
    sla_pausado: Optional[bool] = None
    tecnico_responsavel: Optional[str] = None
    pedido_id: Optional[str] = None
    codigo_curso: Optional[str] = None
    nome_curso: Optional[str] = None
    turno: Optional[str] = None
    periodo_letivo: Optional[str] = None
    quantidade_vagas: Optional[int] = None
    modalidade: Optional[str] = None
    forma_pagamento: Optional[str] = None

class InteracaoCreate(BaseModel):
    tipo: str = "comentario"
    conteudo: str
    visibilidade: str = "interno"

MODALIDADES_BMP = [
    {"sigla": "CAP", "nome": "Curso de Aprendizagem Profissional"},
    {"sigla": "IP", "nome": "Itinerário Profissional"},
    {"sigla": "CAI", "nome": "Curso de Aprendizagem Industrial"},
    {"sigla": "CQPH", "nome": "Curso de Qualificação Profissional"},
    {"sigla": "CQP", "nome": "Curso de Qualificação Profissional"},
]
FORMAS_PAGAMENTO = ["Empresa", "Aluno", "Gratuidade Regimental", "Gratuidade Não Regimental"]

def _iso(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    return str(val)


@router.get("")
async def listar_chamados(
    status: Optional[str] = None, prioridade: Optional[int] = None,
    critico: Optional[bool] = None, busca: Optional[str] = None,
    pagina: int = Query(1, ge=1), por_pagina: int = Query(20, ge=1, le=100),
    usuario: Usuario = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if prioridade is not None:
        query["prioridade"] = prioridade
    if critico is not None:
        query["critico"] = critico
    if busca:
        query["$or"] = [{"numero_ticket": {"$regex": busca, "$options": "i"}},
                        {"titulo": {"$regex": busca, "$options": "i"}},
                        {"nome_curso": {"$regex": busca, "$options": "i"}}]

    total = await db.chamados_sgc.count_documents(query)
    offset = (pagina - 1) * por_pagina
    docs = await db.chamados_sgc.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(por_pagina).to_list(por_pagina)

    return {"chamados": docs, "total": total,
            "paginacao": {"pagina_atual": pagina, "por_pagina": por_pagina,
                          "total_itens": total, "total_paginas": (total + por_pagina - 1) // por_pagina}}


@router.get("/dashboard")
async def dashboard_chamados(usuario: Usuario = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.chamados_sgc.aggregate(pipeline).to_list(20)
    por_status = {r["_id"]: r["count"] for r in result}
    total = sum(por_status.values())
    abertos = total - por_status.get("concluido", 0) - por_status.get("cancelado", 0)

    # critico pode ser boolean True ou int 1
    criticos = await db.chamados_sgc.count_documents(
        {"critico": {"$in": [True, 1]}, "status": {"$nin": ["concluido", "cancelado"]}}
    )

    # SLA critico: chamados com data_previsao_fim expirada e ainda abertos
    now_iso = now.isoformat()
    sla_critico = await db.chamados_sgc.count_documents({
        "data_previsao_fim": {"$lt": now_iso, "$ne": None},
        "status": {"$nin": ["concluido", "cancelado"]}
    })

    # Fechados hoje
    hoje_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    fechados_hoje = await db.chamados_sgc.count_documents({
        "updated_at": {"$gte": hoje_inicio},
        "status": "concluido"
    })

    pipeline_mod = [{"$match": {"modalidade": {"$ne": None}}},
                    {"$group": {"_id": "$modalidade", "count": {"$sum": 1}}}]
    por_modalidade = {r["_id"]: r["count"] for r in await db.chamados_sgc.aggregate(pipeline_mod).to_list(20)}

    return {"total": total, "abertos": abertos, "total_abertos": abertos,
            "criticos": criticos, "sla_critico": sla_critico,
            "fechados_hoje": fechados_hoje,
            "por_status": por_status, "por_modalidade": por_modalidade}


@router.post("", status_code=201)
async def criar_chamado(dto: ChamadoCreate, usuario: Usuario = Depends(get_current_user)):
    existing = await db.chamados_sgc.find_one({"numero_ticket": dto.numero_ticket})
    if existing:
        raise HTTPException(409, f"Chamado {dto.numero_ticket} já existe")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()), **dto.model_dump(),
        "status": "backlog", "sla_pausado": False,
        "criado_por_id": usuario.id, "criado_por_nome": usuario.nome,
        "created_at": now, "updated_at": now
    }
    # Convert datetime to isoformat
    for k in ["data_abertura", "data_previsao_inicio", "data_previsao_fim", "data_inicio_curso", "data_fim_curso"]:
        if doc.get(k) and isinstance(doc[k], datetime):
            doc[k] = doc[k].isoformat()
    await db.chamados_sgc.insert_one(doc)
    return {"id": doc["id"], "numero_ticket": doc["numero_ticket"], "message": "Chamado criado"}


@router.get("/opcoes")
async def opcoes_chamado():
    return {"modalidades": MODALIDADES_BMP, "formas_pagamento": FORMAS_PAGAMENTO,
            "status": ["backlog", "em_atendimento", "aguardando_retorno", "concluido", "cancelado"],
            "prioridades": [{"valor": 0, "label": "Normal"}, {"valor": 1, "label": "Alta"},
                           {"valor": 2, "label": "Urgente"}, {"valor": 3, "label": "Crítico"}]}


@router.get("/{chamado_id}")
async def buscar_chamado(chamado_id: str, usuario: Usuario = Depends(get_current_user)):
    doc = await db.chamados_sgc.find_one({"id": chamado_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Chamado não encontrado")
    interacoes = await db.chamados_sgc_interacoes.find({"chamado_id": chamado_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    # Retornar estrutura nested esperada pelo frontend
    return {"chamado": doc, "andamentos": [], "interacoes": interacoes}


@router.put("/{chamado_id}")
async def atualizar_chamado(chamado_id: str, dto: ChamadoUpdate, usuario: Usuario = Depends(get_current_user)):
    existing = await db.chamados_sgc.find_one({"id": chamado_id})
    if not existing:
        raise HTTPException(404, "Chamado não encontrado")

    updates = {"updated_at": datetime.now(timezone.utc).isoformat(),
               "atualizado_por_id": usuario.id, "atualizado_por_nome": usuario.nome}
    for k, v in dto.model_dump(exclude_unset=True).items():
        if v is not None:
            updates[k] = v.isoformat() if isinstance(v, datetime) else v
    await db.chamados_sgc.update_one({"id": chamado_id}, {"$set": updates})
    return {"message": "Chamado atualizado"}


@router.post("/{chamado_id}/interacoes")
async def criar_interacao(chamado_id: str, dto: InteracaoCreate, usuario: Usuario = Depends(get_current_user)):
    existing = await db.chamados_sgc.find_one({"id": chamado_id})
    if not existing:
        raise HTTPException(404, "Chamado não encontrado")
    now = datetime.now(timezone.utc).isoformat()
    interacao = {
        "id": str(uuid.uuid4()), "chamado_id": chamado_id, "tipo": dto.tipo,
        "conteudo": dto.conteudo, "visibilidade": dto.visibilidade,
        "usuario_id": usuario.id, "usuario_nome": usuario.nome, "created_at": now
    }
    await db.chamados_sgc_interacoes.insert_one(interacao)
    await db.chamados_sgc.update_one({"id": chamado_id}, {"$set": {"updated_at": now}})
    return interacao


@router.delete("/{chamado_id}")
async def deletar_chamado(chamado_id: str, usuario: Usuario = Depends(get_current_user)):
    if usuario.role.value != "admin":
        raise HTTPException(403, "Apenas admin pode deletar")
    result = await db.chamados_sgc.delete_one({"id": chamado_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Chamado não encontrado")
    await db.chamados_sgc_interacoes.delete_many({"chamado_id": chamado_id})
    return {"message": "Chamado deletado"}
