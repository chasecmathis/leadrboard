from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime, timezone
from core.security import create_access_token, verify_password, get_password_hash
from config import get_settings
from database import db
from api.v1.models.users import User, UserCreate

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=User)
async def create_user(user: UserCreate):
    db_user = await db.get_db().users.find_one({"username": user.username})
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    user_dict["created_at"] = datetime.now(timezone.utc)
    del user_dict["password"]

    result = await db.get_db().users.insert_one(user_dict)
    created_user = await db.get_db().users.find_one({"_id": result.inserted_id})
    return User(**created_user)


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.get_db().users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
