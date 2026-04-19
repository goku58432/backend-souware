from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import os, uuid
from pathlib import Path
from database import get_db
from dependencies import get_current_user, get_current_admin
import models, schemas
import cloudinary
import cloudinary.uploader

# ─── Cloudinary config ────────────────────────────────────────────────────────
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

router = APIRouter()

def upload_to_cloudinary(file: UploadFile, folder: str, resource_type: str = "auto") -> str:
    contents = file.file.read()
    result = cloudinary.uploader.upload(
        contents,
        folder=f"soundwave/{folder}",
        resource_type=resource_type,
        public_id=f"{uuid.uuid4()}"
    )
    return result["secure_url"]

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

@router.get("/top/popular", response_model=List[schemas.SongOut])
def get_popular(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.Song).filter(
        models.Song.is_active == True
    ).order_by(models.Song.play_count.desc()).limit(limit).all()

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
        final_image = upload_to_cloudinary(image_file, "images", "image")

    if audio_file and audio_file.filename:
        final_audio = upload_to_cloudinary(audio_file, "songs", "video")

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
