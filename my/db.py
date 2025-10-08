import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DB_NAME = os.environ.get("DB_NAME", "my_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", 5432)
DB_PASSWORD = os.environ["DB_PASSWORD"]

DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DB_URL, future=True)

AsyncDBSession = sessionmaker(autoflush=True, bind=engine, class_=AsyncSession, future=True)


async def get_db():
    async with AsyncDBSession() as session:
        yield session
