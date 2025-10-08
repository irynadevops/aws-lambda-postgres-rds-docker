from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.engine import Result

from my.models.api.task import TaskCreate
from my.models.persistence import Task, User


async def create_task(session: AsyncSession, task_create: TaskCreate, user_id: int) -> Task:
    task = Task(**task_create.dict(), owner_id=user_id)
    task.done = False
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, id: int) -> Task | None:
    query = select(Task).where(Task.id == id)
    result = await session.execute(query)
    return result.scalar()


async def get_tasks(session: AsyncSession, id_: int) -> list[Task]:
    stmt = select(Task).where(User.id == id_)
    result: Result = await session.execute(stmt)
    return result.scalars().all()


async def update_task(session: AsyncSession, task: Task) -> Task:
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
    await session.commit()
