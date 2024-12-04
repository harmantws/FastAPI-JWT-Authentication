from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    posts = relationship("Post", back_populates="author")
    profile = relationship("Profile", back_populates="user", uselist=False)


class Book(Base):
    __tablename__ = 'books'

    id= Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=True, index=True)
    price = Column(Float, nullable=False, index=True)

class Post(Base):
    __tablename__ = "posts"
    id= Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, index=True, default=datetime.datetime.now)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    author = relationship("User", back_populates="posts")

class Profile(Base):
    __tablename__ = 'profiles'
    id= Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bio = Column(String, nullable=True, index=True)
    location = Column(String, nullable=True, index=True)
    birthdate = Column(DateTime, nullable=True, index=True)
    image_url = Column(String, nullable=True, index=True)

    user = relationship("User", back_populates="profile")