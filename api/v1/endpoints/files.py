#!/usr/bin/env python3
"""
File management endpoints for Visa AI Interviewer
"""

import os
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db, FileMetadata
from app.core.security import get_current_active_user
from app.core.config import settings
from app.core.database import User

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = "document",
    session_id: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Upload a file"""
    
    # Validate file type
    allowed_types = ["audio", "video", "image", "document"]
    if file_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Create storage directory if it doesn't exist
    storage_path = settings.LOCAL_STORAGE_PATH
    os.makedirs(storage_path, exist_ok=True)
    
    # Save file
    file_path = os.path.join(storage_path, f"{file_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create file metadata
    file_metadata = FileMetadata(
        file_id=file_id,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=file_type,
        mime_type=file.content_type,
        user_id=current_user.id,
        session_id=session_id,
        storage_type="local"
    )
    
    db.add(file_metadata)
    db.commit()
    db.refresh(file_metadata)
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "status": "uploaded"
    }


@router.get("/files")
async def get_user_files(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user's files"""
    
    files = db.query(FileMetadata).filter(
        FileMetadata.user_id == current_user.id
    ).order_by(FileMetadata.created_at.desc()).all()
    
    return [
        {
            "file_id": file.file_id,
            "original_filename": file.original_filename,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "mime_type": file.mime_type,
            "processing_status": file.processing_status,
            "storage_url": file.storage_url,
            "created_at": file.created_at
        }
        for file in files
    ]


@router.get("/files/{file_id}")
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get specific file information"""
    
    file_metadata = db.query(FileMetadata).filter(
        FileMetadata.file_id == file_id,
        FileMetadata.user_id == current_user.id
    ).first()
    
    if not file_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return {
        "file_id": file_metadata.file_id,
        "original_filename": file_metadata.original_filename,
        "file_type": file_metadata.file_type,
        "file_size": file_metadata.file_size,
        "mime_type": file_metadata.mime_type,
        "processing_status": file_metadata.processing_status,
        "processing_error": file_metadata.processing_error,
        "storage_url": file_metadata.storage_url,
        "created_at": file_metadata.created_at
    }


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a file"""
    
    file_metadata = db.query(FileMetadata).filter(
        FileMetadata.file_id == file_id,
        FileMetadata.user_id == current_user.id
    ).first()
    
    if not file_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Delete physical file
    if os.path.exists(file_metadata.file_path):
        os.remove(file_metadata.file_path)
    
    # Delete database record
    db.delete(file_metadata)
    db.commit()
    
    return {
        "file_id": file_id,
        "status": "deleted",
        "message": "File deleted successfully"
    } 