"""Value Object - Telefone"""
import re
from dataclasses import dataclass
from ..exceptions.domain_exceptions import TelefoneInvalidoException


@dataclass(frozen=True)
class Telefone:
    """Value Object para Telefone com validação"""
    valor: str

    def __post_init__(self):
        telefone_limpo = self._limpar(self.valor)
        if not self._validar(telefone_limpo):
            raise TelefoneInvalidoException(self.valor)
        object.__setattr__(self, 'valor', telefone_limpo)

    @staticmethod
    def _limpar(telefone: str) -> str:
        """Remove caracteres não numéricos"""
        return re.sub(r'\D', '', telefone)

    @staticmethod
    def _validar(telefone: str) -> bool:
        """Valida telefone brasileiro (10 ou 11 dígitos)"""
        return len(telefone) in [10, 11]

    def formatado(self) -> str:
        """Retorna telefone formatado"""
        if len(self.valor) == 11:
            return f"({self.valor[:2]}) {self.valor[2:7]}-{self.valor[7:]}"
        return f"({self.valor[:2]}) {self.valor[2:6]}-{self.valor[6:]}"

    def __str__(self) -> str:
        return self.formatado()

    def __eq__(self, other):
        if isinstance(other, Telefone):
            return self.valor == other.valor
        return False

    def __hash__(self):
        return hash(self.valor)
