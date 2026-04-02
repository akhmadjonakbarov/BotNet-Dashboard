from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Integer, String, ForeignKey

from apps.base.models import Base
from config.security import generate_access_token, get_expiration_date


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)


class AccessToken(Base):
    __tablename__ = 'access_tokens'
    access_token: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, default=generate_access_token)
    expires_in: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=get_expiration_date)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    user: Mapped[User] = relationship("User", lazy="joined", )
