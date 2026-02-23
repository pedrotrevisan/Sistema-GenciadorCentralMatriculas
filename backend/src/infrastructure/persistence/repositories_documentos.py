"""
Repositório para Pendências Documentais
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, case
from datetime import datetime

from src.domain.entities_documentos import PendenciaDocumental
from src.domain.documentos import TipoDocumentoEnum, StatusDocumentoEnum, PrioridadeDocumentoEnum
from src.infrastructure.persistence.models_documentos import PendenciaDocumentalModel


class PendenciaDocumentalRepository:
    """Repositório para operações com pendências documentais"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def salvar(self, pendencia: PendenciaDocumental) -> None:
        """Salva ou atualiza uma pendência"""
        pendencia_model = PendenciaDocumentalModel(
            id=pendencia.id,
            pedido_id=pendencia.pedido_id,
            aluno_id=pendencia.aluno_id,
            tipo=pendencia.tipo,
            status=pendencia.status,
            prioridade=pendencia.prioridade,
            obrigatorio=pendencia.obrigatorio,
            descricao=pendencia.descricao,
            observacoes=pendencia.observacoes,
            arquivo_url=pendencia.arquivo_url,
            arquivo_nome=pendencia.arquivo_nome,
            arquivo_tamanho=pendencia.arquivo_tamanho,
            prazo_limite=pendencia.prazo_limite,
            data_envio=pendencia.data_envio,
            data_validacao=pendencia.data_validacao,
            validado_por_id=pendencia.validado_por_id,
            validado_por_nome=pendencia.validado_por_nome,
            motivo_recusa=pendencia.motivo_recusa,
            criado_por_id=pendencia.criado_por_id,
            criado_por_nome=pendencia.criado_por_nome,
            criado_em=pendencia.criado_em,
            atualizado_em=datetime.now()
        )
        
        # Use merge instead of add to handle both insert and update
        await self.session.merge(pendencia_model)
        await self.session.flush()
    
    async def buscar_por_id(self, pendencia_id: str) -> Optional[PendenciaDocumental]:
        """Busca pendência por ID"""
        result = await self.session.execute(
            select(PendenciaDocumentalModel).where(PendenciaDocumentalModel.id == pendencia_id)
        )
        pendencia_model = result.scalar_one_or_none()
        
        if not pendencia_model:
            return None
        
        return self._model_to_entity(pendencia_model)
    
    async def listar_por_pedido(
        self,
        pedido_id: str,
        status: Optional[StatusDocumentoEnum] = None
    ) -> List[PendenciaDocumental]:
        """Lista pendências de um pedido"""
        query = select(PendenciaDocumentalModel).where(
            PendenciaDocumentalModel.pedido_id == pedido_id
        )
        
        if status:
            query = query.where(PendenciaDocumentalModel.status == status)
        
        query = query.order_by(
            PendenciaDocumentalModel.obrigatorio.desc(),
            PendenciaDocumentalModel.prazo_limite
        )
        
        result = await self.session.execute(query)
        pendencias_model = result.scalars().all()
        
        return [self._model_to_entity(p) for p in pendencias_model]
    
    async def contar_pendentes_por_pedido(self, pedido_id: str) -> int:
        """Conta quantos documentos ainda estão pendentes"""
        result = await self.session.execute(
            select(func.count(PendenciaDocumentalModel.id))
            .where(
                and_(
                    PendenciaDocumentalModel.pedido_id == pedido_id,
                    PendenciaDocumentalModel.status.in_([
                        StatusDocumentoEnum.PENDENTE,
                        StatusDocumentoEnum.ENVIADO,
                        StatusDocumentoEnum.EM_ANALISE
                    ])
                )
            )
        )
        return result.scalar()
    
    async def listar_para_validacao(self, limite: Optional[int] = None) -> List[PendenciaDocumental]:
        """Lista documentos aguardando validação"""
        query = (
            select(PendenciaDocumentalModel)
            .where(PendenciaDocumentalModel.status == StatusDocumentoEnum.ENVIADO)
            .order_by(
                PendenciaDocumentalModel.prioridade.desc(),
                PendenciaDocumentalModel.data_envio
            )
        )
        
        if limite:
            query = query.limit(limite)
        
        result = await self.session.execute(query)
        pendencias_model = result.scalars().all()
        
        return [self._model_to_entity(p) for p in pendencias_model]
    
    async def listar_proximas_expirar(self, dias: int = 3) -> List[PendenciaDocumental]:
        """Lista pendências que vão expirar nos próximos N dias"""
        data_limite = datetime.now()
        from datetime import timedelta
        data_limite_futura = data_limite + timedelta(days=dias)
        
        query = (
            select(PendenciaDocumentalModel)
            .where(
                and_(
                    PendenciaDocumentalModel.status == StatusDocumentoEnum.PENDENTE,
                    PendenciaDocumentalModel.prazo_limite.isnot(None),
                    PendenciaDocumentalModel.prazo_limite <= data_limite_futura
                )
            )
            .order_by(PendenciaDocumentalModel.prazo_limite)
        )
        
        result = await self.session.execute(query)
        pendencias_model = result.scalars().all()
        
        return [self._model_to_entity(p) for p in pendencias_model]
    
    # ========== MÉTODOS PARA ESTATÍSTICAS E GRÁFICOS ==========
    
    async def obter_estatisticas_gerais(self) -> dict:
        """Estatísticas gerais de documentos"""
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
        stats = result.one()
        
        total = stats.total or 0
        pendentes = stats.pendentes or 0
        aprovados = stats.aprovados or 0
        
        return {
            'total': total,
            'pendentes': pendentes,
            'enviados': stats.enviados or 0,
            'em_analise': stats.em_analise or 0,
            'aprovados': aprovados,
            'recusados': stats.recusados or 0,
            'expirados': stats.expirados or 0,
            'taxa_aprovacao': round((aprovados / total * 100), 2) if total > 0 else 0
        }
    
    async def obter_estatisticas_por_tipo(self) -> List[dict]:
        """Estatísticas agrupadas por tipo de documento"""
        result = await self.session.execute(
            select(
                PendenciaDocumentalModel.tipo,
                func.count(PendenciaDocumentalModel.id).label('total'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.PENDENTE, 1), else_=0)).label('pendentes'),
                func.sum(case((PendenciaDocumentalModel.status == StatusDocumentoEnum.APROVADO, 1), else_=0)).label('aprovados')
            )
            .group_by(PendenciaDocumentalModel.tipo)
            .order_by(func.count(PendenciaDocumentalModel.id).desc())
        )
        
        stats = result.all()
        
        return [
            {
                'tipo': row.tipo.value,
                'total': row.total,
                'pendentes': row.pendentes or 0,
                'aprovados': row.aprovados or 0,
                'taxa_aprovacao': round((row.aprovados / row.total * 100), 2) if row.total > 0 else 0
            }
            for row in stats
        ]
    
    def _model_to_entity(self, model: PendenciaDocumentalModel) -> PendenciaDocumental:
        """Converte model para entidade"""
        return PendenciaDocumental(
            id=model.id,
            pedido_id=model.pedido_id,
            aluno_id=model.aluno_id,
            tipo=TipoDocumentoEnum(model.tipo),
            status=StatusDocumentoEnum(model.status),
            prioridade=PrioridadeDocumentoEnum(model.prioridade),
            obrigatorio=model.obrigatorio,
            descricao=model.descricao,
            observacoes=model.observacoes,
            arquivo_url=model.arquivo_url,
            arquivo_nome=model.arquivo_nome,
            arquivo_tamanho=model.arquivo_tamanho,
            prazo_limite=model.prazo_limite,
            data_envio=model.data_envio,
            data_validacao=model.data_validacao,
            validado_por_id=model.validado_por_id,
            validado_por_nome=model.validado_por_nome,
            motivo_recusa=model.motivo_recusa,
            criado_por_id=model.criado_por_id,
            criado_por_nome=model.criado_por_nome,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em
        )
