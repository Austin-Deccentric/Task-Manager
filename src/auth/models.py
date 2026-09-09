from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Annotated
import re

class UserBase(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    # is_active: bool = True
    
    
class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8)]
    age: Annotated[int, Field(ge=16, lt= 120)]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # pydantic-core (Rust regex) doesn't support (?=...) look-ahead,
        # so validate with Python instead.
        if not re.fullmatch(r"[A-Za-z\d]{8,}", v):
            raise ValueError("must be 8+ chars, letters and numbers only")
        if not re.search(r"[a-z]", v) or not re.search(r"[A-Z]", v) or not re.search(r"\d", v):
            raise ValueError("must contain upper, lower and digit")
        return v

# class UserPublic(UserBase):
#     id: int

class UserLogin(BaseModel):
    email: str
    password: str