from pydantic import BaseModel


class UserBase(BaseModel):
    username: str

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str


class UserPartialUpdate(UserBase):
    username: str | None = None
    password: str | None = None


class UserRead(UserBase):
    id: int
