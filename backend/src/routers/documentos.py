"""
Router do Módulo de Documentos (Clean Architecture - Fase 2)

Este router implementa a API REST para gestão de pendências documentais
usando a nova arquitetura Clean Architecture.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Usuario
from src.domain.documentos import (
    TipoDocumentoEnum, StatusDocumentoEnum, PrioridadeDocumentoEnum,
    TIPO_DOCUMENTO_LABELS, STATUS_DOCUMENTO_LABELS, PRIORIDADE_LABELS,
    STATUS_DOCUMENTO_COLORS, PRIORIDADE_COLORS
)
from src.infrastructure.persistence.repositories_documentos import PendenciaDocumentalRepository
from src.application.use_cases_documentos import (
    CriarPendenciaDocumentalUseCase,
    CriarPendenciasPadraoUseCase,
    ValidarDocumentoUseCase,
    ConsultarPendenciasUseCase,
    ObterEstatisticasDocumentosUseCase
)
from src.application.use_cases_reports import (
    EstatisticasDocumentosUseCase,
    EstatisticasGeralUseCase,
    DashboardBIUseCase
)

from .dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/documentos", tags=["Documentos"])


# ==================== DTOs ====================

class CriarPendenciaDTO(BaseModel):
    pedido_id: str
    tipo: str  # Valor do enum TipoDocumentoEnum
    obrigatorio: bool = True
    prioridade: str = "media"  # baixa, media, alta, urgente
    prazo_dias: int = Field(default=7, ge=1, le=90)
    descricao: Optional[str] = None
    aluno_id: Optional[str] = None


class EnviarDocumentoDTO(BaseModel):
    arquivo_url: str
    arquivo_nome: str
    arquivo_tamanho: str  # Ex: "2.5 MB"


class ValidarDocumentoDTO(BaseModel):
    aprovado: bool
    motivo: Optional[str] = None  # Obrigatório se aprovado=False


class AtualizarObservacoesDTO(BaseModel):
    observacoes: str


# ==================== ENDPOINTS DE REFERÊNCIA ====================

@router.get("/tipos")
async def listar_tipos_documento(
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista todos os tipos de documento disponíveis
    
    Retorna os enums de tipos de documento com labels e informações
    """
    return [
        {
            "value": tipo.value,
            "label": TIPO_DOCUMENTO_LABELS.get(tipo, tipo.value)
        }
        for tipo in TipoDocumentoEnum
    ]


