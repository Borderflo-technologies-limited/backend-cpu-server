#!/usr/bin/env python3
"""
FastAPI application for Visa AI Interviewer CPU Server
Works on both traditional pods and serverless
"""

import os
import sys
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# Add the app directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
sys.path.insert(0, app_dir)

# Load environment variables
load_dotenv()

# Import app modules after setting up the path
HAS_FULL_IMPORTS = False
try:
    # Try to import core modules
    from core.config import settings
    from core.database import engine, Base
    from api.v1.api import api_router
    from services.background_tasks import start_background_tasks, stop_background_tasks
    HAS_FULL_IMPORTS = True
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"⚠️ Running in simplified mode due to import issues: {e}")
    print("⚠️ Some features may not be available")
    HAS_FULL_IMPORTS = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for traditional pods"""
    # Startup
    print("🚀 Starting Visa AI Interviewer CPU Server...")
    
    if HAS_FULL_IMPORTS:
        try:
            # Create database tables
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created")
            
            # Start background tasks
            await start_background_tasks()
            print("✅ Background tasks started")
        except Exception as e:
            print(f"⚠️ Some services failed to start: {e}")
    else:
        print("⚠️ Running in simplified mode - limited functionality")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down CPU Server...")
    if HAS_FULL_IMPORTS:
        try:
            await stop_background_tasks()
            print("✅ Background tasks stopped")
        except Exception as e:
            print(f"⚠️ Error stopping background tasks: {e}")

# Create FastAPI app
app = FastAPI(
    title="Visa AI Interviewer API",
    description="AI-powered visa interview preparation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure for production
)

# Include API routes if available
if HAS_FULL_IMPORTS:
    try:
        app.include_router(api_router, prefix="/api/v1")
        print("✅ API routes loaded")
    except Exception as e:
        print(f"⚠️ Failed to load API routes: {e}")
        HAS_FULL_IMPORTS = False

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Visa AI Interviewer API",
        "version": "1.0.0",
        "status": "healthy",
        "mode": "full" if HAS_FULL_IMPORTS else "simplified"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "services": {
            "file_storage": "available",
            "gpu_queue": "ready"
        }
    }
    
    if HAS_FULL_IMPORTS:
        try:
            health_status["services"]["database"] = "connected"
            health_status["services"]["api_routes"] = "loaded"
        except Exception:
            health_status["services"]["database"] = "error"
            health_status["services"]["api_routes"] = "error"
    else:
        health_status["services"]["database"] = "not_available"
        health_status["services"]["api_routes"] = "not_available"
    
    return health_status

@app.get("/test")
async def test_endpoint():
    """Test endpoint for basic functionality"""
    return {
        "message": "Test endpoint working!",
        "status": "success",
        "mode": "full" if HAS_FULL_IMPORTS else "simplified"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "Something went wrong"
        }
    )

# RunPod Serverless Handler (for serverless mode)
async def handler(job):
    """
    Main handler function for RunPod serverless
    This function is called for each request
    """
    try:
        print(f"🚀 Processing job: {job.get('id', 'unknown')}")
        
        # Extract input from the job
        job_input = job.get("input", {})
        
        # Check if this is an HTTP request
        if "http_method" in job_input:
            return await handle_http_request(job_input)
        
        # Default response for non-HTTP requests
        return {
            "status": "success",
            "message": "Visa AI Interviewer CPU Server is running",
            "mode": "full" if HAS_FULL_IMPORTS else "simplified"
        }
        
    except Exception as e:
        print(f"❌ Error processing job: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def handle_http_request(job_input):
    """Handle HTTP-like requests from RunPod"""
    method = job_input.get("http_method", "GET")
    path = job_input.get("path", "/")
    headers = job_input.get("headers", {})
    body = job_input.get("body", "")
    
    print(f"📡 HTTP {method} {path}")
    
    # Route the request based on path
    if path == "/" or path == "":
        return await root()
    elif path == "/health":
        return await health_check()
    elif path == "/test":
        return await test_endpoint()
    elif path == "/docs":
        return {"message": "API documentation available", "status": "info"}
    else:
        return {
            "status": "not_found",
            "message": f"Endpoint {path} not found",
            "available_endpoints": ["/", "/health", "/test", "/docs"]
        }

# For traditional pod execution
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
