from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from my.db import get_db
from my.models.api.user import Token, UserCreate, User
from my.services.auth import get_hashed_password, authenticate_user, create_access_token, get_current_user
from my.models.persistence import User as DBUser

from my.services.user import create_user

router = APIRouter(prefix="", tags=["user"])


@router.post("/users", response_model=User)
async def register_user(user_input: UserCreate, session: AsyncSession = Depends(get_db)):
    user_input.password = get_hashed_password(user_input.password)
    user = await create_user(session, user_input)
    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.sub)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: DBUser = Depends(get_current_user)):
    return current_user
