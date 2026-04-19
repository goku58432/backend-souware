from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from dependencies import get_current_user
import models, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.PlaylistOut])
def get_my_playlists(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Playlist).filter(
        models.Playlist.owner_id == current_user.id
    ).all()

@router.get("/public", response_model=List[schemas.PlaylistOut])
def get_public_playlists(db: Session = Depends(get_db)):
    return db.query(models.Playlist).filter(
        models.Playlist.is_public == True
    ).all()

@router.get("/{playlist_id}", response_model=schemas.PlaylistOut)
def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if not playlist.is_public and playlist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return playlist

@router.post("/", response_model=schemas.PlaylistOut, status_code=201)
def create_playlist(
    data: schemas.PlaylistCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    playlist = models.Playlist(
        name=data.name,
        description=data.description,
        is_public=data.is_public,
        owner_id=current_user.id
    )
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    return playlist

@router.put("/{playlist_id}", response_model=schemas.PlaylistOut)
def update_playlist(
    playlist_id: int,
    data: schemas.PlaylistUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if playlist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your playlist")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(playlist, k, v)
    db.commit()
    db.refresh(playlist)
    return playlist

@router.delete("/{playlist_id}", status_code=204)
def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if playlist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your playlist")
    db.delete(playlist)
    db.commit()

@router.post("/{playlist_id}/songs", response_model=dict)
def add_song(
    playlist_id: int,
    data: schemas.AddSongToPlaylist,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if playlist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your playlist")

    song = db.query(models.Song).filter(models.Song.id == data.song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    if song in playlist.songs:
        raise HTTPException(status_code=400, detail="Song already in playlist")

    playlist.songs.append(song)
    db.commit()
    return {"message": "Song added to playlist"}

@router.delete("/{playlist_id}/songs/{song_id}", status_code=204)
def remove_song(
    playlist_id: int,
    song_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if playlist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your playlist")

    song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if song in playlist.songs:
        playlist.songs.remove(song)
        db.commit()
