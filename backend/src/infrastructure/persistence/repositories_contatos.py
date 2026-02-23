"""
Repository - Módulo de Log de Contatos (Fase 3)
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, desc

from src.infrastructure.persistence.models_contatos import LogContatoModel
from src.domain.entities_contatos import (
    ContatoEntity, 
    ResumoContatosPedido,
    TipoContatoEnum,
    ResultadoContatoEnum,
    MotivoContatoEnum
)


class LogContatoRepository:
    """
    Repositório para operações de Log de Contatos
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def salvar(self, entity: ContatoEntity) -> ContatoEntity:
        """Salva ou atualiza um contato"""
        # Verificar se já existe
        result = await self.session.execute(
            select(LogContatoModel).where(LogContatoModel.id == entity.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Atualizar campos
            existing.tipo = entity.tipo
            existing.resultado = entity.resultado
            existing.motivo = entity.motivo
            existing.descricao = entity.descricao
            existing.contato_nome = entity.contato_nome
            existing.contato_telefone = entity.contato_telefone
            existing.contato_email = entity.contato_email
            existing.data_retorno = entity.data_retorno
            existing.retorno_realizado = entity.retorno_realizado
            existing.atualizado_em = datetime.now()
            model = existing
        else:
            # Criar novo
            model = LogContatoModel.from_entity(entity)
            self.session.add(model)
        
        await self.session.flush()
        return model.to_entity()
    
    async def buscar_por_id(self, contato_id: str) -> Optional[ContatoEntity]:
        """Busca contato por ID"""
        result = await self.session.execute(
            select(LogContatoModel).where(LogContatoModel.id == contato_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def listar_por_pedido(
        self, 
        pedido_id: str,
        tipo: Optional[TipoContatoEnum] = None,
        resultado: Optional[ResultadoContatoEnum] = None,
        limite: int = 50
    ) -> List[ContatoEntity]:
        """Lista contatos de um pedido"""
        query = select(LogContatoModel).where(LogContatoModel.pedido_id == pedido_id)
        
        if tipo:
            query = query.where(LogContatoModel.tipo == tipo)
        if resultado:
            query = query.where(LogContatoModel.resultado == resultado)
        
        query = query.order_by(desc(LogContatoModel.criado_em)).limit(limite)
        
        result = await self.session.execute(query)
        return [m.to_entity() for m in result.scalars().all()]
    
    async def obter_resumo_pedido(self, pedido_id: str) -> ResumoContatosPedido:
        """Obtém resumo de contatos de um pedido"""
        # Estatísticas gerais
        stats_result = await self.session.execute(
            select(
                func.count(LogContatoModel.id).label('total'),
                func.sum(case(
                    (LogContatoModel.resultado == ResultadoContatoEnum.SUCESSO, 1), 
                    else_=0
                )).label('sucesso'),
                func.sum(case(
                    (and_(
                        LogContatoModel.data_retorno.isnot(None),
                        LogContatoModel.retorno_realizado == False
                    ), 1),
                    else_=0
                )).label('retornos_pendentes')
            ).where(LogContatoModel.pedido_id == pedido_id)
        )
        stats = stats_result.one()
        
        # Último contato
        ultimo_result = await self.session.execute(
            select(LogContatoModel)
            .where(LogContatoModel.pedido_id == pedido_id)
            .order_by(desc(LogContatoModel.criado_em))
            .limit(1)
        )
        ultimo = ultimo_result.scalar_one_or_none()
        
        total = stats.total or 0
        sucesso = stats.sucesso or 0
        
        return ResumoContatosPedido(
            pedido_id=pedido_id,
            total_contatos=total,
            contatos_sucesso=sucesso,
            contatos_sem_sucesso=total - sucesso,
            ultimo_contato=ultimo.criado_em if ultimo else None,
            ultimo_tipo=ultimo.tipo if ultimo else None,
            retornos_pendentes=stats.retornos_pendentes or 0
        )
    
    async def listar_retornos_pendentes(self, limite: int = 50) -> List[ContatoEntity]:
        """Lista contatos com retorno pendente"""
        result = await self.session.execute(
            select(LogContatoModel)
            .where(
                and_(
                    LogContatoModel.data_retorno.isnot(None),
                    LogContatoModel.retorno_realizado == False,
                    LogContatoModel.data_retorno <= datetime.now() + timedelta(days=1)
                )
            )
            .order_by(LogContatoModel.data_retorno)
            .limit(limite)
        )
        return [m.to_entity() for m in result.scalars().all()]
    
    async def listar_retornos_atrasados(self) -> List[ContatoEntity]:
        """Lista retornos que já passaram da data"""
        result = await self.session.execute(
            select(LogContatoModel)
            .where(
                and_(
                    LogContatoModel.data_retorno.isnot(None),
                    LogContatoModel.retorno_realizado == False,
                    LogContatoModel.data_retorno < datetime.now()
                )
            )
            .order_by(LogContatoModel.data_retorno)
        )
        return [m.to_entity() for m in result.scalars().all()]
    
    async def obter_estatisticas_gerais(self) -> dict:
        """Obtém estatísticas gerais de contatos"""
        # Por tipo
        tipo_result = await self.session.execute(
            select(
                LogContatoModel.tipo,
                func.count(LogContatoModel.id).label('total')
            ).group_by(LogContatoModel.tipo)
        )
        por_tipo = {row.tipo.value: row.total for row in tipo_result}
        
        # Por resultado
        resultado_result = await self.session.execute(
            select(
                LogContatoModel.resultado,
                func.count(LogContatoModel.id).label('total')
            ).group_by(LogContatoModel.resultado)
        )
        por_resultado = {row.resultado.value: row.total for row in resultado_result}
        
        # Totais
        totais_result = await self.session.execute(
            select(
                func.count(LogContatoModel.id).label('total'),
                func.sum(case(
                    (LogContatoModel.resultado == ResultadoContatoEnum.SUCESSO, 1),
                    else_=0
                )).label('sucesso'),
                func.sum(case(
                    (and_(
                        LogContatoModel.data_retorno.isnot(None),
                        LogContatoModel.retorno_realizado == False
                    ), 1),
                    else_=0
                )).label('retornos_pendentes')
            )
        )
        totais = totais_result.one()
        
        # Contatos hoje
        hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_result = await self.session.execute(
            select(func.count(LogContatoModel.id))
            .where(LogContatoModel.criado_em >= hoje_inicio)
        )
        contatos_hoje = hoje_result.scalar() or 0
        
        total = totais.total or 0
        sucesso = totais.sucesso or 0
        
        return {
            "total": total,
            "sucesso": sucesso,
            "sem_sucesso": total - sucesso,
            "taxa_sucesso": round((sucesso / total * 100), 1) if total > 0 else 0,
            "retornos_pendentes": totais.retornos_pendentes or 0,
            "contatos_hoje": contatos_hoje,
            "por_tipo": por_tipo,
            "por_resultado": por_resultado
        }
    
    async def excluir(self, contato_id: str) -> bool:
        """Exclui um contato"""
        result = await self.session.execute(
            select(LogContatoModel).where(LogContatoModel.id == contato_id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False
