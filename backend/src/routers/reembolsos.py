"""Router do Módulo de Reembolsos - MongoDB version"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from src.domain.entities import Usuario
from src.infrastructure.persistence.mongodb import db
from src.utils.text_formatters import formatar_nome_proprio
from src.routers.dependencies import get_current_user

router = APIRouter(prefix="/reembolsos", tags=["Reembolsos"])

MOTIVOS_REEMBOLSO = {
    "sem_escolaridade": {"label": "Sem Escolaridade", "reter_taxa": False},
    "sem_vaga": {"label": "Sem Vaga 2026.1", "reter_taxa": False},
    "passou_bolsista": {"label": "Passou como Bolsista", "reter_taxa": False},
    "nao_tem_vaga": {"label": "Não Tem Vaga", "reter_taxa": False},
    "desistencia": {"label": "Desistência do Aluno", "reter_taxa": True},
    "outros": {"label": "Outros", "reter_taxa": False}
}
STATUS_REEMBOLSO = {
    "aberto": "Aberto", "aguardando_dados_bancarios": "Aguardando Dados Bancários",
    "enviado_financeiro": "Enviado ao Financeiro", "pago": "Pago", "cancelado": "Cancelado"
}


class CriarReembolsoDTO(BaseModel):
    aluno_nome: str
    aluno_cpf: Optional[str] = None
    aluno_email: Optional[str] = None
    aluno_telefone: Optional[str] = None
    aluno_menor_idade: Optional[bool] = False
    curso: str
    turma: Optional[str] = None
    motivo: str
    motivo_descricao: Optional[str] = None
    numero_chamado_sgc: Optional[str] = None
    observacoes: Optional[str] = None

class AtualizarReembolsoDTO(BaseModel):
    status: Optional[str] = None
    numero_chamado_sgc: Optional[str] = None
    data_retorno_financeiro: Optional[str] = None
    data_provisao_pagamento: Optional[str] = None
    data_pagamento: Optional[str] = None
    observacoes: Optional[str] = None

class RegistrarDadosBancariosDTO(BaseModel):
    banco_titular_nome: str
    banco_titular_cpf: str
    banco_nome: str
    banco_agencia: str
    banco_operacao: Optional[str] = None
    banco_conta: str
    banco_tipo_conta: str
    banco_responsavel_financeiro: Optional[bool] = False


def _reembolso_to_dict(r):
    return {
        "id": r["id"], "aluno_nome": r.get("aluno_nome"), "aluno_cpf": r.get("aluno_cpf"),
        "aluno_email": r.get("aluno_email"), "aluno_telefone": r.get("aluno_telefone"),
        "aluno_menor_idade": r.get("aluno_menor_idade"), "curso": r.get("curso"),
        "turma": r.get("turma"), "motivo": r.get("motivo"),
        "motivo_label": MOTIVOS_REEMBOLSO.get(r.get("motivo"), {}).get("label", r.get("motivo")),
        "reter_taxa": r.get("reter_taxa"), "numero_chamado_sgc": r.get("numero_chamado_sgc"),
        "status": r.get("status"),
        "status_label": STATUS_REEMBOLSO.get(r.get("status"), r.get("status")),
        "tem_dados_bancarios": r.get("banco_titular_nome") is not None,
        "data_abertura": r.get("data_abertura"),
        "data_retorno_financeiro": r.get("data_retorno_financeiro"),
        "data_provisao_pagamento": r.get("data_provisao_pagamento"),
        "data_pagamento": r.get("data_pagamento"),
        "observacoes": r.get("observacoes"), "criado_por_nome": r.get("criado_por_nome"),
        "created_at": r.get("created_at")
    }


@router.get("/motivos")
async def listar_motivos(usuario: Usuario = Depends(get_current_user)):
    return [{"value": k, "label": v["label"], "reter_taxa": v["reter_taxa"]} for k, v in MOTIVOS_REEMBOLSO.items()]

@router.get("/status")
async def listar_status(usuario: Usuario = Depends(get_current_user)):
    return [{"value": k, "label": v} for k, v in STATUS_REEMBOLSO.items()]


@router.get("/templates-email")
async def listar_templates_email(usuario: Usuario = Depends(get_current_user)):
    return {
        "solicitacao_dados_bancarios": {
            "assunto": "SENAI CIMATEC - Solicitação de Dados Bancários para Reembolso",
            "corpo": "Olá, boa tarde!\n\nInformamos que sua matrícula no curso [NOME_DO_CURSO] foi cancelada. Para prosseguirmos com o reembolso, solicitamos seus dados bancários.\n\n[NOME_ATENDENTE]\nCentral de Atendimento ao Candidato"
        },
        "confirmacao_recebimento": {
            "assunto": "SENAI CIMATEC - Confirmação de Recebimento dos Dados Bancários",
            "corpo": "Olá!\n\nConfirmamos o recebimento dos seus dados bancários. O crédito será em até 15 dias úteis.\n\n[NOME_ATENDENTE]"
        },
        "confirmacao_pagamento": {
            "assunto": "SENAI CIMATEC - Reembolso Efetuado",
            "corpo": "Olá!\n\nInformamos que o reembolso foi efetuado. Verifique sua conta.\n\n[NOME_ATENDENTE]"
        }
    }


@router.get("/dashboard")
async def dashboard_reembolsos(usuario: Usuario = Depends(get_current_user)):
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    result = await db.reembolsos.aggregate(pipeline).to_list(20)
    contagem_status = {r["_id"]: r["count"] for r in result}

    pipeline_motivo = [{"$group": {"_id": "$motivo", "count": {"$sum": 1}}}]
    motivo_result = await db.reembolsos.aggregate(pipeline_motivo).to_list(20)
    por_motivo = [{"motivo": MOTIVOS_REEMBOLSO.get(r["_id"], {}).get("label", r["_id"]), "total": r["count"]} for r in motivo_result]

    total = await db.reembolsos.count_documents({})
    total_abertos = await db.reembolsos.count_documents({"status": {"$nin": ["pago", "cancelado"]}})

    return {
        "contagem_status": contagem_status, "por_motivo": por_motivo, "total": total,
        "total_abertos": total_abertos,
        "total_aberto": contagem_status.get("aberto", 0),
        "total_aguardando": contagem_status.get("aguardando_dados", 0) + contagem_status.get("aguardando_dados_bancarios", 0),
        "total_enviado": contagem_status.get("enviado_financeiro", 0) + contagem_status.get("no_financeiro", 0),
        "total_pago": contagem_status.get("pago", 0),
        "total_cancelado": contagem_status.get("cancelado", 0)
    }


@router.get("")
async def listar_reembolsos(
    status: Optional[str] = None, motivo: Optional[str] = None,
    aluno_nome: Optional[str] = None,
    pagina: int = Query(1, ge=1), por_pagina: int = Query(20, ge=1, le=100),
    usuario: Usuario = Depends(get_current_user)
):
    query = {}
    if status and status != "todos":
        query["status"] = status
    if motivo and motivo != "todos":
        query["motivo"] = motivo
    if aluno_nome:
        query["aluno_nome"] = {"$regex": aluno_nome, "$options": "i"}

    total = await db.reembolsos.count_documents(query)
    offset = (pagina - 1) * por_pagina
    docs = await db.reembolsos.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(por_pagina).to_list(por_pagina)

    return {
        "reembolsos": [_reembolso_to_dict(r) for r in docs],
        "paginacao": {"pagina_atual": pagina, "por_pagina": por_pagina, "total_itens": total,
                      "total_paginas": (total + por_pagina - 1) // por_pagina}
    }


@router.post("")
async def criar_reembolso(dto: CriarReembolsoDTO, usuario: Usuario = Depends(get_current_user)):
    if dto.motivo not in MOTIVOS_REEMBOLSO:
        raise HTTPException(400, f"Motivo inválido")

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "aluno_nome": formatar_nome_proprio(dto.aluno_nome) if dto.aluno_nome else None,
        "aluno_cpf": dto.aluno_cpf, "aluno_email": dto.aluno_email.lower() if dto.aluno_email else None,
        "aluno_telefone": dto.aluno_telefone, "aluno_menor_idade": dto.aluno_menor_idade or False,
        "curso": formatar_nome_proprio(dto.curso) if dto.curso else None,
        "turma": dto.turma.upper() if dto.turma else None,
        "motivo": dto.motivo, "motivo_descricao": dto.motivo_descricao,
        "reter_taxa": MOTIVOS_REEMBOLSO[dto.motivo]["reter_taxa"],
        "numero_chamado_sgc": dto.numero_chamado_sgc,
        "status": "aberto", "observacoes": dto.observacoes,
        "criado_por_id": usuario.id, "criado_por_nome": usuario.nome,
        "data_abertura": now, "created_at": now, "updated_at": now,
        "banco_titular_nome": None, "responsavel_id": None, "responsavel_nome": None
    }
    await db.reembolsos.insert_one(doc)
    return {"id": doc["id"], "mensagem": "Reembolso criado com sucesso", "status": "aberto", "reter_taxa": doc["reter_taxa"]}


@router.get("/{reembolso_id}")
async def buscar_reembolso(reembolso_id: str, usuario: Usuario = Depends(get_current_user)):
    r = await db.reembolsos.find_one({"id": reembolso_id}, {"_id": 0})
    if not r:
        raise HTTPException(404, "Reembolso não encontrado")
    result = _reembolso_to_dict(r)
    # Add bank details
    result.update({
        "motivo_descricao": r.get("motivo_descricao"),
        "banco_titular_nome": r.get("banco_titular_nome"), "banco_titular_cpf": r.get("banco_titular_cpf"),
        "banco_nome": r.get("banco_nome"), "banco_agencia": r.get("banco_agencia"),
        "banco_operacao": r.get("banco_operacao"), "banco_conta": r.get("banco_conta"),
        "banco_tipo_conta": r.get("banco_tipo_conta"),
        "banco_responsavel_financeiro": r.get("banco_responsavel_financeiro"),
        "dados_bancarios_recebidos_em": r.get("dados_bancarios_recebidos_em"),
        "data_solicitacao_dados_bancarios": r.get("data_solicitacao_dados_bancarios"),
        "atualizado_por_nome": r.get("atualizado_por_nome"),
        "updated_at": r.get("updated_at")
    })
    return result


@router.put("/{reembolso_id}")
async def atualizar_reembolso(reembolso_id: str, dto: AtualizarReembolsoDTO, usuario: Usuario = Depends(get_current_user)):
    r = await db.reembolsos.find_one({"id": reembolso_id})
    if not r:
        raise HTTPException(404, "Reembolso não encontrado")

    updates = {"atualizado_por_id": usuario.id, "atualizado_por_nome": usuario.nome,
               "updated_at": datetime.now(timezone.utc).isoformat()}
    if dto.status:
        if dto.status not in STATUS_REEMBOLSO:
            raise HTTPException(400, "Status inválido")
        updates["status"] = dto.status
        if dto.status == "pago" and not r.get("data_pagamento"):
            updates["data_pagamento"] = datetime.now(timezone.utc).isoformat()
    if dto.numero_chamado_sgc:
        updates["numero_chamado_sgc"] = dto.numero_chamado_sgc
    if dto.data_retorno_financeiro:
        updates["data_retorno_financeiro"] = dto.data_retorno_financeiro
    if dto.data_provisao_pagamento:
        updates["data_provisao_pagamento"] = dto.data_provisao_pagamento
    if dto.data_pagamento:
        updates["data_pagamento"] = dto.data_pagamento
    if dto.observacoes is not None:
        updates["observacoes"] = dto.observacoes

    await db.reembolsos.update_one({"id": reembolso_id}, {"$set": updates})
    return {"id": reembolso_id, "mensagem": "Reembolso atualizado", "status": updates.get("status", r["status"])}


@router.delete("/{reembolso_id}")
async def deletar_reembolso(reembolso_id: str, usuario: Usuario = Depends(get_current_user)):
    if usuario.role.value != "admin":
        raise HTTPException(403, "Apenas administradores podem excluir")
    result = await db.reembolsos.delete_one({"id": reembolso_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Reembolso não encontrado")
    return {"mensagem": "Reembolso excluído com sucesso"}


@router.post("/{reembolso_id}/dados-bancarios")
async def registrar_dados_bancarios(reembolso_id: str, dto: RegistrarDadosBancariosDTO, usuario: Usuario = Depends(get_current_user)):
    r = await db.reembolsos.find_one({"id": reembolso_id})
    if not r:
        raise HTTPException(404, "Reembolso não encontrado")
    now = datetime.now(timezone.utc).isoformat()
    await db.reembolsos.update_one({"id": reembolso_id}, {"$set": {
        "banco_titular_nome": dto.banco_titular_nome, "banco_titular_cpf": dto.banco_titular_cpf,
        "banco_nome": dto.banco_nome, "banco_agencia": dto.banco_agencia,
        "banco_operacao": dto.banco_operacao, "banco_conta": dto.banco_conta,
        "banco_tipo_conta": dto.banco_tipo_conta,
        "banco_responsavel_financeiro": dto.banco_responsavel_financeiro or False,
        "dados_bancarios_recebidos_em": now,
        "atualizado_por_id": usuario.id, "atualizado_por_nome": usuario.nome, "updated_at": now
    }})
    return {"id": reembolso_id, "mensagem": "Dados bancários registrados", "status": r["status"]}


@router.post("/{reembolso_id}/marcar-email-enviado")
async def marcar_email_enviado(reembolso_id: str, usuario: Usuario = Depends(get_current_user)):
    r = await db.reembolsos.find_one({"id": reembolso_id})
    if not r:
        raise HTTPException(404, "Reembolso não encontrado")
    now = datetime.now(timezone.utc).isoformat()
    await db.reembolsos.update_one({"id": reembolso_id}, {"$set": {
        "data_solicitacao_dados_bancarios": now, "status": "aguardando_dados_bancarios",
        "atualizado_por_id": usuario.id, "atualizado_por_nome": usuario.nome
    }})
    return {"id": reembolso_id, "mensagem": "Email marcado como enviado", "status": "aguardando_dados_bancarios"}
