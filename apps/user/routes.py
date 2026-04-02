from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exc
from starlette import status

from apps.user import schemas
from apps.user.authentication import authenticate, create_access_token
from apps.user.models import User
from apps.user.schemas import UserCreate
from config.database import get_async_session
from config.security import get_password_hash

router = APIRouter(
    prefix="/authentication",
    tags=["Authentication"],
)


@router.post(
    "/register", status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserRead
)
async def register(
        user_create: UserCreate,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        username = user_create.username
        password = user_create.password
        user = User(username=username, password=get_password_hash(password))
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except exc.IntegrityError as e:
        print(str(e))
        await session.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        await  session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
        form_date: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        username = form_date.username
        password = form_date.password
        user = await authenticate(username, password, session)
        if user is None:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        token = await create_access_token(user, session)
        return token
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-token")
async def create_token(
        form_date: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        username = form_date.username
        password = form_date.password
        user = await  authenticate(username, password, session)
        if user is None:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        token = await  create_access_token(user, session)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/logout")
async def logout():
    pass
