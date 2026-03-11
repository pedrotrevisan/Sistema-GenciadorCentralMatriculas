"""Router de Atribuições - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/atribuicoes", tags=["Atribuições"])

class AtribuirRequest(BaseModel):
    tipo: str
    item_id: str
    responsavel_id: str
    prioridade: Optional[str] = "normal"
    observacao: Optional[str] = None

class NotificacaoRequest(BaseModel):
    destinatario_id: str
    titulo: str
    mensagem: str
    tipo: str = "info"
    link: Optional[str] = None


@router.get("/minha-caixa")
async def minha_caixa_entrada(status: Optional[str] = None, tipo: Optional[str] = None,
                               usuario: Usuario = Depends(get_current_user)):
    items = []
    if not tipo or tipo == "pedido":
        pedidos = await db.pedidos.find({"responsavel_id": usuario.id}, {"_id": 0}).sort("updated_at", -1).to_list(200)
        for p in pedidos:
            items.append({"id": p["id"], "tipo": "pedido",
                          "titulo": f"Matrícula - {p.get('numero_protocolo', 'S/N')}",
                          "descricao": p.get("curso_nome", ""), "status": p.get("status"),
                          "prioridade": p.get("prioridade", "normal"),
                          "created_at": p.get("created_at"), "updated_at": p.get("updated_at"),
                          "link": f"/pedidos/{p['id']}"})
    if not tipo or tipo == "pendencia":
        pends = await db.pendencias.find({"responsavel_id": usuario.id}, {"_id": 0}).sort("updated_at", -1).to_list(200)
        for pend in pends:
            items.append({"id": pend["id"], "tipo": "pendencia",
                          "titulo": f"Pendência - {pend.get('documento_tipo', '')}",
                          "descricao": pend.get("aluno_nome", ""), "status": pend.get("status"),
                          "prioridade": pend.get("prioridade", "normal"),
                          "created_at": pend.get("created_at"), "updated_at": pend.get("updated_at"),
                          "link": f"/pendencias/{pend['id']}"})
    if not tipo or tipo == "reembolso":
        reembs = await db.reembolsos.find({"responsavel_id": usuario.id}, {"_id": 0}).sort("updated_at", -1).to_list(200)
        for r in reembs:
            items.append({"id": r["id"], "tipo": "reembolso",
                          "titulo": f"Reembolso - {r.get('aluno_nome', '')}",
                          "descricao": r.get("curso", ""), "status": r.get("status"),
                          "prioridade": r.get("prioridade", "normal"),
                          "created_at": r.get("created_at"), "updated_at": r.get("updated_at"),
                          "link": f"/reembolsos/{r['id']}"})
    if status:
        items = [i for i in items if i["status"] == status]
    items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    pipeline_stats = [{"$match": {"responsavel_id": usuario.id}},
                      {"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    ped_stats = {r["_id"]: r["count"] for r in await db.pedidos.aggregate(pipeline_stats).to_list(20)}
    return {"items": items, "total": len(items), "estatisticas": ped_stats}


@router.post("/atribuir")
async def atribuir_item(req: AtribuirRequest, usuario: Usuario = Depends(get_current_user)):
    if usuario.role.value not in ("admin", "assistente"):
        raise HTTPException(403, "Sem permissão")
    resp = await db.usuarios.find_one({"id": req.responsavel_id}, {"_id": 0, "nome": 1})
    if not resp:
        raise HTTPException(404, "Responsável não encontrado")
    now = datetime.now(timezone.utc).isoformat()
    collection = {"pedido": "pedidos", "pendencia": "pendencias", "reembolso": "reembolsos"}.get(req.tipo)
    if not collection:
        raise HTTPException(400, f"Tipo inválido: {req.tipo}")
    result = await db[collection].update_one({"id": req.item_id}, {"$set": {
        "responsavel_id": req.responsavel_id, "responsavel_nome": resp["nome"],
        "prioridade": req.prioridade, "updated_at": now
    }})
    if result.matched_count == 0:
        raise HTTPException(404, f"{req.tipo} não encontrado")
    await db.notificacoes.insert_one({
        "id": str(uuid.uuid4()), "destinatario_id": req.responsavel_id,
        "titulo": f"Nova atribuição: {req.tipo}", "mensagem": f"{req.tipo} atribuído por {usuario.nome}",
        "tipo": "info", "link": f"/{collection}/{req.item_id}", "lida": False, "created_at": now
    })
    return {"message": f"{req.tipo.title()} atribuído para {resp['nome']}", "responsavel_nome": resp["nome"]}


@router.post("/desatribuir/{tipo}/{item_id}")
async def desatribuir(tipo: str, item_id: str, usuario: Usuario = Depends(get_current_user)):
    collection = {"pedido": "pedidos", "pendencia": "pendencias", "reembolso": "reembolsos"}.get(tipo)
    if not collection:
        raise HTTPException(400, "Tipo inválido")
    now = datetime.now(timezone.utc).isoformat()
    result = await db[collection].update_one({"id": item_id}, {"$set": {
        "responsavel_id": None, "responsavel_nome": None, "updated_at": now
    }})
    if result.matched_count == 0:
        raise HTTPException(404, f"{tipo} não encontrado")
    return {"message": f"Atribuição removida"}


@router.get("/notificacoes")
async def minhas_notificacoes(usuario: Usuario = Depends(get_current_user)):
    notifs = await db.notificacoes.find({"destinatario_id": usuario.id}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    nao_lidas = await db.notificacoes.count_documents({"destinatario_id": usuario.id, "lida": False})
    return {"notificacoes": notifs, "nao_lidas": nao_lidas, "total": len(notifs)}


@router.put("/notificacoes/{notificacao_id}/ler")
async def marcar_lida(notificacao_id: str, usuario: Usuario = Depends(get_current_user)):
    await db.notificacoes.update_one({"id": notificacao_id}, {"$set": {"lida": True}})
    return {"message": "Notificação marcada como lida"}


@router.put("/notificacoes/ler-todas")
async def marcar_todas_lidas(usuario: Usuario = Depends(get_current_user)):
    await db.notificacoes.update_many({"destinatario_id": usuario.id}, {"$set": {"lida": True}})
    return {"message": "Todas as notificações marcadas como lidas"}


@router.post("/notificacoes/enviar")
async def enviar_notificacao(req: NotificacaoRequest, usuario: Usuario = Depends(get_current_user)):
    if usuario.role.value not in ("admin",):
        raise HTTPException(403, "Sem permissão")
    now = datetime.now(timezone.utc).isoformat()
    doc = {"id": str(uuid.uuid4()), "destinatario_id": req.destinatario_id,
           "titulo": req.titulo, "mensagem": req.mensagem, "tipo": req.tipo,
           "link": req.link, "lida": False, "created_at": now}
    await db.notificacoes.insert_one(doc)
    return {"message": "Notificação enviada", "id": doc["id"]}


@router.get("/resumo")
async def resumo_caixa(usuario: Usuario = Depends(get_current_user)):
    """Resumo da caixa de entrada do usuário atual"""
    pedidos_atribuidos = await db.pedidos.count_documents({"responsavel_id": usuario.id})
    pendencias_atribuidas = await db.pendencias.count_documents({"responsavel_id": usuario.id})
    reembolsos_atribuidos = await db.reembolsos.count_documents({"responsavel_id": usuario.id})

    pedidos_pendentes = await db.pedidos.count_documents({"responsavel_id": usuario.id, "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}})
    total = pedidos_atribuidos + pendencias_atribuidas + reembolsos_atribuidos

    return {
        "total": total,
        "pedidos": pedidos_atribuidos,
        "pendencias": pendencias_atribuidas,
        "reembolsos": reembolsos_atribuidos,
        "pendentes": pedidos_pendentes,
        "usuario": usuario.nome
    }


@router.get("/responsaveis")
async def listar_responsaveis(usuario: Usuario = Depends(get_current_user)):
    users = await db.usuarios.find({"ativo": True, "role": {"$in": ["admin", "assistente"]}},
                                    {"_id": 0, "id": 1, "nome": 1, "role": 1}).sort("nome", 1).to_list(100)
    return {"responsaveis": users}
