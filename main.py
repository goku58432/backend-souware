from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
from pathlib import Path

from database import engine, Base
from routers import auth, songs, playlists, users, ai_recommendations
import models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SoundWave API",
    description="Spotify-like music streaming API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
(uploads_dir / "songs").mkdir(exist_ok=True)
(uploads_dir / "images").mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(songs.router, prefix="/api/songs", tags=["Songs"])
app.include_router(playlists.router, prefix="/api/playlists", tags=["Playlists"])
app.include_router(ai_recommendations.router, prefix="/api/ai", tags=["AI Recommendations"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "now_playing":
                await manager.send_personal_message({
                    "type": "now_playing_ack",
                    "song_id": data.get("song_id")
                }, user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@app.get("/")
def root():
    return {"message": "SoundWave API is running 🎵", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
