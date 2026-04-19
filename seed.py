"""
Run: python seed.py
Seeds the database with genres, an admin user, and sample songs.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
from models import Genre, Song, User
from auth_utils import get_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ─── GENRES (10) ─────────────────────────────────────────────────────────────
genres_data = [
    {"name": "Pop",          "description": "Popular mainstream music",               "color": "#FF6B6B"},
    {"name": "Rock",         "description": "Guitar-driven rock music",               "color": "#E74C3C"},
    {"name": "Hip-Hop",      "description": "Urban beats and rap",                    "color": "#9B59B6"},
    {"name": "Electronic",   "description": "Synthesizers and digital production",    "color": "#3498DB"},
    {"name": "Jazz",         "description": "Improvisation and swing",                "color": "#F39C12"},
    {"name": "Classical",    "description": "Orchestral and composed music",          "color": "#1ABC9C"},
    {"name": "Reggaeton",    "description": "Latin urban beats",                      "color": "#E67E22"},
    {"name": "R&B",          "description": "Rhythm and Blues",                       "color": "#E91E63"},
    {"name": "Metal",        "description": "Heavy guitar distortion",               "color": "#607D8B"},
    {"name": "Latin",        "description": "Latin rhythms and sounds",              "color": "#FF5722"},
]

genre_map = {}
for g in genres_data:
    existing = db.query(Genre).filter(Genre.name == g["name"]).first()
    if not existing:
        genre = Genre(**g)
        db.add(genre)
        db.flush()
        genre_map[g["name"]] = genre.id
    else:
        genre_map[g["name"]] = existing.id

db.commit()
print("✅ Genres seeded")

# ─── ADMIN USER ──────────────────────────────────────────────────────────────
admin = db.query(User).filter(User.email == "admin@soundwave.com").first()
if not admin:
    admin = User(
        username="admin",
        email="admin@soundwave.com",
        full_name="SoundWave Admin",
        hashed_password=get_password_hash("admin123"),
        is_admin=True,
        is_verified=True,
        is_active=True,
        validation_code="ADMIN1"
    )
    db.add(admin)
    db.commit()
    print("✅ Admin user created  →  admin@soundwave.com / admin123")

# ─── SAMPLE SONGS (3) ─────────────────────────────────────────────────────────
sample_songs = [
    {
        "title": "Neon Dreams",
        "author": "SynthWave Collective",
        "album": "Digital Horizons",
        "release_date": "2024-03-15",
        "duration": 213.0,
        "genre": "Electronic",
        "image_url": "https://picsum.photos/seed/song1/400/400",
        "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3",
    },
    {
        "title": "Fuego Latino",
        "author": "Bad Bunny Style",
        "album": "Verano 2024",
        "release_date": "2024-06-01",
        "duration": 187.0,
        "genre": "Reggaeton",
        "image_url": "https://picsum.photos/seed/song2/400/400",
        "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3",
    },
    {
        "title": "Midnight Jazz",
        "author": "The Jazz Ensemble",
        "album": "Blue Notes",
        "release_date": "2023-11-20",
        "duration": 301.0,
        "genre": "Jazz",
        "image_url": "https://picsum.photos/seed/song3/400/400",
        "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3",
    },
]

for s in sample_songs:
    exists = db.query(Song).filter(Song.title == s["title"]).first()
    if not exists:
        song = Song(
            title=s["title"],
            author=s["author"],
            album=s["album"],
            release_date=s["release_date"],
            duration=s["duration"],
            genre_id=genre_map[s["genre"]],
            image_url=s["image_url"],
            audio_url=s["audio_url"],
            play_count=0
        )
        db.add(song)

db.commit()
print("✅ Sample songs seeded")
print("\n🎵 Database ready! Start with: uvicorn main:app --reload")
db.close()
