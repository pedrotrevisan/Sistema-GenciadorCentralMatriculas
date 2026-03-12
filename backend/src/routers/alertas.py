"""Router de Alertas - MongoDB version"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta

from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user
from src.domain.entities.usuario import Usuario

router = APIRouter(prefix="/alertas", tags=["Alertas"])


@router.get("/dashboard")
async def get_alertas_dashboard(usuario: Usuario = Depends(get_current_user)):
    alertas = []
    now = datetime.now(timezone.utc)
    limite_48h = (now - timedelta(hours=48)).isoformat()
    limite_24h = (now - timedelta(hours=24)).isoformat()
    limite_5d = (now - timedelta(days=5)).isoformat()
    hoje = now.strftime("%Y-%m-%d")

    # 1. Pedidos críticos (>48h)
    criticos = await db.pedidos.find(
        {"updated_at": {"$lt": limite_48h}, "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}},
        {"_id": 0}
    ).sort("updated_at", 1).limit(20).to_list(20)

    for p in criticos:
        try:
            horas = int((now - datetime.fromisoformat(str(p.get("updated_at", "")).replace("Z", "+00:00").replace("+00:00", "")).replace(tzinfo=timezone.utc)).total_seconds() / 3600)
        except Exception:
            horas = 99
        alertas.append({
            "id": f"critico_{p['id']}", "tipo": "critico", "prioridade": "alta",
            "icone": "alert-triangle", "cor": "red",
            "titulo": f"Pedido parado há {horas}h",
            "descricao": f"{p.get('numero_protocolo', '')} - {p.get('curso_nome', '')}",
            "detalhes": {"pedido_id": p["id"], "protocolo": p.get("numero_protocolo"), "status": p.get("status"), "horas_parado": horas},
            "acao": {"label": "Ver Pedido", "url": f"/admin/pedido/{p['id']}"},
            "created_at": p.get("updated_at")
        })

    # 2. Pedidos em risco (24-48h)
    risco = await db.pedidos.find(
        {"updated_at": {"$lt": limite_24h, "$gte": limite_48h}, "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}},
        {"_id": 0}
    ).sort("updated_at", 1).limit(10).to_list(10)

    for p in risco:
        try:
            horas = int((now - datetime.fromisoformat(str(p.get("updated_at", "")).replace("Z", "+00:00").replace("+00:00", "")).replace(tzinfo=timezone.utc)).total_seconds() / 3600)
        except Exception:
            horas = 30
        alertas.append({
            "id": f"sla_risco_{p['id']}", "tipo": "sla_risco", "prioridade": "media",
            "icone": "clock", "cor": "amber",
            "titulo": f"SLA em risco ({horas}h)",
            "descricao": f"{p.get('numero_protocolo', '')} - {p.get('curso_nome', '')}",
            "detalhes": {"pedido_id": p["id"], "protocolo": p.get("numero_protocolo"), "status": p.get("status")},
            "acao": {"label": "Ver Pedido", "url": f"/admin/pedido/{p['id']}"},
            "created_at": p.get("updated_at")
        })

    # 3. Reembolsos pendentes - MELHORADO: Se não houver antigos (>5d), mostra recentes (>2d)
    reemb_antigos = await db.reembolsos.find(
        {"created_at": {"$lt": limite_5d, "$ne": None, "$exists": True}, "status": {"$in": ["aberto", "aguardando_dados", "no_financeiro"]}},
        {"_id": 0}
    ).sort("created_at", 1).limit(10).to_list(10)
    
    # Se não há reembolsos antigos, buscar os recentes (>2 dias)
    if not reemb_antigos:
        limite_2d = (now - timedelta(days=2)).isoformat()
        reemb_antigos = await db.reembolsos.find(
            {"created_at": {"$lt": limite_2d, "$ne": None, "$exists": True}, "status": {"$in": ["aberto", "aguardando_dados", "no_financeiro"]}},
            {"_id": 0}
        ).sort("created_at", 1).limit(5).to_list(5)
    
    # Também buscar reembolsos pendentes SEM created_at (considerados antigos)
    reemb_sem_data = await db.reembolsos.find(
        {"$or": [{"created_at": None}, {"created_at": {"$exists": False}}], "status": {"$in": ["aberto", "aguardando_dados", "no_financeiro"]}},
        {"_id": 0}
    ).limit(10).to_list(10)
    
    reemb = reemb_antigos + reemb_sem_data

    for r in reemb:
        try:
            dt_str = r.get("created_at")
            if dt_str:
                dias = int((now - datetime.fromisoformat(str(dt_str).replace("Z", "+00:00").replace("+00:00", "")).replace(tzinfo=timezone.utc)).total_seconds() / 86400)
            else:
                dias = 10  # Assume 10 dias se não tem data
        except Exception:
            dias = 10
        alertas.append({
            "id": f"reembolso_{r['id']}", "tipo": "reembolso",
            "prioridade": "media" if dias < 10 else "alta",
            "icone": "dollar-sign", "cor": "orange",
            "titulo": f"Reembolso pendente" + (f" há {dias} dias" if r.get("created_at") else " (sem data)"),
            "descricao": f"{r.get('aluno_nome', '')} - {r.get('curso', '')}",
            "detalhes": {"reembolso_id": r["id"], "status": r.get("status"), "dias_pendente": dias},
            "acao": {"label": "Ver Reembolso", "url": f"/reembolsos?id={r['id']}"},
            "created_at": r.get("created_at")
        })

    # 4. Turmas lotando (>= 90%)
    turmas = await db.painel_turmas.find({"status": {"$ne": "cancelado"}}, {"_id": 0}).to_list(200)
    for t in turmas:
        total = t.get("vagas_totais", 0)
        ocupadas = t.get("vagas_ocupadas", 0)
        if total > 0:
            ocupacao = (ocupadas / total) * 100
            if ocupacao >= 90:
                alertas.append({
                    "id": f"vagas_{t['id']}", "tipo": "vagas",
                    "prioridade": "alta" if ocupacao >= 95 else "media",
                    "icone": "graduation-cap", "cor": "purple",
                    "titulo": f"Turma quase lotada ({ocupacao:.0f}%)",
                    "descricao": f"{t.get('nome_curso', '')} - {total - ocupadas} vaga(s)",
                    "detalhes": {"turma_id": t["id"], "ocupacao": ocupacao},
                    "acao": {"label": "Ver Painel", "url": "/painel-vagas"},
                    "created_at": None
                })

    # 5. NOVO: Tarefas com horário passado (não concluídas)
    tarefas_atrasadas = await db.tarefas_diarias.find({
        "usuario_id": usuario.id,
        "concluida": False,
        "ativo": {"$ne": False},
        "data_tarefa": hoje,
        "horario_sugerido": {"$ne": None, "$ne": ""}
    }, {"_id": 0}).to_list(20)
    
    hora_atual = now.strftime("%H:%M")
    for t in tarefas_atrasadas:
        horario = t.get("horario_sugerido", "")
        if horario and horario < hora_atual:
            alertas.append({
                "id": f"tarefa_atrasada_{t['id']}", "tipo": "tarefa",
                "prioridade": "media",
                "icone": "check-circle", "cor": "blue",
                "titulo": f"Tarefa atrasada: {horario}",
                "descricao": t.get("titulo", ""),
                "detalhes": {"tarefa_id": t["id"]},
                "acao": {"label": "Ver Tarefa", "url": "/meu-dia"},
                "created_at": None
            })

    # 6. NOVO: Lembretes do dia não concluídos
    lembretes_hoje = await db.lembretes.find({
        "usuario_id": usuario.id,
        "concluido": False,
        "ativo": {"$ne": False},
        "data_lembrete": {"$regex": f"^{hoje}"}
    }, {"_id": 0}).to_list(10)
    
    for l in lembretes_hoje:
        alertas.append({
            "id": f"lembrete_{l['id']}", "tipo": "lembrete",
            "prioridade": "media",
            "icone": "bell", "cor": "purple",
            "titulo": f"Lembrete: {l.get('titulo', '')}",
            "descricao": l.get("descricao", ""),
            "detalhes": {"lembrete_id": l["id"]},
            "acao": {"label": "Ver Meu Dia", "url": "/meu-dia"},
            "created_at": l.get("data_lembrete")
        })

    # 7. NOVO: Pendências urgentes (alta prioridade não resolvidas)
    pendencias_urgentes = await db.pendencias.find({
        "status": {"$in": ["pendente", "aguardando_aluno"]},
        "prioridade": "alta"
    }, {"_id": 0}).limit(10).to_list(10)
    
    for p in pendencias_urgentes:
        alertas.append({
            "id": f"pendencia_{p['id']}", "tipo": "pendencia",
            "prioridade": "alta",
            "icone": "file-text", "cor": "red",
            "titulo": f"Pendência urgente",
            "descricao": f"{p.get('aluno_nome', '')} - {p.get('tipo_documento', '')}",
            "detalhes": {"pendencia_id": p["id"]},
            "acao": {"label": "Ver Pendências", "url": "/pendencias"},
            "created_at": p.get("created_at")
        })

    prioridade_ordem = {"alta": 0, "media": 1, "baixa": 2}
    alertas.sort(key=lambda x: prioridade_ordem.get(x["prioridade"], 2))

    stats = {
        "total": len(alertas),
        "criticos": len([a for a in alertas if a["tipo"] == "critico"]),
        "sla_risco": len([a for a in alertas if a["tipo"] == "sla_risco"]),
        "reembolsos": len([a for a in alertas if a["tipo"] == "reembolso"]),
        "vagas": len([a for a in alertas if a["tipo"] == "vagas"]),
        "tarefas": len([a for a in alertas if a["tipo"] == "tarefa"]),
        "lembretes": len([a for a in alertas if a["tipo"] == "lembrete"]),
        "pendencias": len([a for a in alertas if a["tipo"] == "pendencia"])
    }
    return {"alertas": alertas, "estatisticas": stats, "generated_at": now.isoformat()}


@router.get("/contagem")
async def get_contagem_alertas():
    now = datetime.now(timezone.utc)
    limite_48h = (now - timedelta(hours=48)).isoformat()
    limite_24h = (now - timedelta(hours=24)).isoformat()
    limite_5d = (now - timedelta(days=5)).isoformat()

    criticos = await db.pedidos.count_documents(
        {"updated_at": {"$lt": limite_48h}, "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}}
    )
    risco = await db.pedidos.count_documents(
        {"updated_at": {"$lt": limite_24h, "$gte": limite_48h}, "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}}
    )
    reembolsos = await db.reembolsos.count_documents(
        {"created_at": {"$lt": limite_5d}, "status": {"$in": ["aberto", "aguardando_dados", "no_financeiro"]}}
    )
    return {"total": criticos + risco + reembolsos, "criticos": criticos, "sla_risco": risco, "reembolsos": reembolsos}
