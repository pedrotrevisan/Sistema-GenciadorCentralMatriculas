"""
Domain Entities - Módulo de Log de Contatos (Fase 3)

Entidades de domínio para registro de interações com alunos.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TipoContatoEnum(str, Enum):
    """Tipos de contato disponíveis"""
    LIGACAO = "ligacao"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PRESENCIAL = "presencial"
    SMS = "sms"
    OUTRO = "outro"


class ResultadoContatoEnum(str, Enum):
    """Resultado do contato"""
    SUCESSO = "sucesso"              # Conseguiu falar/contactar
    NAO_ATENDEU = "nao_atendeu"      # Não atendeu ligação
    CAIXA_POSTAL = "caixa_postal"    # Caiu na caixa postal
    NUMERO_ERRADO = "numero_errado"  # Número incorreto
    SEM_RESPOSTA = "sem_resposta"    # WhatsApp/Email sem resposta
    PENDENTE = "pendente"            # Aguardando retorno
    AGENDADO = "agendado"            # Agendou retorno/visita


class MotivoContatoEnum(str, Enum):
    """Motivo/assunto do contato"""
    DOCUMENTACAO = "documentacao"           # Solicitar documentos
    ACOMPANHAMENTO = "acompanhamento"       # Acompanhamento geral
    CONFIRMACAO = "confirmacao"             # Confirmar matrícula
    REEMBOLSO = "reembolso"                 # Assuntos de reembolso
    PENDENCIA = "pendencia"                 # Resolver pendência
    INFORMACAO = "informacao"               # Fornecer informação
    DESISTENCIA = "desistencia"             # Processo de desistência
    BOAS_VINDAS = "boas_vindas"             # Contato de boas-vindas
    LEMBRETE = "lembrete"                   # Lembrete de prazo
    OUTRO = "outro"


# Labels para exibição
TIPO_CONTATO_LABELS = {
    TipoContatoEnum.LIGACAO: "Ligação Telefônica",
    TipoContatoEnum.WHATSAPP: "WhatsApp",
    TipoContatoEnum.EMAIL: "E-mail",
    TipoContatoEnum.PRESENCIAL: "Presencial",
    TipoContatoEnum.SMS: "SMS",
    TipoContatoEnum.OUTRO: "Outro"
}

RESULTADO_CONTATO_LABELS = {
    ResultadoContatoEnum.SUCESSO: "Sucesso",
    ResultadoContatoEnum.NAO_ATENDEU: "Não Atendeu",
    ResultadoContatoEnum.CAIXA_POSTAL: "Caixa Postal",
    ResultadoContatoEnum.NUMERO_ERRADO: "Número Errado",
    ResultadoContatoEnum.SEM_RESPOSTA: "Sem Resposta",
    ResultadoContatoEnum.PENDENTE: "Aguardando Retorno",
    ResultadoContatoEnum.AGENDADO: "Retorno Agendado"
}

MOTIVO_CONTATO_LABELS = {
    MotivoContatoEnum.DOCUMENTACAO: "Solicitação de Documentos",
    MotivoContatoEnum.ACOMPANHAMENTO: "Acompanhamento",
    MotivoContatoEnum.CONFIRMACAO: "Confirmação de Matrícula",
    MotivoContatoEnum.REEMBOLSO: "Reembolso",
    MotivoContatoEnum.PENDENCIA: "Resolução de Pendência",
    MotivoContatoEnum.INFORMACAO: "Informação",
    MotivoContatoEnum.DESISTENCIA: "Desistência",
    MotivoContatoEnum.BOAS_VINDAS: "Boas-vindas",
    MotivoContatoEnum.LEMBRETE: "Lembrete de Prazo",
    MotivoContatoEnum.OUTRO: "Outro"
}

# Cores para UI
TIPO_CONTATO_COLORS = {
    TipoContatoEnum.LIGACAO: "blue",
    TipoContatoEnum.WHATSAPP: "green",
    TipoContatoEnum.EMAIL: "purple",
    TipoContatoEnum.PRESENCIAL: "orange",
    TipoContatoEnum.SMS: "cyan",
    TipoContatoEnum.OUTRO: "gray"
}

RESULTADO_CONTATO_COLORS = {
    ResultadoContatoEnum.SUCESSO: "green",
    ResultadoContatoEnum.NAO_ATENDEU: "red",
    ResultadoContatoEnum.CAIXA_POSTAL: "orange",
    ResultadoContatoEnum.NUMERO_ERRADO: "red",
    ResultadoContatoEnum.SEM_RESPOSTA: "amber",
    ResultadoContatoEnum.PENDENTE: "blue",
    ResultadoContatoEnum.AGENDADO: "purple"
}

# Ícones sugeridos para cada tipo
TIPO_CONTATO_ICONS = {
    TipoContatoEnum.LIGACAO: "Phone",
    TipoContatoEnum.WHATSAPP: "MessageCircle",
    TipoContatoEnum.EMAIL: "Mail",
    TipoContatoEnum.PRESENCIAL: "User",
    TipoContatoEnum.SMS: "MessageSquare",
    TipoContatoEnum.OUTRO: "MoreHorizontal"
}


@dataclass
class ContatoEntity:
    """
    Entidade de domínio para Log de Contato
    """
    id: str
    pedido_id: str
    tipo: TipoContatoEnum
    resultado: ResultadoContatoEnum
    motivo: MotivoContatoEnum
    descricao: str
    
    # Dados do contato
    contato_nome: Optional[str] = None       # Nome de quem atendeu (se diferente do aluno)
    contato_telefone: Optional[str] = None   # Telefone usado
    contato_email: Optional[str] = None      # Email usado
    
    # Agendamento de retorno
    data_retorno: Optional[datetime] = None
    retorno_realizado: bool = False
    
    # Auditoria
    usuario_id: str = ""
    usuario_nome: str = ""
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Converte a entidade para dicionário"""
        return {
            "id": self.id,
            "pedido_id": self.pedido_id,
            "tipo": self.tipo.value,
            "tipo_label": TIPO_CONTATO_LABELS.get(self.tipo, self.tipo.value),
            "tipo_color": TIPO_CONTATO_COLORS.get(self.tipo, "gray"),
            "tipo_icon": TIPO_CONTATO_ICONS.get(self.tipo, "MoreHorizontal"),
            "resultado": self.resultado.value,
            "resultado_label": RESULTADO_CONTATO_LABELS.get(self.resultado, self.resultado.value),
            "resultado_color": RESULTADO_CONTATO_COLORS.get(self.resultado, "gray"),
            "motivo": self.motivo.value,
            "motivo_label": MOTIVO_CONTATO_LABELS.get(self.motivo, self.motivo.value),
            "descricao": self.descricao,
            "contato_nome": self.contato_nome,
            "contato_telefone": self.contato_telefone,
            "contato_email": self.contato_email,
            "data_retorno": self.data_retorno.isoformat() if self.data_retorno else None,
            "retorno_realizado": self.retorno_realizado,
            "usuario_id": self.usuario_id,
            "usuario_nome": self.usuario_nome,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
            "sucesso": self.resultado == ResultadoContatoEnum.SUCESSO,
            "precisa_retorno": self.data_retorno is not None and not self.retorno_realizado
        }
    
    def marcar_retorno_realizado(self):
        """Marca que o retorno agendado foi realizado"""
        self.retorno_realizado = True
        self.atualizado_em = datetime.now()
    
    def agendar_retorno(self, data: datetime):
        """Agenda um retorno"""
        self.data_retorno = data
        self.retorno_realizado = False
        self.atualizado_em = datetime.now()


