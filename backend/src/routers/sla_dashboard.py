"""Router SLA Dashboard - MongoDB version"""
from fastapi import APIRouter
from datetime import datetime, timezone, timedelta

from src.infrastructure.persistence.mongodb import db
from src.services.metricas_sla_service import (
    get_tipos_processo_seletivo, SLA_CONFIG, TIPOS_PS_INFO
)

router = APIRouter(prefix="/sla", tags=["Dashboard SLA"])


@router.get("/dashboard")
async def get_dashboard_sla():
    now = datetime.now(timezone.utc)
    # Resumo geral
    total = await db.pedidos.count_documents({})
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.pedidos.aggregate(pipeline).to_list(20)
    por_status = {r["_id"]: r["count"] for r in result}

    mes_inicio = now.replace(day=1, hour=0, minute=0, second=0).isoformat()
    pedidos_mes = await db.pedidos.count_documents({"created_at": {"$gte": mes_inicio}})

    aprovados = por_status.get("aprovado", 0) + por_status.get("realizado", 0) + por_status.get("exportado", 0)
    taxa = round((aprovados / total * 100) if total > 0 else 0, 1)

    # Produtividade
    produtividade = []
    resp_pipeline = [
        {"$match": {"responsavel_id": {"$ne": None}}},
        {"$group": {"_id": {"rid": "$responsavel_id", "rnome": "$responsavel_nome", "status": "$status"}, "total": {"$sum": 1}}}
    ]
    resp_result = await db.pedidos.aggregate(resp_pipeline).to_list(200)
    resp_map = {}
    for r in resp_result:
        uid = r["_id"]["rid"]
        if uid not in resp_map:
            resp_map[uid] = {"nome": r["_id"]["rnome"], "total": 0, "concluidos": 0, "pendentes": 0}
        resp_map[uid]["total"] += r["total"]
        if r["_id"]["status"] in ("aprovado", "realizado", "exportado"):
            resp_map[uid]["concluidos"] += r["total"]
        elif r["_id"]["status"] in ("pendente", "em_analise", "documentacao_pendente"):
            resp_map[uid]["pendentes"] += r["total"]
    produtividade = sorted(resp_map.values(), key=lambda x: x["total"], reverse=True)

    # Alertas
    limite_48h = (now - timedelta(hours=48)).isoformat()
    alertas_count = await db.pedidos.count_documents({
        "updated_at": {"$lt": limite_48h}, "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}
    })

    return {
        "resumo_geral": {
            "total_pedidos": total, "pedidos_mes": pedidos_mes,
            "aprovados": aprovados, "taxa_aprovacao": taxa,
            "por_status": por_status
        },
        "produtividade_atendentes": produtividade,
        "alertas": {"total_atrasados": alertas_count},
        "generated_at": now.isoformat()
    }


@router.get("/resumo")
async def get_resumo():
    total = await db.pedidos.count_documents({})
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.pedidos.aggregate(pipeline).to_list(20)
    return {"total": total, "por_status": {r["_id"]: r["count"] for r in result}}


@router.get("/por-status")
async def get_por_status():
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.pedidos.aggregate(pipeline).to_list(20)
    return [{"status": r["_id"], "total": r["count"]} for r in result]


@router.get("/produtividade")
async def get_produtividade():
    pipeline = [
        {"$match": {"responsavel_id": {"$ne": None}}},
        {"$group": {"_id": {"rid": "$responsavel_id", "rnome": "$responsavel_nome"}, "total": {"$sum": 1}}}
    ]
    result = await db.pedidos.aggregate(pipeline).to_list(100)
    return [{"nome": r["_id"]["rnome"], "total": r["total"]} for r in result]


@router.get("/por-tipo-ps")
async def get_por_tipo_ps():
    pipeline = [
        {"$match": {"tipo_processo_seletivo": {"$ne": None}}},
        {"$group": {"_id": "$tipo_processo_seletivo", "total": {"$sum": 1}}}
    ]
    result = await db.pedidos.aggregate(pipeline).to_list(20)
    return [{"tipo": r["_id"], "total": r["count"]} for r in result] if result else []


@router.get("/evolucao")
async def get_evolucao():
    now = datetime.now(timezone.utc)
    semanas = []
    for i in range(3, -1, -1):
        inicio = (now - timedelta(weeks=i+1)).isoformat()
        fim = (now - timedelta(weeks=i)).isoformat()
        count = await db.pedidos.count_documents({"created_at": {"$gte": inicio, "$lt": fim}})
        semanas.append({"semana": f"Semana {4-i}", "total": count})
    return semanas


@router.get("/alertas")
async def get_alertas():
    now = datetime.now(timezone.utc)
    limite = (now - timedelta(hours=48)).isoformat()
    atrasados = await db.pedidos.find(
        {"updated_at": {"$lt": limite}, "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}},
        {"_id": 0, "id": 1, "numero_protocolo": 1, "curso_nome": 1, "status": 1, "updated_at": 1}
    ).sort("updated_at", 1).limit(20).to_list(20)
    return {"total": len(atrasados), "atrasados": atrasados}


@router.get("/config")
async def get_config():
    return {"sla_por_etapa": SLA_CONFIG}

@router.get("/tipos-processo-seletivo")
async def listar_tipos_ps():
    return {"tipos": get_tipos_processo_seletivo()}
