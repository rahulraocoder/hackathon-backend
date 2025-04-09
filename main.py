from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models.submissions import Base
from api.submissions import router as submissions_router
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List
import json

import logging
from config import settings
settings.configure_logging()
logger = logging.getLogger(__name__)
logger.info("Application starting", extra={"version": "1.0"})

from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Essential database connection check
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    
    # Initialize tables
    Base.metadata.create_all(bind=engine)
    yield
    
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 5
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(
    lifespan=lifespan,
    title="Hackathon Evaluator API",
    description="API for evaluating and tracking team submissions",
    version="1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# Include routers
app.include_router(submissions_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Hackathon Evaluator API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/ws/scores")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Function to broadcast score updates
async def broadcast_scores(db):
    teams = db.query(Team).all()
    scores = [
        {
            "team_key": t.team_key,
            "best_score": t.best_score,
            "last_submission": t.last_submission.isoformat() if t.last_submission else None
        }
        for t in teams
        if t.best_score is not None  # Only include teams with actual scores
    ]
    await manager.broadcast({"type": "scores_update", "data": scores})

# Import Team model after manager is defined
from models.submissions import Team
