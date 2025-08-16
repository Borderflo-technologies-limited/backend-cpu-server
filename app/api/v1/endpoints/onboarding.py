#!/usr/bin/env python3
"""
Onboarding endpoints for Visa AI Interviewer
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db, OnboardingResponse
from app.core.security import get_current_active_user
from app.core.database import User

router = APIRouter()


class OnboardingData(BaseModel):
    """Onboarding questionnaire data model"""
    visa_type: str
    destination_country: str
    travel_purpose: str
    previous_travels: Optional[str] = None
    education_level: Optional[str] = None
    employment_status: Optional[str] = None
    preferred_interview_duration: int = 30
    preferred_question_difficulty: str = "medium"
    preferred_interview_style: str = "formal"
    special_requirements: Optional[str] = None
    language_preference: str = "english"


@router.post("/submit")
async def submit_onboarding(
    onboarding_data: OnboardingData,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Submit onboarding questionnaire responses"""
    
    # Check if user already has onboarding data
    existing_onboarding = db.query(OnboardingResponse).filter(
        OnboardingResponse.user_id == current_user.id
    ).first()
    
    if existing_onboarding:
        # Update existing onboarding data
        existing_onboarding.visa_type = onboarding_data.visa_type
        existing_onboarding.destination_country = onboarding_data.destination_country
        existing_onboarding.travel_purpose = onboarding_data.travel_purpose
        existing_onboarding.previous_travels = onboarding_data.previous_travels
        existing_onboarding.education_level = onboarding_data.education_level
        existing_onboarding.employment_status = onboarding_data.employment_status
        existing_onboarding.preferred_interview_duration = onboarding_data.preferred_interview_duration
        existing_onboarding.preferred_question_difficulty = onboarding_data.preferred_question_difficulty
        existing_onboarding.preferred_interview_style = onboarding_data.preferred_interview_style
        existing_onboarding.special_requirements = onboarding_data.special_requirements
        existing_onboarding.language_preference = onboarding_data.language_preference
        
        db.commit()
        db.refresh(existing_onboarding)
        
        return {
            "message": "Onboarding data updated successfully",
            "status": "updated"
        }
    else:
        # Create new onboarding data
        new_onboarding = OnboardingResponse(
            user_id=current_user.id,
            visa_type=onboarding_data.visa_type,
            destination_country=onboarding_data.destination_country,
            travel_purpose=onboarding_data.travel_purpose,
            previous_travels=onboarding_data.previous_travels,
            education_level=onboarding_data.education_level,
            employment_status=onboarding_data.employment_status,
            preferred_interview_duration=onboarding_data.preferred_interview_duration,
            preferred_question_difficulty=onboarding_data.preferred_question_difficulty,
            preferred_interview_style=onboarding_data.preferred_interview_style,
            special_requirements=onboarding_data.special_requirements,
            language_preference=onboarding_data.language_preference
        )
        
        db.add(new_onboarding)
        db.commit()
        db.refresh(new_onboarding)
        
        return {
            "message": "Onboarding data submitted successfully",
            "status": "created"
        }


@router.get("/data")
async def get_onboarding_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user's onboarding data"""
    
    onboarding_data = db.query(OnboardingResponse).filter(
        OnboardingResponse.user_id == current_user.id
    ).first()
    
    if not onboarding_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding data not found"
        )
    
    return {
        "visa_type": onboarding_data.visa_type,
        "destination_country": onboarding_data.destination_country,
        "travel_purpose": onboarding_data.travel_purpose,
        "previous_travels": onboarding_data.previous_travels,
        "education_level": onboarding_data.education_level,
        "employment_status": onboarding_data.employment_status,
        "preferred_interview_duration": onboarding_data.preferred_interview_duration,
        "preferred_question_difficulty": onboarding_data.preferred_question_difficulty,
        "preferred_interview_style": onboarding_data.preferred_interview_style,
        "special_requirements": onboarding_data.special_requirements,
        "language_preference": onboarding_data.language_preference
    }


@router.get("/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Check if user has completed onboarding"""
    
    onboarding_data = db.query(OnboardingResponse).filter(
        OnboardingResponse.user_id == current_user.id
    ).first()
    
    return {
        "completed": onboarding_data is not None,
        "can_start_interview": onboarding_data is not None
    } 