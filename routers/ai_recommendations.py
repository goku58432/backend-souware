from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from dependencies import get_current_user
import models, schemas
import math

router = APIRouter()

def genre_similarity(song: models.Song, candidate: models.Song) -> float:
    """Simple similarity score based on genre, author and era."""
    score = 0.0
    if song.genre_id == candidate.genre_id:
        score += 0.6
    if song.author.lower() == candidate.author.lower():
        score += 0.3
    if song.album and candidate.album and song.album.lower() == candidate.album.lower():
        score += 0.1
    return score

def tfidf_similarity(song: models.Song, candidate: models.Song) -> float:
    """Lightweight text similarity using shared words in title/author/album."""
    def tokenize(s: models.Song):
        tokens = set()
        for field in [s.title, s.author, s.album or ""]:
            tokens.update(field.lower().split())
        return tokens

    tokens_a = tokenize(song)
    tokens_b = tokenize(candidate)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    return len(intersection) / math.sqrt(len(tokens_a) * len(tokens_b))

@router.get("/recommendations/{song_id}", response_model=schemas.RecommendationOut)
def get_recommendations(
    song_id: int,
    limit: int = 6,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    song = db.query(models.Song).filter(
        models.Song.id == song_id,
        models.Song.is_active == True
    ).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    candidates = db.query(models.Song).filter(
        models.Song.id != song_id,
        models.Song.is_active == True
    ).all()

    scored = []
    for c in candidates:
        score = genre_similarity(song, c) * 0.7 + tfidf_similarity(song, c) * 0.3
        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:limit]]

    genre_name = song.genre.name if song.genre else "similar"
    reason = f"Based on genre '{genre_name}' and listening patterns"

    return schemas.RecommendationOut(songs=top, reason=reason)

@router.get("/similar-genre/{genre_id}", response_model=List[schemas.SongOut])
def songs_by_genre(
    genre_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Song).filter(
        models.Song.genre_id == genre_id,
        models.Song.is_active == True
    ).order_by(models.Song.play_count.desc()).limit(limit).all()
