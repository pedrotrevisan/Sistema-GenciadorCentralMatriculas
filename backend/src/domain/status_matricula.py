"""
Enums e Value Objects para Máquina de Estados
"""
from enum import Enum


class StatusMatriculaEnum(str, Enum):
    """
    Estados possíveis de uma matrícula
    
    Fluxo principal:
    INSCRITO → ANALISE_DOCUMENTAL → MATRICULADO
                     ↓                    ↓
                CANCELADO            TRANCADO
    """
    INSCRITO = "inscrito"                      # Inicial - pedido criado
    ANALISE_DOCUMENTAL = "analise_documental"  # Aguardando documentos
    PENDENTE_PAGAMENTO = "pendente_pagamento"  # Aguardando confirmação de pagamento
    MATRICULADO = "matriculado"                # Efetivamente matriculado
    TRANCADO = "trancado"                      # Matrícula trancada
    CANCELADO = "cancelado"                    # Cancelado/Desistiu
    CONCLUIDO = "concluido"                    # Curso concluído
    EVADIDO = "evadido"                        # Evasão


class TipoTransicao(str, Enum):
    """Tipos de transição de status"""
    MANUAL = "manual"           # Mudança manual por usuário
    AUTOMATICA = "automatica"   # Mudança automática pelo sistema
    INTEGRACAO = "integracao"   # Mudança via integração externa


# Mapeamento de transições válidas
TRANSICOES_VALIDAS = {
    StatusMatriculaEnum.INSCRITO: [
        StatusMatriculaEnum.ANALISE_DOCUMENTAL,
        StatusMatriculaEnum.CANCELADO
    ],
    StatusMatriculaEnum.ANALISE_DOCUMENTAL: [
        StatusMatriculaEnum.PENDENTE_PAGAMENTO,
        StatusMatriculaEnum.MATRICULADO,
        StatusMatriculaEnum.CANCELADO
    ],
    StatusMatriculaEnum.PENDENTE_PAGAMENTO: [
        StatusMatriculaEnum.MATRICULADO,
        StatusMatriculaEnum.CANCELADO
    ],
    StatusMatriculaEnum.MATRICULADO: [
        StatusMatriculaEnum.TRANCADO,
        StatusMatriculaEnum.CONCLUIDO,
        StatusMatriculaEnum.EVADIDO,
        StatusMatriculaEnum.CANCELADO  # Caso excepcional
    ],
    StatusMatriculaEnum.TRANCADO: [
        StatusMatriculaEnum.MATRICULADO,  # Reativação
        StatusMatriculaEnum.CANCELADO
    ],
    StatusMatriculaEnum.CANCELADO: [],  # Estado final
    StatusMatriculaEnum.CONCLUIDO: [],  # Estado final
    StatusMatriculaEnum.EVADIDO: [
        StatusMatriculaEnum.MATRICULADO  # Retorno
    ]
}


# Labels amigáveis para UI
STATUS_LABELS = {
    StatusMatriculaEnum.INSCRITO: "Inscrito",
    StatusMatriculaEnum.ANALISE_DOCUMENTAL: "Análise Documental",
    StatusMatriculaEnum.PENDENTE_PAGAMENTO: "Pendente Pagamento",
    StatusMatriculaEnum.MATRICULADO: "Matriculado",
    StatusMatriculaEnum.TRANCADO: "Trancado",
    StatusMatriculaEnum.CANCELADO: "Cancelado",
    StatusMatriculaEnum.CONCLUIDO: "Concluído",
    StatusMatriculaEnum.EVADIDO: "Evadido"
}


# Cores para UI
STATUS_COLORS = {
    StatusMatriculaEnum.INSCRITO: "blue",
    StatusMatriculaEnum.ANALISE_DOCUMENTAL: "yellow",
    StatusMatriculaEnum.PENDENTE_PAGAMENTO: "orange",
    StatusMatriculaEnum.MATRICULADO: "green",
    StatusMatriculaEnum.TRANCADO: "purple",
    StatusMatriculaEnum.CANCELADO: "red",
    StatusMatriculaEnum.CONCLUIDO: "gray",
    StatusMatriculaEnum.EVADIDO: "red"
}


def pode_transicionar(status_atual: StatusMatriculaEnum, status_novo: StatusMatriculaEnum) -> bool:
    """
    Verifica se uma transição de status é válida
    
    Args:
        status_atual: Status atual
        status_novo: Status desejado
    
    Returns:
        True se transição é válida, False caso contrário
    """
    if status_atual == status_novo:
        return False  # Não pode transicionar para o mesmo estado
    
    return status_novo in TRANSICOES_VALIDAS.get(status_atual, [])


def obter_proximos_status_validos(status_atual: StatusMatriculaEnum) -> list[StatusMatriculaEnum]:
    """
    Retorna lista de próximos status válidos a partir do status atual
    
    Args:
        status_atual: Status atual
    
    Returns:
        Lista de status válidos para transição
    """
    return TRANSICOES_VALIDAS.get(status_atual, [])
