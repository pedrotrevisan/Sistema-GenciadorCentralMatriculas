"""
DTOs para Máquina de Estados
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TransicionarStatusDTO(BaseModel):
    """DTO para transicionar status"""
    status_novo: str = Field(..., description="Novo status (enum)")
    motivo: Optional[str] = Field(None, max_length=500, description="Motivo da mudança")
    observacoes: Optional[str] = Field(None, max_length=1000, description="Observações adicionais")


class TransicaoStatusResponseDTO(BaseModel):
    """DTO de resposta para transição"""
    id: str
    pedido_id: str
    status_anterior: str
    status_novo: str
    tipo_transicao: str
    data_transicao: datetime
    motivo: Optional[str]
    observacoes: Optional[str]
    usuario_id: Optional[str]
    usuario_nome: Optional[str]
    usuario_email: Optional[str]
    
    class Config:
        from_attributes = True


class HistoricoStatusResponseDTO(BaseModel):
    """DTO de resposta para histórico"""
    total: int
    transicoes: List[TransicaoStatusResponseDTO]


class StatusDisponivelDTO(BaseModel):
    """DTO para status disponível"""
    valor: str
    label: str


class ProximosStatusResponseDTO(BaseModel):
    """DTO de resposta para próximos status"""
    status_atual: StatusDisponivelDTO
    proximos_status: List[StatusDisponivelDTO]
