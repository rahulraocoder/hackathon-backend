from fastapi import APIRouter, HTTPException, Body, Depends, Header, BackgroundTasks
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from datetime import datetime
import json
from typing import Union, Optional
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from models.submissions import Submission, Team, get_db
from tenacity import retry, stop_after_attempt, wait_exponential
from core.scoring import calculate_score
from api.models import MetricsPayload, CombinedMetricsPayload

router = APIRouter()

import logging
logger = logging.getLogger(__name__)

@router.post("/submit", response_model=dict)
def submit_metrics(
    background_tasks: BackgroundTasks,
    authorization: str = Header(..., alias="Authorization"),
    payload: Union[MetricsPayload, CombinedMetricsPayload] = Body(...),
    db = Depends(get_db),
):
    # Handle both old and new payload formats
    if isinstance(payload, CombinedMetricsPayload):
        metrics = payload.business_metrics
        perf_metrics = payload.performance_metrics
    else:
        metrics = payload
        perf_metrics = None
    try:
        logger.info(f"Submission request from {authorization}")
        logger.debug(f"Full payload: {payload.json()}")
        logger.debug(f"Business metrics: {metrics}")
        if perf_metrics:
            logger.debug(f"Performance metrics: {perf_metrics}")
        from config import settings
        
        # Validate team key format
        if not authorization.startswith(settings.TEAM_KEY_PREFIX):
            raise HTTPException(
                status_code=401,
                detail=f"Key must start with {settings.TEAM_KEY_PREFIX}"
            )
        
        # Debug log team key and existing teams
        logger.debug(f"Checking team key: {authorization}")
        result = db.execute(select(Team))
        all_teams = result.scalars().all()
        logger.debug(f"Existing teams: {[t.team_key for t in all_teams]}")
        
        # Check submission limit
        result = db.execute(
            select(Team).where(Team.team_key == authorization)
        )
        team = result.scalar_one_or_none()
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
            performance_metrics=perf_metrics.json() if perf_metrics else None
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
        logger.error(f"Error submitting metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        db.close()

@router.get("/scores", response_model=list)
def get_scores(db = Depends(get_db)):
    try:
        # Get all teams regardless of submissions
        teams = db.query(Team).order_by(Team.team_name).all()
        response = []
        
        for team in teams:
            # Get all submissions for this team
            submissions = db.query(Submission)\
                .filter_by(team_key=team.team_key)\
                .order_by(Submission.timestamp.desc())\
                .all()
                
            # Get best score
            best_score = db.query(func.max(Submission.score))\
                .filter_by(team_key=team.team_key)\
                .scalar()
                
            # Build scores array
            scores = []
            trend = []
            for sub in submissions:
                scores.append({
                    "value": sub.score,
                    "is_best": sub.score == best_score,
                    "id": str(sub.id),
                    "timestamp": sub.timestamp.isoformat()
                })
                trend.append(sub.score)
                
            response.append({
                "team_key": team.team_key,
                "team_name": team.team_name,
                "avatar": team.avatar if hasattr(team, 'avatar') else team.team_key[0],
                "scores": scores,
                "best_score": best_score,
                "trend": trend,
                "latest_score": submissions[0].score if submissions else None,
                "status": submissions[0].status if submissions else None,
                "has_submissions": len(submissions) > 0
            })
            
        # Sort by best score descending
        response.sort(key=lambda x: x["best_score"] or 0, reverse=True)
        return JSONResponse(content=response)
    finally:
        db.close()
