"""
Models para Chamados SGC Plus - Sistema de Tickets BMP
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class ChamadoSGCModel(Base):
    """Modelo para Chamados SGC - Tickets de Matrícula BMP"""
    __tablename__ = "chamados_sgc"
    
    id = Column(String(36), primary_key=True)
    numero_ticket = Column(String(50), unique=True, nullable=False, index=True)
    titulo = Column(String(255))
    descricao = Column(Text)
    
    # Datas
    data_abertura = Column(DateTime)
    data_previsao_inicio = Column(DateTime)
    data_previsao_fim = Column(DateTime)
    data_fechamento = Column(DateTime)
    
    # Status e Prioridade
    status = Column(String(50), default="backlog", index=True)
    prioridade = Column(Integer, default=0)
    critico = Column(Boolean, default=False)
    
    # SLA
    sla_horas = Column(Float, default=32.0)
    sla_consumido = Column(Float, default=0.0)
    sla_pausado = Column(Boolean, default=False)
    
    # Solicitante (dados do formulário SGC)
    solicitante_nome = Column(String(255))
    solicitante_telefone = Column(String(20))
    solicitante_unidade = Column(String(255))
    
    # Classificação
    area = Column(String(100))
    classificacao = Column(String(100), default="Matrícula")
    produto = Column(String(100), default="MATRÍCULA BMP")
    dono_produto = Column(String(255))
    tecnico_responsavel = Column(String(255))
    
    # ========================================
    # NOVOS CAMPOS - Formulário SGC Plus BMP
    # ========================================
    
    # Informações do Curso
    codigo_curso = Column(String(50))
    nome_curso = Column(String(255))
    turno = Column(String(50))  # Manhã, Tarde, Noite, Integral
    periodo_letivo = Column(String(50))
    quantidade_vagas = Column(Integer)
    modalidade = Column(String(50))  # CAP, IP, CAI, CQPH, CQP
    forma_pagamento = Column(String(100))  # Empresa, Aluno, Gratuidade Regimental
    cont = Column(String(100))  # CONT do curso
    requisito_acesso = Column(Text)  # Requisitos para acesso ao curso
    
    # Dados da Empresa (cliente)
    empresa_nome = Column(String(255))
    empresa_contato = Column(String(255))
    empresa_email = Column(String(255))
    empresa_telefone = Column(String(50))
    
    # Período do Curso
    data_inicio_curso = Column(DateTime)
    data_fim_curso = Column(DateTime)
    
    # Documentos
    documentos_obrigatorios = Column(Text)  # Lista de documentos separados por vírgula
    
    # ========================================
    
    # Relacionamento com Pedido (se vinculado)
    pedido_id = Column(String(36), ForeignKey("pedidos.id"), nullable=True)
    
    # Auditoria
    criado_por_id = Column(String(36))
    criado_por_nome = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ChamadoSGCAndamentoModel(Base):
    """Modelo para Andamentos de Chamados SGC"""
    __tablename__ = "chamados_sgc_andamentos"
    
    id = Column(String(36), primary_key=True)
    chamado_id = Column(String(36), ForeignKey("chamados_sgc.id"), nullable=False, index=True)
    andamento = Column(String(100), nullable=False)
    observacao = Column(Text)
    usuario_id = Column(String(36))
    usuario_nome = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChamadoSGCInteracaoModel(Base):
    """Modelo para Interações/Comunicações de Chamados SGC"""
    __tablename__ = "chamados_sgc_interacoes"
    
    id = Column(String(36), primary_key=True)
    chamado_id = Column(String(36), ForeignKey("chamados_sgc.id"), nullable=False, index=True)
    tipo = Column(String(50), default="comunicacao")  # comunicacao, email, telefone
    mensagem = Column(Text, nullable=False)
    usuario_id = Column(String(36))
    usuario_nome = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChamadoSGCEsforcoModel(Base):
    """Modelo para Registro de Esforço (Horas) de Chamados SGC"""
    __tablename__ = "chamados_sgc_esforco"
    
    id = Column(String(36), primary_key=True)
    chamado_id = Column(String(36), ForeignKey("chamados_sgc.id"), nullable=False, index=True)
    analista_id = Column(String(36))
    analista_nome = Column(String(255))
    horas = Column(Float, nullable=False)
    data = Column(String(10))  # YYYY-MM-DD
    descricao = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
