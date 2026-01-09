"""Entidade - Aluno"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from ..value_objects import CPF, Email, Telefone
from ..exceptions.domain_exceptions import ValidationException


@dataclass
class Aluno:
    """Entidade Aluno com validações de invariantes"""
    id: str
    nome: str
    cpf: CPF
    email: Email
    telefone: Telefone
    data_nascimento: datetime
    rg: str
    rg_orgao_emissor: str
    rg_uf: str
    endereco_cep: str
    endereco_logradouro: str
    endereco_numero: str
    endereco_bairro: str
    endereco_cidade: str
    endereco_uf: str
    endereco_complemento: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        self._validar_invariantes()

    def _validar_invariantes(self):
        """Valida invariantes da entidade"""
        if not self.nome or len(self.nome.strip()) < 3:
            raise ValidationException("Nome deve ter pelo menos 3 caracteres", "nome")
        
        if not self.rg or len(self.rg.strip()) < 5:
            raise ValidationException("RG inválido", "rg")
        
        if not self.endereco_cep or len(self.endereco_cep) < 8:
            raise ValidationException("CEP inválido", "endereco_cep")

    def atualizar_dados(self, **kwargs):
        """Atualiza dados do aluno com validação"""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc)
        self._validar_invariantes()

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf.valor,
            "cpf_formatado": self.cpf.formatado(),
            "email": self.email.valor,
            "telefone": self.telefone.valor,
            "telefone_formatado": self.telefone.formatado(),
            "data_nascimento": self.data_nascimento.isoformat(),
            "rg": self.rg,
            "rg_orgao_emissor": self.rg_orgao_emissor,
            "rg_uf": self.rg_uf,
            "endereco_cep": self.endereco_cep,
            "endereco_logradouro": self.endereco_logradouro,
            "endereco_numero": self.endereco_numero,
            "endereco_complemento": self.endereco_complemento,
            "endereco_bairro": self.endereco_bairro,
            "endereco_cidade": self.endereco_cidade,
            "endereco_uf": self.endereco_uf,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Aluno":
        """Cria Aluno a partir de dicionário"""
        return cls(
            id=data.get("id"),
            nome=data.get("nome"),
            cpf=CPF(data.get("cpf")),
            email=Email(data.get("email")),
            telefone=Telefone(data.get("telefone")),
            data_nascimento=datetime.fromisoformat(data.get("data_nascimento")) if isinstance(data.get("data_nascimento"), str) else data.get("data_nascimento"),
            rg=data.get("rg"),
            rg_orgao_emissor=data.get("rg_orgao_emissor"),
            rg_uf=data.get("rg_uf"),
            endereco_cep=data.get("endereco_cep"),
            endereco_logradouro=data.get("endereco_logradouro"),
            endereco_numero=data.get("endereco_numero"),
            endereco_complemento=data.get("endereco_complemento"),
            endereco_bairro=data.get("endereco_bairro"),
            endereco_cidade=data.get("endereco_cidade"),
            endereco_uf=data.get("endereco_uf"),
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") and isinstance(data.get("created_at"), str) else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") and isinstance(data.get("updated_at"), str) else datetime.now(timezone.utc)
        )
