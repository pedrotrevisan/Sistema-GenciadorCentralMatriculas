"""Implementação do Repositório de Auditoria com PostgreSQL/SQLAlchemy"""
from typing import List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from src.domain.repositories import IAuditoriaRepository
from ..models import AuditoriaModel


class AuditoriaRepository(IAuditoriaRepository):
    """Implementação concreta do repositório de auditoria usando PostgreSQL"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def registrar(
        self,
        pedido_id: str,
        usuario_id: str,
        acao: str,
        detalhes: dict
    ) -> None:
        """Registra uma ação de auditoria"""
        registro = AuditoriaModel(
            id=str(uuid.uuid4()),
            pedido_id=pedido_id,
            usuario_id=usuario_id,
            acao=acao,
            detalhes=detalhes,
            timestamp=datetime.now(timezone.utc)
        )
        self.session.add(registro)
        await self.session.commit()

    async def listar_por_pedido(self, pedido_id: str) -> List[dict]:
        """Lista histórico de auditoria de um pedido"""
        result = await self.session.execute(
            select(AuditoriaModel)
            .where(AuditoriaModel.pedido_id == pedido_id)
            .order_by(AuditoriaModel.timestamp.desc())
        )
        models = result.scalars().all()
        
        return [
            {
                "id": m.id,
                "pedido_id": m.pedido_id,
                "usuario_id": m.usuario_id,
                "acao": m.acao,
                "detalhes": m.detalhes,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None
            }
            for m in models
        ]
