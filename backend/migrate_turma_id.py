"""
Script de migração - Adiciona coluna turma_id
"""
import asyncio
from sqlalchemy import text
from src.infrastructure.persistence.database import engine

async def migrate():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE pedidos ADD COLUMN turma_id TEXT"))
            print("✅ Coluna turma_id adicionada!")
        except Exception as e:
            if "duplicate" in str(e).lower() or "already" in str(e).lower():
                print("✅ Coluna já existe")
            else:
                raise

if __name__ == "__main__":
    asyncio.run(migrate())
