"""Value Object - Status do Pedido"""
from enum import Enum
from typing import List
from ..exceptions.domain_exceptions import TransicaoStatusInvalidaException


class StatusPedido(Enum):
    """Enum com lógica de transições válidas"""
    PENDENTE = "pendente"
    EM_ANALISE = "em_analise"
    DOCUMENTACAO_PENDENTE = "documentacao_pendente"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"
    REALIZADO = "realizado"
    CANCELADO = "cancelado"
    EXPORTADO = "exportado"

    @property
    def transicoes_validas(self) -> List["StatusPedido"]:
        """Define as transições válidas para cada status"""
        transicoes = {
            StatusPedido.PENDENTE: [
                StatusPedido.EM_ANALISE,
                StatusPedido.CANCELADO
            ],
            StatusPedido.EM_ANALISE: [
                StatusPedido.DOCUMENTACAO_PENDENTE,
                StatusPedido.APROVADO,
                StatusPedido.REJEITADO,
                StatusPedido.CANCELADO
            ],
            StatusPedido.DOCUMENTACAO_PENDENTE: [
                StatusPedido.EM_ANALISE,
                StatusPedido.CANCELADO
            ],
            StatusPedido.APROVADO: [
                StatusPedido.REALIZADO,
                StatusPedido.CANCELADO
            ],
            StatusPedido.REJEITADO: [],
            StatusPedido.REALIZADO: [
                StatusPedido.EXPORTADO
            ],
            StatusPedido.CANCELADO: [],
            StatusPedido.EXPORTADO: []
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
