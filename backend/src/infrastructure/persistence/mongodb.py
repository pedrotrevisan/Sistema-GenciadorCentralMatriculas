"""MongoDB Database Configuration"""
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


async def init_db():
    """Initialize MongoDB - create indexes (idempotent)"""
    index_tasks = [
        (db.usuarios, "email", {"unique": True}),
        (db.pedidos, "numero_protocolo", {"unique": True, "sparse": True}),
        (db.pedidos, "consultor_id", {}),
        (db.pedidos, "status", {}),
        (db.pedidos, "created_at", {}),
        (db.pedidos, "responsavel_id", {}),
        (db.alunos, "pedido_id", {}),
        (db.alunos, "cpf", {}),
        (db.auditoria, "pedido_id", {}),
        (db.auditoria, "usuario_id", {}),
        (db.auditoria, "timestamp", {}),
        (db.cursos, "nome", {"unique": True}),
        (db.cursos, "tipo", {}),
        (db.projetos, "nome", {"unique": True}),
        (db.empresas, "nome", {"unique": True}),
        (db.reembolsos, "status", {}),
        (db.reembolsos, "created_at", {}),
        (db.pendencias, "pedido_id", {}),
        (db.pendencias, "aluno_id", {}),
        (db.pendencias, "status", {}),
        (db.chamados_sgc, "numero_ticket", {"unique": True, "sparse": True}),
        (db.chamados_sgc, "status", {}),
        (db.painel_turmas, "periodo_letivo", {}),
        (db.painel_turmas, "codigo_turma", {}),
        (db.tarefas_diarias, "usuario_id", {}),
        (db.atividades_usuario, "usuario_id", {}),
        (db.atividades_usuario, "created_at", {}),
        (db.tipos_documento, "codigo", {"unique": True}),
    ]
    for collection, field, kwargs in index_tasks:
        try:
            await collection.create_index(field, **kwargs)
        except Exception:
            pass  # Index already exists with compatible or conflicting spec


async def get_db():
    """Dependency injection - returns database instance"""
    return db
