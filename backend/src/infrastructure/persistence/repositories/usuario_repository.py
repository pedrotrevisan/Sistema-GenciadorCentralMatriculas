"""Implementação do Repositório de Usuários com PostgreSQL/SQLAlchemy"""
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from src.domain.repositories import IUsuarioRepository
from src.domain.entities import Usuario, RoleUsuario
from src.domain.value_objects import Email
from ..models import UsuarioModel


class UsuarioRepository(IUsuarioRepository):
    """Implementação concreta do repositório de usuários usando PostgreSQL"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _model_to_entity(self, model: UsuarioModel) -> Usuario:
        """Converte model SQLAlchemy para entidade de domínio"""
        return Usuario(
            id=model.id,
            nome=model.nome,
            email=Email(model.email),
            senha_hash=model.senha_hash,
            role=RoleUsuario.from_string(model.role),
            ativo=model.ativo,
            created_at=model.created_at,
            updated_at=model.updated_at,
            ultimo_acesso=model.ultimo_acesso
        )

    async def salvar(self, usuario: Usuario) -> Usuario:
        """Salva ou atualiza um usuário"""
        result = await self.session.execute(
            select(UsuarioModel).where(UsuarioModel.id == usuario.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.nome = usuario.nome
            existing.email = usuario.email.valor
            existing.senha_hash = usuario.senha_hash
            existing.role = usuario.role.value
            existing.ativo = usuario.ativo
            existing.updated_at = datetime.now(timezone.utc)
            existing.ultimo_acesso = usuario.ultimo_acesso
        else:
            usuario_model = UsuarioModel(
                id=usuario.id,
                nome=usuario.nome,
                email=usuario.email.valor,
                senha_hash=usuario.senha_hash,
                role=usuario.role.value,
                ativo=usuario.ativo,
                created_at=usuario.created_at,
                updated_at=usuario.updated_at,
                ultimo_acesso=usuario.ultimo_acesso
            )
            self.session.add(usuario_model)

        await self.session.commit()
        return usuario

    async def buscar_por_id(self, usuario_id: str) -> Optional[Usuario]:
        """Busca usuário por ID"""
        result = await self.session.execute(
            select(UsuarioModel).where(UsuarioModel.id == usuario_id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            return self._model_to_entity(model)
        return None

    async def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """Busca usuário por email"""
        result = await self.session.execute(
            select(UsuarioModel).where(UsuarioModel.email == email.lower())
        )
        model = result.scalar_one_or_none()
        
        if model:
            return self._model_to_entity(model)
        return None

    async def listar_todos(
        self,
        ativo: Optional[bool] = None,
        pagina: int = 1,
        por_pagina: int = 10
    ) -> Tuple[List[Usuario], int]:
        """Lista todos os usuários com paginação"""
        query = select(UsuarioModel)
        count_query = select(func.count(UsuarioModel.id))
        
        if ativo is not None:
            query = query.where(UsuarioModel.ativo == ativo)
            count_query = count_query.where(UsuarioModel.ativo == ativo)
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        offset = (pagina - 1) * por_pagina
        query = query.order_by(UsuarioModel.nome).offset(offset).limit(por_pagina)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        usuarios = [self._model_to_entity(model) for model in models]
        return usuarios, total

    async def deletar(self, usuario_id: str) -> bool:
        """Deleta um usuário"""
        result = await self.session.execute(
            delete(UsuarioModel).where(UsuarioModel.id == usuario_id)
        )
        await self.session.commit()
        return result.rowcount > 0
