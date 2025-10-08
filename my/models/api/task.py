from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(..., example="Do the dishes")


class Task(TaskBase):
    id: int
    done: bool = Field(False, description="Has the task been completed?")

    class Config:
        orm_mode = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    done: bool = Field(False, description="Has the task been completed?")
