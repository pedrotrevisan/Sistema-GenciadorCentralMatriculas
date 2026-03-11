"""Router de Produtividade - MongoDB version"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging

from src.infrastructure.persistence.mongodb import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/produtividade", tags=["Produtividade"])


@router.get("/dashboard")
async def get_dashboard_produtividade(
    periodo: Optional[str] = Query("30d", description="Período: 7d, 15d, 30d, 90d, all")
):
    now = datetime.now(timezone.utc)
    if periodo == "7d":
        data_inicio = (now - timedelta(days=7)).isoformat()
        label = "Últimos 7 dias"
    elif periodo == "15d":
        data_inicio = (now - timedelta(days=15)).isoformat()
        label = "Últimos 15 dias"
    elif periodo == "90d":
        data_inicio = (now - timedelta(days=90)).isoformat()
        label = "Últimos 90 dias"
    elif periodo == "all":
        data_inicio = "2020-01-01T00:00:00"
        label = "Todo o período"
    else:
        data_inicio = (now - timedelta(days=30)).isoformat()
        label = "Últimos 30 dias"

    # Users
    usuarios = await db.usuarios.find({"ativo": True, "role": {"$in": ["admin", "assistente"]}}, {"_id": 0}).to_list(100)
    usuarios_map = {u["id"]: {"nome": u["nome"], "email": u.get("email"), "role": u.get("role")} for u in usuarios}

    # Pedidos by consultor
    pipeline_pedidos = [
        {"$match": {"created_at": {"$gte": data_inicio}}},
        {"$group": {"_id": {"cid": "$consultor_id", "cnome": "$consultor_nome"}, "total": {"$sum": 1}}}
    ]
    pedidos_result = await db.pedidos.aggregate(pipeline_pedidos).to_list(100)
    pedidos_por_consultor = {r["_id"]["cid"]: {"nome": r["_id"]["cnome"], "total": r["total"]} for r in pedidos_result}

    # Auditorias by user
    pipeline_aud = [
        {"$match": {"timestamp": {"$gte": data_inicio}}},
        {"$group": {"_id": {"uid": "$usuario_id", "acao": "$acao"}, "total": {"$sum": 1}}}
    ]
    aud_result = await db.auditoria.aggregate(pipeline_aud).to_list(200)
    auditorias_por_usuario = {}
    for r in aud_result:
        uid = r["_id"]["uid"]
        if uid not in auditorias_por_usuario:
            auditorias_por_usuario[uid] = {}
        auditorias_por_usuario[uid][r["_id"]["acao"]] = r["total"]

    # Responsavel
    pipeline_resp = [
        {"$match": {"responsavel_id": {"$ne": None}, "updated_at": {"$gte": data_inicio}}},
        {"$group": {"_id": {"rid": "$responsavel_id", "rnome": "$responsavel_nome", "status": "$status"}, "total": {"$sum": 1}}}
    ]
    resp_result = await db.pedidos.aggregate(pipeline_resp).to_list(200)
    responsavel_data = {}
    for r in resp_result:
        uid = r["_id"]["rid"]
        if uid not in responsavel_data:
            responsavel_data[uid] = {"nome": r["_id"]["rnome"], "total": 0, "concluidos": 0}
        responsavel_data[uid]["total"] += r["total"]
        if r["_id"]["status"] in ("aprovado", "realizado", "exportado"):
            responsavel_data[uid]["concluidos"] += r["total"]

    # Reembolsos by user
    pipeline_reemb = [
        {"$match": {"responsavel_id": {"$ne": None}, "updated_at": {"$gte": data_inicio}}},
        {"$group": {"_id": {"rid": "$responsavel_id", "rnome": "$responsavel_nome", "status": "$status"}, "total": {"$sum": 1}}}
    ]
    reemb_result = await db.reembolsos.aggregate(pipeline_reemb).to_list(100)
    reembolsos_data = {}
    for r in reemb_result:
        uid = r["_id"]["rid"]
        if uid not in reembolsos_data:
            reembolsos_data[uid] = {"nome": r["_id"]["rnome"], "total": 0, "concluidos": 0}
        reembolsos_data[uid]["total"] += r["total"]
        if r["_id"]["status"] in ("pago", "concluido"):
            reembolsos_data[uid]["concluidos"] += r["total"]

    # Build members
    all_ids = set(usuarios_map.keys()) | set(pedidos_por_consultor.keys())
    membros = []
    for uid in all_ids:
        info = usuarios_map.get(uid, {})
        nome = info.get("nome") or pedidos_por_consultor.get(uid, {}).get("nome", "Desconhecido")
        role = info.get("role", "")
        pc = pedidos_por_consultor.get(uid, {}).get("total", 0)
        audits = auditorias_por_usuario.get(uid, {})
        total_aud = sum(audits.values())
        resp = responsavel_data.get(uid, {"total": 0, "concluidos": 0})
        reemb = reembolsos_data.get(uid, {"total": 0, "concluidos": 0})
        total_acoes = pc + total_aud + resp["total"] + reemb["total"]

        membros.append({
            "usuario_id": uid, "nome": nome, "role": role,
            "pedidos_criados": pc, "alteracoes_status": audits.get("ATUALIZACAO_STATUS", 0),
            "total_auditorias": total_aud, "pedidos_atribuidos": resp["total"],
            "pedidos_concluidos": resp["concluidos"], "reembolsos_tratados": reemb["total"],
            "reembolsos_concluidos": reemb["concluidos"], "total_acoes": total_acoes
        })
    membros.sort(key=lambda x: x["total_acoes"], reverse=True)

    # KPIs
    total_pedidos = await db.pedidos.count_documents({"created_at": {"$gte": data_inicio}})
    total_aprovados = await db.pedidos.count_documents({"created_at": {"$gte": data_inicio}, "status": {"$in": ["aprovado", "realizado", "exportado"]}})
    total_reembolsos = await db.reembolsos.count_documents({"created_at": {"$gte": data_inicio}})
    total_auds = await db.auditoria.count_documents({"timestamp": {"$gte": data_inicio}})

    dias_periodo = max((now - datetime.fromisoformat(data_inicio).replace(tzinfo=timezone.utc)).days, 1)
    media_diaria = round(total_pedidos / dias_periodo, 1)

    # Daily evolution
    dias_evolucao = min(dias_periodo, 14)
    evolucao = []
    for i in range(dias_evolucao - 1, -1, -1):
        dia = now - timedelta(days=i)
        dia_inicio = dia.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        dia_fim = dia.replace(hour=23, minute=59, second=59).isoformat()
        p_count = await db.pedidos.count_documents({"created_at": {"$gte": dia_inicio, "$lte": dia_fim}})
        a_count = await db.auditoria.count_documents({"timestamp": {"$gte": dia_inicio, "$lte": dia_fim}})
        evolucao.append({"data": dia.strftime("%d/%m"), "pedidos": p_count, "acoes": a_count})

    return {
        "periodo": label,
        "kpis": {"total_pedidos": total_pedidos, "total_aprovados": total_aprovados,
                 "total_reembolsos": total_reembolsos, "total_auditorias": total_auds,
                 "media_diaria_pedidos": media_diaria,
                 "membros_ativos": len([m for m in membros if m["total_acoes"] > 0])},
        "membros": membros, "evolucao_diaria": evolucao, "generated_at": now.isoformat()
    }
