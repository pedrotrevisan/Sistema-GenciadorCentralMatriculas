"""Domain Exceptions - Hierarquia de exceções de domínio"""

class DomainException(Exception):
    """Base exception para todas as exceções de domínio"""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationException(DomainException):
    """Exceção para erros de validação"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class CPFInvalidoException(ValidationException):
    """Exceção para CPF inválido"""
    def __init__(self, cpf: str):
        super().__init__(f"CPF inválido: {cpf}", "cpf")


class EmailInvalidoException(ValidationException):
    """Exceção para Email inválido"""
    def __init__(self, email: str):
        super().__init__(f"Email inválido: {email}", "email")


class TelefoneInvalidoException(ValidationException):
    """Exceção para Telefone inválido"""
    def __init__(self, telefone: str):
        super().__init__(f"Telefone inválido: {telefone}", "telefone")


class BusinessRuleException(DomainException):
    """Exceção para regras de negócio violadas"""
    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_RULE_ERROR")


class TransicaoStatusInvalidaException(BusinessRuleException):
    """Exceção para transição de status inválida"""
    def __init__(self, status_atual: str, status_destino: str):
        super().__init__(
            f"Transição de '{status_atual}' para '{status_destino}' não é permitida"
        )


class PedidoNaoEditavelException(BusinessRuleException):
    """Exceção quando pedido não pode ser editado"""
    def __init__(self, pedido_id: str, status: str):
        super().__init__(
            f"Pedido {pedido_id} não pode ser editado. Status atual: {status}"
        )


class PedidoSemAlunoException(BusinessRuleException):
    """Exceção quando pedido não tem alunos"""
    def __init__(self):
        super().__init__("Um pedido deve ter pelo menos 1 aluno")


class NotFoundException(DomainException):
    """Exceção para recursos não encontrados"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} não encontrado: {identifier}", "NOT_FOUND")


class PedidoNaoEncontradoException(NotFoundException):
    """Exceção para pedido não encontrado"""
    def __init__(self, pedido_id: str):
        super().__init__("Pedido", pedido_id)


class UsuarioNaoEncontradoException(NotFoundException):
    """Exceção para usuário não encontrado"""
    def __init__(self, identifier: str):
        super().__init__("Usuário", identifier)


class DuplicidadeException(BusinessRuleException):
    """Exceção para duplicidade de registros"""
    def __init__(self, message: str):
        super().__init__(message)


class AuthenticationException(DomainException):
    """Exceção para erros de autenticação"""
    def __init__(self, message: str = "Credenciais inválidas"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationException(DomainException):
    """Exceção para erros de autorização"""
    def __init__(self, message: str = "Acesso não autorizado"):
        super().__init__(message, "AUTHORIZATION_ERROR")
