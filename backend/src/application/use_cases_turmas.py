"""
Casos de Uso - Gestão de Turmas e Vagas
"""
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import uuid4

from src.domain.entities_turmas import Curso, Turma, ReservaVaga, StatusReserva, StatusTurma, Modalidade
from src.infrastructure.persistence.repositories_turmas import CursoRepository, TurmaRepository, ReservaVagaRepository
from src.domain.exceptions import NotFoundException, BusinessRuleException, ValidationException


class CriarCursoUseCase:
    """Caso de uso: Criar novo curso"""
    
    def __init__(self, curso_repo: CursoRepository):
        self.curso_repo = curso_repo
    
    async def execute(
        self,
        nome: str,
        codigo: str,
        carga_horaria: int,
        modalidade: str,
        descricao: Optional[str] = None
    ) -> Curso:
        """
        Cria um novo curso
        
        Raises:
            ValidationException: Se já existir curso com mesmo código
        """
        # Verificar se já existe curso com esse código
        curso_existente = await self.curso_repo.buscar_por_codigo(codigo)
        if curso_existente:
            raise ValidationException(f"Já existe um curso com o código '{codigo}'")
        
        # Criar curso
        curso = Curso(
            id=str(uuid4()),
            nome=nome.strip(),
            codigo=codigo.upper().strip(),
            carga_horaria=carga_horaria,
            modalidade=Modalidade(modalidade),
            descricao=descricao.strip() if descricao else None,
            ativo=True,
            criado_em=datetime.now()
        )
        
        await self.curso_repo.salvar(curso)
        
        return curso


