from fastapi import APIRouter, HTTPException
from pwdlib import PasswordHash

from src.auth.models import UserBase, UserCreate, UserLogin
from src.auth.schemas import User
from src.db import SessionDep

router = APIRouter(prefix="/auth")

hasher = PasswordHash.recommended()

@router.post("/register", response_model = UserBase, status_code=201, summary="Register a new user")
async def create_user(
    user: UserCreate,
    session: SessionDep
):
    """Create a new user account.

    - body: `email`, `username`, `password`, `age`
    - 400 if the email is already registered
    """
    _user = session.get(User, user.email)
    if _user:
        raise HTTPException(status_code=400, detail="User already exists")
    password = user.password
    
    new_user = User(**user.model_dump(), hashed_password= hasher.hash(password))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@router.post("/login", response_model=UserBase, summary="Log in")
async def login(
    user: UserLogin,
    session: SessionDep
):
    """Authenticate a user and return their profile.

    - body: `email`, `password`
    - 404 if the email is not registered
    - 401 if the password is incorrect
    """
    _user = session.get(User, user.email)
    if not _user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not hasher.verify(user.password, _user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    return _user


# TODO: get all tasks for a user
