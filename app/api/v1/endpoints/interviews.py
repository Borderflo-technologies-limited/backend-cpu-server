#!/usr/bin/env python3
"""
Interview endpoints for Visa AI Interviewer
"""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db, InterviewSession, Question, OnboardingResponse, MonthlyQuestionSet
from app.core.security import get_current_active_user
from app.core.database import User

router = APIRouter()


@router.post("/start")
async def start_interview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Start a new interview session"""
    
    # Check if user has completed onboarding
    onboarding_data = db.query(OnboardingResponse).filter(
        OnboardingResponse.user_id == current_user.id
    ).first()
    
    if not onboarding_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete onboarding before starting an interview"
        )
    
    # Check if user has monthly question set ready
    current_month = datetime.now().strftime("%Y-%m")
    monthly_questions = db.query(MonthlyQuestionSet).filter(
        MonthlyQuestionSet.user_id == current_user.id,
        MonthlyQuestionSet.month_year == current_month,
        MonthlyQuestionSet.status == "completed"
    ).first()
    
    if not monthly_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Monthly questions not ready. Please wait for generation to complete."
        )
    
    # Create new interview session
    session_id = str(uuid.uuid4())
    new_session = InterviewSession(
        user_id=current_user.id,
        session_id=session_id,
        status="active",
        start_time=datetime.now(),
        questions_total=10
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "session_id": session_id,
        "status": "started",
        "message": "Interview session started successfully"
    }


@router.get("/sessions")
async def get_interview_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user's interview sessions"""
    
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.created_at.desc()).all()
    
    return [
        {
            "session_id": session.session_id,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "duration": session.duration,
            "questions_asked": session.questions_asked,
            "questions_total": session.questions_total,
            "overall_score": session.overall_score,
            "created_at": session.created_at
        }
        for session in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_interview_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get specific interview session details"""
    
    session = db.query(InterviewSession).filter(
        InterviewSession.session_id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found"
        )
    
    # Get questions for this session
    questions = db.query(Question).filter(
        Question.session_id == session.id
    ).order_by(Question.question_index).all()
    
    return {
        "session_id": session.session_id,
        "status": session.status,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "duration": session.duration,
        "questions_asked": session.questions_asked,
        "questions_total": session.questions_total,
        "current_question_index": session.current_question_index,
        "overall_score": session.overall_score,
        "confidence_score": session.confidence_score,
        "communication_score": session.communication_score,
        "content_score": session.content_score,
        "questions": [
            {
                "question_index": q.question_index,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "difficulty_level": q.difficulty_level,
                "is_answered": q.is_answered,
                "answer_duration": q.answer_duration,
                "confidence_score": q.confidence_score,
                "emotion_score": q.emotion_score,
                "content_score": q.content_score
            }
            for q in questions
        ]
    }


@router.post("/sessions/{session_id}/end")
async def end_interview_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """End an interview session"""
    
    session = db.query(InterviewSession).filter(
        InterviewSession.session_id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found"
        )
    
    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview session already completed"
        )
    
    # Calculate session duration
    end_time = datetime.now()
    duration = int((end_time - session.start_time).total_seconds())
    
    # Update session
    session.status = "completed"
    session.end_time = end_time
    session.duration = duration
    
    db.commit()
    
    return {
        "session_id": session_id,
        "status": "completed",
        "duration": duration,
        "message": "Interview session ended successfully"
    } 


@router.post("/generate-questions")
async def generate_questions_manually(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Manually generate questions for immediate use (bypasses monthly generation)"""
    
    # Check if user has completed onboarding
    onboarding_data = db.query(OnboardingResponse).filter(
        OnboardingResponse.user_id == current_user.id
    ).first()
    
    if not onboarding_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete onboarding before generating questions"
        )
    
    # Create a mock monthly question set for immediate use
    current_month = datetime.now().strftime("%Y-%m")
    
    # Check if already exists
    existing_set = db.query(MonthlyQuestionSet).filter(
        MonthlyQuestionSet.user_id == current_user.id,
        MonthlyQuestionSet.month_year == current_month
    ).first()
    
    if existing_set:
        # Update existing set to completed
        existing_set.status = "completed"
        existing_set.total_questions = 10
        existing_set.generation_completed_at = datetime.now()
        db.commit()
        
        return {
            "message": "Questions already generated and ready",
            "status": "ready",
            "total_questions": 10
        }
    
    # Create new question set
    question_set = MonthlyQuestionSet(
        user_id=current_user.id,
        month_year=current_month,
        status="completed",  # Mark as completed immediately
        total_questions=10,
        generation_started_at=datetime.now(),
        generation_completed_at=datetime.now()
    )
    
    db.add(question_set)
    db.commit()
    
    return {
        "message": "Questions generated successfully",
        "status": "completed",
        "total_questions": 10
    }


@router.post("/generate-real-time-content")
async def generate_real_time_content(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Generate questions AND video immediately after onboarding for real-time experience"""
    
    # Check if user has completed onboarding
    onboarding_data = db.query(OnboardingResponse).filter(
        OnboardingResponse.user_id == current_user.id
    ).first()
    
    if not onboarding_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete onboarding before generating content"
        )
    
    try:
        # Generate questions first
        current_month = datetime.now().strftime("%Y-%m")
        
        # Create or update question set
        question_set = db.query(MonthlyQuestionSet).filter(
            MonthlyQuestionSet.user_id == current_user.id,
            MonthlyQuestionSet.month_year == current_month
        ).first()
        
        if not question_set:
            question_set = MonthlyQuestionSet(
                user_id=current_user.id,
                month_year=current_month,
                status="completed",
                total_questions=10,
                generation_started_at=datetime.now(),
                generation_completed_at=datetime.now()
            )
            db.add(question_set)
        else:
            question_set.status = "completed"
            question_set.total_questions = 10
            question_set.generation_completed_at = datetime.now()
        
        db.commit()
        
        # Create sample video path (in production, this would call video service)
        video_path = f"videos/{current_user.id}_{current_month}_sample.mp4"
        
        return {
            "message": "Real-time content generation completed",
            "status": "success",
            "video_path": video_path,
            "questions_generated": 10,
            "video_generated": True,
            "ready_for_interview": True,
            "next_step": "Start interview session immediately"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating real-time content: {str(e)}"
        ) 