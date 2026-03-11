"""Router de Regras de Negócio - MongoDB version (no DB dependency, just services)"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from src.services.regras_negocio_service import (
    ValidadorPreRequisitos, CalculadorPrazos, TipoCurso,
    REGRAS_PRE_REQUISITOS, PRAZOS_SENAI,
    get_documentos_por_tipo_curso, get_tipos_curso_disponiveis
)
from src.services.templates_mensagem_service import (
    render_email_template, render_whatsapp_template, gerar_link_whatsapp,
    get_templates_disponiveis, EMAIL_TEMPLATES, WHATSAPP_TEMPLATES
)

router = APIRouter(prefix="/regras", tags=["Regras de Negócio"])

class ValidacaoIdadeRequest(BaseModel):
    data_nascimento: str
    tipo_curso: str
    is_pcd: bool = False

class ValidacaoCompletaRequest(BaseModel):
    data_nascimento: str
    escolaridade: str
    documentos: List[str] = []
    tipo_curso: str
    is_pcd: bool = False
    is_menor: bool = False
    tem_empresa: bool = False

class CalculoPrazoRequest(BaseModel):
    data_criacao: str

class TemplateEmailRequest(BaseModel):
    tipo: str
    dados: dict
    formato: str = "html"

class TemplateWhatsAppRequest(BaseModel):
    tipo: str
    dados: dict
    telefone: Optional[str] = None

@router.get("/tipos-curso")
async def listar_tipos_curso():
    return get_tipos_curso_disponiveis()

@router.get("/tipos-curso/{tipo_curso}")
async def get_tipo_curso(tipo_curso: str):
    try:
        tipo = TipoCurso(tipo_curso)
        regras = REGRAS_PRE_REQUISITOS.get(tipo, {})
        return {"tipo": tipo.value, **regras, "documentos": get_documentos_por_tipo_curso(tipo_curso)}
    except ValueError:
        raise HTTPException(404, f"Tipo não encontrado: {tipo_curso}")

@router.get("/tipos-curso/{tipo_curso}/documentos")
async def listar_documentos_curso(tipo_curso: str):
    docs = get_documentos_por_tipo_curso(tipo_curso)
    if not docs:
        raise HTTPException(404, f"Tipo não encontrado: {tipo_curso}")
    return {"tipo_curso": tipo_curso, "documentos": docs, "total": len(docs)}

@router.post("/validar/idade")
async def validar_idade(request: ValidacaoIdadeRequest):
    try:
        return ValidadorPreRequisitos.validar_idade(datetime.fromisoformat(request.data_nascimento), TipoCurso(request.tipo_curso), request.is_pcd)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/validar/escolaridade")
async def validar_escolaridade(escolaridade: str = Query(...), tipo_curso: str = Query(...)):
    try:
        return ValidadorPreRequisitos.validar_escolaridade(escolaridade, TipoCurso(tipo_curso))
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/validar/documentos")
async def validar_documentos(documentos: List[str], tipo_curso: str = Query(...), is_menor: bool = Query(False)):
    try:
        return ValidadorPreRequisitos.validar_documentos(documentos, TipoCurso(tipo_curso), is_menor)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/validar/completo")
async def validar_completo(request: ValidacaoCompletaRequest):
    try:
        return ValidadorPreRequisitos.validar_completo(
            datetime.fromisoformat(request.data_nascimento), request.escolaridade,
            request.documentos, TipoCurso(request.tipo_curso),
            request.is_pcd, request.is_menor, request.tem_empresa)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/prazos")
async def listar_prazos():
    return {"prazos": PRAZOS_SENAI}

@router.post("/prazos/pendencia")
async def calcular_prazo_pendencia(request: CalculoPrazoRequest):
    try:
        return CalculadorPrazos.calcular_prazo_pendencia(datetime.fromisoformat(request.data_criacao))
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/prazos/pagamento")
async def calcular_prazo_pagamento(request: CalculoPrazoRequest):
    try:
        return CalculadorPrazos.calcular_prazo_pagamento(datetime.fromisoformat(request.data_criacao))
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/prazos/sla")
async def calcular_sla(data_criacao: str = Query(...), status_atual: str = Query(...)):
    try:
        return CalculadorPrazos.calcular_sla(datetime.fromisoformat(data_criacao), status_atual)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/escolaridades")
async def listar_escolaridades():
    return {"escolaridades": [
        {"value": "fundamental_incompleto", "label": "Ensino Fundamental Incompleto", "ordem": 1},
        {"value": "fundamental_completo", "label": "Ensino Fundamental Completo", "ordem": 2},
        {"value": "medio_cursando", "label": "Ensino Médio Cursando", "ordem": 3},
        {"value": "medio_completo", "label": "Ensino Médio Completo", "ordem": 4},
        {"value": "superior_cursando", "label": "Ensino Superior Cursando", "ordem": 5},
        {"value": "superior_completo", "label": "Ensino Superior Completo", "ordem": 6},
        {"value": "pos_graduacao", "label": "Pós-Graduação", "ordem": 7}
    ]}

@router.get("/templates")
async def listar_templates():
    return get_templates_disponiveis()

@router.get("/templates/email")
async def listar_templates_email():
    import re
    templates = []
    for nome, t in EMAIL_TEMPLATES.items():
        placeholders = list(set(re.findall(r'\{(\w+)\}', t["assunto"] + t["corpo_texto"])))
        templates.append({"nome": nome, "assunto_exemplo": t["assunto"], "campos_necessarios": placeholders})
    return {"templates": templates}

@router.get("/templates/whatsapp")
async def listar_templates_whatsapp():
    import re
    templates = []
    for nome, t in WHATSAPP_TEMPLATES.items():
        placeholders = list(set(re.findall(r'\{(\w+)\}', t["mensagem"])))
        templates.append({"nome": nome, "campos_necessarios": placeholders})
    return {"templates": templates}

@router.post("/templates/email/render")
async def renderizar_email(request: TemplateEmailRequest):
    try:
        return render_email_template(request.tipo, request.dados, request.formato)
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.post("/templates/whatsapp/render")
async def renderizar_whatsapp(request: TemplateWhatsAppRequest):
    try:
        mensagem = render_whatsapp_template(request.tipo, request.dados)
        resultado = {"mensagem": mensagem, "tipo": request.tipo}
        if request.telefone:
            resultado["link_whatsapp"] = gerar_link_whatsapp(request.telefone, mensagem)
        return resultado
    except ValueError as e:
        raise HTTPException(404, str(e))
