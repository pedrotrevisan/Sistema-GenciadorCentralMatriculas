"""Router de Cancelamento - MongoDB version"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid

from src.infrastructure.persistence.mongodb import db
from src.services.cancelamento_service import (
    TipoCancelamento, get_documentos_escolaridade, get_fluxo_validacao_escolaridade,
    get_responsabilidades_cancelamento, get_tipos_cancelamento,
    DOCUMENTOS_ESCOLARIDADE_TOTVS, PRAZO_NRM_HORAS
)

router = APIRouter(prefix="/cancelamento", tags=["Cancelamento e Documentos TOTVS"])

class SolicitarCancelamentoRequest(BaseModel):
    pedido_id: str
    tipo: str
    motivo: str
    solicitante_id: str
    solicitante_nome: str

class RespostaNRMRequest(BaseModel):
    pedido_id: str
    revertido: bool
    observacoes: str = ""


@router.post("/solicitar")
async def solicitar_cancelamento(request: SolicitarCancelamentoRequest):
    try:
        tipo = TipoCancelamento(request.tipo)
    except ValueError:
        raise HTTPException(400, f"Tipo inválido: {request.tipo}")

    pedido = await db.pedidos.find_one({"id": request.pedido_id})
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")

    now = datetime.now(timezone.utc).isoformat()

    if tipo == TipoCancelamento.SOLICITADO_CANDIDATO:
        await db.pedidos.update_one({"id": request.pedido_id}, {"$set": {
            "status": "aguardando_nrm", "updated_at": now,
            "cancelamento_tipo": request.tipo, "cancelamento_motivo": request.motivo,
            "cancelamento_solicitante": request.solicitante_nome,
            "cancelamento_data": now
        }})
        prazo = (datetime.now(timezone.utc) + timedelta(hours=PRAZO_NRM_HORAS)).isoformat()
        return {"message": "Cancelamento encaminhado ao NRM", "prazo_nrm": prazo, "status": "aguardando_nrm"}
    else:
        await db.pedidos.update_one({"id": request.pedido_id}, {"$set": {
            "status": "cancelado", "updated_at": now,
            "cancelamento_tipo": request.tipo, "cancelamento_motivo": request.motivo
        }})
        await db.auditoria.insert_one({
            "id": str(uuid.uuid4()), "pedido_id": request.pedido_id,
            "usuario_id": request.solicitante_id, "acao": "CANCELAMENTO",
            "detalhes": {"tipo": request.tipo, "motivo": request.motivo}, "timestamp": now
        })
        return {"message": "Pedido cancelado", "status": "cancelado"}


@router.post("/resposta-nrm")
async def resposta_nrm(request: RespostaNRMRequest):
    pedido = await db.pedidos.find_one({"id": request.pedido_id})
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")

    now = datetime.now(timezone.utc).isoformat()
    if request.revertido:
        await db.pedidos.update_one({"id": request.pedido_id}, {"$set": {
            "status": pedido.get("status_antes_nrm", "em_analise"), "updated_at": now,
            "nrm_revertido": True, "nrm_observacoes": request.observacoes
        }})
        return {"message": "NRM reverteu o cancelamento", "status": "revertido"}
    else:
        await db.pedidos.update_one({"id": request.pedido_id}, {"$set": {
            "status": "cancelado", "updated_at": now,
            "nrm_revertido": False, "nrm_observacoes": request.observacoes
        }})
        return {"message": "Cancelamento confirmado pelo NRM", "status": "cancelado"}


@router.get("/verificar-prazo/{pedido_id}")
async def verificar_prazo_nrm(pedido_id: str):
    pedido = await db.pedidos.find_one({"id": pedido_id})
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")
    cancel_data = pedido.get("cancelamento_data")
    if not cancel_data:
        return {"expirado": False, "message": "Sem data de cancelamento"}
    try:
        dt = datetime.fromisoformat(str(cancel_data))
        prazo = dt + timedelta(hours=PRAZO_NRM_HORAS)
        expirado = datetime.now(timezone.utc) > prazo.replace(tzinfo=timezone.utc)
        return {"expirado": expirado, "prazo": prazo.isoformat()}
    except Exception:
        return {"expirado": False, "message": "Erro ao calcular prazo"}


@router.get("/tipos")
async def listar_tipos():
    return {"tipos": get_tipos_cancelamento()}

@router.get("/responsabilidades")
async def listar_responsabilidades():
    return {"responsabilidades": get_responsabilidades_cancelamento(), "prazo_nrm_horas": PRAZO_NRM_HORAS}

@router.get("/documentos/escolaridade")
async def listar_docs_escolaridade():
    return {"documentos": get_documentos_escolaridade()}

@router.get("/documentos/escolaridade/{codigo}")
async def get_doc_escolaridade(codigo: str):
    doc = DOCUMENTOS_ESCOLARIDADE_TOTVS.get(codigo)
    if not doc:
        raise HTTPException(404, f"Documento não encontrado: {codigo}")
    return {"codigo": codigo, **doc}

@router.get("/documentos/fluxo-validacao")
async def get_fluxos():
    return {"fluxos": get_fluxo_validacao_escolaridade()}

@router.post("/documentos/validar-escolaridade")
async def validar_escolaridade(
    tipo_documento: str = Query(...),
    data_entrega: Optional[str] = Query(None)
):
    fluxos = get_fluxo_validacao_escolaridade()
    fluxo = fluxos.get(tipo_documento)
    if not fluxo:
        raise HTTPException(400, f"Tipo inválido. Use: {', '.join(fluxos.keys())}")
    acoes = []
    for cod in fluxo["documentos_validar"]:
        doc = DOCUMENTOS_ESCOLARIDADE_TOTVS.get(cod)
        if cod == "93" and data_entrega:
            acoes.append({"codigo": cod, "nome": doc["nome"], "acao": f"Registrar 'VALIDADO' + data: {data_entrega}"})
        else:
            acoes.append({"codigo": cod, "nome": doc["nome"], "acao": "Registrar 'VALIDADO'"})
    for cod in fluxo["documentos_incluir"]:
        doc = DOCUMENTOS_ESCOLARIDADE_TOTVS.get(cod)
        acoes.append({"codigo": cod, "nome": doc["nome"], "acao": "INCLUIR documento e registrar 'VALIDADO'"})
    return {"tipo_documento": tipo_documento, "descricao": fluxo["descricao"],
            "acoes": acoes, "status_final": fluxo["status_final"],
            "status_final_descricao": "MAC - Matrícula Confirmada"}
