"""Value Object - CPF"""
import re
from dataclasses import dataclass
from ..exceptions.domain_exceptions import CPFInvalidoException


@dataclass(frozen=True)
class CPF:
    """Value Object para CPF com validação completa"""
    valor: str
    validar_digitos: bool = True  # Se False, apenas valida formato (11 dígitos)

    def __post_init__(self):
        cpf_limpo = self._limpar(self.valor)
        
        # Validação básica de formato (11 dígitos)
        if len(cpf_limpo) != 11:
            raise CPFInvalidoException(self.valor)
        
        # Validação estrita com dígitos verificadores (opcional)
        if self.validar_digitos and not self._validar_digitos(cpf_limpo):
            raise CPFInvalidoException(self.valor)
            
        object.__setattr__(self, 'valor', cpf_limpo)

    @staticmethod
    def _limpar(cpf: str) -> str:
        """Remove caracteres não numéricos"""
        return re.sub(r'\D', '', cpf)

    @staticmethod
    def _validar_digitos(cpf: str) -> bool:
        """Valida CPF usando algoritmo de dígitos verificadores"""
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        digito1 = resto if resto < 10 else 0
        
        if digito1 != int(cpf[9]):
            return False
        
        # Calcula segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        digito2 = resto if resto < 10 else 0
        
        return digito2 == int(cpf[10])

    def formatado(self) -> str:
        """Retorna CPF formatado (XXX.XXX.XXX-XX)"""
        return f"{self.valor[:3]}.{self.valor[3:6]}.{self.valor[6:9]}-{self.valor[9:]}"

    def __str__(self) -> str:
        return self.formatado()

    def __eq__(self, other):
        if isinstance(other, CPF):
            return self.valor == other.valor
        return False

    def __hash__(self):
        return hash(self.valor)
