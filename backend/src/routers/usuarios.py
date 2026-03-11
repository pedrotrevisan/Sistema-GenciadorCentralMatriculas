"""Router - Gestão de Usuários (antigo, compatibilidade) - MongoDB version"""
from fastapi import APIRouter

router = APIRouter(prefix="/usuarios-legacy", tags=["Usuarios Legacy"])
# All usuario endpoints are now in usuarios_routes.py
# This file is kept for import compatibility
