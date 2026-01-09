"""Entidade - Usuario"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from ..value_objects import Email
from ..exceptions.domain_exceptions import ValidationException


class RoleUsuario(Enum):
    """Roles do sistema com permissões"""
    CONSULTOR = "consultor"
    ASSISTENTE = "assistente"
    ADMIN = "admin"

    @property
    def permissoes(self) -> list:
        """Retorna permissões do role"""
        permissoes_base = {
            RoleUsuario.CONSULTOR: [
                "pedido:criar",
                "pedido:visualizar_proprio",
                "pedido:editar_proprio"
            ],
            RoleUsuario.ASSISTENTE: [
                "pedido:criar",
                "pedido:visualizar_proprio",
                "pedido:visualizar_todos",
                "pedido:editar_proprio",
                "pedido:editar_status",
                "pedido:exportar"
            ],
            RoleUsuario.ADMIN: [
                "pedido:criar",
                "pedido:visualizar_proprio",
                "pedido:visualizar_todos",
                "pedido:editar_proprio",
                "pedido:editar_status",
                "pedido:exportar",
                "usuario:gerenciar"
            ]
        }
        return permissoes_base.get(self, [])

    def tem_permissao(self, permissao: str) -> bool:
        """Verifica se o role tem determinada permissão"""
        return permissao in self.permissoes

    @classmethod
    def from_string(cls, value: str) -> "RoleUsuario":
        """Cria RoleUsuario a partir de string"""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Role inválido: {value}")


@dataclass
class Usuario:
    """Entidade Usuario com validações"""
    id: str
    nome: str
    email: Email
    senha_hash: str
    role: RoleUsuario
    ativo: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ultimo_acesso: Optional[datetime] = None

    def __post_init__(self):
        self._validar_invariantes()

    def _validar_invariantes(self):
        """Valida invariantes da entidade"""
        if not self.nome or len(self.nome.strip()) < 3:
            raise ValidationException("Nome deve ter pelo menos 3 caracteres", "nome")

    def tem_permissao(self, permissao: str) -> bool:
        """Verifica se o usuário tem determinada permissão"""
        return self.ativo and self.role.tem_permissao(permissao)

    def pode_visualizar_pedido(self, pedido_consultor_id: str) -> bool:
        """Verifica se pode visualizar um pedido"""
        if self.tem_permissao("pedido:visualizar_todos"):
            return True
        return self.id == pedido_consultor_id and self.tem_permissao("pedido:visualizar_proprio")

    def pode_editar_pedido(self, pedido_consultor_id: str) -> bool:
        """Verifica se pode editar um pedido"""
        if self.tem_permissao("pedido:editar_status"):
            return True
        return self.id == pedido_consultor_id and self.tem_permissao("pedido:editar_proprio")

    def registrar_acesso(self) -> None:
        """Registra último acesso"""
        self.ultimo_acesso = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def atualizar_dados(self, nome: str = None, ativo: bool = None) -> None:
        """Atualiza dados do usuário"""
        if nome:
            self.nome = nome
        if ativo is not None:
            self.ativo = ativo
        self.updated_at = datetime.now(timezone.utc)
        self._validar_invariantes()

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Converte para dicionário"""
        data = {
            "id": self.id,
            "nome": self.nome,
            "email": self.email.valor,
            "role": self.role.value,
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "ultimo_acesso": self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
            "permissoes": self.role.permissoes
        }
        if include_sensitive:
            data["senha_hash"] = self.senha_hash
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Usuario":
        """Cria Usuario a partir de dicionário"""
        return cls(
            id=data.get("id"),
            nome=data.get("nome"),
            email=Email(data.get("email")),
            senha_hash=data.get("senha_hash", ""),
            role=RoleUsuario.from_string(data.get("role", "consultor")),
            ativo=data.get("ativo", True),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(timezone.utc),
            ultimo_acesso=datetime.fromisoformat(data["ultimo_acesso"]) if data.get("ultimo_acesso") else None
        )