class CriarTurmaUseCase:
    """Caso de uso: Criar nova turma"""
    
    def __init__(self, turma_repo: TurmaRepository, curso_repo: CursoRepository):
        self.turma_repo = turma_repo
        self.curso_repo = curso_repo
    
    async def execute(
        self,
        curso_id: str,
        codigo: str,
        capacidade_total: int,
        periodo: str,
        turno: str,
        campus: Optional[str] = None,
        sala: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> Turma:
        """
        Cria uma nova turma
        
        Raises:
            NotFoundException: Se curso não existir
            ValidationException: Se já existir turma com mesmo código
        """
        # Verificar se curso existe
        curso = await self.curso_repo.buscar_por_id(curso_id)
        if not curso:
            raise NotFoundException(f"Curso com ID '{curso_id}' não encontrado")
        
        # Verificar se já existe turma com esse código
        turma_existente = await self.turma_repo.buscar_por_codigo(codigo)
        if turma_existente:
            raise ValidationException(f"Já existe uma turma com o código '{codigo}'")
        
        # Criar turma
        turma = Turma(
            id=str(uuid4()),
            curso_id=curso_id,
            codigo=codigo.upper().strip(),
            capacidade_total=capacidade_total,
            vagas_disponiveis=capacidade_total,  # Inicialmente todas disponíveis
            periodo=periodo.strip(),
            turno=turno.lower().strip(),
            status=StatusTurma.PLANEJADA,
            campus=campus.strip() if campus else None,
            sala=sala.strip() if sala else None,
            data_inicio=data_inicio,
            data_fim=data_fim,
            criado_em=datetime.now()
        )
        
        await self.turma_repo.salvar(turma)
        
        return turma


class ReservarVagaUseCase:
    """Caso de uso: Reservar vaga em turma"""
    
    def __init__(
        self,
        turma_repo: TurmaRepository,
        reserva_repo: ReservaVagaRepository
    ):
        self.turma_repo = turma_repo
        self.reserva_repo = reserva_repo
    
    async def execute(
        self,
        turma_id: str,
        pedido_id: str,
        reservado_por: str,
        dias_expiracao: int = 7
    ) -> ReservaVaga:
        """
        Reserva uma vaga na turma para um pedido
        
        Args:
            turma_id: ID da turma
            pedido_id: ID do pedido de matrícula
            reservado_por: Usuário que está fazendo a reserva
            dias_expiracao: Dias até a reserva expirar (padrão: 7)
        
        Raises:
            NotFoundException: Se turma não existir
            BusinessRuleException: Se não houver vagas ou turma não estiver aberta
            ValidationException: Se já existir reserva ativa para o pedido
        """
        # Buscar turma
        turma = await self.turma_repo.buscar_por_id(turma_id)
        if not turma:
            raise NotFoundException(f"Turma com ID '{turma_id}' não encontrada")
        
        # Verificar se turma está aberta
        if turma.status != StatusTurma.ABERTA:
            raise BusinessRuleException(f"Turma '{turma.codigo}' não está aberta para inscrições (status: {turma.status.value})")
        
        # Verificar se já existe reserva ativa para este pedido
        reserva_existente = await self.reserva_repo.buscar_por_pedido(pedido_id)
        if reserva_existente:
            raise ValidationException(f"Já existe uma reserva ativa para este pedido na turma '{reserva_existente.turma_id}'")
        
        # Reservar vaga na turma (validação de disponibilidade é feita na entidade)
        turma.reservar_vaga()
        
        # Criar reserva
        reserva = ReservaVaga(
            id=str(uuid4()),
            turma_id=turma_id,
            pedido_id=pedido_id,
            status=StatusReserva.RESERVADA,
            data_reserva=datetime.now(),
            reservado_por=reservado_por,
            data_expiracao=datetime.now() + timedelta(days=dias_expiracao)
        )
        
        # Persistir
        await self.turma_repo.atualizar_vagas(turma_id, turma.vagas_disponiveis)
        await self.reserva_repo.salvar(reserva)
        
        return reserva


class ConfirmarReservaUseCase:
    """Caso de uso: Confirmar reserva (aluno matriculado)"""
    
    def __init__(self, reserva_repo: ReservaVagaRepository):
        self.reserva_repo = reserva_repo
    
    async def execute(self, reserva_id: str) -> ReservaVaga:
        """
        Confirma uma reserva de vaga
        
        Raises:
            NotFoundException: Se reserva não existir
            BusinessRuleException: Se reserva não puder ser confirmada
        """
        # Buscar reserva
        reserva = await self.reserva_repo.buscar_por_id(reserva_id)
        if not reserva:
            raise NotFoundException(f"Reserva com ID '{reserva_id}' não encontrada")
        
        # Verificar se pode ser confirmada
        if not reserva.pode_ser_confirmada():
            raise BusinessRuleException(
                f"Reserva não pode ser confirmada. Status atual: {reserva.status.value}"
            )
        
        # Confirmar
        reserva.confirmar()
        
        # Persistir
        await self.reserva_repo.salvar(reserva)
        
        return reserva


class CancelarReservaUseCase:
    """Caso de uso: Cancelar reserva e liberar vaga"""
    
    def __init__(
        self,
        reserva_repo: ReservaVagaRepository,
        turma_repo: TurmaRepository
    ):
        self.reserva_repo = reserva_repo
        self.turma_repo = turma_repo
    
    async def execute(self, reserva_id: str, motivo: str) -> ReservaVaga:
        """
        Cancela uma reserva e libera a vaga
        
        Raises:
            NotFoundException: Se reserva não existir
        """
        # Buscar reserva
        reserva = await self.reserva_repo.buscar_por_id(reserva_id)
        if not reserva:
            raise NotFoundException(f"Reserva com ID '{reserva_id}' não encontrada")
        
        # Buscar turma
        turma = await self.turma_repo.buscar_por_id(reserva.turma_id)
        if not turma:
            raise NotFoundException(f"Turma com ID '{reserva.turma_id}' não encontrada")
        
        # Cancelar ou liberar dependendo do status
        if reserva.status == StatusReserva.CONFIRMADA:
            reserva.liberar(motivo)
        else:
            reserva.cancelar(motivo)
        
        # Liberar vaga na turma
        turma.liberar_vaga()
        
        # Persistir
        await self.turma_repo.atualizar_vagas(turma.id, turma.vagas_disponiveis)
        await self.reserva_repo.salvar(reserva)
        
        return reserva


class ConsultarDisponibilidadeTurmaUseCase:
    """Caso de uso: Consultar disponibilidade de vagas em turma"""
    
    def __init__(self, turma_repo: TurmaRepository):
        self.turma_repo = turma_repo
    
    async def execute(self, turma_id: str) -> dict:
        """
        Consulta informações de disponibilidade da turma
        
        Returns:
            Dict com informações de ocupação e disponibilidade
        """
        turma = await self.turma_repo.buscar_por_id(turma_id)
        if not turma:
            raise NotFoundException(f"Turma com ID '{turma_id}' não encontrada")
        
        return {
            'turma_id': turma.id,
            'codigo': turma.codigo,
            'capacidade_total': turma.capacidade_total,
            'vagas_disponiveis': turma.vagas_disponiveis,
            'vagas_ocupadas': turma.capacidade_total - turma.vagas_disponiveis,
            'ocupacao_percentual': round(turma.calcular_ocupacao_percentual(), 2),
            'esta_lotada': turma.esta_lotada(),
            'esta_quase_lotada': turma.esta_quase_lotada(),
            'status': turma.status.value,
            'aceita_inscricoes': turma.status == StatusTurma.ABERTA and turma.tem_vagas_disponiveis()
        }


class ListarTurmasDisponiveisUseCase:
    """Caso de uso: Listar turmas com vagas disponíveis"""
    
    def __init__(self, turma_repo: TurmaRepository, curso_repo: CursoRepository):
        self.turma_repo = turma_repo
        self.curso_repo = curso_repo
    
    async def execute(self, curso_id: Optional[str] = None) -> List[dict]:
        """
        Lista turmas com vagas disponíveis
        
        Args:
            curso_id: Filtrar por curso específico (opcional)
        
        Returns:
            Lista de turmas com informações de disponibilidade
        """
        # Buscar turmas
        if curso_id:
            turmas = await self.turma_repo.listar_por_curso(curso_id)
            turmas = [t for t in turmas if t.status == StatusTurma.ABERTA and t.tem_vagas_disponiveis()]
        else:
            turmas = await self.turma_repo.listar_com_vagas()
        
        # Montar resposta com informações do curso
        resultado = []
        for turma in turmas:
            curso = await self.curso_repo.buscar_por_id(turma.curso_id)
            
            resultado.append({
                'turma_id': turma.id,
                'codigo': turma.codigo,
                'curso': {
                    'id': curso.id if curso else None,
                    'nome': curso.nome if curso else 'Curso não encontrado',
                    'codigo': curso.codigo if curso else None
                },
                'periodo': turma.periodo,
                'turno': turma.turno,
                'campus': turma.campus,
                'capacidade_total': turma.capacidade_total,
                'vagas_disponiveis': turma.vagas_disponiveis,
                'ocupacao_percentual': round(turma.calcular_ocupacao_percentual(), 2),
                'esta_quase_lotada': turma.esta_quase_lotada()
            })
        
        return resultado


class ObterEstatisticasGeraisUseCase:
    """Caso de uso: Obter estatísticas gerais do sistema de vagas"""
    
    def __init__(self, turma_repo: TurmaRepository):
        self.turma_repo = turma_repo
    
    async def execute(self) -> dict:
        """
        Retorna estatísticas gerais de ocupação
        """
        stats = await self.turma_repo.obter_estatisticas_ocupacao()
        
        # Calcular percentuais
        if stats['capacidade_total'] > 0:
            ocupacao_geral = (stats['vagas_ocupadas'] / stats['capacidade_total']) * 100
        else:
            ocupacao_geral = 0.0
        
        return {
            'total_turmas': stats['total_turmas'],
            'capacidade_total': stats['capacidade_total'],
            'vagas_disponiveis': stats['vagas_disponiveis'],
            'vagas_ocupadas': stats['vagas_ocupadas'],
            'ocupacao_percentual': round(ocupacao_geral, 2)
        }
