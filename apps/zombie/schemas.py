from pydantic import BaseModel


class ZombieCreate(BaseModel):
    os_name: str


class ZombieRead(BaseModel):
    id: int
    os_name: str
    unique_key: str
    status: str
