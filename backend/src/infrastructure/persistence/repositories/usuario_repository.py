"""Implementação do Repositório de Usuários com MongoDB"""
from typing import List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.domain.repositories import IUsuarioRepository
from src.domain.entities import Usuario


class UsuarioRepositoryMongo(IUsuarioRepository):
    """Implementação concreta do repositório de usuários usando MongoDB"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.usuarios

    async def salvar(self, usuario: Usuario) -> Usuario:
        """Salva ou atualiza um usuário"""
        usuario_dict = usuario.to_dict(include_sensitive=True)
        
        existente = await self.collection.find_one({"id": usuario.id})
        
        if existente:
            await self.collection.update_one(
                {"id": usuario.id},
                {"$set": usuario_dict}
            )
        else:
            await self.collection.insert_one(usuario_dict)
        
        return usuario

    async def buscar_por_id(self, usuario_id: str) -> Optional[Usuario]:
        """Busca usuário por ID"""
        doc = await self.collection.find_one({"id": usuario_id}, {"_id": 0})
        if doc:
            return Usuario.from_dict(doc)
        return None

    async def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """Busca usuário por email"""
        doc = await self.collection.find_one({"email": email.lower()}, {"_id": 0})
        if doc:
            return Usuario.from_dict(doc)
        return None

    async def listar_todos(
        self,
        ativo: Optional[bool] = None,
        pagina: int = 1,
        por_pagina: int = 10
    ) -> Tuple[List[Usuario], int]:
        """Lista todos os usuários com paginação"""
        filtro = {}
        if ativo is not None:
            filtro["ativo"] = ativo
        
        total = await self.collection.count_documents(filtro)
        skip = (pagina - 1) * por_pagina
        
        cursor = self.collection.find(filtro, {"_id": 0}).sort("nome", 1).skip(skip).limit(por_pagina)
        docs = await cursor.to_list(length=por_pagina)
        
        usuarios = [Usuario.from_dict(doc) for doc in docs]
        return usuarios, total

    async def deletar(self, usuario_id: str) -> bool:
        """Deleta um usuário"""
        result = await self.collection.delete_one({"id": usuario_id})
        return result.deleted_count > 0
