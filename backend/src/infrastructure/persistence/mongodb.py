"""MongoDB Database Configuration"""
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


async def init_db():
    """Initialize MongoDB - create indexes"""
    # Usuarios
    await db.usuarios.create_index("email", unique=True)
    # Pedidos
    await db.pedidos.create_index("numero_protocolo", unique=True, sparse=True)
    await db.pedidos.create_index("consultor_id")
    await db.pedidos.create_index("status")
    await db.pedidos.create_index("created_at")
    await db.pedidos.create_index("responsavel_id")
    # Alunos
    await db.alunos.create_index("pedido_id")
    await db.alunos.create_index("cpf")
    # Auditoria
    await db.auditoria.create_index("pedido_id")
    await db.auditoria.create_index("usuario_id")
    await db.auditoria.create_index("timestamp")
    # Cursos
    await db.cursos.create_index("nome", unique=True)
    await db.cursos.create_index("tipo")
    # Projetos & Empresas
    await db.projetos.create_index("nome", unique=True)
    await db.empresas.create_index("nome", unique=True)
    # Reembolsos
    await db.reembolsos.create_index("status")
    await db.reembolsos.create_index("created_at")
    # Pendencias
    await db.pendencias.create_index("pedido_id")
    await db.pendencias.create_index("aluno_id")
    await db.pendencias.create_index("status")
    # Chamados SGC
    await db.chamados_sgc.create_index("numero_ticket", unique=True)
    await db.chamados_sgc.create_index("status")
    # Painel Turmas
    await db.painel_turmas.create_index("periodo_letivo")
    await db.painel_turmas.create_index("codigo_turma")
    # Tarefas
    await db.tarefas_diarias.create_index("usuario_id")
    # Atividades
    await db.atividades_usuario.create_index("usuario_id")
    await db.atividades_usuario.create_index("created_at")
    # Tipos Documento
    await db.tipos_documento.create_index("codigo", unique=True)


async def get_db():
    """Dependency injection - returns database instance"""
    return db
