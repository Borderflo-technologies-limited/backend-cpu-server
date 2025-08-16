#!/usr/bin/env python3
"""
Database configuration and models for Visa AI Interviewer
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    onboarding_responses = relationship("OnboardingResponse", back_populates="user")
    interview_sessions = relationship("InterviewSession", back_populates="user")
    monthly_question_sets = relationship("MonthlyQuestionSet", back_populates="user")


class OnboardingResponse(Base):
    """Onboarding questionnaire responses"""
    __tablename__ = "onboarding_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Personal Information
    visa_type = Column(String, nullable=False)
    destination_country = Column(String, nullable=False)
    travel_purpose = Column(String, nullable=False)
    previous_travels = Column(Text)
    education_level = Column(String)
    employment_status = Column(String)
    
    # Interview Preferences
    preferred_interview_duration = Column(Integer, default=30)  # minutes
    preferred_question_difficulty = Column(String, default="medium")
    preferred_interview_style = Column(String, default="formal")
    
    # Additional Information
    special_requirements = Column(Text)
    language_preference = Column(String, default="english")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="onboarding_responses")


class InterviewSession(Base):
    """Interview session model"""
    __tablename__ = "interview_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    
    # Session Details
    status = Column(String, default="pending")  # pending, active, completed, failed
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Integer)  # seconds
    
    # Session Data
    questions_asked = Column(Integer, default=0)
    questions_total = Column(Integer, default=10)
    current_question_index = Column(Integer, default=0)
    
    # Evaluation Results
    overall_score = Column(Float)
    confidence_score = Column(Float)
    communication_score = Column(Float)
    content_score = Column(Float)
    
    # Files
    audio_file_path = Column(String)
    video_file_path = Column(String)
    evaluation_report_path = Column(String)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="interview_sessions")
    questions = relationship("Question", back_populates="session")


class Question(Base):
    """Individual question in an interview session"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question_index = Column(Integer, nullable=False)
    
    # Question Content
    question_text = Column(Text, nullable=False)
    question_type = Column(String, default="general")  # general, personal, technical
    difficulty_level = Column(String, default="medium")
    
    # User Response
    user_response = Column(Text)
    response_audio_path = Column(String)
    response_video_path = Column(String)
    
    # Evaluation
    is_answered = Column(Boolean, default=False)
    answer_duration = Column(Integer)  # seconds
    confidence_score = Column(Float)
    emotion_score = Column(Float)
    content_score = Column(Float)
    
    # Timing
    asked_at = Column(DateTime)
    answered_at = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    session = relationship("InterviewSession", back_populates="questions")


class MonthlyQuestionSet(Base):
    """Pre-generated monthly question sets for users"""
    __tablename__ = "monthly_question_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    month_year = Column(String, nullable=False)  # format: "2024-01"
    
    # Generation Status
    status = Column(String, default="generating")  # generating, completed, failed
    total_questions = Column(Integer, default=0)
    generated_questions = Column(Integer, default=0)
    
    # Content
    questions_data = Column(Text)  # JSON string of questions
    audio_files_generated = Column(Boolean, default=False)
    video_files_generated = Column(Boolean, default=False)
    
    # Metadata
    generation_started_at = Column(DateTime)
    generation_completed_at = Column(DateTime)
    last_accessed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="monthly_question_sets")


class FileMetadata(Base):
    """File storage metadata"""
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    file_type = Column(String, nullable=False)  # audio, video, image, document
    mime_type = Column(String)
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    
    # Processing Status
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text)
    
    # Storage
    storage_type = Column(String, default="local")  # local, b2, cloudinary
    storage_url = Column(String)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class GPUProcessingQueue(Base):
    """Queue for GPU processing tasks"""
    __tablename__ = "gpu_processing_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)
    task_type = Column(String, nullable=False)  # video_generation, evaluation
    
    # Task Details
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    
    # Input/Output
    input_file_path = Column(String)
    output_file_path = Column(String)
    parameters = Column(Text)  # JSON string of processing parameters
    
    # Status
    status = Column(String, default="queued")  # queued, processing, completed, failed
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high
    
    # GPU Server
    gpu_server_id = Column(String)
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    processing_error = Column(Text)
    
    # Cost tracking
    gpu_cost = Column(Float, default=0.0)
    processing_duration = Column(Integer)  # seconds
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# Database dependency
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 