from fastapi import FastAPI, Form, HTTPException, Body, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import time
from datetime import datetime
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import func

import models, schemas, crud, database
from chatbot.service import NewsAssistantService
from security import hash_password, verify_password

app = FastAPI()
assistant_service = NewsAssistantService()
NEWSDATA_API_URL = "https://newsdata.io/api/1/news"
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "pub_e79060a6b07f48949fbc203737376524")


def serialize_user(user: models.User):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "interests": [
            interest.name.lower()
            for interest in sorted(user.interests, key=lambda interest: interest.name.lower())
        ],
    }

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"Finished request: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.2f}s")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily allow ALL for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/news-feed")
def get_news_feed(request: Request):
    forwarded_params = {
        key: value
        for key, value in request.query_params.items()
        if key != "apikey" and value not in (None, "")
    }
    forwarded_params["apikey"] = NEWSDATA_API_KEY

    provider_url = f"{NEWSDATA_API_URL}?{urlencode(forwarded_params)}"

    try:
        with urlopen(provider_url, timeout=15) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(
            status_code=exc.code,
            detail=detail or "The upstream news provider returned an error.",
        )
    except URLError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"The upstream news provider is currently unavailable: {exc.reason}",
        )

@app.post("/register")
def register_user(
    full_name: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    try:
        print(f"--- Registration attempt for {email} ---")
        new_user = models.User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"Success! User ID: {new_user.id}")
        return {"message": "Success", "user_id": new_user.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This email is already registered. Please use a different one.")
    except Exception as e:
        db.rollback()
        print(f"Unexpected error: {e}")
        return {"error": str(e)}
    finally:
        print("--- Registration attempt finished ---")

@app.get("/interests")
def get_interests(db: Session = Depends(database.get_db)):
    try:
        interests = db.query(models.Interest).all()
        return [{"id": i.id, "name": i.name} for i in interests]
    except Exception as e:
        print(f"Error fetching interests: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch interests")

@app.post("/save-interests")
def save_interests(user_id: int = Body(...), interest_ids: List[int] = Body(...), db: Session = Depends(database.get_db)):
    try:
        if len(interest_ids) > 3:
            raise HTTPException(status_code=400, detail="You can select up to 3 interests.")

        # Delete existing
        db.query(models.UserInterest).filter(models.UserInterest.user_id == user_id).delete()
        
        # Insert new
        new_interests = [models.UserInterest(user_id=user_id, interest_id=i_id) for i_id in interest_ids]
        db.add_all(new_interests)
        db.commit()
        return {"message": "Interests saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/complete-signup")
def complete_signup(data: schemas.SignupData, db: Session = Depends(database.get_db)):
    try:
        print(f"--- Atomic Signup attempt for {data.email} ---")

        if len(data.interest_ids) > 3:
            raise HTTPException(status_code=400, detail="You can select up to 3 interests.")
        
        # 1. Insert User
        new_user = models.User(
            full_name=data.full_name,
            email=data.email,
            password_hash=hash_password(data.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"User created with ID: {new_user.id}")

        # 2. Insert Interests
        if data.interest_ids:
            interests = [models.UserInterest(user_id=new_user.id, interest_id=i_id) for i_id in data.interest_ids]
            db.add_all(interests)
            db.commit()
            print(f"Linked {len(data.interest_ids)} interests.")

        print("Signup transaction committed successfully.")
        db.refresh(new_user)
        return {
            "message": "Signup complete",
            "user_id": new_user.id,
            "user": serialize_user(new_user)
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This email is already registered.")
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        print("--- Atomic Signup finished ---")

@app.get("/check-email/{email}")
def check_email(email: str, db: Session = Depends(database.get_db)):
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        return {"exists": user is not None}
    except Exception as e:
        print(f"Error checking email: {e}")
        raise HTTPException(status_code=500, detail="Error checking email")

@app.post("/login")
def login(data: schemas.LoginData, db: Session = Depends(database.get_db)):
    try:
        user = db.query(models.User).filter(models.User.email == data.email).first()
        
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return {
            "message": "Login successful", 
            "user": serialize_user(user)
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user_profile(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize_user(user)


@app.put("/users/{user_id}/profile")
def update_user_profile(user_id: int, data: schemas.ProfileUpdateData, db: Session = Depends(database.get_db)):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        normalized_name = data.full_name.strip()
        normalized_email = data.email.strip().lower()

        if not normalized_name:
            raise HTTPException(status_code=400, detail="Full name is required")

        if not normalized_email:
            raise HTTPException(status_code=400, detail="Email is required")

        existing_user = db.query(models.User).filter(
            func.lower(models.User.email) == normalized_email,
            models.User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="This email is already registered. Please use a different one.")

        if data.new_password:
            if len(data.new_password) < 8:
                raise HTTPException(status_code=400, detail="The new password must contain at least 8 characters.")
            if not data.current_password:
                raise HTTPException(status_code=400, detail="Current password is required to change your password.")
            if not verify_password(data.current_password, user.password_hash):
                raise HTTPException(status_code=400, detail="The current password is incorrect.")

            user.password_hash = hash_password(data.new_password)

        user.full_name = normalized_name
        user.email = normalized_email

        db.commit()
        db.refresh(user)

        return {
            "message": "Profile updated successfully",
            "user": serialize_user(user)
        }
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/favorites")
def save_favorite(payload: schemas.SaveFavoriteRequest, db: Session = Depends(database.get_db)):
    try:
        news_id = crud.upsert_news_record(db, payload.article)
        
        stmt = mysql_insert(models.Favorite).values(
            user_id=payload.user_id,
            news_id=news_id
        )
        stmt = stmt.on_duplicate_key_update(
            saved_at=func.current_timestamp()
        )
        db.execute(stmt)
        db.commit()
        return {"message": "Article saved", "news_id": news_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")

@app.post("/comments")
def add_comment(payload: schemas.CommentRequest, db: Session = Depends(database.get_db)):
    try:
        cleaned_comment = payload.comment_text.strip()
        if not cleaned_comment:
            raise HTTPException(status_code=400, detail="Comment text is required")

        news_id = crud.upsert_news_record(db, payload.article)
        
        new_comment = models.Comment(
            user_id=payload.user_id,
            news_id=news_id,
            comment_content=cleaned_comment
        )
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)
        
        return {"message": "Comment added", "comment_id": new_comment.comment_id, "news_id": news_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")

@app.delete("/favorites")
def remove_favorite(payload: schemas.RemoveFavoriteRequest, db: Session = Depends(database.get_db)):
    try:
        if payload.news_id is not None:
            db.query(models.Favorite).filter(
                models.Favorite.user_id == payload.user_id,
                models.Favorite.news_id == payload.news_id
            ).delete()
        elif payload.article_url:
            news = db.query(models.News).filter(models.News.article_url == payload.article_url).first()
            if news:
                db.query(models.Favorite).filter(
                    models.Favorite.user_id == payload.user_id,
                    models.Favorite.news_id == news.id
                ).delete()
        else:
            raise HTTPException(status_code=400, detail="Provide news_id or article_url")

        db.commit()
        return {"message": "Article removed from favorites", "removed": True}
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")

@app.get("/favorites-status")
def check_favorite(user_id: int, article_url: str, db: Session = Depends(database.get_db)):
    try:
        news = db.query(models.News).filter(models.News.article_url == article_url).first()
        if not news:
            return {"saved": False, "news_id": None}
            
        fav = db.query(models.Favorite).filter(
            models.Favorite.user_id == user_id, 
            models.Favorite.news_id == news.id
        ).first()
        
        return {"saved": fav is not None, "news_id": news.id if fav else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")

@app.get("/favorites/{user_id}")
def get_favorites(user_id: int, db: Session = Depends(database.get_db)):
    try:
        favorites = db.query(models.Favorite).filter(models.Favorite.user_id == user_id).order_by(desc(models.Favorite.saved_at)).all()
        
        result = []
        for fav in favorites:
            news = fav.news
            interest_name = news.interest.name if news.interest else 'Technology'
            source_name = news.source.source_name if news.source else 'Unknown source'
            
            result.append({
                "news_id": news.id,
                "id": news.external_id or str(news.id),
                "title": news.title,
                "description": news.content or "",
                "content": news.content or "",
                "imageUrl": news.image_url or "",
                "sourceName": source_name,
                "publishedAt": news.published_at.isoformat() if news.published_at else datetime.utcnow().isoformat(),
                "url": news.article_url,
                "category": interest_name.lower(),
                "savedAt": fav.saved_at.isoformat() if fav.saved_at else None,
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")

@app.get("/comments")
def get_comments(article_url: str, db: Session = Depends(database.get_db)):
    try:
        news = db.query(models.News).filter(models.News.article_url == article_url).first()
        if not news:
            return []
            
        comments = db.query(models.Comment).filter(models.Comment.news_id == news.id).order_by(desc(models.Comment.createdAt)).all()
        
        return [
            {
                "comment_id": c.comment_id,
                "comment_content": c.comment_content,
                "createdAt": c.createdAt.isoformat() if c.createdAt else None,
                "user_id": c.user_id,
                "full_name": c.user.full_name,
            }
            for c in comments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")


@app.post("/chatbot/article-brief")
def get_article_brief(payload: schemas.ArticleBriefRequest):
    try:
        return assistant_service.get_article_brief(payload.article.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot brief error: {e}")


@app.post("/chatbot/ask")
def ask_chatbot(payload: schemas.AskChatbotRequest):
    try:
        return assistant_service.ask(
            article_payload=payload.article.model_dump(),
            message=payload.message,
            history_payload=[turn.model_dump() for turn in payload.history],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot response error: {e}")
