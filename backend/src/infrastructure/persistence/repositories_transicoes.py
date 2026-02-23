"""
Repositório para Transições de Status
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime
import json

from src.domain.entities_transicoes import TransicaoStatus
from src.domain.status_matricula import StatusMatriculaEnum, TipoTransicao
from src.infrastructure.persistence.models_transicoes import TransicaoStatusModel


class TransicaoStatusRepository:
    """Repositório para operações com transições de status"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def salvar(self, transicao: TransicaoStatus) -> None:
        """Salva uma transição"""
        transicao_model = TransicaoStatusModel(
            id=transicao.id,
            pedido_id=transicao.pedido_id,
            status_anterior=transicao.status_anterior,
            status_novo=transicao.status_novo,
            tipo_transicao=transicao.tipo_transicao,
            motivo=transicao.motivo,
            observacoes=transicao.observacoes,
            usuario_id=transicao.usuario_id,
            usuario_nome=transicao.usuario_nome,
            usuario_email=transicao.usuario_email,
            data_transicao=transicao.data_transicao,
            metadados=json.dumps(transicao.metadados) if transicao.metadados else None
        )
        
        self.session.add(transicao_model)
        await self.session.flush()
    
    async def buscar_por_id(self, transicao_id: str) -> Optional[TransicaoStatus]:
        """Busca transição por ID"""
        result = await self.session.execute(
            select(TransicaoStatusModel).where(TransicaoStatusModel.id == transicao_id)
        )
        transicao_model = result.scalar_one_or_none()
        
        if not transicao_model:
            return None
        
        return self._model_to_entity(transicao_model)
    
    async def listar_por_pedido(
        self,
        pedido_id: str,
        limite: Optional[int] = None
    ) -> List[TransicaoStatus]:
        """
        Lista todas as transições de um pedido
        
        Args:
            pedido_id: ID do pedido
            limite: Número máximo de resultados (None = todos)
        
        Returns:
            Lista de transições ordenadas por data (mais recente primeiro)
        """
        query = (
            select(TransicaoStatusModel)
            .where(TransicaoStatusModel.pedido_id == pedido_id)
            .order_by(desc(TransicaoStatusModel.data_transicao))
        )
        
        if limite:
            query = query.limit(limite)
        
        result = await self.session.execute(query)
        transicoes_model = result.scalars().all()
        
        return [self._model_to_entity(t) for t in transicoes_model]
    
    async def obter_ultima_transicao(self, pedido_id: str) -> Optional[TransicaoStatus]:
        """Obtém a última transição de um pedido"""
        result = await self.session.execute(
            select(TransicaoStatusModel)
            .where(TransicaoStatusModel.pedido_id == pedido_id)
            .order_by(desc(TransicaoStatusModel.data_transicao))
            .limit(1)
        )
        transicao_model = result.scalar_one_or_none()
        
        if not transicao_model:
            return None
        
        return self._model_to_entity(transicao_model)
    
    async def contar_por_pedido(self, pedido_id: str) -> int:
        """Conta número de transições de um pedido"""
        from sqlalchemy import func
        
        result = await self.session.execute(
            select(func.count(TransicaoStatusModel.id))
            .where(TransicaoStatusModel.pedido_id == pedido_id)
        )
        return result.scalar()
    
    async def listar_por_status_destino(
        self,
        status: StatusMatriculaEnum,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> List[TransicaoStatus]:
        """
        Lista transições que resultaram em um status específico
        
        Útil para relatórios como "quem foi matriculado hoje?"
        """
        query = select(TransicaoStatusModel).where(
            TransicaoStatusModel.status_novo == status
        )
        
        if data_inicio:
            query = query.where(TransicaoStatusModel.data_transicao >= data_inicio)
        
        if data_fim:
            query = query.where(TransicaoStatusModel.data_transicao <= data_fim)
        
        query = query.order_by(desc(TransicaoStatusModel.data_transicao))
        
        result = await self.session.execute(query)
        transicoes_model = result.scalars().all()
        
        return [self._model_to_entity(t) for t in transicoes_model]
    
    async def listar_por_usuario(
        self,
        usuario_id: str,
        limite: Optional[int] = None
    ) -> List[TransicaoStatus]:
        """Lista transições feitas por um usuário específico"""
        query = (
            select(TransicaoStatusModel)
            .where(TransicaoStatusModel.usuario_id == usuario_id)
            .order_by(desc(TransicaoStatusModel.data_transicao))
        )
        
        if limite:
            query = query.limit(limite)
        
        result = await self.session.execute(query)
        transicoes_model = result.scalars().all()
        
        return [self._model_to_entity(t) for t in transicoes_model]
    
    def _model_to_entity(self, model: TransicaoStatusModel) -> TransicaoStatus:
        """Converte model para entidade"""
        metadados = None
        if model.metadados:
            try:
                metadados = json.loads(model.metadados)
            except:
                pass
        
        return TransicaoStatus(
            id=model.id,
            pedido_id=model.pedido_id,
            status_anterior=StatusMatriculaEnum(model.status_anterior),
            status_novo=StatusMatriculaEnum(model.status_novo),
            tipo_transicao=TipoTransicao(model.tipo_transicao),
            data_transicao=model.data_transicao,
            motivo=model.motivo,
            observacoes=model.observacoes,
            usuario_id=model.usuario_id,
            usuario_nome=model.usuario_nome,
            usuario_email=model.usuario_email,
            metadados=metadados
        )
