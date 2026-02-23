"""Database Configuration - PostgreSQL (production) / SQLite (development)"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Database URL from environment
# For PostgreSQL (production/local): postgresql+asyncpg://user:pass@host:port/db
# For SQLite (development): sqlite+aiosqlite:///./data/database.db
DATABASE_URL = os.environ.get("DATABASE_URL")

# Determine engine configuration based on database type
if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True
    )
else:
    # SQLite fallback for development/preview
    import pathlib
    data_dir = pathlib.Path(__file__).parent.parent.parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    sqlite_url = f"sqlite+aiosqlite:///{data_dir}/database.db"
    engine = create_async_engine(
        sqlite_url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}
    )

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


async def init_db():
    """Initialize database - create all tables"""
    # Import all models to ensure they are registered with Base.metadata
    from src.infrastructure.persistence.models import (
        UsuarioModel, PedidoModel, AlunoModel, AuditoriaModel,
        CursoModel, ProjetoModel, EmpresaModel, TipoDocumentoModel,
        PendenciaModel, HistoricoContatoModel, ReembolsoModel
    )
    # Import turmas models
    from src.infrastructure.persistence.models_turmas import (
        CursoTurmaModel,
        TurmaModel,
        ReservaVagaModel
    )
    # Import transicoes models
    from src.infrastructure.persistence.models_transicoes import (
        TransicaoStatusModel
    )
    # Import documentos models (Fase 2 - Clean Architecture)
    from src.infrastructure.persistence.models_documentos import (
        PendenciaDocumentalModel
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session() as session:
        yield session
