"""
Use Cases para Máquina de Estados de Matrícula
"""
from typing import Optional, List
from datetime import datetime
from uuid import uuid4

from src.domain.entities_transicoes import TransicaoStatus
from src.domain.entities import Usuario
from src.domain.status_matricula import (
    StatusMatriculaEnum, 
    TipoTransicao, 
    pode_transicionar,
    obter_proximos_status_validos,
    STATUS_LABELS
)
from src.domain.exceptions import BusinessRuleException, NotFoundException
from src.infrastructure.persistence.repositories_transicoes import TransicaoStatusRepository
from src.infrastructure.persistence.repositories import PedidoRepository as IPedidoRepository
from src.application.use_cases_integracao_vagas import GerenciarReservaPedidoUseCase
from src.infrastructure.persistence.repositories_turmas import TurmaRepository, ReservaVagaRepository


class TransicionarStatusUseCase:
    """
    Use Case: Transicionar status de matrícula com validação
    
    Garante que:
    1. Transição é válida (fluxo permitido)
    2. Histórico é registrado
    3. Ações automáticas são executadas (ex: confirmar reserva ao matricular)
    """
    
    def __init__(
        self,
        pedido_repo: IPedidoRepository,
        transicao_repo: TransicaoStatusRepository,
        turma_repo: Optional[TurmaRepository] = None,
        reserva_repo: Optional[ReservaVagaRepository] = None
    ):
        self.pedido_repo = pedido_repo
        self.transicao_repo = transicao_repo
        self.turma_repo = turma_repo
        self.reserva_repo = reserva_repo
    
    async def executar(
        self,
        pedido_id: str,
        status_novo: StatusMatriculaEnum,
        usuario: Usuario,
        motivo: Optional[str] = None,
        observacoes: Optional[str] = None
    ) -> TransicaoStatus:
        """
        Executa transição de status com validação
        
        Args:
            pedido_id: ID do pedido
            status_novo: Novo status desejado
            usuario: Usuário executando a transição
            motivo: Motivo da mudança (obrigatório para alguns casos)
            observacoes: Observações adicionais
        
        Returns:
            TransicaoStatus criada
        
        Raises:
            NotFoundException: Se pedido não existir
            BusinessRuleException: Se transição for inválida
        """
        # Buscar pedido
        pedido = await self.pedido_repo.buscar_por_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")
        
        # Converter status atual do pedido para o novo enum
        # (Temporariamente, enquanto migramos os dados antigos)
        status_atual = self._mapear_status_antigo(pedido.status.value)
        
        # Validar transição
        if not pode_transicionar(status_atual, status_novo):
            status_validos = obter_proximos_status_validos(status_atual)
            labels_validos = [STATUS_LABELS[s] for s in status_validos]
            
            raise BusinessRuleException(
                f"Transição inválida: {STATUS_LABELS[status_atual]} → {STATUS_LABELS[status_novo]}. "
                f"Status válidos: {', '.join(labels_validos)}"
            )
        
        # Validar motivo obrigatório para alguns casos
        if status_novo == StatusMatriculaEnum.CANCELADO and not motivo:
            raise BusinessRuleException("Motivo é obrigatório para cancelamento")
        
        # Criar transição
        transicao = TransicaoStatus(
            id=str(uuid4()),
            pedido_id=pedido_id,
            status_anterior=status_atual,
            status_novo=status_novo,
            tipo_transicao=TipoTransicao.MANUAL,
            data_transicao=datetime.now(),
            motivo=motivo,
            observacoes=observacoes,
            usuario_id=usuario.id,
            usuario_nome=usuario.nome,
            usuario_email=usuario.email.value
        )
        
        # Salvar transição
        await self.transicao_repo.salvar(transicao)
        
        # Atualizar status do pedido
        # TODO: Quando migrar completamente, usar status_novo diretamente
        pedido.status = self._mapear_para_status_antigo(status_novo)
        await self.pedido_repo.salvar(pedido)
        
        # ========== AÇÕES AUTOMÁTICAS ==========
        
        # Se matriculou → Confirmar reserva de vaga
        if status_novo == StatusMatriculaEnum.MATRICULADO and self.turma_repo and self.reserva_repo:
            await self._confirmar_reserva_vaga(pedido_id)
        
        # Se cancelou → Liberar vaga
        if status_novo == StatusMatriculaEnum.CANCELADO and self.turma_repo and self.reserva_repo:
            await self._liberar_vaga(pedido_id, motivo or "Cancelado")
        
        # Se trancou → Liberar vaga
        if status_novo == StatusMatriculaEnum.TRANCADO and self.turma_repo and self.reserva_repo:
            await self._liberar_vaga(pedido_id, motivo or "Trancado")
        
        return transicao
    
    async def _confirmar_reserva_vaga(self, pedido_id: str):
        """Confirma reserva de vaga ao matricular"""
        try:
            gerenciar_uc = GerenciarReservaPedidoUseCase(self.turma_repo, self.reserva_repo)
            await gerenciar_uc.confirmar_reserva_ao_matricular(pedido_id)
        except Exception as e:
            print(f"⚠️  Erro ao confirmar reserva: {e}")
    
    async def _liberar_vaga(self, pedido_id: str, motivo: str):
        """Libera vaga ao cancelar/trancar"""
        try:
            gerenciar_uc = GerenciarReservaPedidoUseCase(self.turma_repo, self.reserva_repo)
            await gerenciar_uc.liberar_vaga_ao_cancelar(pedido_id, motivo)
        except Exception as e:
            print(f"⚠️  Erro ao liberar vaga: {e}")
    
    def _mapear_status_antigo(self, status_antigo: str) -> StatusMatriculaEnum:
        """Mapeia status antigo (string) para novo enum"""
        mapeamento = {
            "pendente": StatusMatriculaEnum.INSCRITO,
            "aguardando_documentacao": StatusMatriculaEnum.ANALISE_DOCUMENTAL,
            "realizado": StatusMatriculaEnum.MATRICULADO,
            "rejeitado": StatusMatriculaEnum.CANCELADO,
            "exportado": StatusMatriculaEnum.MATRICULADO,
            "matriculado": StatusMatriculaEnum.MATRICULADO,
            "cancelado": StatusMatriculaEnum.CANCELADO
        }
        return mapeamento.get(status_antigo.lower(), StatusMatriculaEnum.INSCRITO)
    
    def _mapear_para_status_antigo(self, status_novo: StatusMatriculaEnum):
        """Mapeia novo enum para status antigo (temporário durante migração)"""
        from src.domain.value_objects import StatusPedido
        
        mapeamento = {
            StatusMatriculaEnum.INSCRITO: StatusPedido.PENDENTE,
            StatusMatriculaEnum.ANALISE_DOCUMENTAL: StatusPedido.AGUARDANDO_DOCUMENTACAO,
            StatusMatriculaEnum.PENDENTE_PAGAMENTO: StatusPedido.PENDENTE,
            StatusMatriculaEnum.MATRICULADO: StatusPedido.REALIZADO,
            StatusMatriculaEnum.CANCELADO: StatusPedido.REJEITADO,
            StatusMatriculaEnum.TRANCADO: StatusPedido.REJEITADO,
            StatusMatriculaEnum.CONCLUIDO: StatusPedido.EXPORTADO,
            StatusMatriculaEnum.EVADIDO: StatusPedido.REJEITADO
        }
        return mapeamento.get(status_novo, StatusPedido.PENDENTE)


