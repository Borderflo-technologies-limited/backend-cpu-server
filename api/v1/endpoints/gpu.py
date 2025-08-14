#!/usr/bin/env python3
"""
GPU processing endpoints for Visa AI Interviewer
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db, GPUProcessingQueue, FileMetadata
from app.core.security import get_current_active_user
from app.services.background_tasks import queue_gpu_task, get_gpu_task_status
from app.core.database import User

router = APIRouter()


@router.post("/queue/video-generation")
async def queue_video_generation(
    input_file_id: str,
    parameters: dict,
    priority: int = 1,
    session_id: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Queue a video generation task"""
    
    # Get file metadata
    file_metadata = db.query(FileMetadata).filter(
        FileMetadata.file_id == input_file_id,
        FileMetadata.user_id == current_user.id
    ).first()
    
    if not file_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Input file not found"
        )
    
    # Queue the task
    task_id = await queue_gpu_task(
        task_type="video_generation",
        user_id=current_user.id,
        input_file_path=file_metadata.file_path,
        parameters=parameters,
        priority=priority,
        session_id=session_id
    )
    
    return {
        "task_id": task_id,
        "task_type": "video_generation",
        "status": "queued",
        "message": "Video generation task queued successfully"
    }


@router.post("/queue/evaluation")
async def queue_evaluation_task(
    input_file_id: str,
    parameters: dict,
    priority: int = 1,
    session_id: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Queue an evaluation task"""
    
    # Get file metadata
    file_metadata = db.query(FileMetadata).filter(
        FileMetadata.file_id == input_file_id,
        FileMetadata.user_id == current_user.id
    ).first()
    
    if not file_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Input file not found"
        )
    
    # Queue the task
    task_id = await queue_gpu_task(
        task_type="evaluation",
        user_id=current_user.id,
        input_file_path=file_metadata.file_path,
        parameters=parameters,
        priority=priority,
        session_id=session_id
    )
    
    return {
        "task_id": task_id,
        "task_type": "evaluation",
        "status": "queued",
        "message": "Evaluation task queued successfully"
    }


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get GPU task status"""
    
    task_status = await get_gpu_task_status(task_id)
    
    if not task_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task_status


@router.get("/queue/status")
async def get_queue_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get GPU queue status for current user"""
    
    # Get user's queued tasks
    queued_tasks = db.query(GPUProcessingQueue).filter(
        GPUProcessingQueue.user_id == current_user.id,
        GPUProcessingQueue.status.in_(["queued", "processing"])
    ).order_by(GPUProcessingQueue.priority.desc(), GPUProcessingQueue.created_at.asc()).all()
    
    # Get completed tasks
    completed_tasks = db.query(GPUProcessingQueue).filter(
        GPUProcessingQueue.user_id == current_user.id,
        GPUProcessingQueue.status == "completed"
    ).order_by(GPUProcessingQueue.created_at.desc()).limit(10).all()
    
    return {
        "queued_tasks": [
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at
            }
            for task in queued_tasks
        ],
        "completed_tasks": [
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status,
                "processing_duration": task.processing_duration,
                "gpu_cost": task.gpu_cost,
                "completed_at": task.processing_completed_at
            }
            for task in completed_tasks
        ],
        "queue_length": len(queued_tasks),
        "total_completed": len(completed_tasks)
    }


@router.get("/stats")
async def get_gpu_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get GPU processing statistics"""
    
    # Get all user's GPU tasks
    all_tasks = db.query(GPUProcessingQueue).filter(
        GPUProcessingQueue.user_id == current_user.id
    ).all()
    
    # Calculate statistics
    total_tasks = len(all_tasks)
    completed_tasks = len([t for t in all_tasks if t.status == "completed"])
    failed_tasks = len([t for t in all_tasks if t.status == "failed"])
    total_cost = sum([t.gpu_cost or 0 for t in all_tasks])
    total_duration = sum([t.processing_duration or 0 for t in all_tasks])
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "success_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2),
        "total_gpu_cost": round(total_cost, 4),
        "total_processing_time": total_duration,
        "average_cost_per_task": round(total_cost / total_tasks, 4) if total_tasks > 0 else 0
    } 