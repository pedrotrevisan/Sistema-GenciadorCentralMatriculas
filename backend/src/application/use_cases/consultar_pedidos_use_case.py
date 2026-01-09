"""Use Case - Consultar Pedidos"""
from typing import Optional, Tuple, List
import math

from src.domain.entities import PedidoMatricula, Usuario
from src.domain.value_objects import StatusPedido
from src.domain.repositories import IPedidoRepository
from src.domain.exceptions import AuthorizationException, PedidoNaoEncontradoException
from src.application.dtos.request import FiltrosPedidoDTO
from src.application.dtos.response import ListaPedidosResponseDTO, PedidoResponseDTO, PaginacaoDTO


class ConsultarPedidosUseCase:
    """Use Case para consultar pedidos"""

    def __init__(self, pedido_repository: IPedidoRepository):
        self.pedido_repository = pedido_repository

    async def listar(
        self,
        filtros: FiltrosPedidoDTO,
        usuario: Usuario
    ) -> ListaPedidosResponseDTO:
        """Lista pedidos com filtros e paginação"""
        
        # Verifica permissão
        pode_ver_todos = usuario.tem_permissao("pedido:visualizar_todos")
        
        # Se não pode ver todos, força filtro por consultor
        consultor_id = filtros.consultor_id
        if not pode_ver_todos:
            consultor_id = usuario.id

        # Converte status se informado
        status = None
        if filtros.status:
            status = StatusPedido.from_string(filtros.status)

        # Busca pedidos
        if consultor_id and not pode_ver_todos:
            pedidos, total = await self.pedido_repository.listar_por_consultor(
                consultor_id=consultor_id,
                status=status,
                pagina=filtros.pagina,
                por_pagina=filtros.por_pagina
            )
        else:
            pedidos, total = await self.pedido_repository.listar_todos(
                status=status,
                consultor_id=consultor_id,
                data_inicio=filtros.data_inicio,
                data_fim=filtros.data_fim,
                pagina=filtros.pagina,
                por_pagina=filtros.por_pagina
            )

        # Converte para DTOs de resposta
        pedidos_dto = [PedidoResponseDTO(**p.to_dict()) for p in pedidos]
        
        paginacao = PaginacaoDTO(
            pagina_atual=filtros.pagina,
            itens_por_pagina=filtros.por_pagina,
            total_itens=total,
            total_paginas=math.ceil(total / filtros.por_pagina) if total > 0 else 0
        )

        return ListaPedidosResponseDTO(pedidos=pedidos_dto, paginacao=paginacao)

    async def buscar_por_id(
        self,
        pedido_id: str,
        usuario: Usuario
    ) -> PedidoResponseDTO:
        """Busca pedido por ID"""
        
        pedido = await self.pedido_repository.buscar_por_id(pedido_id)
        if not pedido:
            raise PedidoNaoEncontradoException(pedido_id)

        # Verifica permissão
        if not usuario.pode_visualizar_pedido(pedido.consultor_id):
            raise AuthorizationException("Sem permissão para visualizar este pedido")

        return PedidoResponseDTO(**pedido.to_dict())

    async def contar_por_status(self, usuario: Usuario) -> dict:
        """Conta pedidos por status"""
        
        consultor_id = None
        if not usuario.tem_permissao("pedido:visualizar_todos"):
            consultor_id = usuario.id
        
        return await self.pedido_repository.contar_por_status(consultor_id)
