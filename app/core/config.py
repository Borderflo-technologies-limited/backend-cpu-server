#!/usr/bin/env python3
"""
Configuration settings for Visa AI Interviewer CPU Server
"""

from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "sqlite:///./visa_ai_interviewer.db"
    
    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Storage
    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_PATH: str = "./local_storage"
    
    # GPU Server Communication (defaults for local docker-compose)
    GPU_SERVER_BASE_URL: str = os.getenv("GPU_SERVER_BASE_URL", "https://dyet7q0rq0ntg9-8000.proxy.runpod.net")
    VIDEO_GENERATION_URL: str = os.getenv("VIDEO_GENERATION_URL", "https://hjwymndlz5f4xe-8001.proxy.runpod.net")
    EVALUATION_AGENT_URL: str = os.getenv("EVALUATION_AGENT_URL", "https://ft5vi4h6gxqku8-8002.proxy.runpod.net")
    
    # RunPod Configuration
    RUNPOD_API_KEY: str = ""
    RUNPOD_ENDPOINT_ID: str = ""
    RUNPOD_API_URL: str = "https://api.runpod.io/v2"
    
    # Auto-scaling Settings
    MIN_GPU_INSTANCES: int = 0
    MAX_GPU_INSTANCES: int = 2
    SCALE_UP_THRESHOLD: int = 3
    SCALE_DOWN_THRESHOLD: int = 1
    MAX_COST_PER_HOUR: float = 2.0
    
    # Background Processing
    REDIS_URL: str = "redis://localhost:6379"
    QUEUE_NAME: str = "gpu_processing_queue"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000"
    ]
    
    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Interview Settings
    MAX_INTERVIEW_DURATION: int = 1800  # 30 minutes
    QUESTIONS_PER_SESSION: int = 10
    PRE_GENERATION_ENABLED: bool = True
    
    # AI Service Configuration
    GROQ_API_KEY: str = ""
    
    # Audio/Video Storage
    AUDIO_STORAGE_PATH: str = "storage/audio"
    VIDEO_STORAGE_PATH: str = "storage/videos"
    
    # GPU Service URLs - Use environment variables for RunPod deployment
    # Default to actual RunPod URLs, but allow environment override
    VIDEO_SERVICE_HOST: str = os.getenv("VIDEO_SERVICE_HOST", "hjwymndlz5f4xe-8001.proxy.runpod.net")
    EVALUATION_SERVICE_HOST: str = os.getenv("EVALUATION_SERVICE_HOST", "ft5vi4h6gxqku8-8002.proxy.runpod.net")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()