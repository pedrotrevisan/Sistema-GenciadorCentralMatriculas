"""
Use Cases para integração entre Pedidos e Reservas de Vagas
"""
from typing import Optional
from datetime import datetime

from src.domain.entities import PedidoMatricula
from src.domain.entities_turmas import ReservaVaga, StatusReserva
from src.infrastructure.persistence.repositories_turmas import TurmaRepository, ReservaVagaRepository
from src.application.use_cases_turmas import ReservarVagaUseCase, ConfirmarReservaUseCase, CancelarReservaUseCase
from src.domain.exceptions import BusinessRuleException, NotFoundException


class GerenciarReservaPedidoUseCase:
    """
    Caso de uso: Gerenciar reserva de vaga ao criar/atualizar pedido
    
    Fluxo automático:
    1. Criar pedido com turma → Reserva vaga
    2. Status = "realizado" → Confirma reserva
    3. Status = "cancelado" → Libera vaga
    """
    
    def __init__(
        self,
        turma_repo: TurmaRepository,
        reserva_repo: ReservaVagaRepository
    ):
        self.turma_repo = turma_repo
        self.reserva_repo = reserva_repo
    
    async def reservar_vaga_ao_criar_pedido(
        self,
        pedido_id: str,
        turma_id: str,
        usuario_email: str
    ) -> Optional[ReservaVaga]:
        """
        Reserva vaga automaticamente ao criar pedido com turma
        
        Args:
            pedido_id: ID do pedido criado
            turma_id: ID da turma selecionada
            usuario_email: Email do usuário que está criando
        
        Returns:
            ReservaVaga criada ou None se turma_id não fornecido
        """
        if not turma_id:
            return None
        
        # Verificar se já existe reserva
        reserva_existente = await self.reserva_repo.buscar_por_pedido(pedido_id)
        if reserva_existente:
            return reserva_existente
        
        # Criar reserva usando o use case existente
        use_case = ReservarVagaUseCase(self.turma_repo, self.reserva_repo)
        
        try:
            reserva = await use_case.execute(
                turma_id=turma_id,
                pedido_id=pedido_id,
                reservado_por=usuario_email,
                dias_expiracao=7
            )
            
            return reserva
        
        except BusinessRuleException as e:
            # Se não houver vagas ou turma não estiver aberta, não bloqueia a criação do pedido
            # Mas loga o problema
            print(f"⚠️  Não foi possível reservar vaga: {str(e)}")
            return None
    
    async def confirmar_reserva_ao_matricular(
        self,
        pedido_id: str
    ) -> Optional[ReservaVaga]:
        """
        Confirma reserva quando status do pedido = "realizado" (matriculado)
        
        Args:
            pedido_id: ID do pedido
        
        Returns:
            ReservaVaga confirmada ou None se não houver reserva
        """
        # Buscar reserva ativa do pedido
        reserva = await self.reserva_repo.buscar_por_pedido(pedido_id)
        
        if not reserva:
            return None
        
        if reserva.status == StatusReserva.CONFIRMADA:
            # Já está confirmada
            return reserva
        
        # Confirmar usando o use case existente
        use_case = ConfirmarReservaUseCase(self.reserva_repo)
        
        try:
            reserva_confirmada = await use_case.execute(reserva.id)
            return reserva_confirmada
        except BusinessRuleException as e:
            print(f"⚠️  Erro ao confirmar reserva: {str(e)}")
            return None
    
    async def liberar_vaga_ao_cancelar(
        self,
        pedido_id: str,
        motivo: str = "Pedido cancelado"
    ) -> Optional[ReservaVaga]:
        """
        Libera vaga quando pedido é cancelado
        
        Args:
            pedido_id: ID do pedido
            motivo: Motivo do cancelamento
        
        Returns:
            ReservaVaga cancelada ou None se não houver reserva
        """
        # Buscar reserva ativa do pedido
        reserva = await self.reserva_repo.buscar_por_pedido(pedido_id)
        
        if not reserva:
            return None
        
        if reserva.status in [StatusReserva.CANCELADA, StatusReserva.LIBERADA, StatusReserva.EXPIRADA]:
            # Já foi liberada
            return reserva
        
        # Cancelar/liberar usando o use case existente
        use_case = CancelarReservaUseCase(self.reserva_repo, self.turma_repo)
        
        try:
            reserva_cancelada = await use_case.execute(reserva.id, motivo)
            return reserva_cancelada
        except Exception as e:
            print(f"⚠️  Erro ao liberar vaga: {str(e)}")
            return None
    
    async def atualizar_reserva_ao_mudar_turma(
        self,
        pedido_id: str,
        turma_id_nova: str,
        turma_id_antiga: Optional[str],
        usuario_email: str
    ) -> Optional[ReservaVaga]:
        """
        Atualiza reserva quando turma do pedido é alterada
        
        1. Libera vaga da turma antiga
        2. Reserva vaga na turma nova
        
        Args:
            pedido_id: ID do pedido
            turma_id_nova: ID da nova turma
            turma_id_antiga: ID da turma anterior (pode ser None)
            usuario_email: Email do usuário
        
        Returns:
            Nova ReservaVaga ou None
        """
        # Se não mudou nada, retorna
        if turma_id_nova == turma_id_antiga:
            reserva = await self.reserva_repo.buscar_por_pedido(pedido_id)
            return reserva
        
        # Liberar vaga antiga se houver
        if turma_id_antiga:
            await self.liberar_vaga_ao_cancelar(
                pedido_id=pedido_id,
                motivo="Turma alterada"
            )
        
        # Reservar vaga nova
        if turma_id_nova:
            nova_reserva = await self.reservar_vaga_ao_criar_pedido(
                pedido_id=pedido_id,
                turma_id=turma_id_nova,
                usuario_email=usuario_email
            )
            return nova_reserva
        
        return None


class ProcessarReservasExpiradasUseCase:
    """
    Caso de uso: Processar reservas expiradas automaticamente
    
    Deve ser executado periodicamente (ex: job diário)
    """
    
    def __init__(
        self,
        reserva_repo: ReservaVagaRepository,
        turma_repo: TurmaRepository
    ):
        self.reserva_repo = reserva_repo
        self.turma_repo = turma_repo
    
    async def execute(self) -> dict:
        """
        Processa todas as reservas expiradas
        
        Returns:
            Dict com estatísticas do processamento
        """
        # Buscar reservas expiradas
        reservas_expiradas = await self.reserva_repo.listar_expiradas()
        
        total = len(reservas_expiradas)
        processadas = 0
        erros = 0
        
        for reserva in reservas_expiradas:
            try:
                # Marcar como expirada
                reserva.expirar()
                await self.reserva_repo.salvar(reserva)
                
                # Liberar vaga na turma
                turma = await self.turma_repo.buscar_por_id(reserva.turma_id)
                if turma:
                    turma.liberar_vaga()
                    await self.turma_repo.atualizar_vagas(turma.id, turma.vagas_disponiveis)
                
                processadas += 1
                
            except Exception as e:
                print(f"❌ Erro ao processar reserva {reserva.id}: {str(e)}")
                erros += 1
        
        return {
            'total_expiradas': total,
            'processadas': processadas,
            'erros': erros,
            'data_processamento': datetime.now()
        }
