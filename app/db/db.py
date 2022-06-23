import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

default_db_name = "postgresql+asyncpg://postgres:654zz321xx@localhost:5432/test_app"
DATABASE_URL = os.getenv('DATABASE_URL', default_db_name)


engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
