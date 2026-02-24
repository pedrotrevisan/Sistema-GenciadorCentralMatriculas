"""Value Object - Status do Pedido - Alinhado com Fluxo SENAI/CAC"""
from enum import Enum
from typing import List, Dict, Any
from ..exceptions.domain_exceptions import TransicaoStatusInvalidaException


class StatusPedido(Enum):
    """
    Enum com lógica de transições válidas - Fluxo SENAI CAC
    
    Fluxo Principal:
    INSCRICAO → ANALISE_DOCUMENTAL → DOCUMENTACAO_PENDENTE (5 dias) → APROVADO → 
    AGUARDANDO_PAGAMENTO → MATRICULADO → EXPORTADO
    
    Fluxos Alternativos:
    - NAO_ATENDE_REQUISITO: Quando não cumpre pré-requisitos (cancelamento imediato)
    - TRANCADO: Interrupção temporária (apenas cursos técnicos)
    - TRANSFERIDO: Mudança de curso/turma/unidade
    """
    # Fluxo principal
    PENDENTE = "pendente"  # Legado - mapeado para INSCRICAO
    INSCRICAO = "inscricao"  # Novo - Inscrição recebida
    EM_ANALISE = "em_analise"  # Legado - mapeado para ANALISE_DOCUMENTAL
    ANALISE_DOCUMENTAL = "analise_documental"  # Novo - Análise de documentos
    DOCUMENTACAO_PENDENTE = "documentacao_pendente"  # Prazo de 5 dias
    APROVADO = "aprovado"  # Documentação OK
    AGUARDANDO_PAGAMENTO = "aguardando_pagamento"  # Novo - Aguardando pagamento
    MATRICULADO = "matriculado"  # Novo - Matrícula efetivada
    REALIZADO = "realizado"  # Legado - mapeado para MATRICULADO
    EXPORTADO = "exportado"  # Enviado para TOTVS
    
    # Fluxos alternativos
    NAO_ATENDE_REQUISITO = "nao_atende_requisito"  # Novo - Não cumpre pré-requisitos
    REJEITADO = "rejeitado"  # Legado
    CANCELADO = "cancelado"
    TRANCADO = "trancado"  # Novo - Trancamento de matrícula
    TRANSFERIDO = "transferido"  # Novo - Transferência

    @property
    def transicoes_validas(self) -> List["StatusPedido"]:
        """Define as transições válidas para cada status - Fluxo SENAI"""
        transicoes = {
            # Fluxo de entrada
            StatusPedido.PENDENTE: [
                StatusPedido.EM_ANALISE,
                StatusPedido.ANALISE_DOCUMENTAL,
                StatusPedido.CANCELADO
            ],
            StatusPedido.INSCRICAO: [
                StatusPedido.ANALISE_DOCUMENTAL,
                StatusPedido.NAO_ATENDE_REQUISITO,
                StatusPedido.CANCELADO
            ],
            
            # Análise documental
            StatusPedido.EM_ANALISE: [
                StatusPedido.DOCUMENTACAO_PENDENTE,
                StatusPedido.APROVADO,
                StatusPedido.REJEITADO,
                StatusPedido.NAO_ATENDE_REQUISITO,
                StatusPedido.CANCELADO
            ],
            StatusPedido.ANALISE_DOCUMENTAL: [
                StatusPedido.DOCUMENTACAO_PENDENTE,
                StatusPedido.APROVADO,
                StatusPedido.NAO_ATENDE_REQUISITO,
                StatusPedido.CANCELADO
            ],
            
            # Pendência documental (prazo 5 dias)
            StatusPedido.DOCUMENTACAO_PENDENTE: [
                StatusPedido.EM_ANALISE,
                StatusPedido.ANALISE_DOCUMENTAL,
                StatusPedido.APROVADO,
                StatusPedido.NAO_ATENDE_REQUISITO,
                StatusPedido.CANCELADO
            ],
            
            # Aprovação e pagamento
            StatusPedido.APROVADO: [
                StatusPedido.AGUARDANDO_PAGAMENTO,
                StatusPedido.MATRICULADO,
                StatusPedido.REALIZADO,
                StatusPedido.CANCELADO
            ],
            StatusPedido.AGUARDANDO_PAGAMENTO: [
                StatusPedido.MATRICULADO,
                StatusPedido.REALIZADO,
                StatusPedido.CANCELADO
            ],
            
            # Matrícula efetivada
            StatusPedido.MATRICULADO: [
                StatusPedido.EXPORTADO,
                StatusPedido.TRANCADO,
                StatusPedido.TRANSFERIDO,
                StatusPedido.CANCELADO
            ],
            StatusPedido.REALIZADO: [
                StatusPedido.EXPORTADO,
                StatusPedido.TRANCADO,
                StatusPedido.TRANSFERIDO
            ],
            
            # Estados finais
            StatusPedido.EXPORTADO: [],
            StatusPedido.REJEITADO: [],
            StatusPedido.NAO_ATENDE_REQUISITO: [],
            StatusPedido.CANCELADO: [],
            
            # Trancamento pode ser reativado
            StatusPedido.TRANCADO: [
                StatusPedido.MATRICULADO,
                StatusPedido.REALIZADO,
                StatusPedido.CANCELADO
            ],
            
            # Transferência é estado final
            StatusPedido.TRANSFERIDO: []
        }
        return transicoes.get(self, [])

    def pode_transitar_para(self, novo_status: "StatusPedido") -> bool:
        """Verifica se a transição é válida"""
        return novo_status in self.transicoes_validas

    def transitar_para(self, novo_status: "StatusPedido") -> "StatusPedido":
        """Realiza a transição se válida, senão lança exceção"""
        if not self.pode_transitar_para(novo_status):
            raise TransicaoStatusInvalidaException(self.value, novo_status.value)
        return novo_status

    @property
    def permite_edicao(self) -> bool:
        """Verifica se o status permite edição do pedido"""
        return self in [
            StatusPedido.PENDENTE,
            StatusPedido.EM_ANALISE,
            StatusPedido.DOCUMENTACAO_PENDENTE
        ]

    @property
    def permite_exportacao(self) -> bool:
        """Verifica se o status permite exportação"""
        return self == StatusPedido.REALIZADO

    @property
    def label(self) -> str:
        """Retorna o label legível do status"""
        labels = {
            StatusPedido.PENDENTE: "Pendente",
            StatusPedido.EM_ANALISE: "Em Análise",
            StatusPedido.DOCUMENTACAO_PENDENTE: "Documentação Pendente",
            StatusPedido.APROVADO: "Aprovado",
            StatusPedido.REJEITADO: "Rejeitado",
            StatusPedido.REALIZADO: "Realizado",
            StatusPedido.CANCELADO: "Cancelado",
            StatusPedido.EXPORTADO: "Exportado"
        }
        return labels.get(self, self.value)

    @classmethod
    def from_string(cls, value: str) -> "StatusPedido":
        """Cria StatusPedido a partir de string"""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Status inválido: {value}")
