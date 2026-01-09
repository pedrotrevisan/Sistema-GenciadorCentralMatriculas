"""Implementação do Repositório de Auditoria com MongoDB"""
from typing import List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

from ...domain.repositories import IAuditoriaRepository


class AuditoriaRepositoryMongo(IAuditoriaRepository):
    """Implementação concreta do repositório de auditoria usando MongoDB"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.auditoria

    async def registrar(
        self,
        pedido_id: str,
        usuario_id: str,
        acao: str,
        detalhes: dict
    ) -> None:
        """Registra uma ação de auditoria"""
        registro = {
            "id": str(uuid.uuid4()),
            "pedido_id": pedido_id,
            "usuario_id": usuario_id,
            "acao": acao,
            "detalhes": detalhes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.collection.insert_one(registro)

    async def listar_por_pedido(self, pedido_id: str) -> List[dict]:
        """Lista histórico de auditoria de um pedido"""
        cursor = self.collection.find(
            {"pedido_id": pedido_id},
            {"_id": 0}
        ).sort("timestamp", -1)
        
        return await cursor.to_list(length=100)
