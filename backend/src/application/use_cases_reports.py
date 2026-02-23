"""
Use Cases para Estatísticas e Reports (Dashboard/Gráficos)
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_

from src.infrastructure.persistence.models_documentos import PendenciaDocumentalModel
from src.infrastructure.persistence.models import PedidoModel, ReembolsoModel, PendenciaModel
from src.domain.documentos import StatusDocumentoEnum, TipoDocumentoEnum


class EstatisticasDocumentosUseCase:
    """Use Case: Gerar estatísticas de documentos pendentes"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def obter_resumo_geral(self) -> dict:
        """
        Retorna estatísticas gerais de documentos
        """
        result = await self.session.execute(
            select(
                func.count(PendenciaDocumentalModel.id).label('total'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.PENDENTE, 1), else_=0)).label('pendentes'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.ENVIADO, 1), else_=0)).label('enviados'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.EM_ANALISE, 1), else_=0)).label('em_analise'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.APROVADO, 1), else_=0)).label('aprovados'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.RECUSADO, 1), else_=0)).label('recusados'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.EXPIRADO, 1), else_=0)).label('expirados')
            )
        )
        row = result.one()
        
        total = row.total or 0
        aprovados = row.aprovados or 0
        
        return {
            'total': total,
            'pendentes': row.pendentes or 0,
            'enviados': row.enviados or 0,
            'em_analise': row.em_analise or 0,
            'aprovados': aprovados,
            'recusados': row.recusados or 0,
            'expirados': row.expirados or 0,
            'taxa_aprovacao': round((aprovados / total * 100), 2) if total > 0 else 0,
            'total_em_aberto': (row.pendentes or 0) + (row.enviados or 0) + (row.em_analise or 0)
        }
    
    async def obter_por_tipo_documento(self) -> List[dict]:
        """
        Retorna estatísticas agrupadas por tipo de documento
        Para gráfico de barras/pizza
        """
        result = await self.session.execute(
            select(
                PendenciaDocumentalModel.tipo,
                func.count(PendenciaDocumentalModel.id).label('total'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.PENDENTE, 1), else_=0)).label('pendentes'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.APROVADO, 1), else_=0)).label('aprovados'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.RECUSADO, 1), else_=0)).label('recusados')
            )
            .group_by(PendenciaDocumentalModel.tipo)
            .order_by(func.count(PendenciaDocumentalModel.id).desc())
        )
        
        from src.domain.documentos import TIPO_DOCUMENTO_LABELS
        
        return [
            {
                'tipo': row.tipo.value,
                'tipo_label': TIPO_DOCUMENTO_LABELS.get(row.tipo, row.tipo.value),
                'total': row.total,
                'pendentes': row.pendentes or 0,
                'aprovados': row.aprovados or 0,
                'recusados': row.recusados or 0,
                'taxa_aprovacao': round((row.aprovados / row.total * 100), 2) if row.total > 0 else 0
            }
            for row in result
        ]
    
    async def obter_proximos_vencer(self, dias: int = 3) -> List[dict]:
        """
        Retorna documentos prestes a expirar
        Para alertas no dashboard
        """
        data_limite = datetime.now() + timedelta(days=dias)
        
        result = await self.session.execute(
            select(PendenciaDocumentalModel)
            .where(
                and_(
                    PendenciaDocumentalModel.status == StatusDocumentoEnum.PENDENTE,
                    PendenciaDocumentalModel.prazo_limite.isnot(None),
                    PendenciaDocumentalModel.prazo_limite <= data_limite,
                    PendenciaDocumentalModel.prazo_limite > datetime.now()
                )
            )
            .order_by(PendenciaDocumentalModel.prazo_limite)
            .limit(10)
        )
        
        from src.domain.documentos import TIPO_DOCUMENTO_LABELS
        
        return [
            {
                'id': p.id,
                'pedido_id': p.pedido_id,
                'tipo': p.tipo.value,
                'tipo_label': TIPO_DOCUMENTO_LABELS.get(p.tipo, p.tipo.value),
                'prazo_limite': p.prazo_limite.isoformat() if p.prazo_limite else None,
                'dias_restantes': (p.prazo_limite - datetime.now()).days if p.prazo_limite else None,
                'prioridade': p.prioridade.value
            }
            for p in result.scalars().all()
        ]


