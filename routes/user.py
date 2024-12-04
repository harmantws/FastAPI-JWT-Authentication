import logging
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request,APIRouter
from sqlalchemy.orm import Session
from database import get_db
from datetime import timedelta
from schemas import *
from models import *
from auth import *
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse

logger = logging.getLogger("uvicorn")
router = APIRouter()
security = HTTPBearer()

@router.post("/register/", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")
    
    hashed_password = get_password_hash(user.password1)
    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post('/login/')
def login_user(response: Response,user: UserLogin, db:Session=Depends(get_db)):

    db_user = db.query(User).filter((User.username == user.username_or_email) | (User.email == user.username_or_email)).first()
    
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect username or password")
    user_data = {
        "username": db_user.username,
        "email": db_user.email,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        "user_id": str(db_user.id)
    }
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data=user_data ,expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(hours=5)
    refresh_token = create_refresh_token(
        data=user_data, expires_delta=refresh_token_expires
    )
    return {"access_token": access_token, "refresh_token": refresh_token,"username": db_user.username,
        "email": db_user.email,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name}

@router.get("/profile/")
async def profile(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    logger.info("Profile GET API Initiated")
    user = request.state.user
    logger.info('Data Fetched Successfully')
    return {
        "username": user["username"],
        "email": user["email"],
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name")
    }

@router.post('/refresh_token')
async def refresh_api_token(request:RefreshTokenRequest):
    logger.info("Refresh Token API Initiated")
    payload = decode_token(request.refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    username = payload.get("username")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token_expires = timedelta(minutes=30)
    new_access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(hours=5)
    new_refresh_token = create_refresh_token(data={"sub": username}, expires_delta=refresh_token_expires)

    return JSONResponse({"message":"Token Refreshed Successfully",'access_token':new_access_token, "refresh_token":new_refresh_token}, status_code=200)