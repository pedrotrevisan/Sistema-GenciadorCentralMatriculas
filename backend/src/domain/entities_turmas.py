"""
Entidades de Domínio - Gestão de Turmas e Vagas
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class Modalidade(str, Enum):
    """Modalidades de curso"""
    PRESENCIAL = "presencial"
    SEMIPRESENCIAL = "semipresencial"
    EAD = "ead"


class StatusTurma(str, Enum):
    """Status possíveis de uma turma"""
    PLANEJADA = "planejada"
    ABERTA = "aberta"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class StatusReserva(str, Enum):
    """Status possíveis de uma reserva"""
    RESERVADA = "reservada"
    CONFIRMADA = "confirmada"
    EXPIRADA = "expirada"
    CANCELADA = "cancelada"
    LIBERADA = "liberada"


@dataclass
class Curso:
    """
    Entidade Curso
    Representa um curso oferecido pela instituição
    """
    id: str
    nome: str
    codigo: str
    carga_horaria: int
    modalidade: Modalidade
    descricao: Optional[str] = None
    ativo: bool = True
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
    
    def desativar(self):
        """Desativa o curso"""
        self.ativo = False
    
    def ativar(self):
        """Ativa o curso"""
        self.ativo = True
    
    def __post_init__(self):
        """Validações após inicialização"""
        if self.carga_horaria <= 0:
            raise ValueError("Carga horária deve ser maior que zero")
        
        if len(self.nome.strip()) < 3:
            raise ValueError("Nome do curso deve ter pelo menos 3 caracteres")


@dataclass
class Turma:
    """
    Entidade Turma
    Representa uma turma específica de um curso com controle de vagas
    """
    id: str
    curso_id: str
    codigo: str
    capacidade_total: int
    vagas_disponiveis: int
    periodo: str
    turno: str
    status: StatusTurma
    campus: Optional[str] = None
    sala: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
    
    def __post_init__(self):
        """Validações após inicialização"""
        if self.capacidade_total <= 0:
            raise ValueError("Capacidade total deve ser maior que zero")
        
        if self.vagas_disponiveis < 0:
            raise ValueError("Vagas disponíveis não pode ser negativo")
        
        if self.vagas_disponiveis > self.capacidade_total:
            raise ValueError("Vagas disponíveis não pode ser maior que capacidade total")
    
    def tem_vagas_disponiveis(self) -> bool:
        """Verifica se há vagas disponíveis"""
        return self.vagas_disponiveis > 0
    
    def reservar_vaga(self) -> None:
        """
        Reserva uma vaga na turma
        Raises:
            ValueError: Se não houver vagas disponíveis
        """
        if not self.tem_vagas_disponiveis():
            raise ValueError(f"Turma {self.codigo} não possui vagas disponíveis")
        
        self.vagas_disponiveis -= 1
    
    def liberar_vaga(self) -> None:
        """
        Libera uma vaga na turma
        Raises:
            ValueError: Se tentar liberar além da capacidade
        """
        if self.vagas_disponiveis >= self.capacidade_total:
            raise ValueError(f"Turma {self.codigo} já está com capacidade máxima")
        
        self.vagas_disponiveis += 1
    
    def calcular_ocupacao_percentual(self) -> float:
        """Calcula percentual de ocupação da turma"""
        ocupadas = self.capacidade_total - self.vagas_disponiveis
        return (ocupadas / self.capacidade_total) * 100
    
    def esta_lotada(self) -> bool:
        """Verifica se a turma está lotada"""
        return self.vagas_disponiveis == 0
    
    def esta_quase_lotada(self, threshold: float = 90.0) -> bool:
        """Verifica se a turma está quase lotada (padrão: 90% ocupação)"""
        return self.calcular_ocupacao_percentual() >= threshold
    
    def abrir_inscricoes(self) -> None:
        """Abre a turma para inscrições"""
        if self.status != StatusTurma.PLANEJADA:
            raise ValueError("Apenas turmas planejadas podem ser abertas")
        self.status = StatusTurma.ABERTA
    
    def iniciar_aulas(self) -> None:
        """Inicia as aulas da turma"""
        if self.status != StatusTurma.ABERTA:
            raise ValueError("Apenas turmas abertas podem iniciar")
        self.status = StatusTurma.EM_ANDAMENTO
    
    def concluir(self) -> None:
        """Conclui a turma"""
        if self.status != StatusTurma.EM_ANDAMENTO:
            raise ValueError("Apenas turmas em andamento podem ser concluídas")
        self.status = StatusTurma.CONCLUIDA
    
    def cancelar(self) -> None:
        """Cancela a turma"""
        if self.status in [StatusTurma.CONCLUIDA, StatusTurma.CANCELADA]:
            raise ValueError("Turma já está finalizada")
        self.status = StatusTurma.CANCELADA


@dataclass
class ReservaVaga:
    """
    Entidade ReservaVaga
    Controla o ciclo de vida de uma reserva de vaga
    """
    id: str
    turma_id: str
    pedido_id: str
    status: StatusReserva
    data_reserva: datetime
    reservado_por: str
    data_confirmacao: Optional[datetime] = None
    data_liberacao: Optional[datetime] = None
    data_expiracao: Optional[datetime] = None
    motivo_cancelamento: Optional[str] = None
    observacoes: Optional[str] = None
    
    def confirmar(self) -> None:
        """
        Confirma a reserva (aluno matriculado)
        Raises:
            ValueError: Se reserva não estiver em status válido
        """
        if self.status != StatusReserva.RESERVADA:
            raise ValueError(f"Apenas reservas com status RESERVADA podem ser confirmadas. Status atual: {self.status}")
        
        self.status = StatusReserva.CONFIRMADA
        self.data_confirmacao = datetime.now()
    
    def cancelar(self, motivo: str) -> None:
        """
        Cancela a reserva
        Raises:
            ValueError: Se reserva já estiver finalizada
        """
        if self.status in [StatusReserva.CONFIRMADA, StatusReserva.CANCELADA, StatusReserva.LIBERADA]:
            raise ValueError(f"Reserva com status {self.status} não pode ser cancelada")
        
        self.status = StatusReserva.CANCELADA
        self.data_liberacao = datetime.now()
        self.motivo_cancelamento = motivo
    
    def liberar(self, motivo: str) -> None:
        """
        Libera a vaga (aluno desistiu/trancou)
        Raises:
            ValueError: Se não for uma reserva confirmada
        """
        if self.status != StatusReserva.CONFIRMADA:
            raise ValueError("Apenas reservas confirmadas podem ser liberadas")
        
        self.status = StatusReserva.LIBERADA
        self.data_liberacao = datetime.now()
        self.motivo_cancelamento = motivo
    
    def expirar(self) -> None:
        """
        Marca reserva como expirada
        Raises:
            ValueError: Se reserva não estiver aguardando confirmação
        """
        if self.status != StatusReserva.RESERVADA:
            raise ValueError("Apenas reservas pendentes podem expirar")
        
        self.status = StatusReserva.EXPIRADA
        self.data_liberacao = datetime.now()
    
    def esta_ativa(self) -> bool:
        """Verifica se a reserva está ativa (reservada ou confirmada)"""
        return self.status in [StatusReserva.RESERVADA, StatusReserva.CONFIRMADA]
    
    def pode_ser_confirmada(self) -> bool:
        """Verifica se a reserva pode ser confirmada"""
        if self.status != StatusReserva.RESERVADA:
            return False
        
        if self.data_expiracao and datetime.now() > self.data_expiracao:
            return False
        
        return True
