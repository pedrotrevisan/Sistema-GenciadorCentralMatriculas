"""
Entidade de Domínio - Pendência Documental
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.documentos import TipoDocumentoEnum, StatusDocumentoEnum, PrioridadeDocumentoEnum


@dataclass
class PendenciaDocumental:
    """
    Entidade que representa uma pendência documental de matrícula
    """
    id: str
    pedido_id: str
    tipo: TipoDocumentoEnum
    status: StatusDocumentoEnum
    prioridade: PrioridadeDocumentoEnum
    obrigatorio: bool
    aluno_id: Optional[str] = None
    descricao: Optional[str] = None
    observacoes: Optional[str] = None
    arquivo_url: Optional[str] = None
    arquivo_nome: Optional[str] = None
    arquivo_tamanho: Optional[str] = None
    prazo_limite: Optional[datetime] = None
    data_envio: Optional[datetime] = None
    data_validacao: Optional[datetime] = None
    validado_por_id: Optional[str] = None
    validado_por_nome: Optional[str] = None
    motivo_recusa: Optional[str] = None
    criado_por_id: Optional[str] = None
    criado_por_nome: Optional[str] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
    
    def esta_pendente(self) -> bool:
        """Verifica se ainda está pendente"""
        return self.status == StatusDocumentoEnum.PENDENTE
    
    def foi_enviado(self) -> bool:
        """Verifica se foi enviado"""
        return self.status in [
            StatusDocumentoEnum.ENVIADO,
            StatusDocumentoEnum.EM_ANALISE,
            StatusDocumentoEnum.APROVADO
        ]
    
    def foi_aprovado(self) -> bool:
        """Verifica se foi aprovado"""
        return self.status == StatusDocumentoEnum.APROVADO
    
    def foi_recusado(self) -> bool:
        """Verifica se foi recusado"""
        return self.status == StatusDocumentoEnum.RECUSADO
    
    def esta_expirado(self) -> bool:
        """Verifica se o prazo expirou"""
        if not self.prazo_limite:
            return False
        return self.status == StatusDocumentoEnum.EXPIRADO or datetime.now() > self.prazo_limite
    
    def dias_para_prazo(self) -> Optional[int]:
        """Retorna quantos dias faltam para o prazo"""
        if not self.prazo_limite:
            return None
        delta = self.prazo_limite - datetime.now()
        return delta.days
    
    def enviar(self, arquivo_url: str, arquivo_nome: str, arquivo_tamanho: str):
        """Marca como enviado"""
        self.status = StatusDocumentoEnum.ENVIADO
        self.arquivo_url = arquivo_url
        self.arquivo_nome = arquivo_nome
        self.arquivo_tamanho = arquivo_tamanho
        self.data_envio = datetime.now()
    
    def colocar_em_analise(self):
        """Coloca em análise"""
        if self.status != StatusDocumentoEnum.ENVIADO:
            raise ValueError("Apenas documentos enviados podem ser analisados")
        self.status = StatusDocumentoEnum.EM_ANALISE
    
    def aprovar(self, validador_id: str, validador_nome: str):
        """Aprova o documento"""
        self.status = StatusDocumentoEnum.APROVADO
        self.validado_por_id = validador_id
        self.validado_por_nome = validador_nome
        self.data_validacao = datetime.now()
    
    def recusar(self, validador_id: str, validador_nome: str, motivo: str):
        """Recusa o documento"""
        self.status = StatusDocumentoEnum.RECUSADO
        self.validado_por_id = validador_id
        self.validado_por_nome = validador_nome
        self.motivo_recusa = motivo
        self.data_validacao = datetime.now()
    
    def expirar(self):
        """Marca como expirado"""
        if self.status == StatusDocumentoEnum.PENDENTE:
            self.status = StatusDocumentoEnum.EXPIRADO
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "pedido_id": self.pedido_id,
            "aluno_id": self.aluno_id,
            "tipo": self.tipo.value,
            "status": self.status.value,
            "prioridade": self.prioridade.value,
            "obrigatorio": self.obrigatorio,
            "descricao": self.descricao,
            "observacoes": self.observacoes,
            "arquivo_url": self.arquivo_url,
            "arquivo_nome": self.arquivo_nome,
            "arquivo_tamanho": self.arquivo_tamanho,
            "prazo_limite": self.prazo_limite.isoformat() if self.prazo_limite else None,
            "data_envio": self.data_envio.isoformat() if self.data_envio else None,
            "data_validacao": self.data_validacao.isoformat() if self.data_validacao else None,
            "validado_por_id": self.validado_por_id,
            "validado_por_nome": self.validado_por_nome,
            "motivo_recusa": self.motivo_recusa,
            "dias_para_prazo": self.dias_para_prazo(),
            "esta_expirado": self.esta_expirado(),
            "criado_em": self.criado_em.isoformat() if self.criado_em else None
        }
