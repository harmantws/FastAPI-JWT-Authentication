import logging
from fastapi import Depends, HTTPException,Request,APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from schemas import *
from models import *
from auth import *
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("uvicorn")
router = APIRouter()
security = HTTPBearer()

@router.get('/')
async def get_posts(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session=Depends(get_db)):
    db_posts = db.query(Post).filter(Post.user_id== request.state.user.get('user_id')).all()
    return JSONResponse({"total":len(db_posts),'data': [{'id': str(post.id), 'title': post.title, 'content': post.content, 'author': post.author.username} for post in db_posts], 'status': True},status_code=200)

@router.get('/{id}/')
async def get_post_using_id(request:Request,id:str,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session=Depends(get_db)):
    db_posts = db.query(Post).filter(Post.id == id).first()
    if db_posts is None:
        raise HTTPException(status_code=404, detail="Post not found")
    logger.info(f"Post--> {db_posts}")
    return JSONResponse({'message':'Fetched Successfully',"status":True,"data":{
        'id': str(db_posts.id),
        'title': db_posts.title,
        'content': db_posts.content,
        'author': db_posts.author.username
    }},status_code=200)


@router.post('/')
async def create_post(request:Request,post: PostCreate, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session=Depends(get_db)):
    user_id = request.state.user.get('user_id')
    new_post = Post(
        title=post.title,
        content=post.content,
        user_id=user_id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return post


@router.put('/{id}/')
async def update_post(request:Request,id:str, post: PostCreate, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_id = request.state.user.get('user_id')
    db_post = db.query(Post).filter(Post.id == id, Post.user_id == user_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.title = post.title
    db_post.content = post.content
    db.commit()
    db.refresh(db_post)
    return db_post

@router.patch('/{id}/')
async def update_post(request:Request, id:str, post: PostUpdate, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
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

@router.delete('/{id}')
async def delete_post(request:Request, id:str, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_id = request.state.user.get('user_id')
    db_post = db.query(Post).filter(Post.id == id, Post.user_id == user_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(db_post)
    db.commit()
    return JSONResponse({'status':True, "message": "Post deleted successfully"}, status_code=200)