class ConsultarHistoricoStatusUseCase:
    """Use Case: Consultar histórico de transições de um pedido"""
    
    def __init__(self, transicao_repo: TransicaoStatusRepository):
        self.transicao_repo = transicao_repo
    
    async def executar(self, pedido_id: str, limite: Optional[int] = None) -> List[TransicaoStatus]:
        """
        Retorna histórico de transições de um pedido
        
        Args:
            pedido_id: ID do pedido
            limite: Número máximo de resultados
        
        Returns:
            Lista de transições ordenadas por data (mais recente primeiro)
        """
        return await self.transicao_repo.listar_por_pedido(pedido_id, limite)


class ObterProximosStatusUseCase:
    """Use Case: Obter próximos status válidos para transição"""
    
    def __init__(self, pedido_repo: IPedidoRepository):
        self.pedido_repo = pedido_repo
    
    async def executar(self, pedido_id: str) -> dict:
        """
        Retorna próximos status válidos a partir do status atual do pedido
        
        Args:
            pedido_id: ID do pedido
        
        Returns:
            Dict com status atual e próximos válidos
        """
        # Buscar pedido
        pedido = await self.pedido_repo.buscar_por_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")
        
        # Mapear status atual
        status_atual = self._mapear_status_antigo(pedido.status.value)
        
        # Obter próximos válidos
        proximos = obter_proximos_status_validos(status_atual)
        
        return {
            "status_atual": {
                "valor": status_atual.value,
                "label": STATUS_LABELS[status_atual]
            },
            "proximos_status": [
                {
                    "valor": s.value,
                    "label": STATUS_LABELS[s]
                }
                for s in proximos
            ]
        }
    
    def _mapear_status_antigo(self, status_antigo: str) -> StatusMatriculaEnum:
        """Mapeia status antigo para novo enum"""
        mapeamento = {
            "pendente": StatusMatriculaEnum.INSCRITO,
            "aguardando_documentacao": StatusMatriculaEnum.ANALISE_DOCUMENTAL,
            "realizado": StatusMatriculaEnum.MATRICULADO,
            "rejeitado": StatusMatriculaEnum.CANCELADO,
            "exportado": StatusMatriculaEnum.MATRICULADO,
            "matriculado": StatusMatriculaEnum.MATRICULADO,
            "cancelado": StatusMatriculaEnum.CANCELADO
        }
        return mapeamento.get(status_antigo.lower(), StatusMatriculaEnum.INSCRITO)
