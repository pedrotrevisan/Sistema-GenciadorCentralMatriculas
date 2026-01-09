"""Use Case - Atualizar Status do Pedido"""
from src.domain.entities import PedidoMatricula, Usuario
from src.domain.value_objects import StatusPedido
from src.domain.repositories import IPedidoRepository, IAuditoriaRepository
from src.domain.exceptions import PedidoNaoEncontradoException, AuthorizationException
from src.application.dtos.request import AtualizarStatusDTO


class AtualizarStatusPedidoUseCase:
    """Use Case para atualizar status do pedido"""

    def __init__(
        self,
        pedido_repository: IPedidoRepository,
        auditoria_repository: IAuditoriaRepository
    ):
        self.pedido_repository = pedido_repository
        self.auditoria_repository = auditoria_repository

    async def executar(
        self,
        pedido_id: str,
        dto: AtualizarStatusDTO,
        usuario: Usuario
    ) -> PedidoMatricula:
        """Executa a atualização de status"""
        
        # Busca pedido
        pedido = await self.pedido_repository.buscar_por_id(pedido_id)
        if not pedido:
            raise PedidoNaoEncontradoException(pedido_id)

        # Verifica permissão
        if not usuario.tem_permissao("pedido:editar_status"):
            if not usuario.pode_editar_pedido(pedido.consultor_id):
                raise AuthorizationException("Sem permissão para alterar status")

        # Guarda status anterior para auditoria
        status_anterior = pedido.status.value

        # Realiza transição
        novo_status = StatusPedido.from_string(dto.status)
        pedido.transitar_para(novo_status, usuario.id, dto.motivo)

        # Persiste
        pedido = await self.pedido_repository.salvar(pedido)

        # Registra auditoria
        await self.auditoria_repository.registrar(
            pedido_id=pedido.id,
            usuario_id=usuario.id,
            acao="ATUALIZACAO_STATUS",
            detalhes={
                "status_anterior": status_anterior,
                "status_novo": dto.status,
                "motivo": dto.motivo
            }
        )

        return pedido
