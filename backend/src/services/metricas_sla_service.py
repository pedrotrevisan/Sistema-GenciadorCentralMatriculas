"""Serviço de Métricas e Dashboard de SLA - CAC SENAI"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_, or_, desc
from enum import Enum
import logging

from src.infrastructure.persistence.models import (
    PedidoModel, PendenciaModel, ReembolsoModel, 
    UsuarioModel, AuditoriaModel
)

logger = logging.getLogger(__name__)


# ==================== TIPOS DE PROCESSO SELETIVO ====================

class TipoProcessoSeletivo(Enum):
    """Tipos de Processo Seletivo conforme e-mail CAC"""
    PS_PAGANTE = "ps_pagante"  # Processo Seletivo Pagante
    PS_BOLSISTA = "ps_bolsista"  # Processo Seletivo Bolsista
    PS_949 = "ps_949"  # Compra de vaga (Empresa) no PS Pagante
    PS_950 = "ps_950"  # Transferência geral de candidatos PAGANTES
    PS_951 = "ps_951"  # Transferência geral de candidatos BOLSISTAS
    MATRICULA_DIRETA = "matricula_direta"  # Matrícula direta (sem PS)
    REINGRESSO = "reingresso"  # Reingresso de aluno


TIPOS_PS_INFO = {
    TipoProcessoSeletivo.PS_PAGANTE: {
        "label": "PS Pagante",
        "descricao": "Processo Seletivo - Candidato Pagante",
        "cor": "blue",
        "requer_contrato": True
    },
    TipoProcessoSeletivo.PS_BOLSISTA: {
        "label": "PS Bolsista",
        "descricao": "Processo Seletivo - Candidato Bolsista (Gratuidade)",
        "cor": "green",
        "requer_contrato": False
    },
    TipoProcessoSeletivo.PS_949: {
        "label": "PS 949 - Compra Vaga Empresa",
        "descricao": "Compra de vaga por Empresa no PS Pagante",
        "cor": "purple",
        "requer_contrato": True
    },
    TipoProcessoSeletivo.PS_950: {
        "label": "PS 950 - Transf. Pagante",
        "descricao": "Transferência de curso/turno/filial - Pagante",
        "cor": "orange",
        "requer_contrato": True
    },
    TipoProcessoSeletivo.PS_951: {
        "label": "PS 951 - Transf. Bolsista",
        "descricao": "Transferência de curso/turno/filial - Bolsista",
        "cor": "teal",
        "requer_contrato": False
    },
    TipoProcessoSeletivo.MATRICULA_DIRETA: {
        "label": "Matrícula Direta",
        "descricao": "Matrícula sem processo seletivo",
        "cor": "gray",
        "requer_contrato": True
    },
    TipoProcessoSeletivo.REINGRESSO: {
        "label": "Reingresso",
        "descricao": "Reingresso de aluno desistente/trancado",
        "cor": "yellow",
        "requer_contrato": True
    }
}


# ==================== CONFIGURAÇÕES DE SLA ====================

SLA_CONFIG = {
    # Status e seus SLAs em horas úteis
    "analise_documental": {
        "sla_horas": 48,  # 48h para análise
        "descricao": "Análise de documentos",
        "responsavel": "CAC"
    },
    "pre_analise": {
        "sla_horas": 24,  # 24h para pré-análise
        "descricao": "Pré-análise documental",
        "responsavel": "CAC"
    },
    "pendencia_documental": {
        "sla_horas": 120,  # 5 dias (120h) para aluno regularizar
        "descricao": "Aguardando documentos do aluno",
        "responsavel": "Aluno"
    },
    "reversao_cancelamento": {
        "sla_horas": 48,  # 48h para NRM tentar reverter
        "descricao": "Tentativa de reversão pelo NRM",
        "responsavel": "NRM"
    },
    "efetivacao_matricula": {
        "sla_horas": 24,  # 24h após aprovação
        "descricao": "Efetivação da matrícula",
        "responsavel": "CAC"
    },
    "reembolso": {
        "sla_horas": 360,  # 15 dias úteis (360h)
        "descricao": "Processamento de reembolso",
        "responsavel": "Financeiro"
    }
}


# ==================== SERVIÇO DE MÉTRICAS SLA ====================

class MetricasSLAService:
    """Serviço para cálculo de métricas e KPIs de SLA"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_dashboard_sla_completo(self) -> Dict[str, Any]:
        """Retorna dashboard completo de SLA"""
        return {
            "resumo_geral": await self.get_resumo_geral(),
            "metricas_por_status": await self.get_metricas_por_status(),
            "produtividade_atendentes": await self.get_produtividade_atendentes(),
            "sla_por_tipo_ps": await self.get_sla_por_tipo_ps(),
            "evolucao_semanal": await self.get_evolucao_semanal(),
            "alertas_sla": await self.get_alertas_sla(),
            "tempo_medio_etapas": await self.get_tempo_medio_etapas(),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_resumo_geral(self) -> Dict[str, Any]:
        """KPIs gerais do sistema"""
        agora = datetime.now(timezone.utc)
        inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Total de pedidos
        result = await self.session.execute(
            select(func.count(PedidoModel.id))
        )
        total_pedidos = result.scalar() or 0
        
        # Pedidos do mês
        result = await self.session.execute(
            select(func.count(PedidoModel.id))
            .where(PedidoModel.created_at >= inicio_mes)
        )
        pedidos_mes = result.scalar() or 0
        
        # Pedidos em aberto (não finalizados e não aprovados ainda)
        status_abertos = ['pendente', 'inscricao', 'em_analise', 'analise_documental', 
                         'documentacao_pendente', 'aguardando_pagamento']
        result = await self.session.execute(
            select(func.count(PedidoModel.id))
            .where(PedidoModel.status.in_(status_abertos))
        )
        pedidos_abertos = result.scalar() or 0
        
        # Taxa de conclusão (aprovados + matriculados + exportados / total)
        result = await self.session.execute(
            select(func.count(PedidoModel.id))
            .where(PedidoModel.status.in_(['aprovado', 'matriculado', 'realizado', 'exportado']))
        )
        pedidos_concluidos = result.scalar() or 0
        taxa_conclusao = (pedidos_concluidos / total_pedidos * 100) if total_pedidos > 0 else 0
        
        # Pendências ativas
        result = await self.session.execute(
            select(func.count(PendenciaModel.id))
            .where(PendenciaModel.status.in_(['pendente', 'aguardando_aluno', 'em_analise']))
        )
        pendencias_ativas = result.scalar() or 0
        
        # Reembolsos pendentes (status que indicam pendência)
        result = await self.session.execute(
            select(func.count(ReembolsoModel.id))
            .where(ReembolsoModel.status.in_(['aberto', 'aguardando_dados', 'solicitado', 'em_analise', 'enviado_financeiro']))
        )
        reembolsos_pendentes = result.scalar() or 0
        
        return {
            "total_pedidos": total_pedidos,
            "pedidos_mes": pedidos_mes,
            "pedidos_abertos": pedidos_abertos,
            "pedidos_concluidos": pedidos_concluidos,
            "taxa_conclusao": round(taxa_conclusao, 1),
            "pendencias_ativas": pendencias_ativas,
            "reembolsos_pendentes": reembolsos_pendentes
        }
    
    async def get_metricas_por_status(self) -> List[Dict[str, Any]]:
        """Métricas detalhadas por status"""
        result = await self.session.execute(
            select(
                PedidoModel.status,
                func.count(PedidoModel.id).label('quantidade'),
                func.avg(
                    func.julianday(func.current_timestamp()) - 
                    func.julianday(PedidoModel.created_at)
                ).label('tempo_medio_dias')
            )
            .group_by(PedidoModel.status)
        )
        rows = result.all()
        
        metricas = []
        for row in rows:
            sla_info = SLA_CONFIG.get(row.status, {})
            sla_horas = sla_info.get('sla_horas', 0)
            tempo_medio_horas = (row.tempo_medio_dias or 0) * 24
            
            dentro_sla = tempo_medio_horas <= sla_horas if sla_horas > 0 else True
            
            metricas.append({
                "status": row.status,
                "quantidade": row.quantidade,
                "tempo_medio_horas": round(tempo_medio_horas, 1),
                "tempo_medio_dias": round(row.tempo_medio_dias or 0, 1),
                "sla_horas": sla_horas,
                "dentro_sla": dentro_sla,
                "percentual_sla": round((sla_horas / tempo_medio_horas * 100) if tempo_medio_horas > 0 else 100, 1)
            })
        
        return metricas
    
    async def get_produtividade_atendentes(self) -> List[Dict[str, Any]]:
        """Produtividade por atendente/responsável"""
        agora = datetime.now(timezone.utc)
        inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Pedidos atribuídos por responsável
        result = await self.session.execute(
            select(
                PedidoModel.responsavel_id,
                PedidoModel.responsavel_nome,
                func.count(PedidoModel.id).label('total_atribuidos'),
                func.sum(case((PedidoModel.status.in_(['matriculado', 'realizado', 'exportado']), 1), else_=0)).label('concluidos'),
                func.sum(case((PedidoModel.status == 'documentacao_pendente', 1), else_=0)).label('pendentes'),
                func.sum(case((PedidoModel.status.in_(['em_analise', 'analise_documental']), 1), else_=0)).label('em_analise')
            )
            .where(PedidoModel.responsavel_id.isnot(None))
            .where(PedidoModel.created_at >= inicio_mes)
            .group_by(PedidoModel.responsavel_id, PedidoModel.responsavel_nome)
            .order_by(desc('total_atribuidos'))
        )
        rows = result.all()
        
        produtividade = []
        for row in rows:
            taxa_conclusao = (row.concluidos / row.total_atribuidos * 100) if row.total_atribuidos > 0 else 0
            produtividade.append({
                "responsavel_id": row.responsavel_id,
                "responsavel_nome": row.responsavel_nome or "Não identificado",
                "total_atribuidos": row.total_atribuidos,
                "concluidos": row.concluidos or 0,
                "pendentes": row.pendentes or 0,
                "em_analise": row.em_analise or 0,
                "taxa_conclusao": round(taxa_conclusao, 1)
            })
        
        return produtividade
    
    async def get_sla_por_tipo_ps(self) -> List[Dict[str, Any]]:
        """Métricas por tipo de processo seletivo"""
        result = await self.session.execute(
            select(
                PedidoModel.tipo_processo_seletivo,
                func.count(PedidoModel.id).label('quantidade'),
                func.sum(case((PedidoModel.status.in_(['matriculado', 'realizado', 'exportado']), 1), else_=0)).label('concluidos'),
                func.sum(case((PedidoModel.status == 'cancelado', 1), else_=0)).label('cancelados')
            )
            .group_by(PedidoModel.tipo_processo_seletivo)
        )
        rows = result.all()
        
        metricas = []
        for row in rows:
            tipo = row.tipo_processo_seletivo or 'nao_informado'
            info = TIPOS_PS_INFO.get(TipoProcessoSeletivo(tipo) if tipo in [e.value for e in TipoProcessoSeletivo] else None, {})
            
            taxa_conversao = ((row.concluidos or 0) / row.quantidade * 100) if row.quantidade > 0 else 0
            taxa_cancelamento = ((row.cancelados or 0) / row.quantidade * 100) if row.quantidade > 0 else 0
            
            metricas.append({
                "tipo_ps": tipo,
                "label": info.get('label', tipo),
                "cor": info.get('cor', 'gray'),
                "quantidade": row.quantidade,
                "concluidos": row.concluidos or 0,
                "cancelados": row.cancelados or 0,
                "taxa_conversao": round(taxa_conversao, 1),
                "taxa_cancelamento": round(taxa_cancelamento, 1)
            })
        
        return metricas
    
    async def get_evolucao_semanal(self) -> List[Dict[str, Any]]:
        """Evolução de pedidos nas últimas 4 semanas"""
        agora = datetime.now(timezone.utc)
        evolucao = []
        
        for i in range(4, 0, -1):
            inicio_semana = agora - timedelta(weeks=i)
            fim_semana = agora - timedelta(weeks=i-1)
            
            # Criados na semana
            result = await self.session.execute(
                select(func.count(PedidoModel.id))
                .where(and_(
                    PedidoModel.created_at >= inicio_semana,
                    PedidoModel.created_at < fim_semana
                ))
            )
            criados = result.scalar() or 0
            
            # Concluídos na semana
            result = await self.session.execute(
                select(func.count(PedidoModel.id))
                .where(and_(
                    PedidoModel.updated_at >= inicio_semana,
                    PedidoModel.updated_at < fim_semana,
                    PedidoModel.status.in_(['matriculado', 'realizado', 'exportado'])
                ))
            )
            concluidos = result.scalar() or 0
            
            evolucao.append({
                "semana": f"Semana {5-i}",
                "inicio": inicio_semana.strftime("%d/%m"),
                "fim": fim_semana.strftime("%d/%m"),
                "criados": criados,
                "concluidos": concluidos
            })
        
        return evolucao
    
    async def get_alertas_sla(self) -> List[Dict[str, Any]]:
        """Pedidos com SLA crítico ou estourado"""
        agora = datetime.now(timezone.utc)
        alertas = []
        
        # Pedidos em análise há mais de 48h
        limite_analise = agora - timedelta(hours=48)
        result = await self.session.execute(
            select(PedidoModel)
            .where(and_(
                PedidoModel.status.in_(['em_analise', 'analise_documental']),
                PedidoModel.updated_at < limite_analise
            ))
            .limit(10)
        )
        pedidos_atrasados = result.scalars().all()
        
        for p in pedidos_atrasados:
            p_updated = p.updated_at
            if p_updated and p_updated.tzinfo is None:
                p_updated = p_updated.replace(tzinfo=timezone.utc)
            horas_atraso = (agora - p_updated).total_seconds() / 3600 if p_updated else 0
            alertas.append({
                "tipo": "analise_atrasada",
                "nivel": "critico" if horas_atraso > 72 else "alerta",
                "pedido_id": p.id,
                "protocolo": p.numero_protocolo,
                "status": p.status,
                "horas_atraso": round(horas_atraso, 1),
                "responsavel": p.responsavel_nome,
                "mensagem": f"Análise atrasada há {round(horas_atraso)}h (SLA: 48h)"
            })
        
        # Pendências aguardando aluno por mais de 4 dias (alerta antes de expirar os 5 dias)
        limite_pendencia = agora - timedelta(days=4)  # 4 dias = quase expirando
        result = await self.session.execute(
            select(PendenciaModel)
            .where(and_(
                PendenciaModel.status.in_(['pendente', 'aguardando_aluno']),
                PendenciaModel.created_at < limite_pendencia
            ))
            .limit(10)
        )
        pendencias_expirando = result.scalars().all()
        
        for pend in pendencias_expirando:
            pend_created = pend.created_at
            if pend_created and pend_created.tzinfo is None:
                pend_created = pend_created.replace(tzinfo=timezone.utc)
            
            # Calcular data limite (5 dias após criação)
            if pend_created:
                data_limite = pend_created + timedelta(days=5)
                horas_restantes = (data_limite - agora).total_seconds() / 3600
                
                alertas.append({
                    "tipo": "pendencia_expirando",
                    "nivel": "critico" if horas_restantes < 0 else "alerta",
                    "pendencia_id": pend.id,
                    "aluno_nome": getattr(pend, 'aluno_nome', None) or 'Não identificado',
                    "documento": pend.documento_nome,
                    "horas_restantes": round(horas_restantes, 1),
                    "mensagem": f"Pendência {'expirada' if horas_restantes < 0 else 'expira em ' + str(round(horas_restantes)) + 'h'}"
                })
        
        return sorted(alertas, key=lambda x: x.get('horas_atraso', x.get('horas_restantes', 0)), reverse=True)
    
    async def get_tempo_medio_etapas(self) -> Dict[str, Any]:
        """Tempo médio em cada etapa do fluxo"""
        # Esta é uma aproximação baseada em auditorias
        result = await self.session.execute(
            select(
                AuditoriaModel.acao,
                func.count(AuditoriaModel.id).label('total')
            )
            .group_by(AuditoriaModel.acao)
        )
        rows = result.all()
        
        etapas = {}
        for row in rows:
            etapas[row.acao] = row.total
        
        return {
            "etapas_processadas": etapas,
            "nota": "Tempos médios baseados em auditorias do sistema"
        }


def get_tipos_processo_seletivo() -> List[Dict[str, Any]]:
    """Retorna lista de tipos de PS com informações"""
    return [
        {
            "value": tipo.value,
            "label": info["label"],
            "descricao": info["descricao"],
            "cor": info["cor"],
            "requer_contrato": info["requer_contrato"]
        }
        for tipo, info in TIPOS_PS_INFO.items()
    ]