class EstatisticasGeralUseCase:
    """Use Case: Gerar estatísticas gerais do sistema para KPIs"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def obter_kpis_matriculas(self) -> dict:
        """
        KPIs principais de matrículas
        """
        # Total de pedidos por status
        status_result = await self.session.execute(
            select(
                PedidoModel.status,
                func.count(PedidoModel.id).label('total')
            )
            .group_by(PedidoModel.status)
        )
        
        status_counts = {row.status: row.total for row in status_result}
        total_pedidos = sum(status_counts.values())
        
        # Pedidos este mês
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        mes_result = await self.session.execute(
            select(func.count(PedidoModel.id))
            .where(PedidoModel.created_at >= inicio_mes)
        )
        pedidos_mes = mes_result.scalar() or 0
        
        # Taxa de conversão (aprovados + realizados + exportados / total)
        convertidos = (
            status_counts.get('aprovado', 0) + 
            status_counts.get('realizado', 0) + 
            status_counts.get('exportado', 0)
        )
        taxa_conversao = round((convertidos / total_pedidos * 100), 1) if total_pedidos > 0 else 0
        
        return {
            'total_pedidos': total_pedidos,
            'pedidos_mes': pedidos_mes,
            'taxa_conversao': taxa_conversao,
            'por_status': status_counts,
            'pendentes': status_counts.get('pendente', 0),
            'em_analise': status_counts.get('em_analise', 0),
            'aprovados': status_counts.get('aprovado', 0),
            'realizados': status_counts.get('realizado', 0),
            'exportados': status_counts.get('exportado', 0),
            'cancelados': status_counts.get('cancelado', 0)
        }
    
    async def obter_evolucao_mensal(self, meses: int = 6) -> List[dict]:
        """
        Evolução mensal de matrículas para gráfico de linha
        """
        data_inicio = datetime.now() - timedelta(days=meses * 30)
        
        result = await self.session.execute(
            select(
                func.strftime('%Y-%m', PedidoModel.created_at).label('mes'),
                func.count(PedidoModel.id).label('total'),
                func.sum(case((PedidoModel.status.in_(['aprovado', 'realizado', 'exportado']), 1), else_=0)).label('convertidos')
            )
            .where(PedidoModel.created_at >= data_inicio)
            .group_by(func.strftime('%Y-%m', PedidoModel.created_at))
            .order_by(func.strftime('%Y-%m', PedidoModel.created_at))
        )
        
        meses_map = {
            '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
            '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
            '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
        }
        
        return [
            {
                'mes': row.mes,
                'mes_label': meses_map.get(row.mes.split('-')[1], row.mes) if row.mes else '',
                'total': row.total,
                'convertidos': row.convertidos or 0,
                'taxa_conversao': round((row.convertidos / row.total * 100), 1) if row.total > 0 else 0
            }
            for row in result
        ]
    
    async def obter_kpis_reembolsos(self) -> dict:
        """
        KPIs de reembolsos
        """
        result = await self.session.execute(
            select(
                func.count(ReembolsoModel.id).label('total'),
                func.sum(case((ReembolsoModel.status == 'aberto', 1), else_=0)).label('abertos'),
                func.sum(case((ReembolsoModel.status == 'aguardando_dados', 1), else_=0)).label('aguardando'),
                func.sum(case((ReembolsoModel.status == 'enviado_financeiro', 1), else_=0)).label('no_financeiro'),
                func.sum(case((ReembolsoModel.status == 'pago', 1), else_=0)).label('pagos'),
                func.sum(case((ReembolsoModel.status == 'cancelado', 1), else_=0)).label('cancelados'),
                func.sum(ReembolsoModel.valor).label('valor_total'),
                func.sum(case((ReembolsoModel.status == 'pago', ReembolsoModel.valor), else_=0)).label('valor_pago')
            )
        )
        row = result.one()
        
        return {
            'total': row.total or 0,
            'abertos': row.abertos or 0,
            'aguardando': row.aguardando or 0,
            'no_financeiro': row.no_financeiro or 0,
            'pagos': row.pagos or 0,
            'cancelados': row.cancelados or 0,
            'valor_total': float(row.valor_total or 0),
            'valor_pago': float(row.valor_pago or 0),
            'pendentes': (row.abertos or 0) + (row.aguardando or 0) + (row.no_financeiro or 0)
        }
    
    async def obter_kpis_pendencias(self) -> dict:
        """
        KPIs de pendências documentais (sistema antigo)
        """
        result = await self.session.execute(
            select(
                func.count(PendenciaModel.id).label('total'),
                func.sum(case((PendenciaModel.status == 'pendente', 1), else_=0)).label('pendentes'),
                func.sum(case((PendenciaModel.status == 'aguardando_aluno', 1), else_=0)).label('aguardando'),
                func.sum(case((PendenciaModel.status == 'em_analise', 1), else_=0)).label('em_analise'),
                func.sum(case((PendenciaModel.status == 'aprovado', 1), else_=0)).label('aprovados'),
                func.sum(case((PendenciaModel.status == 'rejeitado', 1), else_=0)).label('rejeitados')
            )
        )
        row = result.one()
        
        total = row.total or 0
        aprovados = row.aprovados or 0
        
        return {
            'total': total,
            'pendentes': row.pendentes or 0,
            'aguardando': row.aguardando or 0,
            'em_analise': row.em_analise or 0,
            'aprovados': aprovados,
            'rejeitados': row.rejeitados or 0,
            'em_aberto': (row.pendentes or 0) + (row.aguardando or 0) + (row.em_analise or 0),
            'taxa_aprovacao': round((aprovados / total * 100), 2) if total > 0 else 0
        }


class DashboardBIUseCase:
    """Use Case: Dados completos para Dashboard de BI"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.estatisticas_geral = EstatisticasGeralUseCase(session)
        self.estatisticas_docs = EstatisticasDocumentosUseCase(session)
    
    async def obter_dashboard_completo(self) -> dict:
        """
        Retorna todos os dados necessários para o Dashboard de BI
        """
        # Executar todas as consultas
        kpis_matriculas = await self.estatisticas_geral.obter_kpis_matriculas()
        evolucao_mensal = await self.estatisticas_geral.obter_evolucao_mensal()
        kpis_reembolsos = await self.estatisticas_geral.obter_kpis_reembolsos()
        kpis_pendencias = await self.estatisticas_geral.obter_kpis_pendencias()
        
        return {
            'matriculas': kpis_matriculas,
            'evolucao_mensal': evolucao_mensal,
            'reembolsos': kpis_reembolsos,
            'pendencias': kpis_pendencias,
            'resumo': {
                'total_matriculas': kpis_matriculas['total_pedidos'],
                'matriculas_mes': kpis_matriculas['pedidos_mes'],
                'taxa_conversao': kpis_matriculas['taxa_conversao'],
                'pendencias_abertas': kpis_pendencias['em_aberto'],
                'reembolsos_pendentes': kpis_reembolsos['pendentes']
            }
        }
