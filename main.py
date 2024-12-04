import logging
from fastapi import FastAPI
from database import engine
from schemas import *
from models import *
from auth import *
from middleware import AuthMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.dialects.postgresql import UUID
from routes import user, posts, books, profile

logger = logging.getLogger("uvicorn")

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(AuthMiddleware)
security = HTTPBearer()

app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(posts.router, prefix="/posts", tags=["BlogPosts"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])

@app.get('/')
async def root():
    return {"message": "Hello World"}