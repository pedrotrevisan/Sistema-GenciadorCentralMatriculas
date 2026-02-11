"""
Models para Gestão de Vagas e Turmas
Sistema de controle de capacidade e reservas
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, CheckConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from .database import Base


class ModalidadeEnum(str, enum.Enum):
    """Modalidades de oferta do curso"""
    PRESENCIAL = "presencial"
    SEMIPRESENCIAL = "semipresencial"
    EAD = "ead"


class StatusTurmaEnum(str, enum.Enum):
    """Status da turma"""
    PLANEJADA = "planejada"
    ABERTA = "aberta"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class StatusReservaEnum(str, enum.Enum):
    """Status da reserva de vaga"""
    RESERVADA = "reservada"          # Vaga reservada, aguardando confirmação
    CONFIRMADA = "confirmada"        # Vaga confirmada (aluno matriculado)
    EXPIRADA = "expirada"            # Reserva expirou sem confirmação
    CANCELADA = "cancelada"          # Reserva cancelada manualmente
    LIBERADA = "liberada"            # Vaga liberada (aluno desistiu/trancou)


class CursoTurmaModel(Base):
    """
    Modelo de Curso (Sistema de Gestão de Vagas)
    Representa os cursos oferecidos pela instituição
    """
    __tablename__ = "cursos_turmas"
    
    id = Column(String, primary_key=True)
    nome = Column(String(200), nullable=False, unique=True)
    codigo = Column(String(50), unique=True, index=True)
    carga_horaria = Column(Integer, nullable=False)
    modalidade = Column(SQLEnum(ModalidadeEnum), nullable=False, default=ModalidadeEnum.PRESENCIAL)
    descricao = Column(String(1000))
    ativo = Column(Integer, default=1)  # 1=ativo, 0=inativo (SQLite não tem Boolean nativo)
    
    # Auditoria
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relacionamentos
    turmas = relationship("TurmaModel", back_populates="curso", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Curso {self.codigo}: {self.nome}>"


class TurmaModel(Base):
    """
    Modelo de Turma
    Representa uma turma específica de um curso
    """
    __tablename__ = "turmas"
    
    id = Column(String, primary_key=True)
    curso_id = Column(String, ForeignKey("cursos_turmas.id", ondelete="CASCADE"), nullable=False)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    
    # Capacidade e controle de vagas
    capacidade_total = Column(Integer, nullable=False)
    vagas_disponiveis = Column(Integer, nullable=False)
    
    # Informações da turma
    periodo = Column(String(20))  # Ex: "2025.1", "2025.2"
    turno = Column(String(20))    # Ex: "matutino", "vespertino", "noturno"
    data_inicio = Column(DateTime)
    data_fim = Column(DateTime)
    
    # Status e localização
    status = Column(SQLEnum(StatusTurmaEnum), nullable=False, default=StatusTurmaEnum.PLANEJADA)
    campus = Column(String(100))
    sala = Column(String(50))
    
    # Auditoria
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relacionamentos
    curso = relationship("CursoTurmaModel", back_populates="turmas")
    reservas = relationship("ReservaVagaModel", back_populates="turma", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('vagas_disponiveis >= 0', name='check_vagas_nao_negativas'),
        CheckConstraint('vagas_disponiveis <= capacidade_total', name='check_vagas_limite'),
        Index('idx_turma_curso_periodo', 'curso_id', 'periodo'),
        Index('idx_turma_status', 'status'),
    )
    
    def __repr__(self):
        return f"<Turma {self.codigo}: {self.vagas_disponiveis}/{self.capacidade_total} vagas>"


class ReservaVagaModel(Base):
    """
    Modelo de Reserva de Vaga
    Controla o ciclo de vida de uma vaga (reserva → confirmação → liberação)
    """
    __tablename__ = "reservas_vagas"
    
    id = Column(String, primary_key=True)
    turma_id = Column(String, ForeignKey("turmas.id", ondelete="CASCADE"), nullable=False)
    pedido_id = Column(String, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    
    # Status e controle
    status = Column(SQLEnum(StatusReservaEnum), nullable=False, default=StatusReservaEnum.RESERVADA)
    data_reserva = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    data_confirmacao = Column(DateTime)
    data_liberacao = Column(DateTime)
    data_expiracao = Column(DateTime)  # Prazo para confirmar a reserva
    
    # Auditoria e observações
    reservado_por = Column(String(100))  # Usuário que fez a reserva
    motivo_cancelamento = Column(String(500))
    observacoes = Column(String(1000))
    
    # Relacionamentos
    turma = relationship("TurmaModel", back_populates="reservas")
    
    # Índices para queries frequentes
    __table_args__ = (
        Index('idx_reserva_turma_status', 'turma_id', 'status'),
        Index('idx_reserva_pedido', 'pedido_id'),
        Index('idx_reserva_expiracao', 'data_expiracao'),
    )
    
    def __repr__(self):
        return f"<ReservaVaga {self.id}: {self.status.value}>"
