"""
FastAPI Backend - Sistema SYNAPSE - SENAI CIMATEC
Refatorado para Clean Architecture com routers modulares

NOTA: Este arquivo foi refatorado de 1685 linhas para ~350 linhas.
Todas as rotas foram movidas para arquivos específicos em src/routers/
"""
from fastapi import FastAPI, APIRouter, Response
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
from contextlib import asynccontextmanager
import os
import logging
import uuid
from datetime import datetime, timezone

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Domain imports
from src.domain.exceptions import (
    ValidationException, BusinessRuleException,
    NotFoundException, AuthorizationException,
    DuplicidadeException
)

# Infrastructure imports
from src.infrastructure.persistence.mongodb import db, init_db
from src.infrastructure.security import JWTAuthenticator

# Application imports
from src.application.dtos.response import ErrorResponseDTO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# JWT Authenticator
jwt_auth = JWTAuthenticator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown - MongoDB version"""
    logger.info("Initializing MongoDB...")
    await init_db()

    # Seed default users if collection is empty
    SENHA_PADRAO = "Senai@2026"
    usuarios_oficiais = [
        {"nome": "Pedro Henrique Trevisan Passos Costa", "email": "pedro.passos@fieb.org.br", "role": "admin"},
        {"nome": "Cristiane dos Santos Mendes", "email": "cristiane.mendes@fieb.org.br", "role": "admin"},
        {"nome": "Camila de Deus Mota Reis", "email": "camila.mreis@fieb.org.br", "role": "assistente"},
        {"nome": "Vanessa da Silva Santos", "email": "vanessa.silvasantos@fieb.org.br", "role": "assistente"},
        {"nome": "Saulo Serra Santos", "email": "saulo.serra@fbest.org.br", "role": "assistente"},
        {"nome": "Vitoria Vanessa dos Santos Oliveira", "email": "vitoria.soliveira@fbest.org.br", "role": "assistente"},
        {"nome": "José Hericles Santos de Almeida", "email": "jose.hericles@fieb.org.br", "role": "assistente"},
        {"nome": "Consultor Exemplo", "email": "consultorexemplocimatec@fieb.org.br", "role": "consultor"},
    ]

    for user_data in usuarios_oficiais:
        existing = await db.usuarios.find_one({"email": user_data["email"]})
        if not existing:
            now = datetime.now(timezone.utc).isoformat()
            await db.usuarios.insert_one({
                "id": str(uuid.uuid4()),
                "nome": user_data["nome"],
                "email": user_data["email"],
                "senha_hash": jwt_auth.hash_senha(SENHA_PADRAO),
                "role": user_data["role"],
                "ativo": True,
                "primeiro_acesso": True,
                "created_at": now,
                "updated_at": now,
                "ultimo_acesso": None
            })
            logger.info(f"Usuário criado: {user_data['nome']} ({user_data['email']})")

    # Seed tipos_documento if empty
    tipos_count = await db.tipos_documento.count_documents({})
    if tipos_count == 0:
        tipos_documentos = [
            {"codigo": "94", "nome": "Comprovante de Residência", "obrigatorio": True, "observacoes": "PDF ou JPG – Máx. 10MB"},
            {"codigo": "96", "nome": "Solicitação Desconto (Sindicato/CIEB/Ex-Aluno/Col. Sistema FIEB)", "obrigatorio": False, "observacoes": "Se aplicável"},
            {"codigo": "97", "nome": "CPF/RG Responsável Legal (menor de 18 anos)", "obrigatorio": False, "observacoes": "Se aplicável"},
            {"codigo": "131", "nome": "RG – Frente", "obrigatorio": True, "observacoes": "PDF ou JPG – Máx. 10MB"},
            {"codigo": "132", "nome": "RG – Verso", "obrigatorio": True, "observacoes": "PDF ou JPG – Máx. 10MB"},
            {"codigo": "136", "nome": "Comprovante de Escolaridade – Frente", "obrigatorio": True, "observacoes": "Histórico ou Atestado - PDF ou JPG – Máx. 10MB"},
            {"codigo": "137", "nome": "Comprovante de Escolaridade – Verso", "obrigatorio": True, "observacoes": "Histórico ou Atestado - PDF ou JPG – Máx. 10MB"},
            {"codigo": "205", "nome": "CPF", "obrigatorio": False, "observacoes": "PDF ou JPG – Máx. 10MB"},
        ]
        for tipo in tipos_documentos:
            tipo["id"] = str(uuid.uuid4())
        await db.tipos_documento.insert_many(tipos_documentos)
        logger.info(f"{len(tipos_documentos)} tipos de documento criados")

    logger.info("MongoDB initialized successfully!")

    yield

    logger.info("Shutdown complete.")


# Create the main app
app = FastAPI(
    title="SYNAPSE - Hub de Inteligência Operacional",
    description="API do Sistema Central de Matrículas - SENAI CIMATEC",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins == '*':
    origins = ["*"]
else:
    origins = [origin.strip() for origin in cors_origins.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router
api_router = APIRouter(prefix="/api")


# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(ValidationException)
async def validation_exception_handler(request, exc: ValidationException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code=exc.code,
            field=exc.field
        ).model_dump_json(),
        status_code=400,
        media_type="application/json"
    )


@app.exception_handler(BusinessRuleException)
async def business_rule_exception_handler(request, exc: BusinessRuleException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code=exc.code
        ).model_dump_json(),
        status_code=422,
        media_type="application/json"
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request, exc: NotFoundException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code=exc.code
        ).model_dump_json(),
        status_code=404,
        media_type="application/json"
    )


@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(request, exc: AuthorizationException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code=exc.code
        ).model_dump_json(),
        status_code=403,
        media_type="application/json"
    )


@app.exception_handler(DuplicidadeException)
async def duplicidade_exception_handler(request, exc: DuplicidadeException):
    return Response(
        content=ErrorResponseDTO(
            error=exc.message,
            code="DUPLICIDADE"
        ).model_dump_json(),
        status_code=409,
        media_type="application/json"
    )


# ==================== HEALTH CHECK ====================

@api_router.get("/", tags=["Health"])
async def root():
    return {"message": "SYNAPSE - Hub de Inteligência Operacional", "version": "2.0.0"}


@api_router.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# ==================== INCLUDE MODULAR ROUTERS ====================

# Core routers (refatorados)
from src.routers.auth_routes import router as auth_router
from src.routers.pedidos_routes import router as pedidos_router
from src.routers.usuarios_routes import router as usuarios_router
from src.routers.auxiliares import router as auxiliares_router

# Feature routers
from src.routers.reembolsos import router as reembolsos_router
from src.routers.pendencias import router as pendencias_router
from src.routers.turmas import router as turmas_router
from src.routers.ocr import router as ocr_router
from src.routers.status_matricula import router as status_router
from src.routers.documentos import router as documentos_router
from src.routers.contatos import router as contatos_router
from src.routers.cadastros import router as cadastros_router
from src.routers.apoio_cognitivo import router as apoio_router
from src.routers.atribuicoes import router as atribuicoes_router
from src.routers.regras_negocio import router as regras_router
from src.routers.sla_dashboard import router as sla_router
from src.routers.cancelamento import router as cancelamento_router
from src.routers.formatador import router as formatador_router
from src.routers.importacao_matriculas import router as importacao_router
from src.routers.chamados_sgc import router as chamados_sgc_router
from src.routers.painel_vagas import router as painel_vagas_router
from src.routers.alertas import router as alertas_router
from src.routers.produtividade import router as produtividade_router

# Include core routers
api_router.include_router(auth_router)
api_router.include_router(pedidos_router)
api_router.include_router(usuarios_router)
api_router.include_router(auxiliares_router)

# Include feature routers
api_router.include_router(reembolsos_router)
api_router.include_router(pendencias_router)
api_router.include_router(turmas_router)
api_router.include_router(ocr_router)
api_router.include_router(status_router)
api_router.include_router(documentos_router)
api_router.include_router(contatos_router)
api_router.include_router(cadastros_router)
api_router.include_router(apoio_router)
api_router.include_router(atribuicoes_router)
api_router.include_router(regras_router)
api_router.include_router(sla_router)
api_router.include_router(cancelamento_router)
api_router.include_router(formatador_router)
api_router.include_router(importacao_router)
api_router.include_router(chamados_sgc_router)
api_router.include_router(painel_vagas_router)
api_router.include_router(alertas_router)
api_router.include_router(produtividade_router)

# Mount API router
app.include_router(api_router)
