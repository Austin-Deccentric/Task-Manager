from pydantic import BaseModel, EmailStr, Field
from typing import Annotated

class UserBase(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    # is_active: bool = True
    
    
class UserCreate(UserBase):
    password: Annotated[str, Field(pattern=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$')]
    age: Annotated[int, Field(ge=16, lt= 120)]

# class UserPublic(UserBase):
#     id: int

