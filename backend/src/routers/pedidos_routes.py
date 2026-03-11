"""Router de Pedidos - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import logging

from src.domain.entities import Usuario, PedidoMatricula, Aluno
from src.domain.value_objects import StatusPedido, CPF, Email, Telefone
from src.infrastructure.persistence.mongodb import db
from src.infrastructure.exporters.exportador_totvs import ExportadorXLSXTOTVS, ExportadorCSVTOTVS
from src.application.dtos.request import CriarPedidoDTO, AtualizarStatusDTO, FiltrosPedidoDTO
from src.application.dtos.response import (
    PedidoResponseDTO, ListaPedidosResponseDTO, PaginacaoDTO, AlunoResponseDTO
)
from src.routers.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

STATUS_LABELS = {
    "pendente": "Pendente", "em_analise": "Em Análise",
    "documentacao_pendente": "Documentação Pendente",
    "aprovado": "Aprovado", "rejeitado": "Rejeitado",
    "realizado": "Realizado", "cancelado": "Cancelado", "exportado": "Exportado"
}


def _build_pedido_response(pedido_doc, alunos_docs) -> dict:
    """Build PedidoResponseDTO dict from MongoDB documents"""
    status_val = pedido_doc.get("status", "pendente")
    alunos_response = []
    for a in alunos_docs:
        cpf_val = a.get("cpf", "")
        tel_val = a.get("telefone", "")
        alunos_response.append({
            "id": a["id"], "nome": a["nome"], "cpf": cpf_val,
            "cpf_formatado": f"{cpf_val[:3]}.{cpf_val[3:6]}.{cpf_val[6:9]}-{cpf_val[9:]}" if len(cpf_val) == 11 else cpf_val,
            "email": a.get("email", ""), "telefone": tel_val,
            "telefone_formatado": tel_val,
            "data_nascimento": str(a.get("data_nascimento", "")),
            "rg": a.get("rg", ""), "rg_orgao_emissor": a.get("rg_orgao_emissor", ""),
            "rg_uf": a.get("rg_uf", ""),
            "rg_data_emissao": a.get("rg_data_emissao"),
            "naturalidade": a.get("naturalidade"), "naturalidade_uf": a.get("naturalidade_uf"),
            "sexo": a.get("sexo"), "cor_raca": a.get("cor_raca"),
            "grau_instrucao": a.get("grau_instrucao"),
            "nome_pai": a.get("nome_pai"), "nome_mae": a.get("nome_mae"),
            "endereco_cep": a.get("endereco_cep", ""),
            "endereco_logradouro": a.get("endereco_logradouro", ""),
            "endereco_numero": a.get("endereco_numero", ""),
            "endereco_complemento": a.get("endereco_complemento"),
            "endereco_bairro": a.get("endereco_bairro", ""),
            "endereco_cidade": a.get("endereco_cidade", ""),
            "endereco_uf": a.get("endereco_uf", "")
        })

    pode_editar = status_val in ("pendente", "em_analise", "documentacao_pendente")

    return {
        "id": pedido_doc["id"],
        "numero_protocolo": pedido_doc.get("numero_protocolo"),
        "consultor_id": pedido_doc["consultor_id"],
        "consultor_nome": pedido_doc["consultor_nome"],
        "curso_id": pedido_doc["curso_id"],
        "curso_nome": pedido_doc["curso_nome"],
        "projeto_id": pedido_doc.get("projeto_id"),
        "projeto_nome": pedido_doc.get("projeto_nome"),
        "empresa_id": pedido_doc.get("empresa_id"),
        "empresa_nome": pedido_doc.get("empresa_nome"),
        "alunos": alunos_response,
        "status": status_val,
        "status_label": STATUS_LABELS.get(status_val, status_val),
        "observacoes": pedido_doc.get("observacoes"),
        "motivo_rejeicao": pedido_doc.get("motivo_rejeicao"),
        "data_exportacao": str(pedido_doc["data_exportacao"]) if pedido_doc.get("data_exportacao") else None,
        "exportado_por": pedido_doc.get("exportado_por"),
        "created_at": str(pedido_doc.get("created_at", "")),
        "updated_at": str(pedido_doc.get("updated_at", "")),
        "pode_editar": pode_editar,
        "pode_exportar": status_val == "realizado",
        "total_alunos": len(alunos_response)
    }


async def _gerar_protocolo():
    ano = datetime.now().year
    prefixo = f"CM-{ano}-"
    last = await db.pedidos.find(
        {"numero_protocolo": {"$regex": f"^{prefixo}"}},
        {"numero_protocolo": 1, "_id": 0}
    ).sort("numero_protocolo", -1).limit(1).to_list(1)

    if last:
        try:
            num = int(last[0]["numero_protocolo"].split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"{prefixo}{num:04d}"


@router.post("", response_model=dict)
async def criar_pedido(request: CriarPedidoDTO, current_user: Usuario = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    pedido_id = str(uuid.uuid4())
    protocolo = await _gerar_protocolo()

    pedido_doc = {
        "id": pedido_id, "numero_protocolo": protocolo,
        "consultor_id": current_user.id, "consultor_nome": current_user.nome,
        "curso_id": request.curso_id, "curso_nome": request.curso_nome,
        "turma_id": request.turma_id,
        "projeto_id": request.projeto_id, "projeto_nome": request.projeto_nome,
        "empresa_id": request.empresa_id, "empresa_nome": request.empresa_nome,
        "vinculo_tipo": request.vinculo_tipo,
        "status": "pendente", "observacoes": request.observacoes,
        "motivo_rejeicao": None, "data_exportacao": None, "exportado_por": None,
        "responsavel_id": None, "responsavel_nome": None, "prioridade": "normal",
        "tipo_processo_seletivo": None, "codigo_ps": None,
        "created_at": now, "updated_at": now
    }
    await db.pedidos.insert_one(pedido_doc)

    alunos_docs = []
    for a in request.alunos:
        aluno_doc = {
            "id": str(uuid.uuid4()), "pedido_id": pedido_id,
            "nome": a.nome, "cpf": a.cpf.replace(".", "").replace("-", ""),
            "email": a.email, "telefone": a.telefone,
            "data_nascimento": a.data_nascimento,
            "rg": a.rg, "rg_orgao_emissor": a.rg_orgao_emissor, "rg_uf": a.rg_uf,
            "rg_data_emissao": a.rg_data_emissao,
            "naturalidade": a.naturalidade, "naturalidade_uf": a.naturalidade_uf,
            "sexo": a.sexo, "cor_raca": a.cor_raca, "grau_instrucao": a.grau_instrucao,
            "nome_pai": a.nome_pai, "nome_mae": a.nome_mae,
            "endereco_cep": a.endereco_cep, "endereco_logradouro": a.endereco_logradouro,
            "endereco_numero": a.endereco_numero, "endereco_complemento": a.endereco_complemento,
            "endereco_bairro": a.endereco_bairro, "endereco_cidade": a.endereco_cidade,
            "endereco_uf": a.endereco_uf,
            "created_at": now, "updated_at": now
        }
        alunos_docs.append(aluno_doc)

    if alunos_docs:
        await db.alunos.insert_many(alunos_docs)

    # Auditoria
    await db.auditoria.insert_one({
        "id": str(uuid.uuid4()), "pedido_id": pedido_id,
        "usuario_id": current_user.id, "acao": "CRIACAO",
        "detalhes": {"curso": request.curso_nome}, "timestamp": now
    })

    # Atividade
    try:
        await db.atividades_usuario.insert_one({
            "id": str(uuid.uuid4()), "usuario_id": current_user.id,
            "usuario_nome": current_user.nome, "tipo": "criar_pedido",
            "descricao": f"Criou pedido {protocolo}",
            "entidade_tipo": "pedido", "entidade_id": pedido_id,
            "created_at": now
        })
    except Exception:
        pass

    return {"pedido": _build_pedido_response(pedido_doc, alunos_docs), "reserva": None, "mensagem_reserva": None}


@router.get("", response_model=ListaPedidosResponseDTO)
async def listar_pedidos(
    status_filter: Optional[str] = Query(None, alias="status"),
    consultor_id: Optional[str] = None,
    data_inicio: Optional[str] = None, data_fim: Optional[str] = None,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user)
):
    query = {}
    if current_user.role.value == "consultor":
        query["consultor_id"] = current_user.id
    elif consultor_id:
        query["consultor_id"] = consultor_id

    if status_filter:
        query["status"] = status_filter
    if data_inicio:
        query.setdefault("created_at", {})["$gte"] = data_inicio
    if data_fim:
        query.setdefault("created_at", {})["$lte"] = data_fim

    total = await db.pedidos.count_documents(query)
    offset = (pagina - 1) * por_pagina
    pedidos_cursor = db.pedidos.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(por_pagina)
    pedidos_docs = await pedidos_cursor.to_list(length=por_pagina)

    # Batch fetch alunos para todos os pedidos de uma vez (sem N+1)
    pedido_ids = [p["id"] for p in pedidos_docs]
    alunos_list = await db.alunos.find({"pedido_id": {"$in": pedido_ids}}, {"_id": 0}).to_list(length=None)
    alunos_map = {}
    for a in alunos_list:
        alunos_map.setdefault(a["pedido_id"], []).append(a)

    pedidos_response = []
    for p in pedidos_docs:
        pedidos_response.append(_build_pedido_response(p, alunos_map.get(p["id"], [])))

    import math
    return ListaPedidosResponseDTO(
        pedidos=[PedidoResponseDTO(**pr) for pr in pedidos_response],
        paginacao=PaginacaoDTO(
            pagina_atual=pagina, itens_por_pagina=por_pagina,
            total_itens=total, total_paginas=math.ceil(total / por_pagina) if por_pagina else 1
        )
    )


@router.get("/dashboard")
async def get_dashboard(current_user: Usuario = Depends(get_current_user)):
    query = {}
    if current_user.role.value == "consultor":
        query["consultor_id"] = current_user.id

    pipeline = [{"$match": query}, {"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.pedidos.aggregate(pipeline).to_list(length=100)
    contagem = {r["_id"]: r["count"] for r in result}
    contagem["total"] = sum(contagem.values())

    # Recent pedidos — batch fetch alunos (sem N+1)
    pedidos_cursor = db.pedidos.find(query, {"_id": 0}).sort("created_at", -1).limit(5)
    recentes = await pedidos_cursor.to_list(length=5)
    recentes_ids = [p["id"] for p in recentes]
    alunos_rec = await db.alunos.find({"pedido_id": {"$in": recentes_ids}}, {"_id": 0}).to_list(length=None)
    alunos_rec_map = {}
    for a in alunos_rec:
        alunos_rec_map.setdefault(a["pedido_id"], []).append(a)
    pedidos_response = [_build_pedido_response(p, alunos_rec_map.get(p["id"], [])) for p in recentes]

    return {"contagem_status": contagem, "pedidos_recentes": pedidos_response}


@router.get("/analytics")
async def get_analytics(current_user: Usuario = Depends(get_current_user)):
    query = {}
    if current_user.role.value == "consultor":
        query["consultor_id"] = current_user.id

    # 1. Funil por status
    pipeline = [{"$match": query}, {"$group": {"_id": "$status", "total": {"$sum": 1}}}]
    result = await db.pedidos.aggregate(pipeline).to_list(100)
    funil_data = {r["_id"]: r["total"] for r in result}

    funil_ordem = ["pendente", "em_analise", "documentacao_pendente", "aprovado", "realizado", "exportado"]
    funil = [{"status": s, "label": s.replace("_", " ").title(), "total": funil_data.get(s, 0)} for s in funil_ordem]

    # 2. Tempo médio (placeholder - complex in MongoDB)
    tempo_medio = 0

    # 3. Top empresas
    emp_pipeline = [
        {"$match": {**query, "empresa_nome": {"$ne": None}}},
        {"$group": {"_id": "$empresa_nome", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}, {"$limit": 5}
    ]
    emp_result = await db.pedidos.aggregate(emp_pipeline).to_list(5)
    top_empresas = [{"nome": r["_id"] or "Sem empresa", "total": r["total"]} for r in emp_result]

    # 4. Top projetos
    proj_pipeline = [
        {"$match": {**query, "projeto_nome": {"$ne": None}}},
        {"$group": {"_id": "$projeto_nome", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}, {"$limit": 5}
    ]
    proj_result = await db.pedidos.aggregate(proj_pipeline).to_list(5)
    top_projetos = [{"nome": r["_id"] or "Sem projeto", "total": r["total"]} for r in proj_result]

    # 5. Pedidos críticos
    limite_48h = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    criticos = await db.pedidos.count_documents({
        **query, "updated_at": {"$lt": limite_48h},
        "status": {"$in": ["pendente", "em_analise", "documentacao_pendente"]}
    })

    # 6. Total alunos
    total_alunos = await db.alunos.count_documents({})

    # 7. Matriculas por mês
    matriculas_por_mes = []

    # 8. Taxa conversão
    total_pedidos = await db.pedidos.count_documents(query)
    total_aprovados = await db.pedidos.count_documents({**query, "status": {"$in": ["aprovado", "realizado", "exportado"]}})
    taxa_conversao = (total_aprovados / total_pedidos * 100) if total_pedidos > 0 else 0

    por_status = {s: funil_data.get(s, 0) for s in ["pendente", "em_analise", "documentacao_pendente", "aprovado", "realizado", "exportado", "cancelado", "rejeitado"]}

    return {
        "funil": funil, "tempo_medio_dias": round(tempo_medio, 1),
        "top_empresas": top_empresas, "top_projetos": top_projetos,
        "pedidos_criticos": criticos, "total_alunos": total_alunos,
        "matriculas_por_mes": matriculas_por_mes,
        "taxa_conversao": round(taxa_conversao, 1),
        "total_pedidos": total_pedidos, "por_status": por_status
    }


@router.get("/buscar/protocolo/{numero_protocolo}")
async def buscar_por_protocolo(numero_protocolo: str, current_user: Usuario = Depends(get_current_user)):
    doc = await db.pedidos.find_one({"numero_protocolo": numero_protocolo.upper()})
    if not doc:
        raise HTTPException(404, f"Pedido com protocolo {numero_protocolo} não encontrado")

    if current_user.role.value == "consultor" and doc["consultor_id"] != current_user.id:
        raise HTTPException(403, "Sem permissão")

    alunos = await db.alunos.find({"pedido_id": doc["id"]}, {"_id": 0}).to_list(100)
    return _build_pedido_response(doc, alunos)


@router.get("/exportar/totvs")
async def exportar_totvs(
    formato: str = Query(default="xlsx", pattern="^(xlsx|csv)$"),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role.value not in ("admin", "assistente"):
        raise HTTPException(403, "Sem permissão para exportar")

    # Get realized pedidos
    pedidos_docs = await db.pedidos.find({"status": "realizado"}, {"_id": 0}).sort("created_at", -1).limit(500).to_list(500)

    # Build entities for exporter
    pedidos_entities = []
    for p in pedidos_docs:
        alunos_docs = await db.alunos.find({"pedido_id": p["id"]}, {"_id": 0}).to_list(100)
        alunos = [
            Aluno(
                id=a["id"], nome=a["nome"],
                cpf=CPF(a["cpf"], validar_digitos=False),
                email=Email(a["email"]), telefone=Telefone(a["telefone"]),
                data_nascimento=a.get("data_nascimento"),
                rg=a.get("rg", ""), rg_orgao_emissor=a.get("rg_orgao_emissor", ""),
                rg_uf=a.get("rg_uf", ""),
                endereco_cep=a.get("endereco_cep", ""),
                endereco_logradouro=a.get("endereco_logradouro", ""),
                endereco_numero=a.get("endereco_numero", ""),
                endereco_complemento=a.get("endereco_complemento"),
                endereco_bairro=a.get("endereco_bairro", ""),
                endereco_cidade=a.get("endereco_cidade", ""),
                endereco_uf=a.get("endereco_uf", "")
            ) for a in alunos_docs
        ]
        pedido = PedidoMatricula(
            id=p["id"], numero_protocolo=p.get("numero_protocolo"),
            consultor_id=p["consultor_id"], consultor_nome=p["consultor_nome"],
            curso_id=p["curso_id"], curso_nome=p["curso_nome"],
            projeto_id=p.get("projeto_id"), projeto_nome=p.get("projeto_nome"),
            empresa_id=p.get("empresa_id"), empresa_nome=p.get("empresa_nome"),
            alunos=alunos, status=StatusPedido.from_string(p["status"]),
            observacoes=p.get("observacoes"),
            created_at=p.get("created_at"), updated_at=p.get("updated_at")
        )
        pedidos_entities.append(pedido)

    exportador = ExportadorXLSXTOTVS() if formato == "xlsx" else ExportadorCSVTOTVS()
    arquivo = exportador.exportar(pedidos_entities)
    content_type = exportador.get_content_type()
    ext = exportador.get_extension()
    nome = f"exportacao_totvs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

    # Mark as exported
    now = datetime.now(timezone.utc).isoformat()
    for p in pedidos_docs:
        await db.pedidos.update_one({"id": p["id"]}, {"$set": {
            "status": "exportado", "data_exportacao": now,
            "exportado_por": current_user.id, "updated_at": now
        }})
        await db.auditoria.insert_one({
            "id": str(uuid.uuid4()), "pedido_id": p["id"],
            "usuario_id": current_user.id, "acao": "EXPORTACAO",
            "detalhes": {"formato": formato}, "timestamp": now
        })

    return StreamingResponse(arquivo, media_type=content_type,
                             headers={"Content-Disposition": f"attachment; filename={nome}"})


@router.get("/{pedido_id}")
async def buscar_pedido(pedido_id: str, current_user: Usuario = Depends(get_current_user)):
    doc = await db.pedidos.find_one({"id": pedido_id})
    if not doc:
        raise HTTPException(404, "Pedido não encontrado")

    if current_user.role.value == "consultor" and doc["consultor_id"] != current_user.id:
        raise HTTPException(403, "Sem permissão")

    alunos = await db.alunos.find({"pedido_id": pedido_id}, {"_id": 0}).to_list(100)
    return _build_pedido_response(doc, alunos)


@router.get("/{pedido_id}/timeline")
async def buscar_timeline_pedido(pedido_id: str, current_user: Usuario = Depends(get_current_user)):
    doc = await db.pedidos.find_one({"id": pedido_id})
    if not doc:
        raise HTTPException(404, "Pedido não encontrado")

    if current_user.role.value == "consultor" and doc["consultor_id"] != current_user.id:
        raise HTTPException(403, "Sem permissão")

    auditorias = await db.auditoria.find({"pedido_id": pedido_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)

    ACOES_LABELS = {
        "CRIACAO": {"label": "Solicitação Criada", "icon": "plus", "color": "blue"},
        "PEDIDO_CRIADO": {"label": "Solicitação Criada", "icon": "plus", "color": "blue"},
        "ATUALIZACAO_STATUS": {"label": "Status Alterado", "icon": "refresh", "color": "yellow"},
        "STATUS_ATUALIZADO": {"label": "Status Alterado", "icon": "refresh", "color": "yellow"},
        "EXPORTACAO": {"label": "Exportado para TOTVS", "icon": "download", "color": "green"},
    }

    # Get user names
    user_ids = list(set(a.get("usuario_id") for a in auditorias))
    users = {}
    for uid in user_ids:
        u = await db.usuarios.find_one({"id": uid}, {"nome": 1, "_id": 0})
        if u:
            users[uid] = u["nome"]

    timeline = []
    for a in auditorias:
        info = ACOES_LABELS.get(a.get("acao", ""), {"label": a.get("acao", ""), "icon": "circle", "color": "gray"})
        detalhes_str = ""
        det = a.get("detalhes")
        if isinstance(det, dict):
            if "status_anterior" in det and "status_novo" in det:
                detalhes_str = f"De '{det['status_anterior']}' para '{det['status_novo']}'"
            elif "motivo" in det:
                detalhes_str = det.get("motivo", "")

        timeline.append({
            "id": a.get("id"), "acao": a.get("acao"), "acao_label": info["label"],
            "icon": info["icon"], "color": info["color"],
            "usuario_id": a.get("usuario_id"),
            "usuario_nome": users.get(a.get("usuario_id"), "Desconhecido"),
            "detalhes": detalhes_str, "detalhes_raw": det,
            "timestamp": a.get("timestamp")
        })

    return {"pedido_id": pedido_id, "numero_protocolo": doc.get("numero_protocolo"),
            "total_eventos": len(timeline), "timeline": timeline}


@router.patch("/{pedido_id}/status")
async def atualizar_status(
    pedido_id: str, request: AtualizarStatusDTO,
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role.value not in ("admin", "assistente"):
        raise HTTPException(403, "Sem permissão para alterar status")

    doc = await db.pedidos.find_one({"id": pedido_id})
    if not doc:
        raise HTTPException(404, "Pedido não encontrado")

    old_status = doc.get("status")
    now = datetime.now(timezone.utc).isoformat()

    updates = {"status": request.status, "updated_at": now}
    if request.motivo:
        if request.status in ("rejeitado", "cancelado"):
            updates["motivo_rejeicao"] = request.motivo

    await db.pedidos.update_one({"id": pedido_id}, {"$set": updates})

    await db.auditoria.insert_one({
        "id": str(uuid.uuid4()), "pedido_id": pedido_id,
        "usuario_id": current_user.id, "acao": "ATUALIZACAO_STATUS",
        "detalhes": {"status_anterior": old_status, "status_novo": request.status, "motivo": request.motivo},
        "timestamp": now
    })

    try:
        await db.atividades_usuario.insert_one({
            "id": str(uuid.uuid4()), "usuario_id": current_user.id,
            "usuario_nome": current_user.nome, "tipo": "atualizar_pedido",
            "descricao": f"Alterou status de {old_status} para {request.status}",
            "entidade_tipo": "pedido", "entidade_id": pedido_id, "created_at": now
        })
    except Exception:
        pass

    updated = await db.pedidos.find_one({"id": pedido_id})
    alunos = await db.alunos.find({"pedido_id": pedido_id}, {"_id": 0}).to_list(100)
    return _build_pedido_response(updated, alunos)
