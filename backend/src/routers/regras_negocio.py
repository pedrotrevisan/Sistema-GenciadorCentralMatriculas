"""Router para Regras de Negócio SENAI - Prazos, Pré-Requisitos e Validações"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

from src.services.regras_negocio_service import (
    ValidadorPreRequisitos,
    CalculadorPrazos,
    TipoCurso,
    REGRAS_PRE_REQUISITOS,
    PRAZOS_SENAI,
    get_documentos_por_tipo_curso,
    get_tipos_curso_disponiveis
)
from src.services.templates_mensagem_service import (
    render_email_template,
    render_whatsapp_template,
    gerar_link_whatsapp,
    get_templates_disponiveis,
    EMAIL_TEMPLATES,
    WHATSAPP_TEMPLATES
)

router = APIRouter(prefix="/regras", tags=["Regras de Negócio"])


# ==================== SCHEMAS ====================

class ValidacaoIdadeRequest(BaseModel):
    data_nascimento: str = Field(..., description="Data de nascimento (YYYY-MM-DD)")
    tipo_curso: str = Field(..., description="Tipo do curso")
    is_pcd: bool = Field(default=False, description="Se o aluno é PCD")


class ValidacaoCompletaRequest(BaseModel):
    data_nascimento: str = Field(..., description="Data de nascimento (YYYY-MM-DD)")
    escolaridade: str = Field(..., description="Nível de escolaridade do aluno")
    documentos: List[str] = Field(default=[], description="Lista de documentos apresentados")
    tipo_curso: str = Field(..., description="Tipo do curso")
    is_pcd: bool = Field(default=False)
    is_menor: bool = Field(default=False)
    tem_empresa: bool = Field(default=False)


class CalculoPrazoRequest(BaseModel):
    data_criacao: str = Field(..., description="Data de criação (ISO format)")


# ==================== ENDPOINTS - TIPOS DE CURSO ====================

@router.get("/tipos-curso")
async def listar_tipos_curso():
    """Lista todos os tipos de curso disponíveis com suas regras"""
    return get_tipos_curso_disponiveis()


@router.get("/tipos-curso/{tipo_curso}")
async def get_tipo_curso(tipo_curso: str):
    """Retorna detalhes de um tipo de curso específico"""
    try:
        tipo = TipoCurso(tipo_curso)
        regras = REGRAS_PRE_REQUISITOS.get(tipo, {})
        return {
            "tipo": tipo.value,
            **regras,
            "documentos": get_documentos_por_tipo_curso(tipo_curso)
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Tipo de curso não encontrado: {tipo_curso}")


@router.get("/tipos-curso/{tipo_curso}/documentos")
async def listar_documentos_curso(tipo_curso: str):
    """Lista documentos obrigatórios para um tipo de curso"""
    docs = get_documentos_por_tipo_curso(tipo_curso)
    if not docs:
        raise HTTPException(status_code=404, detail=f"Tipo de curso não encontrado: {tipo_curso}")
    return {
        "tipo_curso": tipo_curso,
        "documentos": docs,
        "total": len(docs)
    }


# ==================== ENDPOINTS - VALIDAÇÃO ====================

@router.post("/validar/idade")
async def validar_idade(request: ValidacaoIdadeRequest):
    """Valida se a idade do aluno atende aos requisitos do curso"""
    try:
        data_nascimento = datetime.fromisoformat(request.data_nascimento)
        tipo_curso = TipoCurso(request.tipo_curso)
        
        resultado = ValidadorPreRequisitos.validar_idade(
            data_nascimento,
            tipo_curso,
            request.is_pcd
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validar/escolaridade")
async def validar_escolaridade(
    escolaridade: str = Query(..., description="Escolaridade do aluno"),
    tipo_curso: str = Query(..., description="Tipo do curso")
):
    """Valida se a escolaridade atende aos requisitos do curso"""
    try:
        tipo = TipoCurso(tipo_curso)
        resultado = ValidadorPreRequisitos.validar_escolaridade(escolaridade, tipo)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validar/documentos")
async def validar_documentos(
    documentos: List[str],
    tipo_curso: str = Query(..., description="Tipo do curso"),
    is_menor: bool = Query(default=False, description="Se o aluno é menor de idade")
):
    """Valida se os documentos apresentados atendem aos requisitos"""
    try:
        tipo = TipoCurso(tipo_curso)
        resultado = ValidadorPreRequisitos.validar_documentos(documentos, tipo, is_menor)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validar/completo")
async def validar_pre_requisitos_completo(request: ValidacaoCompletaRequest):
    """
    Validação completa de todos os pré-requisitos para matrícula.
    Retorna se o aluno pode prosseguir ou se deve ser marcado como 'Não Atende Requisito'.
    """
    try:
        data_nascimento = datetime.fromisoformat(request.data_nascimento)
        tipo_curso = TipoCurso(request.tipo_curso)
        
        resultado = ValidadorPreRequisitos.validar_completo(
            data_nascimento=data_nascimento,
            escolaridade=request.escolaridade,
            documentos=request.documentos,
            tipo_curso=tipo_curso,
            is_pcd=request.is_pcd,
            is_menor=request.is_menor,
            tem_empresa=request.tem_empresa
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ENDPOINTS - PRAZOS ====================

@router.get("/prazos")
async def listar_prazos():
    """Lista todos os prazos configurados"""
    return {
        "prazos": PRAZOS_SENAI,
        "descricoes": {
            "pendencia_documental_dias": "Prazo para aluno regularizar documentos pendentes",
            "nao_atende_requisito_dias": "Prazo para cancelamento por não atender requisitos (imediato)",
            "pagamento_dias": "Prazo para pagamento após aprovação",
            "matricula_web_horas": "Horas mínimas antes da aula para matrícula web",
            "comunicacao_cancelamento_turma_horas": "Horas para comunicar cancelamento de turma",
            "reembolso_dias_uteis": "Dias úteis para processamento de reembolso"
        }
    }


@router.post("/prazos/pendencia")
async def calcular_prazo_pendencia(request: CalculoPrazoRequest):
    """
    Calcula o prazo de pendência documental (5 dias).
    Retorna data limite, dias restantes e nível de alerta.
    """
    try:
        data_criacao = datetime.fromisoformat(request.data_criacao)
        resultado = CalculadorPrazos.calcular_prazo_pendencia(data_criacao)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/prazos/pagamento")
async def calcular_prazo_pagamento(request: CalculoPrazoRequest):
    """Calcula o prazo para pagamento após aprovação"""
    try:
        data_aprovacao = datetime.fromisoformat(request.data_criacao)
        resultado = CalculadorPrazos.calcular_prazo_pagamento(data_aprovacao)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/prazos/sla")
async def calcular_sla(
    data_criacao: str = Query(..., description="Data de criação (ISO format)"),
    status_atual: str = Query(..., description="Status atual do pedido")
):
    """
    Calcula métricas de SLA para um pedido.
    Retorna se está dentro do SLA e quantos dias de atraso.
    """
    try:
        data = datetime.fromisoformat(data_criacao)
        resultado = CalculadorPrazos.calcular_sla(data, status_atual)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ENDPOINTS - ESCOLARIDADE ====================

@router.get("/escolaridades")
async def listar_escolaridades():
    """Lista níveis de escolaridade aceitos pelo sistema"""
    return {
        "escolaridades": [
            {"value": "fundamental_incompleto", "label": "Ensino Fundamental Incompleto", "ordem": 1},
            {"value": "fundamental_completo", "label": "Ensino Fundamental Completo", "ordem": 2},
            {"value": "medio_cursando", "label": "Ensino Médio Cursando", "ordem": 3},
            {"value": "medio_completo", "label": "Ensino Médio Completo", "ordem": 4},
            {"value": "superior_cursando", "label": "Ensino Superior Cursando", "ordem": 5},
            {"value": "superior_completo", "label": "Ensino Superior Completo", "ordem": 6},
            {"value": "pos_graduacao", "label": "Pós-Graduação", "ordem": 7}
        ]
    }


# ==================== ENDPOINTS - TEMPLATES ====================

class TemplateEmailRequest(BaseModel):
    tipo: str = Field(..., description="Tipo do template")
    dados: dict = Field(..., description="Dados para substituição no template")
    formato: str = Field(default="html", description="Formato: html ou texto")


class TemplateWhatsAppRequest(BaseModel):
    tipo: str = Field(..., description="Tipo do template")
    dados: dict = Field(..., description="Dados para substituição no template")
    telefone: Optional[str] = Field(None, description="Telefone para gerar link WhatsApp")


@router.get("/templates")
async def listar_templates():
    """Lista todos os templates de mensagem disponíveis"""
    return get_templates_disponiveis()


@router.get("/templates/email")
async def listar_templates_email():
    """Lista templates de e-mail disponíveis com seus campos"""
    templates = []
    for nome, template in EMAIL_TEMPLATES.items():
        # Extrair placeholders do template
        import re
        placeholders = list(set(re.findall(r'\{(\w+)\}', template["assunto"] + template["corpo_texto"])))
        templates.append({
            "nome": nome,
            "assunto_exemplo": template["assunto"],
            "campos_necessarios": placeholders
        })
    return {"templates": templates}


@router.get("/templates/whatsapp")
async def listar_templates_whatsapp():
    """Lista templates de WhatsApp disponíveis com seus campos"""
    templates = []
    for nome, template in WHATSAPP_TEMPLATES.items():
        import re
        placeholders = list(set(re.findall(r'\{(\w+)\}', template["mensagem"])))
        templates.append({
            "nome": nome,
            "campos_necessarios": placeholders
        })
    return {"templates": templates}


@router.post("/templates/email/render")
async def renderizar_template_email(request: TemplateEmailRequest):
    """Renderiza um template de e-mail com os dados fornecidos"""
    try:
        resultado = render_email_template(request.tipo, request.dados, request.formato)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Campo obrigatório faltando: {e}")


@router.post("/templates/whatsapp/render")
async def renderizar_template_whatsapp(request: TemplateWhatsAppRequest):
    """Renderiza um template de WhatsApp e opcionalmente gera link wa.me"""
    try:
        mensagem = render_whatsapp_template(request.tipo, request.dados)
        resultado = {
            "mensagem": mensagem,
            "tipo": request.tipo
        }
        
        if request.telefone:
            resultado["link_whatsapp"] = gerar_link_whatsapp(request.telefone, mensagem)
        
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Campo obrigatório faltando: {e}")
