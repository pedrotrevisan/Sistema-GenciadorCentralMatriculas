"""
Model para Histórico de Transições de Status
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Enum as SQLEnum, Index
from datetime import datetime, timezone

from .database import Base
from src.domain.status_matricula import StatusMatriculaEnum, TipoTransicao


class TransicaoStatusModel(Base):
    """
    Model para histórico de transições de status de matrícula
    
    Registra cada mudança de status com contexto completo:
    - Quem fez a mudança
    - Quando foi feita
    - Status anterior e novo
    - Motivo da mudança
    - Tipo de transição (manual, automática, integração)
    """
    __tablename__ = "transicoes_status"
    
    id = Column(String, primary_key=True)
    pedido_id = Column(String, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status
    status_anterior = Column(SQLEnum(StatusMatriculaEnum), nullable=False)
    status_novo = Column(SQLEnum(StatusMatriculaEnum), nullable=False)
    
    # Contexto da transição
    tipo_transicao = Column(SQLEnum(TipoTransicao), nullable=False, default=TipoTransicao.MANUAL)
    motivo = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    
    # Auditoria
    usuario_id = Column(String, nullable=True)  # Null se transição automática
    usuario_nome = Column(String, nullable=True)
    usuario_email = Column(String, nullable=True)
    data_transicao = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Metadados adicionais (JSON serializado como string)
    metadados = Column(Text, nullable=True)  # Ex: {"ip": "192.168.1.1", "user_agent": "..."}
    
    # Índices para queries frequentes
    __table_args__ = (
        Index('idx_transicao_pedido_data', 'pedido_id', 'data_transicao'),
        Index('idx_transicao_usuario_data', 'usuario_id', 'data_transicao'),
        Index('idx_transicao_status_novo', 'status_novo'),
    )
    
    def __repr__(self):
        return f"<TransicaoStatus {self.status_anterior.value} → {self.status_novo.value}>"
