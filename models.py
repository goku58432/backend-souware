from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Association table for playlist songs
playlist_songs = Table(
    "playlist_songs",
    Base.metadata,
    Column("playlist_id", Integer, ForeignKey("playlists.id"), primary_key=True),
    Column("song_id", Integer, ForeignKey("songs.id"), primary_key=True),
    Column("added_at", DateTime(timezone=True), server_default=func.now())
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(255))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    validation_code = Column(String(10))
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    playlists = relationship("Playlist", back_populates="owner")
    play_history = relationship("PlayHistory", back_populates="user")

class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    color = Column(String(7), default="#1DB954")  # hex color for UI

    songs = relationship("Song", back_populates="genre")

class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(200), nullable=False)
    album = Column(String(200))
    release_date = Column(String(20))
    duration = Column(Float, nullable=False)  # seconds
    image_url = Column(String(500))
    audio_url = Column(String(500))
    genre_id = Column(Integer, ForeignKey("genres.id"))
    play_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    genre = relationship("Genre", back_populates="songs")
    playlists = relationship("Playlist", secondary=playlist_songs, back_populates="songs")
    play_history = relationship("PlayHistory", back_populates="song")

class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    cover_url = Column(String(500))
    is_public = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="playlists")
    songs = relationship("Song", secondary=playlist_songs, back_populates="playlists")

class PlayHistory(Base):
    __tablename__ = "play_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    song_id = Column(Integer, ForeignKey("songs.id"))
    played_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="play_history")
    song = relationship("Song", back_populates="play_history")
