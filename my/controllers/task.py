from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from my.db import get_db
from my.models.api.task import Task, TaskCreate, TaskUpdate
from my.models.persistence import User
from my.services.auth import get_current_user
from my.services import task as task_service

router = APIRouter(prefix="/tasks", tags=["task"])


@router.get("", response_model=list[Task])
async def list_tasks(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await task_service.get_tasks(db, current_user.id)


@router.post("", response_model=Task)
async def create_task(
    task_body: TaskCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await task_service.create_task(db, task_body, current_user.id)


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_body: TaskUpdate,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authenticated for updating this task")
    task.title = task_body.title
    task.done = task_body.done
    return await task_service.update_task(db, task)


@router.delete("/{task_id}", response_model=None)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authenticated for deleting this task")
    await task_service.delete_task(db, task)
