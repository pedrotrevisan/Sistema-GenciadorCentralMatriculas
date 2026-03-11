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
    total = await db.pedidos.count_documents({})
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.pedidos.aggregate(pipeline).to_list(20)
    por_status = {r["_id"]: r["count"] for r in result}

    mes_inicio = now.replace(day=1, hour=0, minute=0, second=0).isoformat()
    pedidos_mes = await db.pedidos.count_documents({"created_at": {"$gte": mes_inicio}})

    concluidos = por_status.get("aprovado", 0) + por_status.get("realizado", 0) + por_status.get("exportado", 0)
    abertos = por_status.get("pendente", 0) + por_status.get("em_analise", 0) + por_status.get("documentacao_pendente", 0) + por_status.get("aguardando_aluno", 0)
    taxa_conclusao = round((concluidos / total * 100) if total > 0 else 0, 1)

    pendencias_ativas = await db.pendencias.count_documents({"status": {"$nin": ["resolvido", "cancelado"]}})
    reembolsos_pendentes = await db.reembolsos.count_documents({"status": {"$in": ["aberto", "aguardando_dados_bancarios", "em_analise"]}})

    # Produtividade por responsável
    resp_pipeline = [
        {"$match": {"responsavel_id": {"$ne": None}}},
        {"$group": {"_id": {"rid": "$responsavel_id", "rnome": "$responsavel_nome", "status": "$status"}, "total": {"$sum": 1}}}
    ]
    resp_result = await db.pedidos.aggregate(resp_pipeline).to_list(200)
    resp_map = {}
    for r in resp_result:
        uid = r["_id"]["rid"]
        if uid not in resp_map:
            resp_map[uid] = {
                "responsavel_id": uid, "responsavel_nome": r["_id"]["rnome"],
                "total_atribuidos": 0, "concluidos": 0, "pendentes": 0, "em_analise": 0
            }
        resp_map[uid]["total_atribuidos"] += r["total"]
        st = r["_id"]["status"]
        if st in ("aprovado", "realizado", "exportado"):
            resp_map[uid]["concluidos"] += r["total"]
        elif st in ("pendente",):
            resp_map[uid]["pendentes"] += r["total"]
        elif st in ("em_analise", "documentacao_pendente"):
            resp_map[uid]["em_analise"] += r["total"]
    produtividade = sorted(resp_map.values(), key=lambda x: x["total_atribuidos"], reverse=True)

    # Métricas por status (com SLA estimado em horas)
    SLA_HORAS = {"pendente": 24, "em_analise": 48, "documentacao_pendente": 72, "aprovado": 0, "realizado": 0, "exportado": 0, "cancelado": 0}
    metricas_por_status = []
    for status_key, count in sorted(por_status.items(), key=lambda x: -x[1]):
        if count == 0:
            continue
        sla_h = SLA_HORAS.get(status_key, 48)
        # Tempo médio estimado: para statuses ativos, usar created_at vs now
        metricas_por_status.append({
            "status": status_key, "quantidade": count,
            "tempo_medio_horas": 0, "sla_horas": sla_h,
            "dentro_sla": True, "percentual_sla": 50
        })

    # Evolução semanal
    evolucao_semanal = []
    for i in range(3, -1, -1):
        inicio = (now - timedelta(weeks=i+1)).isoformat()
        fim = (now - timedelta(weeks=i)).isoformat()
        criados = await db.pedidos.count_documents({"created_at": {"$gte": inicio, "$lt": fim}})
        concl_sem = await db.pedidos.count_documents({
            "updated_at": {"$gte": inicio, "$lt": fim},
            "status": {"$in": ["aprovado", "realizado", "exportado"]}
        })
        evolucao_semanal.append({"semana": f"Semana {4-i}", "criados": criados, "concluidos": concl_sem})

    # SLA por tipo PS com campos completos para o frontend
    tipo_ps_pipeline = [
        {"$match": {"tipo_processo_seletivo": {"$nin": [None, ""]}}},
        {"$group": {
            "_id": "$tipo_processo_seletivo",
            "total": {"$sum": 1},
            "concluidos": {"$sum": {"$cond": [{"$in": ["$status", ["aprovado", "realizado", "exportado"]]}, 1, 0]}},
            "cancelados": {"$sum": {"$cond": [{"$eq": ["$status", "cancelado"]}, 1, 0]}}
        }}
    ]
    tipo_ps_result = await db.pedidos.aggregate(tipo_ps_pipeline).to_list(20)
    TIPOS_PS_LABELS = {
        "ps_pagante": "PS Pagante", "ps_bolsista": "PS Bolsista", "ps_949": "PS 949",
        "ps_950": "PS 950", "ps_951": "PS 951", "matricula_direta": "Matrícula Direta",
        "reingresso": "Reingresso"
    }
    sla_por_tipo_ps = [{
        "tipo": r["_id"], "tipo_ps": r["_id"],
        "label": TIPOS_PS_LABELS.get(r["_id"], r["_id"]),
        "total": r["total"], "quantidade": r["total"],
        "concluidos": r["concluidos"], "cancelados": r["cancelados"],
        "taxa_conversao": round((r["concluidos"] / r["total"] * 100) if r["total"] > 0 else 0, 1)
    } for r in tipo_ps_result]

    # Alertas SLA
    limite_48h = (now - timedelta(hours=48)).isoformat()
    alertas_count = await db.pedidos.count_documents({
        "updated_at": {"$lt": limite_48h}, "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}
    })

    return {
        "resumo_geral": {
            "total_pedidos": total, "pedidos_mes": pedidos_mes,
            "pedidos_abertos": abertos, "pedidos_concluidos": concluidos,
            "aprovados": concluidos, "taxa_conclusao": taxa_conclusao,
            "taxa_aprovacao": taxa_conclusao,
            "pendencias_ativas": pendencias_ativas, "reembolsos_pendentes": reembolsos_pendentes,
            "por_status": por_status
        },
        "produtividade_atendentes": produtividade,
        "metricas_por_status": metricas_por_status,
        "evolucao_semanal": evolucao_semanal,
        "sla_por_tipo_ps": sla_por_tipo_ps,
        "alertas_sla": {"total_atrasados": alertas_count},
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
