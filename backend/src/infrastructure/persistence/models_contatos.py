"""
SQLAlchemy Models - Módulo de Log de Contatos (Fase 3)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base
from src.domain.entities_contatos import TipoContatoEnum, ResultadoContatoEnum, MotivoContatoEnum


class LogContatoModel(Base):
    """
    Modelo SQLAlchemy para Log de Contatos
    
    Registra todas as interações com alunos (ligações, WhatsApp, emails, etc.)
    """
    __tablename__ = "log_contatos"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pedido_id = Column(String(36), ForeignKey("pedidos.id"), nullable=False, index=True)
    
    # Tipo e resultado do contato
    tipo = Column(SQLEnum(TipoContatoEnum), nullable=False)
    resultado = Column(SQLEnum(ResultadoContatoEnum), nullable=False)
    motivo = Column(SQLEnum(MotivoContatoEnum), nullable=False)
    
    # Descrição do contato
    descricao = Column(Text, nullable=False)
    
    # Dados do contato (quem atendeu, meio utilizado)
    contato_nome = Column(String(200), nullable=True)
    contato_telefone = Column(String(20), nullable=True)
    contato_email = Column(String(200), nullable=True)
    
    # Agendamento de retorno
    data_retorno = Column(DateTime, nullable=True)
    retorno_realizado = Column(Boolean, default=False)
    
    # Auditoria
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    usuario_nome = Column(String(200), nullable=False)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(DateTime, nullable=True, onupdate=datetime.now)
    
    # Relationships
    pedido = relationship("PedidoModel", backref="contatos")
    
    def to_entity(self):
        """Converte o modelo para entidade de domínio"""
        from src.domain.entities_contatos import ContatoEntity
        
        return ContatoEntity(
            id=self.id,
            pedido_id=self.pedido_id,
            tipo=self.tipo,
            resultado=self.resultado,
            motivo=self.motivo,
            descricao=self.descricao,
            contato_nome=self.contato_nome,
            contato_telefone=self.contato_telefone,
            contato_email=self.contato_email,
            data_retorno=self.data_retorno,
            retorno_realizado=self.retorno_realizado,
            usuario_id=self.usuario_id,
            usuario_nome=self.usuario_nome,
            criado_em=self.criado_em,
            atualizado_em=self.atualizado_em
        )
    
    @classmethod
    def from_entity(cls, entity):
        """Cria modelo a partir de entidade de domínio"""
        return cls(
            id=entity.id,
            pedido_id=entity.pedido_id,
            tipo=entity.tipo,
            resultado=entity.resultado,
            motivo=entity.motivo,
            descricao=entity.descricao,
            contato_nome=entity.contato_nome,
            contato_telefone=entity.contato_telefone,
            contato_email=entity.contato_email,
            data_retorno=entity.data_retorno,
            retorno_realizado=entity.retorno_realizado,
            usuario_id=entity.usuario_id,
            usuario_nome=entity.usuario_nome,
            criado_em=entity.criado_em,
            atualizado_em=entity.atualizado_em
        )
