"""DTOs de Request"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class AlunoCreateDTO(BaseModel):
    """DTO para criação de aluno"""
    nome: str = Field(..., min_length=3, max_length=200)
    cpf: str = Field(..., min_length=11, max_length=14)
    email: str = Field(..., min_length=5)
    telefone: str = Field(..., min_length=10, max_length=20)
    data_nascimento: str
    rg: str = Field(..., min_length=5)
    rg_orgao_emissor: str = Field(..., min_length=2)
    rg_uf: str = Field(..., min_length=2, max_length=2)
    rg_data_emissao: Optional[str] = None  # NOVO - Emissão RG
    naturalidade: Optional[str] = None  # NOVO - Naturalidade
    naturalidade_uf: Optional[str] = None  # NOVO - Estado Natal/UF
    sexo: Optional[str] = None  # NOVO - M/F
    cor_raca: Optional[str] = None  # NOVO - Cor/Raça
    grau_instrucao: Optional[str] = None  # NOVO - Grau de Instrução
    nome_pai: Optional[str] = None  # NOVO - Nome do pai
    nome_mae: Optional[str] = None  # NOVO - Nome da mãe
    endereco_cep: str = Field(..., min_length=8, max_length=9)
    endereco_logradouro: str = Field(..., min_length=3)
    endereco_numero: str = Field(..., min_length=1)
    endereco_complemento: Optional[str] = None
    endereco_bairro: str = Field(..., min_length=2)
    endereco_cidade: str = Field(..., min_length=2)
    endereco_uf: str = Field(..., min_length=2, max_length=2)


class CriarPedidoDTO(BaseModel):
    """DTO para criação de pedido"""
    curso_id: str
    curso_nome: str
    projeto_id: Optional[str] = None
    projeto_nome: Optional[str] = None
    empresa_id: Optional[str] = None
    empresa_nome: Optional[str] = None
    alunos: List[AlunoCreateDTO]
    observacoes: Optional[str] = None


class AtualizarStatusDTO(BaseModel):
    """DTO para atualização de status"""
    status: str
    motivo: Optional[str] = None


class LoginDTO(BaseModel):
    """DTO para login"""
    email: str
    senha: str


class CriarUsuarioDTO(BaseModel):
    """DTO para criação de usuário"""
    nome: str = Field(..., min_length=3)
    email: str
    senha: str = Field(..., min_length=6)
    role: str = Field(default="consultor")


class AtualizarUsuarioDTO(BaseModel):
    """DTO para atualização de usuário"""
    nome: Optional[str] = None
    role: Optional[str] = None
    ativo: Optional[bool] = None


class FiltrosPedidoDTO(BaseModel):
    """DTO para filtros de listagem de pedidos"""
    status: Optional[str] = None
    consultor_id: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    pagina: int = Field(default=1, ge=1)
    por_pagina: int = Field(default=10, ge=1, le=100)
