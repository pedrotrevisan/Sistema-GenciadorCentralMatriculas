"""DTOs de Response"""
from pydantic import BaseModel
from typing import List, Optional, Any


class AlunoResponseDTO(BaseModel):
    """DTO de resposta para aluno"""
    id: str
    nome: str
    cpf: str
    cpf_formatado: str
    email: str
    telefone: str
    telefone_formatado: str
    data_nascimento: str
    rg: str
    rg_orgao_emissor: str
    rg_uf: str
    rg_data_emissao: Optional[str] = None
    naturalidade: Optional[str] = None
    naturalidade_uf: Optional[str] = None
    sexo: Optional[str] = None
    cor_raca: Optional[str] = None
    grau_instrucao: Optional[str] = None
    nome_pai: Optional[str] = None
    nome_mae: Optional[str] = None
    endereco_cep: str
    endereco_logradouro: str
    endereco_numero: str
    endereco_complemento: Optional[str]
    endereco_bairro: str
    endereco_cidade: str
    endereco_uf: str


class PedidoResponseDTO(BaseModel):
    """DTO de resposta para pedido"""
    id: str
    numero_protocolo: Optional[str] = None
    consultor_id: str
    consultor_nome: str
    curso_id: str
    curso_nome: str
    projeto_id: Optional[str]
    projeto_nome: Optional[str]
    empresa_id: Optional[str]
    empresa_nome: Optional[str]
    alunos: List[AlunoResponseDTO]
    status: str
    status_label: str
    observacoes: Optional[str]
    motivo_rejeicao: Optional[str]
    data_exportacao: Optional[str]
    exportado_por: Optional[str]
    created_at: str
    updated_at: str
    pode_editar: bool
    pode_exportar: bool
    total_alunos: int


class PaginacaoDTO(BaseModel):
    """DTO para informações de paginação"""
    pagina_atual: int
    itens_por_pagina: int
    total_itens: int
    total_paginas: int


class ListaPedidosResponseDTO(BaseModel):
    """DTO de resposta para lista de pedidos"""
    pedidos: List[PedidoResponseDTO]
    paginacao: PaginacaoDTO


class UsuarioResponseDTO(BaseModel):
    """DTO de resposta para usuário"""
    id: str
    nome: str
    email: str
    role: str
    ativo: bool
    primeiro_acesso: bool = False
    permissoes: List[str]
    created_at: str
    ultimo_acesso: Optional[str]


class LoginResponseDTO(BaseModel):
    """DTO de resposta para login"""
    token: str
    usuario: UsuarioResponseDTO


class ContadorStatusDTO(BaseModel):
    """DTO para contagem por status"""
    pendente: int = 0
    em_analise: int = 0
    documentacao_pendente: int = 0
    aprovado: int = 0
    rejeitado: int = 0
    realizado: int = 0
    cancelado: int = 0
    exportado: int = 0
    total: int = 0


class DashboardDTO(BaseModel):
    """DTO para dados do dashboard"""
    contagem_status: ContadorStatusDTO
    pedidos_recentes: List[PedidoResponseDTO]


class ErrorResponseDTO(BaseModel):
    """DTO para respostas de erro"""
    error: str
    code: str
    field: Optional[str] = None
    details: Optional[Any] = None
