from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# asyncpg driver required for async SQLAlchemy
DATABASE_URL = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace("postgresql+asyncpg+asyncpg://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    # Import models so their tables register on Base.metadata
    import app.models.user  # noqa: F401
    import app.models.media_list  # noqa: F401
    import app.models.media_history  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
