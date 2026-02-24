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
            StatusPedido.INSCRICAO,
            StatusPedido.EM_ANALISE,
            StatusPedido.ANALISE_DOCUMENTAL,
            StatusPedido.DOCUMENTACAO_PENDENTE
        ]

    @property
    def permite_exportacao(self) -> bool:
        """Verifica se o status permite exportação"""
        return self in [StatusPedido.REALIZADO, StatusPedido.MATRICULADO]

    @property
    def is_final(self) -> bool:
        """Verifica se é um estado final (sem transições possíveis)"""
        return self in [
            StatusPedido.EXPORTADO,
            StatusPedido.REJEITADO,
            StatusPedido.NAO_ATENDE_REQUISITO,
            StatusPedido.CANCELADO,
            StatusPedido.TRANSFERIDO
        ]

    @property
    def cor(self) -> str:
        """Retorna a cor associada ao status para UI"""
        cores = {
            StatusPedido.PENDENTE: "yellow",
            StatusPedido.INSCRICAO: "blue",
            StatusPedido.EM_ANALISE: "blue",
            StatusPedido.ANALISE_DOCUMENTAL: "blue",
            StatusPedido.DOCUMENTACAO_PENDENTE: "orange",
            StatusPedido.APROVADO: "green",
            StatusPedido.AGUARDANDO_PAGAMENTO: "purple",
            StatusPedido.MATRICULADO: "green",
            StatusPedido.REALIZADO: "green",
            StatusPedido.EXPORTADO: "gray",
            StatusPedido.REJEITADO: "red",
            StatusPedido.NAO_ATENDE_REQUISITO: "red",
            StatusPedido.CANCELADO: "red",
            StatusPedido.TRANCADO: "orange",
            StatusPedido.TRANSFERIDO: "cyan"
        }
        return cores.get(self, "gray")

    @property
    def icone(self) -> str:
        """Retorna o ícone associado ao status"""
        icones = {
            StatusPedido.PENDENTE: "clock",
            StatusPedido.INSCRICAO: "file-plus",
            StatusPedido.EM_ANALISE: "search",
            StatusPedido.ANALISE_DOCUMENTAL: "file-search",
            StatusPedido.DOCUMENTACAO_PENDENTE: "file-warning",
            StatusPedido.APROVADO: "check-circle",
            StatusPedido.AGUARDANDO_PAGAMENTO: "credit-card",
            StatusPedido.MATRICULADO: "user-check",
            StatusPedido.REALIZADO: "check-circle",
            StatusPedido.EXPORTADO: "upload-cloud",
            StatusPedido.REJEITADO: "x-circle",
            StatusPedido.NAO_ATENDE_REQUISITO: "alert-triangle",
            StatusPedido.CANCELADO: "x-circle",
            StatusPedido.TRANCADO: "pause-circle",
            StatusPedido.TRANSFERIDO: "arrow-right-circle"
        }
        return icones.get(self, "circle")

    @property
    def label(self) -> str:
        """Retorna o label legível do status"""
        labels = {
            StatusPedido.PENDENTE: "Pendente",
            StatusPedido.INSCRICAO: "Inscrição",
            StatusPedido.EM_ANALISE: "Em Análise",
            StatusPedido.ANALISE_DOCUMENTAL: "Análise Documental",
            StatusPedido.DOCUMENTACAO_PENDENTE: "Documentação Pendente",
            StatusPedido.APROVADO: "Aprovado",
            StatusPedido.AGUARDANDO_PAGAMENTO: "Aguardando Pagamento",
            StatusPedido.MATRICULADO: "Matriculado",
            StatusPedido.REALIZADO: "Realizado",
            StatusPedido.EXPORTADO: "Exportado",
            StatusPedido.REJEITADO: "Rejeitado",
            StatusPedido.NAO_ATENDE_REQUISITO: "Não Atende Requisito",
            StatusPedido.CANCELADO: "Cancelado",
            StatusPedido.TRANCADO: "Trancado",
            StatusPedido.TRANSFERIDO: "Transferido"
        }
        return labels.get(self, self.value)

    @property
    def descricao(self) -> str:
        """Retorna descrição detalhada do status"""
        descricoes = {
            StatusPedido.PENDENTE: "Aguardando início da análise",
            StatusPedido.INSCRICAO: "Inscrição recebida, aguardando análise",
            StatusPedido.EM_ANALISE: "Documentos em análise pela CAC",
            StatusPedido.ANALISE_DOCUMENTAL: "Análise de documentos em andamento",
            StatusPedido.DOCUMENTACAO_PENDENTE: "Aguardando documentos do aluno (prazo: 5 dias)",
            StatusPedido.APROVADO: "Documentação aprovada, aguardando efetivação",
            StatusPedido.AGUARDANDO_PAGAMENTO: "Aguardando confirmação de pagamento",
            StatusPedido.MATRICULADO: "Matrícula efetivada no sistema",
            StatusPedido.REALIZADO: "Matrícula realizada com sucesso",
            StatusPedido.EXPORTADO: "Dados exportados para o TOTVS",
            StatusPedido.REJEITADO: "Solicitação rejeitada",
            StatusPedido.NAO_ATENDE_REQUISITO: "Não atende aos pré-requisitos do curso",
            StatusPedido.CANCELADO: "Solicitação cancelada",
            StatusPedido.TRANCADO: "Matrícula trancada temporariamente",
            StatusPedido.TRANSFERIDO: "Transferido para outro curso/unidade"
        }
        return descricoes.get(self, "")

    @classmethod
    def from_string(cls, value: str) -> "StatusPedido":
        """Cria StatusPedido a partir de string"""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Status inválido: {value}")

    @classmethod
    def get_all_with_metadata(cls) -> List[Dict[str, Any]]:
        """Retorna todos os status com seus metadados para API"""
        return [
            {
                "value": status.value,
                "label": status.label,
                "descricao": status.descricao,
                "cor": status.cor,
                "icone": status.icone,
                "is_final": status.is_final,
                "transicoes_validas": [t.value for t in status.transicoes_validas]
            }
            for status in cls
        ]

    @classmethod
    def get_fluxo_principal(cls) -> List["StatusPedido"]:
        """Retorna os status do fluxo principal na ordem"""
        return [
            cls.INSCRICAO,
            cls.ANALISE_DOCUMENTAL,
            cls.DOCUMENTACAO_PENDENTE,
            cls.APROVADO,
            cls.AGUARDANDO_PAGAMENTO,
            cls.MATRICULADO,
            cls.EXPORTADO
        ]
