"""
Model para Pendências Documentais
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Enum as SQLEnum, Boolean, Index
from datetime import datetime, timezone

from .database import Base
from src.domain.documentos import TipoDocumentoEnum, StatusDocumentoEnum, PrioridadeDocumentoEnum


class PendenciaDocumentalModel(Base):
    """
    Model para pendências documentais de matrículas
    
    Cada documento solicitado é uma linha separada com:
    - Tipo do documento
    - Status (pendente, enviado, aprovado, recusado)
    - Arquivo anexado
    - Prazo limite
    - Histórico de validação
    """
    __tablename__ = "pendencias_documentais"
    
    id = Column(String, primary_key=True)
    pedido_id = Column(String, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True)
    aluno_id = Column(String, ForeignKey("alunos.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Tipo e status
    tipo = Column(SQLEnum(TipoDocumentoEnum), nullable=False)
    status = Column(SQLEnum(StatusDocumentoEnum), nullable=False, default=StatusDocumentoEnum.PENDENTE)
    prioridade = Column(SQLEnum(PrioridadeDocumentoEnum), nullable=False, default=PrioridadeDocumentoEnum.MEDIA)
    
    # Obrigatoriedade
    obrigatorio = Column(Boolean, nullable=False, default=True)
    
    # Descrição e observações
    descricao = Column(Text, nullable=True)  # Descrição adicional do que é necessário
    observacoes = Column(Text, nullable=True)
    
    # Arquivo
    arquivo_url = Column(String(500), nullable=True)  # URL/path do arquivo enviado
    arquivo_nome = Column(String(255), nullable=True)
    arquivo_tamanho = Column(String(50), nullable=True)  # Ex: "2.5 MB"
    
    # Datas
    prazo_limite = Column(DateTime, nullable=True)
    data_envio = Column(DateTime, nullable=True)
    data_validacao = Column(DateTime, nullable=True)
    
    # Validação
    validado_por_id = Column(String, nullable=True)
    validado_por_nome = Column(String, nullable=True)
    motivo_recusa = Column(Text, nullable=True)
    
    # Auditoria
    criado_por_id = Column(String, nullable=True)
    criado_por_nome = Column(String, nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Índices para queries frequentes
    __table_args__ = (
        Index('idx_pendencia_pedido_status', 'pedido_id', 'status'),
        Index('idx_pendencia_tipo_status', 'tipo', 'status'),
        Index('idx_pendencia_prazo', 'prazo_limite'),
        Index('idx_pendencia_status', 'status'),
    )
    
    def __repr__(self):
        return f"<PendenciaDocumental {self.tipo.value}: {self.status.value}>"