@dataclass
class ResumoContatosPedido:
    """
    Resumo de contatos de um pedido
    """
    pedido_id: str
    total_contatos: int = 0
    contatos_sucesso: int = 0
    contatos_sem_sucesso: int = 0
    ultimo_contato: Optional[datetime] = None
    ultimo_tipo: Optional[TipoContatoEnum] = None
    retornos_pendentes: int = 0
    
    def to_dict(self) -> dict:
        return {
            "pedido_id": self.pedido_id,
            "total_contatos": self.total_contatos,
            "contatos_sucesso": self.contatos_sucesso,
            "contatos_sem_sucesso": self.contatos_sem_sucesso,
            "taxa_sucesso": round((self.contatos_sucesso / self.total_contatos * 100), 1) if self.total_contatos > 0 else 0,
            "ultimo_contato": self.ultimo_contato.isoformat() if self.ultimo_contato else None,
            "ultimo_tipo": self.ultimo_tipo.value if self.ultimo_tipo else None,
            "ultimo_tipo_label": TIPO_CONTATO_LABELS.get(self.ultimo_tipo) if self.ultimo_tipo else None,
            "retornos_pendentes": self.retornos_pendentes,
            "precisa_contato": self.total_contatos == 0 or (
                self.ultimo_contato and (datetime.now() - self.ultimo_contato).days > 3
            )
        }
