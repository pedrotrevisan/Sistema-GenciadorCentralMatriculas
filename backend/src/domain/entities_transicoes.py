"""
Entidade de Domínio - Transição de Status
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json

from src.domain.status_matricula import StatusMatriculaEnum, TipoTransicao


@dataclass
class TransicaoStatus:
    """
    Entidade que representa uma transição de status de matrícula
    
    Imutável após criação - registra um evento histórico.
    """
    id: str
    pedido_id: str
    status_anterior: StatusMatriculaEnum
    status_novo: StatusMatriculaEnum
    tipo_transicao: TipoTransicao
    data_transicao: datetime
    motivo: Optional[str] = None
    observacoes: Optional[str] = None
    usuario_id: Optional[str] = None
    usuario_nome: Optional[str] = None
    usuario_email: Optional[str] = None
    metadados: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "pedido_id": self.pedido_id,
            "status_anterior": self.status_anterior.value,
            "status_novo": self.status_novo.value,
            "tipo_transicao": self.tipo_transicao.value,
            "data_transicao": self.data_transicao.isoformat(),
            "motivo": self.motivo,
            "observacoes": self.observacoes,
            "usuario_id": self.usuario_id,
            "usuario_nome": self.usuario_nome,
            "usuario_email": self.usuario_email,
            "metadados": self.metadados
        }
    
    def foi_automatica(self) -> bool:
        """Verifica se foi transição automática"""
        return self.tipo_transicao == TipoTransicao.AUTOMATICA
    
    def foi_manual(self) -> bool:
        """Verifica se foi transição manual"""
        return self.tipo_transicao == TipoTransicao.MANUAL
    
    def tem_usuario(self) -> bool:
        """Verifica se tem usuário associado"""
        return self.usuario_id is not None
