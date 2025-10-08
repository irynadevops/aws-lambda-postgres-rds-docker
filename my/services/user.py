from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from my.models.api.user import UserCreate
from my.models.persistence import User


async def create_user(session: AsyncSession, user_input: UserCreate) -> User:
    user = User(**user_input.dict())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_sub(session: AsyncSession, sub: UUID) -> User:
    query = select(User).where(User.sub == str(sub))
    result = await session.execute(query)
    return result.scalar()


async def get_user_by_email(session: AsyncSession, email: str) -> User:
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    return result.scalar()
