from datetime import datetime
from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from apps.user.models import User, AccessToken
from config.database import get_async_session

# Define these once globally so you can reuse them everywhere
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authentication/login")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_current_user(
        token: str,
        session: AsyncSession = Depends(get_async_session)
) -> User:
    print(token)
    query = select(AccessToken).where(
        AccessToken.access_token == token,
        AccessToken.expires_in >= datetime.now(tz=None)
    )
    result = await session.execute(query)
    access_token: AccessToken | None = result.scalar_one_or_none()
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return access_token.user


async def get_current_user_by_token(
        # Use Annotated for cleaner, more readable code
        token_oauth: Annotated[str, Depends(oauth2_scheme)],
        token_api: Annotated[str | None, Depends(api_key_header)],
        session: Annotated[AsyncSession, Depends(get_async_session)]
):
    str(token_oauth)
    print(token_oauth)
    """
    Retrieves the current user by checking the OAuth2 Bearer token
    or an optional API Key.
    """
    # Decide which token to prioritize. Usually OAuth2 (token_oauth)
    # is the standard for Swagger/Web, and API Key is for external scripts.
    effective_token = token_oauth or token_api

    user = await get_current_user(effective_token, session)
    return user
