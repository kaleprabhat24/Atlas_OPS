"""
Async SQLAlchemy engine + session factory for ATLAS-OPS.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_all_tables() -> None:
    """Create all SQLModel tables on startup."""
    # Import all models to register their metadata
    import app.models.transaction  # noqa: F401
    import app.models.gateway  # noqa: F401
    import app.models.ml_result  # noqa: F401

    from sqlalchemy.exc import SQLAlchemyError
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    except SQLAlchemyError as exc:
        print(f"Database connection failed. Ensure PostgreSQL is running. Error: {exc}")
        import sys
        sys.exit(1)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
