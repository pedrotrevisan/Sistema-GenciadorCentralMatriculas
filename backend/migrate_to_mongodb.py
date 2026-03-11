"""Migrate data from SQLite to MongoDB"""
import sqlite3
import asyncio
import os
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

SQLITE_PATH = "/app/data/database.db"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "synapse")


def get_sqlite_rows(cursor, table):
    """Get all rows from a SQLite table as list of dicts"""
    cursor.execute(f"SELECT * FROM [{table}]")
    columns = [desc[0] for desc in cursor.description]
    rows = []
    for row in cursor.fetchall():
        doc = {}
        for i, col in enumerate(columns):
            val = row[i]
            # Convert JSON strings to dicts
            if isinstance(val, str) and col in ('detalhes', 'metadados') and val.startswith('{'):
                try:
                    val = json.loads(val)
                except:
                    pass
            doc[col] = val
        rows.append(doc)
    return rows


async def migrate():
    """Migrate all SQLite tables to MongoDB"""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cursor.fetchall()]
    
    print(f"Found {len(tables)} tables to migrate")
    
    for table in tables:
        rows = get_sqlite_rows(cursor, table)
        if not rows:
            print(f"  {table}: 0 rows (skipped)")
            continue
        
        # Drop existing collection
        await db[table].drop()
        
        # Insert all rows
        await db[table].insert_many(rows)
        print(f"  {table}: {len(rows)} rows migrated")
    
    conn.close()
    
    # Create indexes
    from src.infrastructure.persistence.mongodb import init_db as create_indexes
    # Can't use the module's init_db because it uses the module-level db
    # So create indexes manually
    await db.usuarios.create_index("email", unique=True)
    await db.pedidos.create_index("numero_protocolo", unique=True, sparse=True)
    await db.pedidos.create_index("consultor_id")
    await db.pedidos.create_index("status")
    await db.pedidos.create_index("created_at")
    await db.cursos.create_index("nome", unique=True)
    await db.projetos.create_index("nome", unique=True)
    await db.empresas.create_index("nome", unique=True)
    await db.reembolsos.create_index("status")
    await db.chamados_sgc.create_index("numero_ticket", unique=True, sparse=True)
    await db.painel_turmas.create_index("periodo_letivo")
    await db.auditoria.create_index("pedido_id")
    await db.atividades_usuario.create_index("usuario_id")
    await db.tipos_documento.create_index("codigo", unique=True)
    
    print("\nMigration complete! Indexes created.")
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
