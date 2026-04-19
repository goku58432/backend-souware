from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# ─── AUTH ────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @validator("username")
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric")
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be 3-50 characters")
        return v

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

class UserLogin(BaseModel):
    email: str
    password: str

class UserVerify(BaseModel):
    email: str
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserOut"

# ─── USERS ───────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_admin: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str]
    avatar_url: Optional[str]

# ─── GENRES ──────────────────────────────────────────────────────────────────

class GenreOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str

    class Config:
        from_attributes = True

# ─── SONGS ───────────────────────────────────────────────────────────────────

class SongCreate(BaseModel):
    title: str
    author: str
    album: Optional[str]
    release_date: Optional[str]
    duration: float
    image_url: Optional[str]
    audio_url: Optional[str]
    genre_id: int

class SongUpdate(BaseModel):
    title: Optional[str]
    author: Optional[str]
    album: Optional[str]
    release_date: Optional[str]
    duration: Optional[float]
    image_url: Optional[str]
    audio_url: Optional[str]
    genre_id: Optional[int]

class SongOut(BaseModel):
    id: int
    title: str
    author: str
    album: Optional[str]
    release_date: Optional[str]
    duration: float
    image_url: Optional[str]
    audio_url: Optional[str]
    genre: Optional[GenreOut]
    play_count: int
    created_at: datetime

    class Config:
        from_attributes = True

# ─── PLAYLISTS ────────────────────────────────────────────────────────────────

class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str]
    is_public: bool = True

class PlaylistUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    cover_url: Optional[str]
    is_public: Optional[bool]

class PlaylistOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    cover_url: Optional[str]
    is_public: bool
    owner: UserOut
    songs: List[SongOut] = []
    created_at: datetime

    class Config:
        from_attributes = True

class AddSongToPlaylist(BaseModel):
    song_id: int

# ─── AI ──────────────────────────────────────────────────────────────────────

class RecommendationOut(BaseModel):
    songs: List[SongOut]
    reason: str

Token.model_rebuild()
