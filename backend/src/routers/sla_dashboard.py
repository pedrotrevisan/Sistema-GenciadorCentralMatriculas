"""Router para Dashboard de SLA e Métricas - CAC SENAI"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.services.metricas_sla_service import (
    MetricasSLAService, 
    get_tipos_processo_seletivo,
    SLA_CONFIG,
    TIPOS_PS_INFO
)

router = APIRouter(prefix="/sla", tags=["Dashboard SLA"])


# Dependency para obter sessão do banco
async def get_db_session():
    from server import get_db_session as server_get_db
    async for session in server_get_db():
        yield session


# ==================== ENDPOINTS DE DASHBOARD ====================

@router.get("/dashboard")
async def get_dashboard_sla(session: AsyncSession = Depends(get_db_session)):
    """
    Dashboard completo de SLA com todas as métricas.
    Inclui: resumo geral, métricas por status, produtividade, alertas.
    """
    service = MetricasSLAService(session)
    return await service.get_dashboard_sla_completo()


@router.get("/resumo")
async def get_resumo_geral(session: AsyncSession = Depends(get_db_session)):
    """KPIs gerais do sistema"""
    service = MetricasSLAService(session)
    return await service.get_resumo_geral()


@router.get("/por-status")
async def get_metricas_por_status(session: AsyncSession = Depends(get_db_session)):
    """Métricas detalhadas por status de pedido"""
    service = MetricasSLAService(session)
    return await service.get_metricas_por_status()


@router.get("/produtividade")
async def get_produtividade_atendentes(session: AsyncSession = Depends(get_db_session)):
    """
    Ranking de produtividade por atendente.
    Mostra total atribuído, concluídos, pendentes e taxa de conclusão.
    """
    service = MetricasSLAService(session)
    return await service.get_produtividade_atendentes()


@router.get("/por-tipo-ps")
async def get_sla_por_tipo_ps(session: AsyncSession = Depends(get_db_session)):
    """
    Métricas por tipo de Processo Seletivo.
    Inclui taxa de conversão e cancelamento por tipo.
    """
    service = MetricasSLAService(session)
    return await service.get_sla_por_tipo_ps()


@router.get("/evolucao")
async def get_evolucao_semanal(session: AsyncSession = Depends(get_db_session)):
    """Evolução de pedidos nas últimas 4 semanas"""
    service = MetricasSLAService(session)
    return await service.get_evolucao_semanal()


@router.get("/alertas")
async def get_alertas_sla(session: AsyncSession = Depends(get_db_session)):
    """
    Lista de alertas de SLA críticos.
    Inclui análises atrasadas e pendências expirando.
    """
    service = MetricasSLAService(session)
    return await service.get_alertas_sla()


# ==================== ENDPOINTS DE CONFIGURAÇÃO ====================

@router.get("/config")
async def get_config_sla():
    """Retorna configuração de SLAs por tipo de processo"""
    return {
        "sla_por_etapa": SLA_CONFIG,
        "nota": "SLAs em horas úteis"
    }


@router.get("/tipos-processo-seletivo")
async def listar_tipos_processo_seletivo():
    """
    Lista todos os tipos de Processo Seletivo disponíveis.
    Baseado nos códigos oficiais do SENAI (PS 949, 950, 951, etc.)
    """
    return {
        "tipos": get_tipos_processo_seletivo(),
        "descricao": {
            "ps_949": "Compra de vaga por Empresa no PS Pagante - Fluxo normal com contrato",
            "ps_950": "Transferência de candidatos PAGANTES (curso/turno/filial)",
            "ps_951": "Transferência de candidatos BOLSISTAS (curso/turno/filial) - Também usado quando pagante vira bolsista"
        }
    }
