from fastapi import APIRouter, HTTPException, Body, Depends, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
import json
from typing import Union
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.submissions import Submission, Team, get_db
from core.scoring import calculate_score
from api.models import MetricsPayload, CombinedMetricsPayload

router = APIRouter()

import logging
logger = logging.getLogger(__name__)

@router.post("/submit", response_model=dict)
async def submit_metrics(
    background_tasks: BackgroundTasks,
    authorization: str = Header(..., alias="Authorization"),
    payload: Union[MetricsPayload, CombinedMetricsPayload] = Body(...),
    db: Session = Depends(get_db),
):
    # Handle both old and new payload formats
    if isinstance(payload, CombinedMetricsPayload):
        metrics = payload.business_metrics
        perf_metrics = payload.performance_metrics
    else:
        metrics = payload
        perf_metrics = None
    try:
        logger.info(f"Received submission request. Authorization: {authorization}")
        logger.debug(f"Metrics payload: {metrics}")
        from config import settings
        
        # Validate team key format
        if not authorization.startswith(settings.TEAM_KEY_PREFIX):
            raise HTTPException(
                status_code=401,
                detail=f"Key must start with {settings.TEAM_KEY_PREFIX}"
            )
        
        # Debug log team key and existing teams
        logger.debug(f"Checking team key: {authorization}")
        all_teams = db.query(Team).all()
        logger.debug(f"Existing teams: {[t.team_key for t in all_teams]}")
        
        # Check submission limit
        team = db.query(Team).filter_by(team_key=authorization).first()
        if not team:
            logger.error(f"No team found for key: {authorization}")
            raise HTTPException(status_code=403, detail="Invalid team key. Ensure you're using the correct team key starting with 'TM-'")
            
        if team.submission_count >= settings.SUBMISSIONS_PER_TEAM:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum {settings.SUBMISSIONS_PER_TEAM} submissions reached"
            )

        # Convert metrics to dict and calculate score
        metrics_dict = metrics.dict()
        score = calculate_score(metrics_dict)

        # Create submission record
        submission = Submission(
            team_key=authorization,
            metrics=json.dumps(metrics_dict),
            score=score,
            status='completed',
            timestamp=datetime.utcnow(),
            performance_metrics=json.dumps(perf_metrics.dict()) if perf_metrics else None
        )
        db.add(submission)

        # Update team counters
        team.submission_count = (team.submission_count or 0) + 1
        team.last_submission = datetime.utcnow()
        if not team.best_score or score > team.best_score:
            team.best_score = score

        db.commit()
        
        # Broadcast updated scores to all WebSocket clients
        if background_tasks:
            from main import broadcast_scores
            background_tasks.add_task(broadcast_scores, db)
            
        return {
            "status": "success", 
            "score": score,
            "submissions_remaining": settings.SUBMISSIONS_PER_TEAM - team.submission_count
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/scores", response_model=list)
async def get_scores(db: Session = Depends(get_db)):
    try:
        # Get latest submission for each team
        subquery = db.query(
            Submission.team_key,
            func.max(Submission.timestamp).label('max_timestamp')
        ).group_by(Submission.team_key).subquery()

        latest_submissions = db.query(Submission)\
            .join(
                subquery,
                (Submission.team_key == subquery.c.team_key) & 
                (Submission.timestamp == subquery.c.max_timestamp)
            )\
            .order_by(Submission.score.desc())\
            .all()

        # Get team names and build response
        response = []
        for sub in latest_submissions:
            team = db.query(Team).filter_by(team_key=sub.team_key).first()
            response.append({
                "team_name": team.team_name,
                "latest_score": sub.score,
                "timestamp": sub.timestamp.isoformat(),
                "status": sub.status
            })
            
        return JSONResponse(content=response)
    finally:
        db.close()
