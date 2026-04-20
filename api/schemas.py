from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SignupData(BaseModel):
    full_name: str
    email: str
    password: str
    interest_ids: List[int]

class LoginData(BaseModel):
    email: str
    password: str

class FavoriteArticleData(BaseModel):
    article_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    source_url: str
    source_name: Optional[str] = None
    published_at: Optional[str] = None
    category: Optional[str] = None
    datatype: Optional[str] = None
    country: Optional[str] = None

class SaveFavoriteRequest(BaseModel):
    user_id: int
    article: FavoriteArticleData

class RemoveFavoriteRequest(BaseModel):
    user_id: int
    news_id: Optional[int] = None
    article_url: Optional[str] = None

class CommentRequest(BaseModel):
    user_id: int
    article: FavoriteArticleData
    comment_text: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    
    class Config:
        from_attributes = True

class InterestResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
