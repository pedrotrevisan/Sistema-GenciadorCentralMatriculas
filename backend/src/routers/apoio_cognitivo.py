"""Router de Apoio Cognitivo - Meu Dia e Base de Conhecimento - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, date, timedelta
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/apoio", tags=["Apoio Cognitivo"])


class TarefaCreateDTO(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    descricao: Optional[str] = None
    categoria: Optional[str] = "rotina"
    prioridade: int = Field(default=2, ge=1, le=3)
    recorrente: bool = False
    dias_semana: Optional[str] = None
    horario_sugerido: Optional[str] = None
    data_tarefa: Optional[str] = None

class TarefaUpdateDTO(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    prioridade: Optional[int] = None
    concluida: Optional[bool] = None
    horario_sugerido: Optional[str] = None
    data_tarefa: Optional[str] = None
    ordem: Optional[int] = None

class TarefaReorderDTO(BaseModel):
    tarefas: List[dict]

class ArtigoCreateDTO(BaseModel):
    titulo: str = Field(..., min_length=3)
    conteudo: str = Field(..., min_length=10)
    resumo: Optional[str] = None
    categoria: str = Field(default="procedimento")
    tags: Optional[str] = None
    icone: Optional[str] = None
    destaque: bool = False

class ArtigoUpdateDTO(BaseModel):
    titulo: Optional[str] = None
    conteudo: Optional[str] = None
    resumo: Optional[str] = None
    categoria: Optional[str] = None
    tags: Optional[str] = None
    icone: Optional[str] = None
    destaque: Optional[bool] = None

class LembreteCreateDTO(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    data_lembrete: str
    tipo: Optional[str] = "outro"
    referencia_id: Optional[str] = None
    referencia_tipo: Optional[str] = None


# ==================== MEU DIA ====================

@router.get("/meu-dia")
async def get_meu_dia(data: Optional[str] = None, usuario: Usuario = Depends(get_current_user)):
    hoje = data or date.today().isoformat()
    dia_semana = date.fromisoformat(hoje).isoweekday()

    # Tarefas do dia
    query = {"usuario_id": usuario.id, "ativo": {"$ne": False},
             "$or": [{"data_tarefa": hoje}, {"data_tarefa": None, "recorrente": True}]}
    tarefas = await db.tarefas_diarias.find(query, {"_id": 0}).sort([("ordem", 1), ("prioridade", 1)]).to_list(200)

    # =========================================================
    # LEMBRETES UNIFICADOS — combina 3 fontes em uma lista só
    # =========================================================
    todos_lembretes = []

    # Fonte 1: Lembretes explícitos criados manualmente
    inicio = f"{hoje}T00:00:00"
    fim = f"{hoje}T23:59:59"
    lembretes_raw = await db.lembretes.find(
        {"usuario_id": usuario.id, "data_lembrete": {"$gte": inicio, "$lte": fim}, "concluido": {"$ne": True}},
        {"_id": 0}
    ).sort("data_lembrete", 1).to_list(50)

    for l in lembretes_raw:
        hora = l.get("data_lembrete", "T").split("T")[1][:5] if "T" in str(l.get("data_lembrete", "")) else None
        todos_lembretes.append({
            "id": l["id"], "fonte": "lembrete", "prioridade": "normal",
            "titulo": l.get("titulo", ""), "descricao": l.get("descricao", ""),
            "horario": hora, "tipo": l.get("tipo", "lembrete")
        })

    # Fonte 2: Tarefas do dia com horário definido
    for t in tarefas:
        if t.get("horario_sugerido") and not t.get("concluida"):
            todos_lembretes.append({
                "id": f"tarefa_{t['id']}", "fonte": "tarefa", "prioridade": "normal",
                "titulo": t["titulo"], "descricao": t.get("descricao", ""),
                "horario": t.get("horario_sugerido"), "tipo": "tarefa",
                "tarefa_id": t["id"]
            })

    # Fonte 3: Alertas operacionais automáticos (admin e assistente)
    role_val = usuario.role.value if hasattr(usuario.role, 'value') else str(usuario.role)
    if role_val in ["admin", "assistente"]:
        now = datetime.now(timezone.utc)
        limite_48h = (now - timedelta(hours=48)).isoformat()
        limite_72h = (now - timedelta(hours=72)).isoformat()
        limite_5d = (now - timedelta(days=5)).isoformat()

        # Pedidos críticos parados (>48h)
        criticos = await db.pedidos.find(
            {"updated_at": {"$lt": limite_48h}, "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}},
            {"_id": 0, "id": 1, "numero_protocolo": 1, "curso_nome": 1, "updated_at": 1, "responsavel_nome": 1}
        ).sort("updated_at", 1).limit(5).to_list(5)

        for p in criticos:
            try:
                dt = datetime.fromisoformat(str(p.get("updated_at", "")).replace("Z", "+00:00"))
                horas = int((now - dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else now - dt).total_seconds() / 3600)
            except Exception:
                horas = 99
            prioridade = "critica" if horas > 72 else "alta"
            todos_lembretes.append({
                "id": f"alerta_critico_{p['id']}", "fonte": "alerta", "prioridade": prioridade,
                "titulo": f"Pedido parado há {horas}h — ação necessária",
                "descricao": f"{p.get('numero_protocolo', '')} · {p.get('curso_nome', 'Não informado')}",
                "horario": None, "tipo": "pedido_parado",
                "acao_url": f"/admin/pedido/{p['id']}"
            })

        # Reembolsos pendentes há mais de 5 dias
        reembolsos_pendentes = await db.reembolsos.find(
            {"created_at": {"$lt": limite_5d}, "status": {"$in": ["aberto", "aguardando_dados"]}},
            {"_id": 0, "id": 1, "aluno_nome": 1, "created_at": 1, "valor": 1}
        ).sort("created_at", 1).limit(3).to_list(3)

        for r in reembolsos_pendentes:
            try:
                dt = datetime.fromisoformat(str(r.get("created_at", "")).replace("Z", "+00:00"))
                dias = int((now - dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else now - dt).total_seconds() / 86400)
            except Exception:
                dias = 10
            todos_lembretes.append({
                "id": f"alerta_reembolso_{r['id']}", "fonte": "alerta", "prioridade": "alta",
                "titulo": f"Reembolso pendente há {dias} dias",
                "descricao": f"Aluno: {r.get('aluno_nome', '')}",
                "horario": None, "tipo": "reembolso_pendente",
                "acao_url": "/reembolsos"
            })

    # Ordena: lembretes com horário primeiro, depois alertas críticos, depois outros
    prioridade_ordem = {"critica": 0, "alta": 1, "normal": 2}
    fonte_ordem = {"lembrete": 0, "tarefa": 0, "alerta": 1}

    def sort_key(l):
        return (fonte_ordem.get(l["fonte"], 2), prioridade_ordem.get(l["prioridade"], 2), l.get("horario") or "99:99")

    todos_lembretes.sort(key=sort_key)

    total = len(tarefas)
    concluidas = len([t for t in tarefas if t.get("concluida")])
    progresso = round((concluidas / total * 100) if total > 0 else 0, 1)

    hora = datetime.now(timezone.utc).hour - 3
    if hora < 0: hora += 24
    saudacao = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"

    return {
        "tarefas": tarefas,
        "lembretes": todos_lembretes,           # Lista unificada para o frontend
        "lembretes_tarefas": [l for l in todos_lembretes if l["fonte"] == "tarefa"],  # compatibilidade
        "alertas_operacionais": [l for l in todos_lembretes if l["fonte"] == "alerta"],
        "estatisticas": {"total": total, "concluidas": concluidas, "pendentes": total - concluidas, "progresso": progresso},
        "data": hoje, "dia_semana": dia_semana, "saudacao": saudacao
    }


@router.post("/tarefas")
async def criar_tarefa(dto: TarefaCreateDTO, usuario: Usuario = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()), "usuario_id": usuario.id,
        "titulo": dto.titulo, "descricao": dto.descricao,
        "categoria": dto.categoria, "prioridade": dto.prioridade,
        "recorrente": dto.recorrente, "dias_semana": dto.dias_semana,
        "horario_sugerido": dto.horario_sugerido,
        "data_tarefa": dto.data_tarefa or date.today().isoformat(),
        "concluida": False, "data_conclusao": None, "ordem": 0,
        "ativo": True, "created_at": now, "updated_at": now
    }
    await db.tarefas_diarias.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/tarefas/{tarefa_id}")
async def atualizar_tarefa(tarefa_id: str, dto: TarefaUpdateDTO, usuario: Usuario = Depends(get_current_user)):
    t = await db.tarefas_diarias.find_one({"id": tarefa_id, "usuario_id": usuario.id})
    if not t:
        raise HTTPException(404, "Tarefa não encontrada")
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for k, v in dto.model_dump(exclude_unset=True).items():
        if v is not None:
            updates[k] = v
    if dto.concluida:
        updates["data_conclusao"] = datetime.now(timezone.utc).isoformat()
    await db.tarefas_diarias.update_one({"id": tarefa_id}, {"$set": updates})
    return {"message": "Tarefa atualizada"}


@router.patch("/tarefas/{tarefa_id}/toggle")
async def toggle_tarefa(tarefa_id: str, usuario: Usuario = Depends(get_current_user)):
    t = await db.tarefas_diarias.find_one({"id": tarefa_id, "usuario_id": usuario.id})
    if not t:
        raise HTTPException(404, "Tarefa não encontrada")
    nova = not t.get("concluida", False)
    updates = {"concluida": nova, "updated_at": datetime.now(timezone.utc).isoformat()}
    if nova:
        updates["data_conclusao"] = datetime.now(timezone.utc).isoformat()
    else:
        updates["data_conclusao"] = None
    await db.tarefas_diarias.update_one({"id": tarefa_id}, {"$set": updates})
    return {"concluida": nova}


@router.delete("/tarefas/{tarefa_id}")
async def deletar_tarefa(tarefa_id: str, usuario: Usuario = Depends(get_current_user)):
    result = await db.tarefas_diarias.delete_one({"id": tarefa_id, "usuario_id": usuario.id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Tarefa não encontrada")
    return {"message": "Tarefa deletada"}


@router.put("/tarefas/reorder")
async def reordenar_tarefas(dto: TarefaReorderDTO, usuario: Usuario = Depends(get_current_user)):
    for item in dto.tarefas:
        await db.tarefas_diarias.update_one({"id": item["id"], "usuario_id": usuario.id}, {"$set": {"ordem": item.get("ordem", 0)}})
    return {"message": "Tarefas reordenadas"}


# ==================== LEMBRETES ====================

@router.get("/lembretes")
async def listar_lembretes(dias: int = Query(7, ge=1, le=30), usuario: Usuario = Depends(get_current_user)):
    limite = (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()
    agora = datetime.now(timezone.utc).isoformat()
    query = {"usuario_id": usuario.id, "ativo": {"$ne": False}, "data_lembrete": {"$gte": agora, "$lte": limite}}
    docs = await db.lembretes.find(query, {"_id": 0}).sort("data_lembrete", 1).to_list(100)
    return {"lembretes": docs, "total": len(docs)}


@router.post("/lembretes")
async def criar_lembrete(dto: LembreteCreateDTO, usuario: Usuario = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()), "usuario_id": usuario.id,
        "titulo": dto.titulo, "descricao": dto.descricao,
        "data_lembrete": dto.data_lembrete, "tipo": dto.tipo,
        "referencia_id": dto.referencia_id, "referencia_tipo": dto.referencia_tipo,
        "notificado": False, "concluido": False, "ativo": True, "created_at": now
    }
    await db.lembretes.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.patch("/lembretes/{lembrete_id}/concluir")
async def concluir_lembrete(lembrete_id: str, usuario: Usuario = Depends(get_current_user)):
    result = await db.lembretes.update_one({"id": lembrete_id, "usuario_id": usuario.id},
                                            {"$set": {"concluido": True}})
    if result.matched_count == 0:
        raise HTTPException(404, "Lembrete não encontrado")
    return {"message": "Lembrete concluído"}


@router.delete("/lembretes/{lembrete_id}")
async def deletar_lembrete(lembrete_id: str, usuario: Usuario = Depends(get_current_user)):
    result = await db.lembretes.delete_one({"id": lembrete_id, "usuario_id": usuario.id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Lembrete não encontrado")
    return {"message": "Lembrete deletado"}


# ==================== BASE DE CONHECIMENTO ====================

@router.get("/conhecimento")
async def listar_artigos(
    categoria: Optional[str] = None, busca: Optional[str] = None,
    destaque: Optional[bool] = None,
    usuario: Usuario = Depends(get_current_user)
):
    query = {"ativo": {"$ne": False}}
    if categoria:
        query["categoria"] = categoria
    if destaque is not None:
        query["destaque"] = destaque
    if busca:
        query["$or"] = [{"titulo": {"$regex": busca, "$options": "i"}},
                        {"conteudo": {"$regex": busca, "$options": "i"}},
                        {"tags": {"$regex": busca, "$options": "i"}}]
    artigos = await db.artigos_conhecimento.find(query, {"_id": 0}).sort([("destaque", -1), ("ordem", 1)]).to_list(200)
    categorias = await db.artigos_conhecimento.distinct("categoria", {"ativo": {"$ne": False}})
    return {"artigos": artigos, "total": len(artigos), "categorias": categorias}


@router.get("/conhecimento/{artigo_id}")
async def buscar_artigo(artigo_id: str, usuario: Usuario = Depends(get_current_user)):
    artigo = await db.artigos_conhecimento.find_one({"id": artigo_id}, {"_id": 0})
    if not artigo:
        raise HTTPException(404, "Artigo não encontrado")
    await db.artigos_conhecimento.update_one({"id": artigo_id}, {"$inc": {"visualizacoes": 1}})
    return artigo


@router.post("/conhecimento", status_code=201)
async def criar_artigo(dto: ArtigoCreateDTO, usuario: Usuario = Depends(get_current_user)):
    if usuario.role.value not in ("admin",):
        raise HTTPException(403, "Sem permissão")
    now = datetime.now(timezone.utc).isoformat()
    # Converte tags de string CSV para array
    tags_list = [t.strip() for t in dto.tags.split(',') if t.strip()] if dto.tags else []
    doc = {
        "id": str(uuid.uuid4()), "titulo": dto.titulo, "conteudo": dto.conteudo,
        "resumo": dto.resumo, "categoria": dto.categoria, "tags": tags_list,
        "icone": dto.icone, "destaque": dto.destaque, "ordem": 0,
        "visualizacoes": 0, "criado_por_id": usuario.id, "criado_por_nome": usuario.nome,
        "ativo": True, "created_at": now, "updated_at": now
    }
    await db.artigos_conhecimento.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/conhecimento/{artigo_id}")
async def atualizar_artigo(artigo_id: str, dto: ArtigoUpdateDTO, usuario: Usuario = Depends(get_current_user)):
    if usuario.role.value not in ("admin",):
        raise HTTPException(403, "Sem permissão")
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for k, v in dto.model_dump(exclude_unset=True).items():
        if v is not None:
            # Converte tags de string CSV para array
            if k == "tags" and isinstance(v, str):
                updates[k] = [t.strip() for t in v.split(',') if t.strip()]
            else:
                updates[k] = v
    result = await db.artigos_conhecimento.update_one({"id": artigo_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(404, "Artigo não encontrado")
    return {"message": "Artigo atualizado"}


@router.delete("/conhecimento/{artigo_id}")
async def deletar_artigo(artigo_id: str, usuario: Usuario = Depends(get_current_user)):
    if usuario.role.value not in ("admin",):
        raise HTTPException(403, "Sem permissão")
    result = await db.artigos_conhecimento.update_one({"id": artigo_id}, {"$set": {"ativo": False}})
    if result.matched_count == 0:
        raise HTTPException(404, "Artigo não encontrado")
    return {"message": "Artigo desativado"}


@router.get("/conhecimento/categorias/lista")
async def listar_categorias(usuario: Usuario = Depends(get_current_user)):
    return {"categorias": [
        {"value": "procedimento", "label": "Procedimento", "icone": "clipboard-list"},
        {"value": "faq", "label": "FAQ", "icone": "help-circle"},
        {"value": "documento", "label": "Documento", "icone": "file-text"},
        {"value": "dica", "label": "Dica", "icone": "lightbulb"},
        {"value": "regra", "label": "Regra de Negócio", "icone": "shield"},
        {"value": "fluxo", "label": "Fluxo de Trabalho", "icone": "git-branch"}
    ]}
