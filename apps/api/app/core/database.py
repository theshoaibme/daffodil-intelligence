from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import exc
from contextlib import asynccontextmanager
from .config import get_settings

settings = get_settings()
Base = declarative_base()

_engine = None
_async_session = None

def get_engine():
    global _engine
    if _engine is None:
        try:
            async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            _engine = create_async_engine(
                async_url, 
                echo=False, 
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
        except Exception as e:
            print(f"Database engine error: {e}")
            _engine = None
    return _engine

def get_session_maker():
    global _async_session
    engine = get_engine()
    if engine and _async_session is None:
        _async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _async_session


async def get_db():
    session_maker = get_session_maker()
    if session_maker is None:
        raise Exception("Database not initialized")
    
    async with session_maker() as session:
        try:
            yield session
        except exc.SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    engine = get_engine()
    if engine:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            print(f"Table creation: {e}")


async def close_db():
    global _engine, _async_session
    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session = None