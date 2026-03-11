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


@router.get("/bi/completo")
async def bi_completo(usuario: Usuario = Depends(get_current_user)):
    """Dashboard BI completo - agregação de dados para Business Intelligence"""
    from datetime import datetime as dt, timezone as tz, timedelta
    now = dt.now(tz.utc)

    # Matrículas (pedidos)
    total_pedidos = await db.pedidos.count_documents({})
    pipeline_status = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    status_result = await db.pedidos.aggregate(pipeline_status).to_list(20)
    por_status = {r["_id"]: r["count"] for r in status_result}

    pendentes = por_status.get("pendente", 0)
    em_analise = por_status.get("em_analise", 0) + por_status.get("documentacao_pendente", 0)
    aprovados = por_status.get("aprovado", 0)
    realizados = por_status.get("realizado", 0)
    exportados = por_status.get("exportado", 0)
    cancelados = por_status.get("cancelado", 0)
    convertidos = aprovados + realizados + exportados
    taxa_conversao = round((convertidos / total_pedidos * 100) if total_pedidos > 0 else 0, 1)

    mes_inicio = now.replace(day=1, hour=0, minute=0, second=0).isoformat()
    pedidos_mes = await db.pedidos.count_documents({"created_at": {"$gte": mes_inicio}})

    # Evolução mensal (últimos 6 meses)
    evolucao_mensal = []
    MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    for i in range(5, -1, -1):
        mes_ref = (now.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        proximo_mes = (mes_ref.replace(day=28) + timedelta(days=4)).replace(day=1)
        total_mes = await db.pedidos.count_documents({
            "created_at": {"$gte": mes_ref.isoformat(), "$lt": proximo_mes.isoformat()}
        })
        conv_mes = await db.pedidos.count_documents({
            "created_at": {"$gte": mes_ref.isoformat(), "$lt": proximo_mes.isoformat()},
            "status": {"$in": ["aprovado", "realizado", "exportado"]}
        })
        evolucao_mensal.append({
            "mes_label": MESES_PT[mes_ref.month - 1],
            "total": total_mes, "convertidos": conv_mes,
            "pendentes": max(0, total_mes - conv_mes)
        })

    # Reembolsos
    total_reemb = await db.reembolsos.count_documents({})
    pipeline_reemb = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    reemb_result = await db.reembolsos.aggregate(pipeline_reemb).to_list(20)
    por_status_reemb = {r["_id"]: r["count"] for r in reemb_result}
    reemb_pendentes = por_status_reemb.get("aberto", 0) + por_status_reemb.get("em_analise", 0) + por_status_reemb.get("aguardando_dados_bancarios", 0)
    reemb_pagos = por_status_reemb.get("pago", 0)
    reemb_rejeitados = por_status_reemb.get("rejeitado", 0) + por_status_reemb.get("cancelado", 0)
    valor_total_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$valor"}}}]
    valor_result = await db.reembolsos.aggregate(valor_total_pipeline).to_list(1)
    valor_total = valor_result[0]["total"] if valor_result else 0

    # Pendências
    total_pend = await db.pendencias.count_documents({})
    pipeline_pend = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    pend_result = await db.pendencias.aggregate(pipeline_pend).to_list(20)
    por_status_pend = {r["_id"]: r["count"] for r in pend_result}
    pend_pendentes = por_status_pend.get("pendente", 0) + por_status_pend.get("enviado", 0)
    pend_resolvidas = por_status_pend.get("resolvido", 0)
    taxa_aprov_pend = round((pend_resolvidas / total_pend * 100) if total_pend > 0 else 0, 1)

    # Contatos
    total_contatos = await db.contatos.count_documents({})
    retornos_pendentes = await db.contatos.count_documents(
        {"proximo_retorno": {"$exists": True}, "retorno_realizado": {"$ne": True}}
    )

    return {
        "matriculas": {
            "total": total_pedidos, "pendentes": pendentes, "em_analise": em_analise,
            "aprovados": aprovados, "realizados": realizados, "exportados": exportados,
            "cancelados": cancelados, "taxa_conversao": taxa_conversao,
            "por_status": por_status
        },
        "evolucao_mensal": evolucao_mensal,
        "reembolsos": {
            "total": total_reemb, "pendentes": reemb_pendentes,
            "pagos": reemb_pagos, "rejeitados": reemb_rejeitados,
            "valor_total": round(valor_total, 2),
            "por_status": por_status_reemb
        },
        "pendencias": {
            "total": total_pend, "pendentes": pend_pendentes,
            "aprovados": pend_resolvidas, "taxa_aprovacao": taxa_aprov_pend,
            "por_status": por_status_pend
        },
        "resumo": {
            "total_matriculas": total_pedidos, "matriculas_mes": pedidos_mes,
            "taxa_conversao": taxa_conversao, "pendencias_abertas": pend_pendentes,
            "reembolsos_pendentes": reemb_pendentes,
            "retornos_pendentes": retornos_pendentes,
            "total_contatos": total_contatos
        }
    }


@router.get("/bi/matriculas")
async def bi_matriculas(usuario: Usuario = Depends(get_current_user)):
    """BI de matrículas simplificado"""
    total = await db.pedidos.count_documents({})
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.pedidos.aggregate(pipeline).to_list(20)
    por_status = {r["_id"]: r["count"] for r in result}
    return {"total": total, "por_status": por_status}


@router.get("/bi/reembolsos")
async def bi_reembolsos(usuario: Usuario = Depends(get_current_user)):
    total = await db.reembolsos.count_documents({})
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.reembolsos.aggregate(pipeline).to_list(20)
    return {"total": total, "por_status": {r["_id"]: r["count"] for r in result}}


@router.get("/bi/pendencias")
async def bi_pendencias(usuario: Usuario = Depends(get_current_user)):
    total = await db.pendencias.count_documents({})
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.pendencias.aggregate(pipeline).to_list(20)
    return {"total": total, "por_status": {r["_id"]: r["count"] for r in result}}


@router.get("/bi/evolucao")
async def bi_evolucao(meses: int = 6, usuario: Usuario = Depends(get_current_user)):
    from datetime import datetime as dt, timezone as tz, timedelta
    now = dt.now(tz.utc)
    MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    evolucao = []
    for i in range(meses - 1, -1, -1):
        mes_ref = (now.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        proximo_mes = (mes_ref.replace(day=28) + timedelta(days=4)).replace(day=1)
        total = await db.pedidos.count_documents({
            "created_at": {"$gte": mes_ref.isoformat(), "$lt": proximo_mes.isoformat()}
        })
        evolucao.append({"mes_label": MESES_PT[mes_ref.month - 1], "total": total})
    return evolucao


@router.get("/stats/resumo")
async def stats_resumo(usuario: Usuario = Depends(get_current_user)):
    total = await db.pendencias.count_documents({})
    pendentes = await db.pendencias.count_documents({"status": "pendente"})
    return {"total": total, "pendentes": pendentes}


@router.get("/status")
async def listar_status_doc(usuario: Usuario = Depends(get_current_user)):
    return {"status": STATUS_DOC}


@router.get("/prioridades")
async def listar_prioridades(usuario: Usuario = Depends(get_current_user)):
    return {"prioridades": ["baixa", "normal", "alta", "urgente"]}


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
