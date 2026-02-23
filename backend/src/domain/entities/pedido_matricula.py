"""Entidade Rica - Pedido de Matrícula"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from ..value_objects import StatusPedido
from ..exceptions.domain_exceptions import (
    PedidoSemAlunoException,
    PedidoNaoEditavelException,
    BusinessRuleException
)
from .aluno import Aluno


@dataclass
class PedidoMatricula:
    """
    Entidade Rica que gerencia seu próprio estado e garante invariantes.
    Invariantes:
    - Um pedido deve ter pelo menos 1 aluno
    - Um pedido deve estar vinculado a Projeto, Empresa ou Brasil Mais Produtivo
    - Transições de status devem seguir o fluxo definido
    - Pedidos exportados não podem ser editados
    """
    id: str
    consultor_id: str
    consultor_nome: str
    curso_id: str
    curso_nome: str
    turma_id: Optional[str] = None  # NOVO - ID da turma (para gestão de vagas)
    numero_protocolo: Optional[str] = None  # CM-2026-0001
    projeto_id: Optional[str] = None
    projeto_nome: Optional[str] = None
    empresa_id: Optional[str] = None
    empresa_nome: Optional[str] = None
    vinculo_tipo: Optional[str] = None  # projeto, empresa, brasil_mais_produtivo
    alunos: List[Aluno] = field(default_factory=list)
    status: StatusPedido = StatusPedido.PENDENTE
    observacoes: Optional[str] = None
    motivo_rejeicao: Optional[str] = None
    data_exportacao: Optional[datetime] = None
    exportado_por: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        self._validar_vinculo()

    def _validar_vinculo(self):
        """Valida que pedido tem vínculo válido"""
        if not self.projeto_id and not self.empresa_id:
            raise BusinessRuleException(
                "Um pedido deve estar vinculado a um Projeto, Empresa ou Brasil Mais Produtivo"
            )

    def adicionar_aluno(self, aluno: Aluno) -> None:
        """Adiciona aluno ao pedido validando estado"""
        if not self.pode_ser_editado():
            raise PedidoNaoEditavelException(self.id, self.status.value)
        
        # Verifica duplicidade de CPF
        for a in self.alunos:
            if a.cpf.valor == aluno.cpf.valor:
                raise BusinessRuleException(
                    f"Aluno com CPF {aluno.cpf.formatado()} já existe no pedido"
                )
        
        self.alunos.append(aluno)
        self.updated_at = datetime.now(timezone.utc)

    def remover_aluno(self, aluno_id: str) -> None:
        """Remove aluno do pedido validando estado"""
        if not self.pode_ser_editado():
            raise PedidoNaoEditavelException(self.id, self.status.value)
        
        aluno_encontrado = None
        for a in self.alunos:
            if a.id == aluno_id:
                aluno_encontrado = a
                break
        
        if not aluno_encontrado:
            raise BusinessRuleException(f"Aluno {aluno_id} não encontrado no pedido")
        
        self.alunos.remove(aluno_encontrado)
        self.updated_at = datetime.now(timezone.utc)

    def transitar_para(self, novo_status: StatusPedido, usuario_id: str, motivo: str = None) -> None:
        """Realiza transição de status com validação"""
        status_anterior = self.status
        self.status = status_anterior.transitar_para(novo_status)
        
        if novo_status == StatusPedido.REJEITADO and motivo:
            self.motivo_rejeicao = motivo
        
        self.updated_at = datetime.now(timezone.utc)

    def marcar_como_exportado(self, usuario_id: str) -> None:
        """Marca pedido como exportado"""
        if not self.pode_ser_exportado():
            raise BusinessRuleException(
                f"Pedido não pode ser exportado. Status atual: {self.status.value}"
            )
        
        self.status = StatusPedido.EXPORTADO
        self.data_exportacao = datetime.now(timezone.utc)
        self.exportado_por = usuario_id
        self.updated_at = datetime.now(timezone.utc)

    def pode_ser_editado(self) -> bool:
        """Verifica se o pedido pode ser editado"""
        return self.status.permite_edicao

    def pode_ser_exportado(self) -> bool:
        """Verifica se o pedido pode ser exportado"""
        return self.status.permite_exportacao

    def validar_para_envio(self) -> None:
        """Valida se o pedido está pronto para envio"""
        if not self.alunos:
            raise PedidoSemAlunoException()

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "numero_protocolo": self.numero_protocolo,
            "consultor_id": self.consultor_id,
            "consultor_nome": self.consultor_nome,
            "curso_id": self.curso_id,
            "curso_nome": self.curso_nome,
            "projeto_id": self.projeto_id,
            "projeto_nome": self.projeto_nome,
            "empresa_id": self.empresa_id,
            "empresa_nome": self.empresa_nome,
            "alunos": [a.to_dict() for a in self.alunos],
            "status": self.status.value,
            "status_label": self.status.label,
            "observacoes": self.observacoes,
            "motivo_rejeicao": self.motivo_rejeicao,
            "data_exportacao": self.data_exportacao.isoformat() if self.data_exportacao else None,
            "exportado_por": self.exportado_por,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "pode_editar": self.pode_ser_editado(),
            "pode_exportar": self.pode_ser_exportado(),
            "total_alunos": len(self.alunos)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PedidoMatricula":
        """Cria PedidoMatricula a partir de dicionário"""
        alunos = []
        for aluno_data in data.get("alunos", []):
            alunos.append(Aluno.from_dict(aluno_data))
        
        return cls(
            id=data.get("id"),
            numero_protocolo=data.get("numero_protocolo"),
            consultor_id=data.get("consultor_id"),
            consultor_nome=data.get("consultor_nome"),
            curso_id=data.get("curso_id"),
            curso_nome=data.get("curso_nome"),
            projeto_id=data.get("projeto_id"),
            projeto_nome=data.get("projeto_nome"),
            empresa_id=data.get("empresa_id"),
            empresa_nome=data.get("empresa_nome"),
            alunos=alunos,
            status=StatusPedido.from_string(data.get("status", "pendente")),
            observacoes=data.get("observacoes"),
            motivo_rejeicao=data.get("motivo_rejeicao"),
            data_exportacao=datetime.fromisoformat(data["data_exportacao"]) if data.get("data_exportacao") else None,
            exportado_por=data.get("exportado_por"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(timezone.utc)
        )
