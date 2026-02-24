"""Router para Fluxo de Cancelamento e Documentos TOTVS - CAC SENAI"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List

from src.services.cancelamento_service import (
    CancelamentoService,
    TipoCancelamento,
    get_documentos_escolaridade,
    get_fluxo_validacao_escolaridade,
    get_responsabilidades_cancelamento,
    get_tipos_cancelamento,
    DOCUMENTOS_ESCOLARIDADE_TOTVS,
    PRAZO_NRM_HORAS
)

router = APIRouter(prefix="/cancelamento", tags=["Cancelamento e Documentos TOTVS"])


# ==================== SCHEMAS ====================

class SolicitarCancelamentoRequest(BaseModel):
    pedido_id: str = Field(..., description="ID do pedido a cancelar")
    tipo: str = Field(..., description="Tipo de cancelamento")
    motivo: str = Field(..., description="Motivo do cancelamento")
    solicitante_id: str = Field(..., description="ID do solicitante")
    solicitante_nome: str = Field(..., description="Nome do solicitante")


class RespostaNRMRequest(BaseModel):
    pedido_id: str = Field(..., description="ID do pedido")
    revertido: bool = Field(..., description="Se o NRM conseguiu reverter")
    observacoes: str = Field(default="", description="Observações do NRM")


# ==================== ENDPOINTS DE CANCELAMENTO ====================

@router.post("/solicitar")
async def solicitar_cancelamento(request: SolicitarCancelamentoRequest):
    """
    Inicia processo de cancelamento de matrícula.
    
    Fluxo:
    - Se solicitado pelo candidato → Encaminha para NRM (48h para reverter)
    - Se pelo SENAI ou automático → Cancela direto
    
    Responsabilidades após confirmação:
    - PRÉ-ANÁLISE / ANÁLISE DOCUMENTAL → CAC (dados bancários + chamado financeiro)
    - MATRICULADO → CAA (orientar Portal do Aluno)
    """
    from server import async_session
    
    try:
        tipo = TipoCancelamento(request.tipo)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipo de cancelamento inválido: {request.tipo}")
    
    async with async_session() as session:
        service = CancelamentoService(session)
        resultado = await service.solicitar_cancelamento(
            pedido_id=request.pedido_id,
            tipo=tipo,
            motivo=request.motivo,
            solicitante_id=request.solicitante_id,
            solicitante_nome=request.solicitante_nome
        )
        return resultado


@router.post("/resposta-nrm")
async def registrar_resposta_nrm(request: RespostaNRMRequest):
    """
    Registra resposta do NRM sobre tentativa de reversão.
    
    - Se revertido: Matrícula continua normalmente
    - Se não revertido: Prossegue com cancelamento (CAC ou CAA assume)
    """
    from server import async_session
    
    async with async_session() as session:
        service = CancelamentoService(session)
        resultado = await service.registrar_resposta_nrm(
            pedido_id=request.pedido_id,
            revertido=request.revertido,
            observacoes=request.observacoes
        )
        return resultado


@router.get("/verificar-prazo/{pedido_id}")
async def verificar_prazo_nrm(pedido_id: str):
    """
    Verifica se prazo de 48h do NRM já expirou.
    """
    from server import async_session
    
    async with async_session() as session:
        service = CancelamentoService(session)
        resultado = await service.verificar_prazo_nrm(pedido_id)
        return resultado


@router.get("/tipos")
async def listar_tipos_cancelamento():
    """Lista tipos de cancelamento disponíveis"""
    return {
        "tipos": get_tipos_cancelamento(),
        "descricoes": {
            "solicitado_candidato": "Cancelamento solicitado pelo próprio candidato - encaminha para NRM",
            "senai": "Cancelamento realizado pelo SENAI (falta de documentos, etc)",
            "prazo_expirado": "Cancelamento automático por prazo de 5 dias expirado",
            "nao_atende_requisito": "Candidato não atende pré-requisitos do curso"
        }
    }


@router.get("/responsabilidades")
async def listar_responsabilidades():
    """
    Lista responsabilidades por status de pedido.
    
    Baseado no e-mail CAC:
    - PRÉ-ANÁLISE / ANÁLISE DOCUMENTAL → CAC (dados bancários + chamado financeiro)
    - MATRICULADO → CAA (orientar Portal do Aluno)
    """
    return {
        "responsabilidades": get_responsabilidades_cancelamento(),
        "prazo_nrm_horas": PRAZO_NRM_HORAS,
        "fluxo": {
            "1": "Candidato solicita cancelamento",
            "2": "CAC local recebe e repassa para NRM",
            "3": f"NRM tem {PRAZO_NRM_HORAS}h para tentar reverter",
            "4_a": "Se candidato confirma cancelamento - ver responsabilidades por status",
            "4_b": "Se NRM reverte - matrícula continua normalmente"
        }
    }


# ==================== ENDPOINTS DE DOCUMENTOS TOTVS ====================

@router.get("/documentos/escolaridade")
async def listar_documentos_escolaridade():
    """
    Lista documentos de escolaridade do TOTVS.
    
    Códigos conforme e-mail CAC:
    - 136, 137: Escolaridade geral
    - 93: Data de entrega
    - 182: Histórico Escolar - Ensino Médio
    - 165: Atestado de Conclusão do Ensino Médio
    """
    return {
        "documentos": get_documentos_escolaridade(),
        "nota": "Códigos conforme sistema TOTVS Educacional"
    }


@router.get("/documentos/escolaridade/{codigo}")
async def get_documento_escolaridade(codigo: str):
    """Retorna detalhes de um documento de escolaridade específico"""
    doc = DOCUMENTOS_ESCOLARIDADE_TOTVS.get(codigo)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Documento não encontrado: {codigo}")
    return {"codigo": codigo, **doc}


@router.get("/documentos/fluxo-validacao")
async def get_fluxos_validacao():
    """
    Retorna fluxos de validação de documentos de escolaridade.
    
    Conforme e-mail CAC:
    
    1. Histórico Escolar:
       - Validar: 136, 137, 93
       - Incluir: 182
       - Resultado: MAC (Matrícula Confirmada)
    
    2. Atestado de Matrícula (cursando 2º ano EM):
       - Validar: 136, 137, 93
       - Não inclui documento adicional
       - Resultado: MAC
    
    3. Atestado de Conclusão (sem Histórico):
       - Validar: 136, 137, 93
       - Incluir: 165
       - Resultado: MAC
    """
    return {
        "fluxos": get_fluxo_validacao_escolaridade(),
        "instrucoes": {
            "validar": "Registrar 'VALIDADO' no documento",
            "incluir": "Adicionar documento ao cadastro do aluno",
            "doc_93": "Registrar 'VALIDADO + data entrega'",
            "atestado_conclusao": "Deve ser atualizado com data de 2025, independente do ano de conclusão"
        }
    }


@router.post("/documentos/validar-escolaridade")
async def validar_escolaridade(
    tipo_documento: str = Query(..., description="historico_escolar, atestado_matricula ou atestado_conclusao"),
    data_entrega: Optional[str] = Query(None, description="Data de entrega (formato: DD/MM/YYYY)")
):
    """
    Retorna ações necessárias para validar documentos de escolaridade.
    
    Args:
        tipo_documento: Tipo de documento apresentado pelo aluno
        data_entrega: Data de entrega do documento
    
    Returns:
        Lista de ações a executar no TOTVS
    """
    fluxos = get_fluxo_validacao_escolaridade()
    fluxo = fluxos.get(tipo_documento)
    
    if not fluxo:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de documento inválido. Use: {', '.join(fluxos.keys())}"
        )
    
    acoes = []
    
    # Documentos a validar
    for cod in fluxo["documentos_validar"]:
        doc = DOCUMENTOS_ESCOLARIDADE_TOTVS.get(cod)
        if cod == "93" and data_entrega:
            acoes.append({
                "codigo": cod,
                "nome": doc["nome"],
                "acao": f"Registrar 'VALIDADO' + data: {data_entrega}"
            })
        else:
            acoes.append({
                "codigo": cod,
                "nome": doc["nome"],
                "acao": "Registrar 'VALIDADO'"
            })
    
    # Documentos a incluir
    for cod in fluxo["documentos_incluir"]:
        doc = DOCUMENTOS_ESCOLARIDADE_TOTVS.get(cod)
        acoes.append({
            "codigo": cod,
            "nome": doc["nome"],
            "acao": f"INCLUIR documento e registrar 'VALIDADO'"
        })
    
    return {
        "tipo_documento": tipo_documento,
        "descricao": fluxo["descricao"],
        "acoes": acoes,
        "status_final": fluxo["status_final"],
        "status_final_descricao": "Situação do candidato: MAC - Matrícula Confirmada"
    }
