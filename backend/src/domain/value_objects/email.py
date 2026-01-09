"""Value Object - Email"""
import re
from dataclasses import dataclass
from ..exceptions.domain_exceptions import EmailInvalidoException


@dataclass(frozen=True)
class Email:
    """Value Object para Email com validação"""
    valor: str

    def __post_init__(self):
        email_normalizado = self.valor.strip().lower()
        if not self._validar(email_normalizado):
            raise EmailInvalidoException(self.valor)
        object.__setattr__(self, 'valor', email_normalizado)

    @staticmethod
    def _validar(email: str) -> bool:
        """Valida formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def __str__(self) -> str:
        return self.valor

    def __eq__(self, other):
        if isinstance(other, Email):
            return self.valor == other.valor
        return False

    def __hash__(self):
        return hash(self.valor)