@router.get("/status")
async def listar_status_documento(
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista todos os status de documento disponíveis
    """
    return [
        {
            "value": status.value,
            "label": STATUS_DOCUMENTO_LABELS.get(status, status.value),
            "color": STATUS_DOCUMENTO_COLORS.get(status, "gray")
        }
        for status in StatusDocumentoEnum
    ]


@router.get("/prioridades")
async def listar_prioridades(
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista todas as prioridades disponíveis
    """
    return [
        {
            "value": p.value,
            "label": PRIORIDADE_LABELS.get(p, p.value),
            "color": PRIORIDADE_COLORS.get(p, "gray")
        }
        for p in PrioridadeDocumentoEnum
    ]


# ==================== ENDPOINTS DE ESTATÍSTICAS (DASHBOARD) ====================

@router.get("/stats/resumo")
async def obter_estatisticas_resumo(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Retorna estatísticas resumidas de documentos
    
    Ideal para cards de KPI no dashboard
    """
    use_case = EstatisticasDocumentosUseCase(session)
    return await use_case.obter_resumo_geral()


@router.get("/stats/por-tipo")
async def obter_estatisticas_por_tipo(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Retorna estatísticas agrupadas por tipo de documento
    
    Ideal para gráfico de barras/pizza
    """
    use_case = EstatisticasDocumentosUseCase(session)
    return await use_case.obter_por_tipo_documento()


@router.get("/stats/vencendo")
async def obter_documentos_vencendo(
    dias: int = Query(default=3, ge=1, le=30),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Retorna documentos prestes a expirar
    
    Útil para alertas no dashboard
    """
    use_case = EstatisticasDocumentosUseCase(session)
    return await use_case.obter_proximos_vencer(dias)


# ==================== ENDPOINTS DO DASHBOARD DE BI ====================

@router.get("/bi/matriculas")
async def obter_kpis_matriculas(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    KPIs principais de matrículas para o Dashboard
    """
    use_case = EstatisticasGeralUseCase(session)
    return await use_case.obter_kpis_matriculas()


@router.get("/bi/evolucao")
async def obter_evolucao_mensal(
    meses: int = Query(default=6, ge=1, le=12),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Evolução mensal de matrículas para gráfico de linha
    """
    use_case = EstatisticasGeralUseCase(session)
    return await use_case.obter_evolucao_mensal(meses)


@router.get("/bi/reembolsos")
async def obter_kpis_reembolsos(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    KPIs de reembolsos para o Dashboard
    """
    use_case = EstatisticasGeralUseCase(session)
    return await use_case.obter_kpis_reembolsos()


@router.get("/bi/pendencias")
async def obter_kpis_pendencias(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    KPIs de pendências documentais para o Dashboard
    """
    use_case = EstatisticasGeralUseCase(session)
    return await use_case.obter_kpis_pendencias()


@router.get("/bi/completo")
async def obter_dashboard_completo(
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Dashboard completo de BI com todos os KPIs
    
    Retorna todos os dados necessários em uma única chamada
    """
    use_case = DashboardBIUseCase(session)
    return await use_case.obter_dashboard_completo()


# ==================== CRUD DE PENDÊNCIAS DOCUMENTAIS ====================

@router.post("")
async def criar_pendencia(
    dto: CriarPendenciaDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Cria uma nova pendência documental
    """
    try:
        tipo = TipoDocumentoEnum(dto.tipo)
    except ValueError:
        raise HTTPException(400, f"Tipo de documento inválido: {dto.tipo}")
    
    try:
        prioridade = PrioridadeDocumentoEnum(dto.prioridade)
    except ValueError:
        raise HTTPException(400, f"Prioridade inválida: {dto.prioridade}")
    
    repo = PendenciaDocumentalRepository(session)
    use_case = CriarPendenciaDocumentalUseCase(repo)
    
    pendencia = await use_case.executar(
        pedido_id=dto.pedido_id,
        tipo=tipo,
        usuario=usuario,
        obrigatorio=dto.obrigatorio,
        prioridade=prioridade,
        prazo_dias=dto.prazo_dias,
        descricao=dto.descricao,
        aluno_id=dto.aluno_id
    )
    
    await session.commit()
    
    return {
        "id": pendencia.id,
        "mensagem": "Pendência criada com sucesso",
        "pendencia": pendencia.to_dict()
    }


@router.post("/padrao/{pedido_id}")
async def criar_pendencias_padrao(
    pedido_id: str,
    prazo_dias: int = Query(default=7, ge=1, le=90),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Cria as pendências documentais padrão (obrigatórias) para um pedido
    """
    repo = PendenciaDocumentalRepository(session)
    use_case = CriarPendenciasPadraoUseCase(repo)
    
    pendencias = await use_case.executar(
        pedido_id=pedido_id,
        usuario=usuario,
        prazo_dias=prazo_dias
    )
    
    await session.commit()
    
    return {
        "mensagem": f"{len(pendencias)} pendências padrão criadas",
        "pendencias": [p.to_dict() for p in pendencias]
    }


@router.get("/pedido/{pedido_id}")
async def listar_pendencias_pedido(
    pedido_id: str,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista todas as pendências de um pedido específico
    
    Retorna checklist completo de documentos com estatísticas
    """
    status_enum = None
    if status:
        try:
            status_enum = StatusDocumentoEnum(status)
        except ValueError:
            raise HTTPException(400, f"Status inválido: {status}")
    
    repo = PendenciaDocumentalRepository(session)
    use_case = ConsultarPendenciasUseCase(repo)
    
    return await use_case.executar(pedido_id, status_enum)


@router.get("/{pendencia_id}")
async def buscar_pendencia(
    pendencia_id: str,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Busca detalhes de uma pendência específica
    """
    repo = PendenciaDocumentalRepository(session)
    pendencia = await repo.buscar_por_id(pendencia_id)
    
    if not pendencia:
        raise HTTPException(404, "Pendência não encontrada")
    
    return pendencia.to_dict()


@router.post("/{pendencia_id}/enviar")
async def enviar_documento(
    pendencia_id: str,
    dto: EnviarDocumentoDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Registra o envio de um documento
    """
    repo = PendenciaDocumentalRepository(session)
    pendencia = await repo.buscar_por_id(pendencia_id)
    
    if not pendencia:
        raise HTTPException(404, "Pendência não encontrada")
    
    if not pendencia.esta_pendente():
        raise HTTPException(400, "Documento já foi enviado ou processado")
    
    pendencia.enviar(dto.arquivo_url, dto.arquivo_nome, dto.arquivo_tamanho)
    await repo.salvar(pendencia)
    await session.commit()
    
    return {
        "mensagem": "Documento enviado com sucesso",
        "pendencia": pendencia.to_dict()
    }


@router.post("/{pendencia_id}/validar")
async def validar_documento(
    pendencia_id: str,
    dto: ValidarDocumentoDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Valida (aprova ou recusa) um documento enviado
    """
    repo = PendenciaDocumentalRepository(session)
    use_case = ValidarDocumentoUseCase(repo)
    
    if dto.aprovado:
        pendencia = await use_case.aprovar(pendencia_id, usuario)
        mensagem = "Documento aprovado com sucesso"
    else:
        if not dto.motivo:
            raise HTTPException(400, "Motivo é obrigatório para recusa")
        pendencia = await use_case.recusar(pendencia_id, usuario, dto.motivo)
        mensagem = "Documento recusado"
    
    await session.commit()
    
    return {
        "mensagem": mensagem,
        "pendencia": pendencia.to_dict()
    }


@router.put("/{pendencia_id}/observacoes")
async def atualizar_observacoes(
    pendencia_id: str,
    dto: AtualizarObservacoesDTO,
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Atualiza observações de uma pendência
    """
    repo = PendenciaDocumentalRepository(session)
    pendencia = await repo.buscar_por_id(pendencia_id)
    
    if not pendencia:
        raise HTTPException(404, "Pendência não encontrada")
    
    pendencia.observacoes = dto.observacoes
    await repo.salvar(pendencia)
    await session.commit()
    
    return {
        "mensagem": "Observações atualizadas",
        "pendencia": pendencia.to_dict()
    }


@router.get("/validacao/fila")
async def obter_fila_validacao(
    limite: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Lista documentos aguardando validação
    
    Ordenados por prioridade e data de envio
    """
    repo = PendenciaDocumentalRepository(session)
    pendencias = await repo.listar_para_validacao(limite)
    
    return {
        "total": len(pendencias),
        "pendencias": [p.to_dict() for p in pendencias]
    }
