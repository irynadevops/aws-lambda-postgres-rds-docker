import logging

from fastapi import FastAPI
from my.controllers import user
from my.controllers import task
from my.db import engine
from my.models.persistence import Base

logging.basicConfig()

app = FastAPI()
app.include_router(user.router)
app.include_router(task.router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
