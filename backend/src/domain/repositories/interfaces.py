"""Interfaces de Repositório - Portas para a camada de infraestrutura"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from ..entities import PedidoMatricula, Usuario
from ..value_objects import StatusPedido


class IPedidoRepository(ABC):
    """Interface para repositório de Pedidos"""

    @abstractmethod
    async def salvar(self, pedido: PedidoMatricula) -> PedidoMatricula:
        """Salva ou atualiza um pedido"""
        pass

    @abstractmethod
    async def buscar_por_id(self, pedido_id: str) -> Optional[PedidoMatricula]:
        """Busca pedido por ID"""
        pass

    @abstractmethod
    async def listar_por_consultor(
        self,
        consultor_id: str,
        status: Optional[StatusPedido] = None,
        pagina: int = 1,
        por_pagina: int = 10
    ) -> Tuple[List[PedidoMatricula], int]:
        """Lista pedidos de um consultor com paginação"""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def listar_para_exportacao(self) -> List[PedidoMatricula]:
        """Lista pedidos aptos para exportação (status REALIZADO)"""
        pass

    @abstractmethod
    async def existe_por_cpf_curso(
        self,
        cpf: str,
        curso_id: str,
        excluir_pedido_id: Optional[str] = None
    ) -> bool:
        """Verifica se existe pedido com mesmo CPF e curso"""
        pass

    @abstractmethod
    async def contar_por_status(self, consultor_id: Optional[str] = None) -> dict:
        """Conta pedidos por status"""
        pass

    @abstractmethod
    async def deletar(self, pedido_id: str) -> bool:
        """Deleta um pedido"""
        pass


class IUsuarioRepository(ABC):
    """Interface para repositório de Usuários"""

    @abstractmethod
    async def salvar(self, usuario: Usuario) -> Usuario:
        """Salva ou atualiza um usuário"""
        pass

    @abstractmethod
    async def buscar_por_id(self, usuario_id: str) -> Optional[Usuario]:
        """Busca usuário por ID"""
        pass

    @abstractmethod
    async def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """Busca usuário por email"""
        pass

    @abstractmethod
    async def listar_todos(
        self,
        ativo: Optional[bool] = None,
        pagina: int = 1,
        por_pagina: int = 10
    ) -> Tuple[List[Usuario], int]:
        """Lista todos os usuários com paginação"""
        pass

    @abstractmethod
    async def deletar(self, usuario_id: str) -> bool:
        """Deleta um usuário"""
        pass


class IAuditoriaRepository(ABC):
    """Interface para repositório de Auditoria"""

    @abstractmethod
    async def registrar(
        self,
        pedido_id: str,
        usuario_id: str,
        acao: str,
        detalhes: dict
    ) -> None:
        """Registra uma ação de auditoria"""
        pass

    @abstractmethod
    async def listar_por_pedido(self, pedido_id: str) -> List[dict]:
        """Lista histórico de auditoria de um pedido"""
        pass
