import logging
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import engine, get_db
from datetime import timedelta
from schemas import *
from models import *
from auth import *
from middleware import AuthMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.dialects.postgresql import UUID
logger = logging.getLogger("uvicorn")

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(AuthMiddleware)
security = HTTPBearer()


@app.get('/')
async def root():
    return {"message": "Hello World"}

@app.post("/register/", response_model=UserResponse)
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

@app.post('/login/')
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

@app.get("/profile/")
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

@app.post('/refresh_token')
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

@app.get('/api/books/')
async def get_books(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session=Depends(get_db)):
    db_books = db.query(Book).all()
    return JSONResponse({'data': [{'id': str(book.id), 'title': book.title, 'author': book.author, 'price': book.price} for book in db_books], 'status': True},status_code=200)

@app.post('/api/books/')
async def add_book(book: BookCreate,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session=Depends(get_db)):
    logger.info(f"Adding book--> {book}")
    new_book = Book(
        title=book.title,
        author=book.author,
        price=book.price
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@app.get('/api/books/{id}/')
async def get_book(id: str, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
        db_book = db.query(Book).filter(Book.id == id).first()
        if db_book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        return db_book

@app.put('/api/books/{id}/')
async def put_book(id:str,book: BookCreate,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db_book.title = book.title
    db_book.author = book.author
    db_book.price = book.price
    db.commit()
    db.refresh(db_book)
    return db_book

@app.patch('/api/books/{id}/')
async def patch_book(id:str,book:BookUpdate,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.title:
        db_book.title = book.title
    if book.author:
        db_book.author = book.author
    if book.price:
        db_book.price = book.price
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete('/api/books/{id}')
async def delete_book(id:str,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(db_book)
    db.commit()
    return JSONResponse({'status':True, "message": "Book deleted successfully"}, status_code=200)


@app.get('/api/posts/')
async def get_posts(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session=Depends(get_db)):
    db_posts = db.query(Post).filter(Post.user_id== request.state.user.get('user_id')).all()
    return JSONResponse({"total":len(db_posts),'data': [{'id': str(post.id), 'title': post.title, 'content': post.content, 'author': post.author.username} for post in db_posts], 'status': True},status_code=200)


@app.post('/api/posts/')
async def add_post(request:Request,post: PostCreate, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session=Depends(get_db)):
    user_id = request.state.user.get('user_id')
    new_post = Post(
        title=post.title,
        content=post.content,
        user_id=user_id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@app.put('/api/posts/{id}/')
async def put_post(request:Request,id:str, post: PostCreate, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_id = request.state.user.get('user_id')
    db_post = db.query(Post).filter(Post.id == id, Post.user_id == user_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.title = post.title
    db_post.content = post.content
    db.commit()
    db.refresh(db_post)
    return db_post

@app.patch('/api/posts/{id}/')
async def patch_post(request:Request, id:str, post: PostUpdate, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_id = request.state.user.get('user_id')
    db_post = db.query(Post).filter(Post.id == id, Post.user_id == user_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    update_data = post.dict(exclude_unset=True)
    logger.info(f"Incoming data {update_data}")
    for field, value in update_data.items():
        setattr(db_post, field, value)   # Equivalent to db_post.title = "Updated Title"
    
    db.commit()
    db.refresh(db_post)
    return db_post

@app.delete('/api/posts/{id}')
async def delete_post(request:Request, id:str, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_id = request.state.user.get('user_id')
    db_post = db.query(Post).filter(Post.id == id, Post.user_id == user_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(db_post)
    db.commit()
    return JSONResponse({'status':True, "message": "Post deleted successfully"}, status_code=200)
