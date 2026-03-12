"""Router de Pendências Documentais - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import re
import io
import pandas as pd

from src.domain.entities import Usuario
from src.infrastructure.persistence.mongodb import db
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/pendencias", tags=["Pendências"])

class CriarPendenciaDTO(BaseModel):
    aluno_id: str
    pedido_id: str
    documento_codigo: str
    observacoes: Optional[str] = None

class CriarPendenciaManualDTO(BaseModel):
    aluno_nome: str
    aluno_cpf: str
    aluno_email: Optional[str] = None
    aluno_telefone: Optional[str] = None
    documento_codigo: str
    curso_nome: Optional[str] = None
    observacoes: Optional[str] = None

class AtualizarPendenciaDTO(BaseModel):
    status: str
    observacoes: Optional[str] = None
    motivo_rejeicao: Optional[str] = None

class RegistrarContatoDTO(BaseModel):
    tipo_contato: str
    descricao: str
    resultado: Optional[str] = None

STATUS_PENDENCIA = {
    "pendente": "Pendente", "aguardando_aluno": "Aguardando Aluno",
    "em_analise": "Em Análise", "aprovado": "Aprovado",
    "rejeitado": "Rejeitado", "reenvio_necessario": "Reenvio Necessário"
}


@router.get("/importacao/template")
async def download_template_pendencias():
    """Baixa template Excel para importação de pendências em lote"""
    df = pd.DataFrame(columns=[
        'ALUNO_NOME', 'ALUNO_CPF', 'ALUNO_EMAIL', 'ALUNO_TELEFONE',
        'DOCUMENTO_CODIGO', 'CURSO_NOME', 'OBSERVACOES'
    ])
    df.loc[0] = [
        'João da Silva Santos', '123.456.789-00', 'joao@email.com', '(71) 99999-9999',
        'RG', 'Técnico em Mecânica', 'Urgente'
    ]
    df.loc[1] = [
        'Maria Oliveira', '987.654.321-00', 'maria@email.com', '(71) 98888-8888',
        'CPF', 'Técnico em Redes', ''
    ]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pendencias')
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=template_importacao_pendencias.xlsx"}
    )


@router.get("/buscar-aluno/{cpf}")
async def buscar_aluno_por_cpf(cpf: str, usuario: Usuario = Depends(get_current_user)):
    cpf_limpo = re.sub(r'\D', '', cpf)
    aluno = await db.alunos.find_one({"cpf": {"$regex": cpf_limpo}}, {"_id": 0})
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")
    pedido = await db.pedidos.find_one({"id": aluno.get("pedido_id")}, {"_id": 0, "curso_nome": 1, "status": 1, "numero_protocolo": 1})
    return {**aluno, "pedido": pedido}


@router.get("/tipos-documento")
async def listar_tipos_documento(usuario: Usuario = Depends(get_current_user)):
    tipos = await db.tipos_documento.find({}, {"_id": 0}).sort("nome", 1).to_list(100)
    return {"tipos": tipos}


@router.get("/dashboard")
async def dashboard_pendencias(usuario: Usuario = Depends(get_current_user)):
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.pendencias.aggregate(pipeline).to_list(20)
    por_status = {r["_id"]: r["count"] for r in result}
    total = sum(por_status.values())

    limite_5d = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    vencidas = await db.pendencias.count_documents({
        "status": {"$in": ["pendente", "aguardando_aluno"]}, "created_at": {"$lt": limite_5d}
    })
    pipeline_doc = [{"$match": {"status": "pendente"}},
                    {"$group": {"_id": "$documento_codigo", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}, {"$limit": 5}]
    top_docs = [{"documento": r["_id"], "total": r["count"]} for r in await db.pendencias.aggregate(pipeline_doc).to_list(5)]

    return {"total": total, "por_status": por_status, "vencidas": vencidas,
            "top_documentos_pendentes": top_docs}


@router.get("")
async def listar_pendencias(
    status: Optional[str] = None, aluno_nome: Optional[str] = None,
    documento_codigo: Optional[str] = None, vencidas: Optional[bool] = None,
    pagina: int = Query(1, ge=1), por_pagina: int = Query(20, ge=1, le=100),
    usuario: Usuario = Depends(get_current_user)
):
    query = {}
    if status and status != "todos":
        query["status"] = status
    if aluno_nome:
        query["aluno_nome"] = {"$regex": aluno_nome, "$options": "i"}
    if documento_codigo:
        query["documento_codigo"] = documento_codigo
    if vencidas:
        limite = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        query["created_at"] = {"$lt": limite}
        query["status"] = {"$in": ["pendente", "aguardando_aluno"]}

    total = await db.pendencias.count_documents(query)
    offset = (pagina - 1) * por_pagina
    docs = await db.pendencias.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(por_pagina).to_list(por_pagina)

    # Enrich with contact count
    for d in docs:
        d["total_contatos"] = await db.historico_contatos.count_documents({"pendencia_id": d["id"]})

    return {"pendencias": docs, "total": total,
            "paginacao": {"pagina_atual": pagina, "por_pagina": por_pagina,
                          "total_itens": total, "total_paginas": (total + por_pagina - 1) // por_pagina}}


@router.post("")
async def criar_pendencia(dto: CriarPendenciaDTO, usuario: Usuario = Depends(get_current_user)):
    aluno = await db.alunos.find_one({"id": dto.aluno_id}, {"_id": 0})
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")
    pedido = await db.pedidos.find_one({"id": dto.pedido_id}, {"_id": 0})
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")
    tipo_doc = await db.tipos_documento.find_one({"codigo": dto.documento_codigo}, {"_id": 0})

    now = datetime.now(timezone.utc).isoformat()
    prazo = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    doc = {
        "id": str(uuid.uuid4()), "aluno_id": dto.aluno_id, "pedido_id": dto.pedido_id,
        "aluno_nome": aluno.get("nome"), "aluno_cpf": aluno.get("cpf"),
        "aluno_email": aluno.get("email"), "aluno_telefone": aluno.get("telefone"),
        "curso_nome": pedido.get("curso_nome"),
        "documento_codigo": dto.documento_codigo,
        "documento_nome": tipo_doc.get("nome") if tipo_doc else dto.documento_codigo,
        "status": "pendente", "observacoes": dto.observacoes,
        "responsavel_id": usuario.id, "responsavel_nome": usuario.nome,
        "prazo": prazo, "data_prazo": prazo,
        "created_at": now, "updated_at": now
    }
    await db.pendencias.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.post("/manual")
async def criar_pendencia_manual(dto: CriarPendenciaManualDTO, usuario: Usuario = Depends(get_current_user)):
    tipo_doc = await db.tipos_documento.find_one({"codigo": dto.documento_codigo}, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()
    prazo = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    doc = {
        "id": str(uuid.uuid4()), "aluno_id": None, "pedido_id": None,
        "aluno_nome": dto.aluno_nome, "aluno_cpf": re.sub(r'\D', '', dto.aluno_cpf),
        "aluno_email": dto.aluno_email, "aluno_telefone": dto.aluno_telefone,
        "curso_nome": dto.curso_nome,
        "documento_codigo": dto.documento_codigo,
        "documento_nome": tipo_doc.get("nome") if tipo_doc else dto.documento_codigo,
        "status": "pendente", "observacoes": dto.observacoes,
        "responsavel_id": usuario.id, "responsavel_nome": usuario.nome,
        "prazo": prazo, "data_prazo": prazo,
        "created_at": now, "updated_at": now
    }
    await db.pendencias.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/{pendencia_id}")
async def buscar_pendencia(pendencia_id: str, usuario: Usuario = Depends(get_current_user)):
    p = await db.pendencias.find_one({"id": pendencia_id}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Pendência não encontrada")
    contatos = await db.historico_contatos.find({"pendencia_id": pendencia_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    p["historico_contatos"] = contatos
    return p


@router.patch("/{pendencia_id}")
async def atualizar_pendencia(pendencia_id: str, dto: AtualizarPendenciaDTO, usuario: Usuario = Depends(get_current_user)):
    p = await db.pendencias.find_one({"id": pendencia_id})
    if not p:
        raise HTTPException(404, "Pendência não encontrada")
    updates = {"status": dto.status, "updated_at": datetime.now(timezone.utc).isoformat(),
               "atualizado_por_id": usuario.id, "atualizado_por_nome": usuario.nome}
    if dto.observacoes is not None:
        updates["observacoes"] = dto.observacoes
    if dto.motivo_rejeicao:
        updates["motivo_rejeicao"] = dto.motivo_rejeicao
    if dto.status == "aprovado":
        updates["data_aprovacao"] = datetime.now(timezone.utc).isoformat()
    await db.pendencias.update_one({"id": pendencia_id}, {"$set": updates})
    return {"message": "Pendência atualizada", "status": dto.status}


@router.post("/{pendencia_id}/contato")
async def registrar_contato(pendencia_id: str, dto: RegistrarContatoDTO, usuario: Usuario = Depends(get_current_user)):
    p = await db.pendencias.find_one({"id": pendencia_id})
    if not p:
        raise HTTPException(404, "Pendência não encontrada")
    now = datetime.now(timezone.utc).isoformat()
    contato = {
        "id": str(uuid.uuid4()), "pendencia_id": pendencia_id,
        "tipo_contato": dto.tipo_contato, "descricao": dto.descricao,
        "resultado": dto.resultado, "usuario_id": usuario.id,
        "usuario_nome": usuario.nome, "created_at": now
    }
    await db.historico_contatos.insert_one(contato)
    await db.pendencias.update_one({"id": pendencia_id}, {"$set": {
        "ultimo_contato": now, "updated_at": now
    }})
    contato.pop("_id", None)
    return contato


@router.delete("/{pendencia_id}")
async def deletar_pendencia(pendencia_id: str, usuario: Usuario = Depends(get_current_user)):
    if usuario.role.value != "admin":
        raise HTTPException(403, "Apenas admin pode deletar")
    result = await db.pendencias.delete_one({"id": pendencia_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Pendência não encontrada")
    return {"message": "Pendência deletada"}


@router.get("/exportar/excel")
async def exportar_pendencias(status_filter: Optional[str] = Query(None, alias="status"),
                               usuario: Usuario = Depends(get_current_user)):
    import openpyxl
    query = {}
    if status_filter:
        query["status"] = status_filter
    docs = await db.pendencias.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pendências"
    headers = ["Aluno", "CPF", "Email", "Telefone", "Curso", "Documento", "Status", "Observações", "Data Criação"]
    ws.append(headers)
    for d in docs:
        ws.append([d.get("aluno_nome"), d.get("aluno_cpf"), d.get("aluno_email"),
                   d.get("aluno_telefone"), d.get("curso_nome"),
                   d.get("documento_nome"), d.get("status"),
                   d.get("observacoes"), d.get("created_at")])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(output,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=pendencias.xlsx"})
