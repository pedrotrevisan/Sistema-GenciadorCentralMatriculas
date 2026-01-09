"""Implementação do Repositório de Pedidos com MongoDB"""
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.domain.repositories import IPedidoRepository
from src.domain.entities import PedidoMatricula
from src.domain.value_objects import StatusPedido


class PedidoRepositoryMongo(IPedidoRepository):
    """Implementação concreta do repositório de pedidos usando MongoDB"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.pedidos

    async def salvar(self, pedido: PedidoMatricula) -> PedidoMatricula:
        """Salva ou atualiza um pedido"""
        pedido_dict = pedido.to_dict()
        
        existente = await self.collection.find_one({"id": pedido.id})
        
        if existente:
            await self.collection.update_one(
                {"id": pedido.id},
                {"$set": pedido_dict}
            )
        else:
            await self.collection.insert_one(pedido_dict)
        
        return pedido

    async def buscar_por_id(self, pedido_id: str) -> Optional[PedidoMatricula]:
        """Busca pedido por ID"""
        doc = await self.collection.find_one({"id": pedido_id}, {"_id": 0})
        if doc:
            return PedidoMatricula.from_dict(doc)
        return None

    async def listar_por_consultor(
        self,
        consultor_id: str,
        status: Optional[StatusPedido] = None,
        pagina: int = 1,
        por_pagina: int = 10
    ) -> Tuple[List[PedidoMatricula], int]:
        """Lista pedidos de um consultor com paginação"""
        filtro = {"consultor_id": consultor_id}
        if status:
            filtro["status"] = status.value
        
        total = await self.collection.count_documents(filtro)
        skip = (pagina - 1) * por_pagina
        
        cursor = self.collection.find(filtro, {"_id": 0}).sort("created_at", -1).skip(skip).limit(por_pagina)
        docs = await cursor.to_list(length=por_pagina)
        
        pedidos = [PedidoMatricula.from_dict(doc) for doc in docs]
        return pedidos, total

    async def listar_todos(
        self,
        status: Optional[StatusPedido] = None,
        consultor_id: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        pagina: int = 1,
        por_pagina: int = 10
    ) -> Tuple[List[PedidoMatricula], int]:
        """Lista todos os pedidos com filtros e paginação"""
        filtro = {}
        
        if status:
            filtro["status"] = status.value
        if consultor_id:
            filtro["consultor_id"] = consultor_id
        if data_inicio:
            filtro["created_at"] = {"$gte": data_inicio}
        if data_fim:
            if "created_at" in filtro:
                filtro["created_at"]["$lte"] = data_fim
            else:
                filtro["created_at"] = {"$lte": data_fim}
        
        total = await self.collection.count_documents(filtro)
        skip = (pagina - 1) * por_pagina
        
        cursor = self.collection.find(filtro, {"_id": 0}).sort("created_at", -1).skip(skip).limit(por_pagina)
        docs = await cursor.to_list(length=por_pagina)
        
        pedidos = [PedidoMatricula.from_dict(doc) for doc in docs]
        return pedidos, total

    async def listar_para_exportacao(self) -> List[PedidoMatricula]:
        """Lista pedidos aptos para exportação (status REALIZADO)"""
        cursor = self.collection.find(
            {"status": StatusPedido.REALIZADO.value},
            {"_id": 0}
        ).sort("created_at", -1)
        
        docs = await cursor.to_list(length=1000)
        return [PedidoMatricula.from_dict(doc) for doc in docs]

    async def existe_por_cpf_curso(
        self,
        cpf: str,
        curso_id: str,
        excluir_pedido_id: Optional[str] = None
    ) -> bool:
        """Verifica se existe pedido com mesmo CPF e curso"""
        filtro = {
            "curso_id": curso_id,
            "alunos.cpf": cpf,
            "status": {"$nin": [StatusPedido.CANCELADO.value, StatusPedido.REJEITADO.value]}
        }
        
        if excluir_pedido_id:
            filtro["id"] = {"$ne": excluir_pedido_id}
        
        count = await self.collection.count_documents(filtro)
        return count > 0

    async def contar_por_status(self, consultor_id: Optional[str] = None) -> dict:
        """Conta pedidos por status"""
        match_stage = {}
        if consultor_id:
            match_stage = {"$match": {"consultor_id": consultor_id}}
        
        pipeline = []
        if match_stage:
            pipeline.append(match_stage)
        
        pipeline.append({
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        })
        
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=100)
        
        contagem = {status.value: 0 for status in StatusPedido}
        for result in results:
            if result["_id"] in contagem:
                contagem[result["_id"]] = result["count"]
        
        contagem["total"] = sum(contagem.values())
        return contagem

    async def deletar(self, pedido_id: str) -> bool:
        """Deleta um pedido"""
        result = await self.collection.delete_one({"id": pedido_id})
        return result.deleted_count > 0
