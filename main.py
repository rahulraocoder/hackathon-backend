from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from models.submissions import Base
from api.submissions import router as submissions_router
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List
import json

# Initialize logger

# Database setup - use absolute path to evaluator database
db_path = os.getenv("DATABASE_URL", "sqlite:///evaluation.db").replace("sqlite:///", "")
print(f"Using database at: {db_path}")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
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
    ]
    await manager.broadcast({"type": "scores_update", "data": scores})

# Import Team model after manager is defined
from models.submissions import Team
