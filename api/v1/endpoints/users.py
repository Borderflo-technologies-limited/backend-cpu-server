#!/usr/bin/env python3
"""
User management endpoints for Visa AI Interviewer
"""

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db, InterviewSession
from app.core.security import get_current_active_user
from app.core.database import User
from app.models.user import UserUpdate, UserResponse

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update current user profile"""
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user statistics"""
    # Count interview sessions
    total_sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).count()
    
    # Count completed sessions
    completed_sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id,
        InterviewSession.status == "completed"
    ).count()
    
    # Get average scores
    avg_overall_score = db.query(func.avg(InterviewSession.overall_score)).filter(
        InterviewSession.user_id == current_user.id,
        InterviewSession.status == "completed"
    ).scalar() or 0.0
    
    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "average_score": round(avg_overall_score, 2),
        "success_rate": round((completed_sessions / total_sessions * 100) if total_sessions > 0 else 0, 2)
    } 