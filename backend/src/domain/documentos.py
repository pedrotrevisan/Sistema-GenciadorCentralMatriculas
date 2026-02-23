"""
Enums para Gestão de Documentos
"""
from enum import Enum


class TipoDocumentoEnum(str, Enum):
    """Tipos de documentos que podem ser solicitados"""
    # Documentos de Identidade
    RG_FRENTE = "rg_frente"
    RG_VERSO = "rg_verso"
    RG_COMPLETO = "rg_completo"
    CPF = "cpf"
    CERTIDAO_NASCIMENTO = "certidao_nascimento"
    CERTIDAO_CASAMENTO = "certidao_casamento"
    
    # Documentos Escolares
    HISTORICO_ESCOLAR = "historico_escolar"
    COMPROVANTE_ESCOLARIDADE = "comprovante_escolaridade"
    CERTIFICADO_CONCLUSAO = "certificado_conclusao"
    DECLARACAO_MATRICULA = "declaracao_matricula"
    
    # Comprovantes
    COMPROVANTE_RESIDENCIA = "comprovante_residencia"
    COMPROVANTE_RENDA = "comprovante_renda"
    
    # Fotos
    FOTO_3X4 = "foto_3x4"
    FOTO_DOCUMENTO = "foto_documento"
    
    # Outros
    LAUDO_MEDICO = "laudo_medico"
    DECLARACAO_RESPONSAVEL = "declaracao_responsavel"
    OUTROS = "outros"


class StatusDocumentoEnum(str, Enum):
    """Status de um documento"""
    PENDENTE = "pendente"           # Aguardando envio
    ENVIADO = "enviado"             # Enviado, aguardando validação
    EM_ANALISE = "em_analise"       # Em processo de validação
    APROVADO = "aprovado"           # Validado e aprovado
    RECUSADO = "recusado"           # Validado mas recusado
    EXPIRADO = "expirado"           # Prazo vencido


class PrioridadeDocumentoEnum(str, Enum):
    """Prioridade do documento"""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


# Labels amigáveis
TIPO_DOCUMENTO_LABELS = {
    TipoDocumentoEnum.RG_FRENTE: "RG (Frente)",
    TipoDocumentoEnum.RG_VERSO: "RG (Verso)",
    TipoDocumentoEnum.RG_COMPLETO: "RG (Frente e Verso)",
    TipoDocumentoEnum.CPF: "CPF",
    TipoDocumentoEnum.CERTIDAO_NASCIMENTO: "Certidão de Nascimento",
    TipoDocumentoEnum.CERTIDAO_CASAMENTO: "Certidão de Casamento",
    TipoDocumentoEnum.HISTORICO_ESCOLAR: "Histórico Escolar",
    TipoDocumentoEnum.COMPROVANTE_ESCOLARIDADE: "Comprovante de Escolaridade",
    TipoDocumentoEnum.CERTIFICADO_CONCLUSAO: "Certificado de Conclusão",
    TipoDocumentoEnum.DECLARACAO_MATRICULA: "Declaração de Matrícula",
    TipoDocumentoEnum.COMPROVANTE_RESIDENCIA: "Comprovante de Residência",
    TipoDocumentoEnum.COMPROVANTE_RENDA: "Comprovante de Renda",
    TipoDocumentoEnum.FOTO_3X4: "Foto 3x4",
    TipoDocumentoEnum.FOTO_DOCUMENTO: "Foto do Documento",
    TipoDocumentoEnum.LAUDO_MEDICO: "Laudo Médico",
    TipoDocumentoEnum.DECLARACAO_RESPONSAVEL: "Declaração do Responsável",
    TipoDocumentoEnum.OUTROS: "Outros"
}

STATUS_DOCUMENTO_LABELS = {
    StatusDocumentoEnum.PENDENTE: "Pendente",
    StatusDocumentoEnum.ENVIADO: "Enviado",
    StatusDocumentoEnum.EM_ANALISE: "Em Análise",
    StatusDocumentoEnum.APROVADO: "Aprovado",
    StatusDocumentoEnum.RECUSADO: "Recusado",
    StatusDocumentoEnum.EXPIRADO: "Expirado"
}

PRIORIDADE_LABELS = {
    PrioridadeDocumentoEnum.BAIXA: "Baixa",
    PrioridadeDocumentoEnum.MEDIA: "Média",
    PrioridadeDocumentoEnum.ALTA: "Alta",
    PrioridadeDocumentoEnum.URGENTE: "Urgente"
}

# Cores para UI
STATUS_DOCUMENTO_COLORS = {
    StatusDocumentoEnum.PENDENTE: "orange",
    StatusDocumentoEnum.ENVIADO: "blue",
    StatusDocumentoEnum.EM_ANALISE: "yellow",
    StatusDocumentoEnum.APROVADO: "green",
    StatusDocumentoEnum.RECUSADO: "red",
    StatusDocumentoEnum.EXPIRADO: "gray"
}

PRIORIDADE_COLORS = {
    PrioridadeDocumentoEnum.BAIXA: "gray",
    PrioridadeDocumentoEnum.MEDIA: "blue",
    PrioridadeDocumentoEnum.ALTA: "orange",
    PrioridadeDocumentoEnum.URGENTE: "red"
}


# Documentos obrigatórios por padrão
DOCUMENTOS_OBRIGATORIOS_PADRAO = [
    TipoDocumentoEnum.RG_COMPLETO,
    TipoDocumentoEnum.CPF,
    TipoDocumentoEnum.COMPROVANTE_RESIDENCIA,
    TipoDocumentoEnum.FOTO_3X4,
    TipoDocumentoEnum.HISTORICO_ESCOLAR
]
