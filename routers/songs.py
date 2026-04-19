from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import shutil, os, uuid
from pathlib import Path
from database import get_db
from dependencies import get_current_user, get_current_admin
import models, schemas

router = APIRouter()
UPLOAD_DIR = Path("uploads")

def save_file(upload: UploadFile, subfolder: str) -> str:
    ext = Path(upload.filename).suffix
    filename = f"{uuid.uuid4()}{ext}"
    path = UPLOAD_DIR / subfolder / filename
    with open(path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    return f"{base_url}/uploads/{subfolder}/{filename}"

# ─── GENRES ──────────────────────────────────────────────────────────────────

@router.get("/genres", response_model=List[schemas.GenreOut])
def get_genres(db: Session = Depends(get_db)):
    return db.query(models.Genre).all()

# ─── SONGS ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[schemas.SongOut])
def get_songs(
    skip: int = 0,
    limit: int = 50,
    genre_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.Song).filter(models.Song.is_active == True)
    if genre_id:
        q = q.filter(models.Song.genre_id == genre_id)
    if search:
        q = q.filter(
            models.Song.title.ilike(f"%{search}%") |
            models.Song.author.ilike(f"%{search}%") |
            models.Song.album.ilike(f"%{search}%")
        )
    return q.offset(skip).limit(limit).all()

@router.get("/{song_id}", response_model=schemas.SongOut)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song

@router.post("/", response_model=schemas.SongOut, status_code=201)
async def create_song(
    title: str = Form(...),
    author: str = Form(...),
    album: Optional[str] = Form(None),
    release_date: Optional[str] = Form(None),
    duration: float = Form(...),
    genre_id: int = Form(...),
    image_url: Optional[str] = Form(None),
    audio_url: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    genre = db.query(models.Genre).filter(models.Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    final_image = image_url
    final_audio = audio_url

    if image_file and image_file.filename:
        final_image = save_file(image_file, "images")
    if audio_file and audio_file.filename:
        final_audio = save_file(audio_file, "songs")

    song = models.Song(
        title=title, author=author, album=album,
        release_date=release_date, duration=duration,
        genre_id=genre_id, image_url=final_image, audio_url=final_audio
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    return song

@router.put("/{song_id}", response_model=schemas.SongOut)
def update_song(
    song_id: int,
    song_data: schemas.SongUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    for k, v in song_data.dict(exclude_unset=True).items():
        setattr(song, k, v)
    db.commit()
    db.refresh(song)
    return song

@router.delete("/{song_id}", status_code=204)
def delete_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    song.is_active = False
    db.commit()

@router.post("/{song_id}/play", response_model=dict)
def register_play(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    song.play_count += 1
    history = models.PlayHistory(user_id=current_user.id, song_id=song_id)
    db.add(history)
    db.commit()
    return {"message": "Play registered"}

@router.get("/top/popular", response_model=List[schemas.SongOut])
def get_popular(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.Song).filter(
        models.Song.is_active == True
    ).order_by(models.Song.play_count.desc()).limit(limit).all()
