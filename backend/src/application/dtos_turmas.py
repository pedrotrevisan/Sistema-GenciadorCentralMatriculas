"""
DTOs - Gestão de Turmas e Vagas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


# ========== REQUEST DTOs ==========

class CriarCursoDTO(BaseModel):
    """DTO para criação de curso"""
    nome: str = Field(..., min_length=3, max_length=200, description="Nome do curso")
    codigo: str = Field(..., min_length=2, max_length=50, description="Código único do curso")
    carga_horaria: int = Field(..., gt=0, description="Carga horária em horas")
    modalidade: str = Field(..., description="Modalidade: presencial, semipresencial ou ead")
    descricao: Optional[str] = Field(None, max_length=1000, description="Descrição do curso")
    
    @field_validator('modalidade')
    @classmethod
    def validar_modalidade(cls, v):
        modalidades_validas = ['presencial', 'semipresencial', 'ead']
        if v.lower() not in modalidades_validas:
            raise ValueError(f"Modalidade deve ser uma de: {', '.join(modalidades_validas)}")
        return v.lower()


class CriarTurmaDTO(BaseModel):
    """DTO para criação de turma"""
    curso_id: str = Field(..., description="ID do curso")
    codigo: str = Field(..., min_length=3, max_length=50, description="Código único da turma")
    capacidade_total: int = Field(..., gt=0, le=1000, description="Capacidade total de alunos")
    periodo: str = Field(..., min_length=4, max_length=20, description="Período (ex: 2025.1)")
    turno: str = Field(..., description="Turno: matutino, vespertino ou noturno")
    campus: Optional[str] = Field(None, max_length=100, description="Campus/unidade")
    sala: Optional[str] = Field(None, max_length=50, description="Sala de aula")
    data_inicio: Optional[datetime] = Field(None, description="Data de início das aulas")
    data_fim: Optional[datetime] = Field(None, description="Data de término das aulas")
    
    @field_validator('turno')
    @classmethod
    def validar_turno(cls, v):
        turnos_validos = ['matutino', 'vespertino', 'noturno', 'integral']
        if v.lower() not in turnos_validos:
            raise ValueError(f"Turno deve ser um de: {', '.join(turnos_validos)}")
        return v.lower()


class ReservarVagaDTO(BaseModel):
    """DTO para reservar vaga"""
    turma_id: str = Field(..., description="ID da turma")
    pedido_id: str = Field(..., description="ID do pedido de matrícula")
    dias_expiracao: int = Field(default=7, ge=1, le=30, description="Dias até expiração da reserva")


class AbrirTurmaDTO(BaseModel):
    """DTO para abrir turma para inscrições"""
    turma_id: str = Field(..., description="ID da turma")


class CancelarReservaDTO(BaseModel):
    """DTO para cancelar reserva"""
    motivo: str = Field(..., min_length=3, max_length=500, description="Motivo do cancelamento")


# ========== RESPONSE DTOs ==========

class CursoResponseDTO(BaseModel):
    """DTO de resposta para curso"""
    id: str
    nome: str
    codigo: str
    carga_horaria: int
    modalidade: str
    descricao: Optional[str]
    ativo: bool
    criado_em: datetime
    atualizado_em: Optional[datetime]
    
    class Config:
        from_attributes = True


class TurmaResponseDTO(BaseModel):
    """DTO de resposta para turma"""
    id: str
    curso_id: str
    codigo: str
    capacidade_total: int
    vagas_disponiveis: int
    vagas_ocupadas: int
    ocupacao_percentual: float
    periodo: str
    turno: str
    status: str
    campus: Optional[str]
    sala: Optional[str]
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    esta_lotada: bool
    esta_quase_lotada: bool
    criado_em: datetime
    
    class Config:
        from_attributes = True


class TurmaComCursoResponseDTO(BaseModel):
    """DTO de resposta para turma com informações do curso"""
    turma: TurmaResponseDTO
    curso: CursoResponseDTO


class ReservaVagaResponseDTO(BaseModel):
    """DTO de resposta para reserva de vaga"""
    id: str
    turma_id: str
    pedido_id: str
    status: str
    data_reserva: datetime
    data_confirmacao: Optional[datetime]
    data_liberacao: Optional[datetime]
    data_expiracao: Optional[datetime]
    reservado_por: str
    motivo_cancelamento: Optional[str]
    observacoes: Optional[str]
    
    class Config:
        from_attributes = True


class DisponibilidadeResponseDTO(BaseModel):
    """DTO de resposta para disponibilidade de turma"""
    turma_id: str
    codigo: str
    capacidade_total: int
    vagas_disponiveis: int
    vagas_ocupadas: int
    ocupacao_percentual: float
    esta_lotada: bool
    esta_quase_lotada: bool
    status: str
    aceita_inscricoes: bool


class TurmaDisponivelDTO(BaseModel):
    """DTO para turma disponível"""
    turma_id: str
    codigo: str
    curso: dict
    periodo: str
    turno: str
    campus: Optional[str]
    capacidade_total: int
    vagas_disponiveis: int
    ocupacao_percentual: float
    esta_quase_lotada: bool


class EstatisticasGeraisResponseDTO(BaseModel):
    """DTO de resposta para estatísticas gerais"""
    total_turmas: int
    capacidade_total: int
    vagas_disponiveis: int
    vagas_ocupadas: int
    ocupacao_percentual: float


# ========== Lista Response DTOs ==========

class ListaCursosResponseDTO(BaseModel):
    """DTO de resposta para lista de cursos"""
    total: int
    cursos: list[CursoResponseDTO]


class ListaTurmasResponseDTO(BaseModel):
    """DTO de resposta para lista de turmas"""
    total: int
    turmas: list[TurmaResponseDTO]


class ListaTurmasDisponiveisResponseDTO(BaseModel):
    """DTO de resposta para lista de turmas disponíveis"""
    total: int
    turmas: list[TurmaDisponivelDTO]


class ListaReservasResponseDTO(BaseModel):
    """DTO de resposta para lista de reservas"""
    total: int
    reservas: list[ReservaVagaResponseDTO]
