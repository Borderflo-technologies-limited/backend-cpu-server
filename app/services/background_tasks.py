#!/usr/bin/env python3
"""
Background tasks for Visa AI Interviewer
Handles GPU queue management and monthly content generation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.database import User, MonthlyQuestionSet, GPUProcessingQueue, OnboardingResponse
from app.services.gpu_queue_manager import GPUQueueManager
from app.services.auto_scaler import AutoScaler
from app.services.interview_agent import interview_agent
from app.services.gpu_communication import gpu_comm

logger = logging.getLogger(__name__)

# Global task references
queue_manager: Optional[GPUQueueManager] = None
auto_scaler: Optional[AutoScaler] = None


async def start_background_tasks():
    """Start all background tasks"""
    global queue_manager, auto_scaler
    
    logger.info("Starting background tasks...")
    
    # Initialize GPU queue manager
    queue_manager = GPUQueueManager()
    
    # Initialize auto-scaler
    auto_scaler = AutoScaler()
    
    # Start task loops
    asyncio.create_task(monthly_content_generation_loop())
    asyncio.create_task(gpu_queue_processing_loop())
    asyncio.create_task(auto_scaling_loop())
    
    logger.info("Background tasks started successfully")


async def stop_background_tasks():
    """Stop all background tasks"""
    global queue_manager, auto_scaler
    
    logger.info("Stopping background tasks...")
    
    if queue_manager:
        # Clean up queue manager if needed
        pass
    
    if auto_scaler:
        # Clean up auto scaler if needed
        pass
    
    logger.info("Background tasks stopped")


async def monthly_content_generation_loop():
    """Background loop for generating monthly content"""
    while True:
        try:
            await generate_monthly_content()
            # Run every hour
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error in monthly content generation: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error


async def generate_monthly_content():
    """Generate monthly question sets for users who need them"""
    db = SessionLocal()
    try:
        # Find users who need monthly content generation
        current_month = datetime.now().strftime("%Y-%m")
        
        # Get users without current month's question set
        users_needing_content = db.query(User).filter(
            ~User.monthly_question_sets.any(
                MonthlyQuestionSet.month_year == current_month
            )
        ).all()
        
        for user in users_needing_content:
            await generate_user_monthly_content(user.id, current_month, db)
            
    except Exception as e:
        logger.error(f"Error generating monthly content: {e}")
    finally:
        db.close()


async def generate_user_monthly_content(user_id: int, month_year: str, db: Session):
    """Generate monthly content for a specific user"""
    question_set = None
    try:
        # Get user data for context
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return
        
        # Get user onboarding data
        onboarding = db.query(OnboardingResponse).filter(OnboardingResponse.user_id == user_id).first()
        user_data = {}
        if onboarding:
            user_data = {
                "visa_type": onboarding.visa_type,
                "purpose_of_visit": onboarding.purpose_of_visit,
                "country_of_residence": onboarding.country_of_residence,
                "occupation": onboarding.occupation,
                "education_level": onboarding.education_level
            }
        
        # Create monthly question set
        question_set = MonthlyQuestionSet(
            user_id=user_id,
            month_year=month_year,
            status="generating",
            generation_started_at=datetime.now()
        )
        db.add(question_set)
        db.commit()
        db.refresh(question_set)
        
        logger.info(f"Starting monthly content generation for user {user_id}")
        
        # Generate questions and audio using Interview Agent
        generation_result = await interview_agent.process_monthly_generation(user_id, user_data)
        
        if generation_result["success"]:
            # Update status
            question_set.status = "completed"
            question_set.generation_completed_at = datetime.now()
            question_set.total_questions = generation_result["questions_generated"]
            question_set.audio_generated = True
            db.commit()
            
            logger.info(f"Generated monthly content for user {user_id}: {generation_result['questions_generated']} questions")
        else:
            # Mark as failed
            question_set.status = "failed"
            question_set.error_message = generation_result.get("error", "Unknown error")
            db.commit()
            logger.error(f"Failed to generate content for user {user_id}: {generation_result.get('error')}")
        
    except Exception as e:
        logger.error(f"Error generating content for user {user_id}: {e}")
        if question_set:
            question_set.status = "failed"
            question_set.error_message = str(e)
            db.commit()


async def gpu_queue_processing_loop():
    """Background loop for processing GPU queue"""
    while True:
        try:
            if queue_manager:
                await queue_manager.process_queue()
            await asyncio.sleep(10)  # Check every 10 seconds
        except Exception as e:
            logger.error(f"Error in GPU queue processing: {e}")
            await asyncio.sleep(30)


async def auto_scaling_loop():
    """Background loop for auto-scaling GPU instances"""
    while True:
        try:
            if auto_scaler:
                await auto_scaler.check_and_scale()
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in auto-scaling: {e}")
            await asyncio.sleep(300)


async def queue_gpu_task(
    task_type: str,
    user_id: int,
    input_file_path: str,
    parameters: dict,
    priority: int = 1,
    session_id: Optional[int] = None,
    question_id: Optional[int] = None
) -> str:
    """Queue a task for GPU processing"""
    if not queue_manager:
        raise RuntimeError("GPU queue manager not initialized")
    
    return await queue_manager.add_task(
        task_type=task_type,
        user_id=user_id,
        input_file_path=input_file_path,
        parameters=parameters,
        priority=priority,
        session_id=session_id,
        question_id=question_id
    )


async def get_gpu_task_status(task_id: str) -> dict:
    """Get status of a GPU processing task"""
    if not queue_manager:
        raise RuntimeError("GPU queue manager not initialized")
    
    return await queue_manager.get_task_status(task_id)
