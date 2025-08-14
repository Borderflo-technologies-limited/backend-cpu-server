#!/usr/bin/env python3
"""
Main API router for Visa AI Interviewer
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, onboarding, interviews, files, gpu

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(gpu.router, prefix="/gpu", tags=["gpu"]) 