from typing import Optional

from pydantic import BaseModel


class Owner(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None


class Pet(BaseModel):
    id: Optional[int] = None
    name: str
    species: str
    breed: Optional[str] = None
    owner_id: int