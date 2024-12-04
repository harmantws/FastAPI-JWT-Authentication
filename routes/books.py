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
async def get_books(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session=Depends(get_db)):
    db_books = db.query(Book).all()
    return JSONResponse({'data': [{'id': str(book.id), 'title': book.title, 'author': book.author, 'price': book.price} for book in db_books], 'status': True},status_code=200)

@router.post('/')
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

@router.get('/{id}/')
async def get_book(id: str, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
        db_book = db.query(Book).filter(Book.id == id).first()
        if db_book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        return db_book

@router.put('/{id}/')
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

@router.patch('/{id}/')
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

@router.delete('/{id}/')
async def delete_book(id:str,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(db_book)
    db.commit()
    return JSONResponse({'status':True, "message": "Book deleted successfully"}, status_code=200)