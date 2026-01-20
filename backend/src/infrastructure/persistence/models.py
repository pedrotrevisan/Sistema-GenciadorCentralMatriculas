"""SQLAlchemy Models"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from .database import Base


class StatusPedidoEnum(str, enum.Enum):
    PENDENTE = "pendente"
    EM_ANALISE = "em_analise"
    DOCUMENTACAO_PENDENTE = "documentacao_pendente"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"
    REALIZADO = "realizado"
    CANCELADO = "cancelado"
    EXPORTADO = "exportado"


class RoleEnum(str, enum.Enum):
    CONSULTOR = "consultor"
    ASSISTENTE = "assistente"
    ADMIN = "admin"


class UsuarioModel(Base):
    """SQLAlchemy model for Usuario"""
    __tablename__ = "usuarios"

    id = Column(String(36), primary_key=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    senha_hash = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="consultor")
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    ultimo_acesso = Column(DateTime, nullable=True)

    # Relationships
    pedidos = relationship("PedidoModel", back_populates="consultor")


class PedidoModel(Base):
    """SQLAlchemy model for PedidoMatricula"""
    __tablename__ = "pedidos"

    id = Column(String(36), primary_key=True)
    numero_protocolo = Column(String(20), unique=True, nullable=True, index=True)  # CM-2026-0001
    consultor_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    consultor_nome = Column(String(200), nullable=False)
    curso_id = Column(String(36), nullable=False)
    curso_nome = Column(String(200), nullable=False)
    projeto_id = Column(String(36), nullable=True)
    projeto_nome = Column(String(200), nullable=True)
    empresa_id = Column(String(36), nullable=True)
    empresa_nome = Column(String(200), nullable=True)
    status = Column(String(30), nullable=False, default="pendente", index=True)
    observacoes = Column(Text, nullable=True)
    motivo_rejeicao = Column(Text, nullable=True)
    data_exportacao = Column(DateTime, nullable=True)
    exportado_por = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    consultor = relationship("UsuarioModel", back_populates="pedidos")
    alunos = relationship("AlunoModel", back_populates="pedido", cascade="all, delete-orphan")


class AlunoModel(Base):
    """SQLAlchemy model for Aluno"""
    __tablename__ = "alunos"

    id = Column(String(36), primary_key=True)
    pedido_id = Column(String(36), ForeignKey("pedidos.id"), nullable=False)
    nome = Column(String(200), nullable=False)
    cpf = Column(String(11), nullable=False, index=True)
    email = Column(String(200), nullable=False)
    telefone = Column(String(20), nullable=False)
    data_nascimento = Column(DateTime, nullable=False)
    rg = Column(String(20), nullable=False)
    rg_orgao_emissor = Column(String(20), nullable=False)
    rg_uf = Column(String(2), nullable=False)
    rg_data_emissao = Column(String(10), nullable=True)  # NOVO - Emissão RG
    naturalidade = Column(String(100), nullable=True)  # NOVO - Naturalidade
    naturalidade_uf = Column(String(2), nullable=True)  # NOVO - Estado Natal/UF
    sexo = Column(String(1), nullable=True)  # NOVO - M/F
    cor_raca = Column(String(20), nullable=True)  # NOVO - Cor/Raça
    grau_instrucao = Column(String(50), nullable=True)  # NOVO - Grau de Instrução
    nome_pai = Column(String(200), nullable=True)  # NOVO - Nome do pai
    nome_mae = Column(String(200), nullable=True)  # NOVO - Nome da mãe
    endereco_cep = Column(String(9), nullable=False)
    endereco_logradouro = Column(String(200), nullable=False)
    endereco_numero = Column(String(20), nullable=False)
    endereco_complemento = Column(String(100), nullable=True)
    endereco_bairro = Column(String(100), nullable=False)
    endereco_cidade = Column(String(100), nullable=False)
    endereco_uf = Column(String(2), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    pedido = relationship("PedidoModel", back_populates="alunos")


class AuditoriaModel(Base):
    """SQLAlchemy model for Auditoria"""
    __tablename__ = "auditoria"

    id = Column(String(36), primary_key=True)
    pedido_id = Column(String(36), nullable=False, index=True)
    usuario_id = Column(String(36), nullable=False)
    acao = Column(String(50), nullable=False)
    detalhes = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CursoModel(Base):
    """SQLAlchemy model for Curso"""
    __tablename__ = "cursos"

    id = Column(String(36), primary_key=True)
    nome = Column(String(200), nullable=False, unique=True)
    descricao = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ProjetoModel(Base):
    """SQLAlchemy model for Projeto"""
    __tablename__ = "projetos"

    id = Column(String(36), primary_key=True)
    nome = Column(String(200), nullable=False, unique=True)
    descricao = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class EmpresaModel(Base):
    """SQLAlchemy model for Empresa"""
    __tablename__ = "empresas"

    id = Column(String(36), primary_key=True)
    nome = Column(String(200), nullable=False, unique=True)
    cnpj = Column(String(14), nullable=True)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
