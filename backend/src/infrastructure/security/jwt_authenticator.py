"""Serviço de Autenticação JWT"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import os

from src.domain.entities import Usuario, RoleUsuario
from src.domain.exceptions import AuthenticationException


class JWTAuthenticator:
    """Serviço de autenticação JWT"""

    def __init__(self):
        self.secret_key = os.environ.get("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 8  # 8 horas

    def hash_senha(self, senha: str) -> str:
        """Gera hash da senha usando bcrypt diretamente"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

    def verificar_senha(self, senha: str, hash_senha: str) -> bool:
        """Verifica se a senha corresponde ao hash"""
        try:
            return bcrypt.checkpw(senha.encode('utf-8'), hash_senha.encode('utf-8'))
        except Exception:
            return False

    def criar_token(self, usuario: Usuario) -> str:
        """Cria token JWT para o usuário"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": usuario.id,
            "email": usuario.email.valor,
            "nome": usuario.nome,
            "role": usuario.role.value,
            "permissoes": usuario.role.permissoes,
            "exp": expire
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verificar_token(self, token: str) -> dict:
        """Verifica e decodifica o token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise AuthenticationException(f"Token inválido: {str(e)}")

    def extrair_usuario_id(self, token: str) -> str:
        """Extrai o ID do usuário do token"""
        payload = self.verificar_token(token)
        return payload.get("sub")

    def extrair_role(self, token: str) -> RoleUsuario:
        """Extrai o role do usuário do token"""
        payload = self.verificar_token(token)
        return RoleUsuario.from_string(payload.get("role", "consultor"))
