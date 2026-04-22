from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List

import models, schemas
from security import hash_password

def parse_publication_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    safe_value = value.strip()
    if not safe_value:
        return None
    if safe_value.endswith("Z"):
        safe_value = safe_value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(safe_value)
        return parsed.replace(tzinfo=None)
    except ValueError:
        return None

def get_or_create_interest_id(db: Session, category: Optional[str]) -> Optional[int]:
    if not category:
        return None
    normalized = category.strip()
    if not normalized:
        return None
        
    existing = db.query(models.Interest).filter(func.lower(models.Interest.name) == normalized.lower()).first()
    if existing:
        return existing.id
        
    display_name = normalized[0].upper() + normalized[1:].lower() if len(normalized) > 1 else normalized.upper()
    new_interest = models.Interest(name=display_name)
    db.add(new_interest)
    db.commit()
    db.refresh(new_interest)
    return new_interest.id

def upsert_news_record(db: Session, article: schemas.FavoriteArticleData) -> int:
    article_url = (article.source_url or "").strip()
    if not article_url:
        raise ValueError("Article URL is required")

    source_name = (article.source_name or "Unknown source").strip() or "Unknown source"
    
    stmt_source = mysql_insert(models.Source).values(
        source_name=source_name, 
        source_url=article_url
    )
    stmt_source = stmt_source.on_duplicate_key_update(
        source_url=stmt_source.inserted.source_url
    )
    db.execute(stmt_source)
    source_id = db.query(models.Source).filter_by(source_name=source_name, source_url=article_url).first().id

    interest_id = get_or_create_interest_id(db, article.category)
    published_at = parse_publication_date(article.published_at)
    article_content = article.content or article.description

    stmt_news = mysql_insert(models.News).values(
        external_id=article.article_id,
        title=article.title,
        content=article_content,
        image_url=article.image_url,
        article_url=article_url,
        published_at=published_at,
        interest_id=interest_id,
        source_id=source_id,
        datatype=article.datatype,
        country=article.country
    )
    stmt_news = stmt_news.on_duplicate_key_update(
        external_id=stmt_news.inserted.external_id,
        title=stmt_news.inserted.title,
        content=stmt_news.inserted.content,
        image_url=stmt_news.inserted.image_url,
        published_at=stmt_news.inserted.published_at,
        interest_id=stmt_news.inserted.interest_id,
        source_id=stmt_news.inserted.source_id,
        datatype=stmt_news.inserted.datatype,
        country=stmt_news.inserted.country
    )
    db.execute(stmt_news)
    return db.query(models.News).filter_by(article_url=article_url).first().id
