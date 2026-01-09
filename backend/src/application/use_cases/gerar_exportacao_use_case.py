"""Use Case - Gerar Exportação TOTVS"""
from typing import List
from io import BytesIO

from ...domain.entities import Usuario
from ...domain.repositories import IPedidoRepository, IAuditoriaRepository
from ...domain.exceptions import BusinessRuleException, AuthorizationException
from ...infrastructure.exporters import ExportadorFactory


class GerarExportacaoTOTVSUseCase:
    """Use Case para gerar exportação no formato TOTVS"""

    def __init__(
        self,
        pedido_repository: IPedidoRepository,
        auditoria_repository: IAuditoriaRepository
    ):
        self.pedido_repository = pedido_repository
        self.auditoria_repository = auditoria_repository

    async def executar(
        self,
        usuario: Usuario,
        formato: str = "xlsx"
    ) -> tuple[BytesIO, str, str]:
        """
        Executa a exportação
        Retorna: (arquivo, content_type, nome_arquivo)
        """
        
        # Verifica permissão
        if not usuario.tem_permissao("pedido:exportar"):
            raise AuthorizationException("Sem permissão para exportar")

        # Busca pedidos aptos para exportação
        pedidos = await self.pedido_repository.listar_para_exportacao()
        
        if not pedidos:
            raise BusinessRuleException("Não há pedidos aptos para exportação")

        # Cria exportador via Factory
        exportador = ExportadorFactory.criar(formato)

        # Gera arquivo
        arquivo = exportador.exportar(pedidos)

        # Marca pedidos como exportados e registra auditoria
        pedidos_ids = []
        for pedido in pedidos:
            pedido.marcar_como_exportado(usuario.id)
            await self.pedido_repository.salvar(pedido)
            pedidos_ids.append(pedido.id)

        # Registra auditoria geral
        await self.auditoria_repository.registrar(
            pedido_id="EXPORTACAO_LOTE",
            usuario_id=usuario.id,
            acao="EXPORTACAO",
            detalhes={
                "formato": formato,
                "total_pedidos": len(pedidos),
                "pedidos_ids": pedidos_ids
            }
        )

        # Nome do arquivo
        from datetime import datetime
        nome_arquivo = f"matriculas_totvs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{exportador.get_extension()}"

        return arquivo, exportador.get_content_type(), nome_arquivo
