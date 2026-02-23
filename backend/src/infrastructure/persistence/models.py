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
    turma_id = Column(String(36), ForeignKey("turmas.id"), nullable=True)  # NOVO - Vinculação com turma
    projeto_id = Column(String(36), nullable=True)
    projeto_nome = Column(String(200), nullable=True)
    empresa_id = Column(String(36), nullable=True)
    empresa_nome = Column(String(200), nullable=True)
    vinculo_tipo = Column(String(30), nullable=True, default="projeto")  # projeto, empresa, brasil_mais_produtivo
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


class TipoDocumentoModel(Base):
    """SQLAlchemy model for TipoDocumento - Documentos padronizados"""
    __tablename__ = "tipos_documento"

    id = Column(String(36), primary_key=True)
    codigo = Column(String(10), unique=True, nullable=False, index=True)  # Ex: "94", "131"
    nome = Column(String(200), nullable=False)
    obrigatorio = Column(Boolean, default=True)
    observacoes = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PendenciaModel(Base):
    """SQLAlchemy model for Pendencia Documental"""
    __tablename__ = "pendencias"

    id = Column(String(36), primary_key=True)
    aluno_id = Column(String(36), ForeignKey("alunos.id"), nullable=False, index=True)
    pedido_id = Column(String(36), ForeignKey("pedidos.id"), nullable=False, index=True)
    tipo_documento_id = Column(String(36), ForeignKey("tipos_documento.id"), nullable=True)  # Nullable para pendências manuais antigas
    documento_codigo = Column(String(10), nullable=False)  # Código do documento (ex: "94", "131")
    documento_nome = Column(String(200), nullable=True)   # Nome do documento
    status = Column(String(30), nullable=False, default="pendente", index=True)
    # Status: pendente, aguardando_aluno, em_analise, aprovado, rejeitado, reenvio_necessario
    observacoes = Column(Text, nullable=True)
    motivo_rejeicao = Column(Text, nullable=True)
    
    # Auditoria
    criado_por_id = Column(String(36), ForeignKey("usuarios.id"), nullable=True)
    criado_por_nome = Column(String(200), nullable=True)
    atualizado_por_id = Column(String(36), ForeignKey("usuarios.id"), nullable=True)
    atualizado_por_nome = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)  # Data de resolução

    # Relationships
    aluno = relationship("AlunoModel", backref="pendencias")
    pedido = relationship("PedidoModel", backref="pendencias")
    tipo_documento = relationship("TipoDocumentoModel")
    historico_contatos = relationship("HistoricoContatoModel", back_populates="pendencia", cascade="all, delete-orphan")


class HistoricoContatoModel(Base):
    """SQLAlchemy model for Histórico de Contatos com o Aluno"""
    __tablename__ = "historico_contatos"

    id = Column(String(36), primary_key=True)
    pendencia_id = Column(String(36), ForeignKey("pendencias.id"), nullable=False, index=True)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    usuario_nome = Column(String(200), nullable=False)
    tipo_contato = Column(String(30), nullable=False)  # telefone, whatsapp, email, presencial
    descricao = Column(Text, nullable=False)
    resultado = Column(String(50), nullable=True)  # atendeu, nao_atendeu, retornou, sem_resposta
    data_contato = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    pendencia = relationship("PendenciaModel", back_populates="historico_contatos")
    usuario = relationship("UsuarioModel")


class ReembolsoModel(Base):
    """SQLAlchemy model for Solicitação de Reembolso"""
    __tablename__ = "reembolsos"

    id = Column(String(36), primary_key=True)
    
    # Dados do Aluno (independente de pedidos existentes)
    aluno_nome = Column(String(200), nullable=False)
    aluno_cpf = Column(String(14), nullable=True)
    aluno_email = Column(String(200), nullable=True)
    aluno_telefone = Column(String(20), nullable=True)
    aluno_menor_idade = Column(Boolean, default=False)  # Se é menor de 18 anos
    curso = Column(String(200), nullable=False)
    turma = Column(String(100), nullable=True)
    
    # Dados da Solicitação
    motivo = Column(String(100), nullable=False)
    # Motivos: sem_escolaridade, sem_vaga, passou_bolsista, nao_tem_vaga, desistencia, outros
    motivo_descricao = Column(Text, nullable=True)  # Descrição adicional se "outros"
    reter_taxa = Column(Boolean, default=False)  # True se deve reter 10%
    
    # Chamado SGC Plus
    numero_chamado_sgc = Column(String(50), nullable=True)  # Número de referência
    
    # Dados Bancários (preenchidos quando aluno responder)
    banco_titular_nome = Column(String(200), nullable=True)
    banco_titular_cpf = Column(String(14), nullable=True)
    banco_nome = Column(String(100), nullable=True)  # Nome do banco (Caixa, Bradesco, etc)
    banco_agencia = Column(String(20), nullable=True)
    banco_operacao = Column(String(10), nullable=True)  # Operação (013 para poupança Caixa, etc)
    banco_conta = Column(String(30), nullable=True)  # Número da conta com dígito
    banco_tipo_conta = Column(String(20), nullable=True)  # corrente ou poupanca
    banco_responsavel_financeiro = Column(Boolean, default=False)  # True se conta é do responsável (menor de 18)
    dados_bancarios_recebidos_em = Column(DateTime, nullable=True)  # Data que recebeu os dados
    
    # Datas do Fluxo
    data_abertura = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    data_solicitacao_dados_bancarios = Column(DateTime, nullable=True)  # Data que enviou email solicitando
    data_retorno_financeiro = Column(DateTime, nullable=True)
    data_provisao_pagamento = Column(DateTime, nullable=True)
    data_pagamento = Column(DateTime, nullable=True)
    
    # Status do Fluxo
    status = Column(String(50), nullable=False, default="aberto", index=True)
    # Status: aberto, aguardando_dados_bancarios, enviado_financeiro, pago, cancelado
    
    observacoes = Column(Text, nullable=True)
    
    # Auditoria
    criado_por_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    criado_por_nome = Column(String(200), nullable=False)
    atualizado_por_id = Column(String(36), ForeignKey("usuarios.id"), nullable=True)
    atualizado_por_nome = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    criado_por = relationship("UsuarioModel", foreign_keys=[criado_por_id])
    atualizado_por = relationship("UsuarioModel", foreign_keys=[atualizado_por_id])
