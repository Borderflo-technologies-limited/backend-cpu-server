#!/usr/bin/env python3
"""
GPU Communication Service
Handles communication with Video Generation and Evaluation Agent services
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
import aiohttp
import aiofiles
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

class GPUCommunicationService:
    """Service for communicating with GPU servers"""
    
    def __init__(self):
        self.video_service_url = f"http://{settings.VIDEO_SERVICE_HOST}:{settings.VIDEO_SERVICE_PORT}"
        self.evaluation_service_url = f"http://{settings.EVALUATION_SERVICE_HOST}:{settings.EVALUATION_SERVICE_PORT}"
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
        
    async def check_gpu_services_health(self) -> Dict[str, Any]:
        """Check health of both GPU services"""
        results = {
            "video_generation": await self._check_service_health(f"{self.video_service_url}/health"),
            "evaluation_agent": await self._check_service_health(f"{self.evaluation_service_url}/health")
        }
        
        all_healthy = all(result["healthy"] for result in results.values())
        
        return {
            "all_services_healthy": all_healthy,
            "services": results
        }
    
    async def _check_service_health(self, health_url: str) -> Dict[str, Any]:
        """Check health of a single service"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(health_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "healthy": True,
                            "status": data.get("status", "unknown"),
                            "details": data
                        }
                    else:
                        return {
                            "healthy": False,
                            "status": f"HTTP {response.status}",
                            "error": f"Service returned status {response.status}"
                        }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    async def generate_video(self, audio_path: str, face_path: str, session_id: str = None, question_id: str = None) -> Dict[str, Any]:
        """
        Request video generation from Video Generation Service
        
        Args:
            audio_path: Path to audio file
            face_path: Path to face image/video file
            session_id: Optional session identifier
            question_id: Optional question identifier
            
        Returns:
            Video generation result
        """
        try:
            logger.info(f"Requesting video generation for session {session_id}")
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            
            # Add audio file
            async with aiofiles.open(audio_path, 'rb') as f:
                audio_data = await f.read()
                data.add_field('audio_file', audio_data, 
                              filename=os.path.basename(audio_path),
                              content_type='audio/wav')
            
            # Add face file
            async with aiofiles.open(face_path, 'rb') as f:
                face_data = await f.read()
                face_filename = os.path.basename(face_path)
                content_type = self._get_content_type(face_filename)
                data.add_field('face_file', face_data,
                              filename=face_filename,
                              content_type=content_type)
            
            # Add optional parameters
            if session_id:
                data.add_field('session_id', session_id)
            if question_id:
                data.add_field('question_id', question_id)
            
            # Make request to video generation service
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(f"{self.video_service_url}/generate-video", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Video generation completed: {result.get('task_id')}")
                        return {
                            "success": True,
                            "result": result
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Video generation failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Video service error: {response.status}",
                            "details": error_text
                        }
                        
        except Exception as e:
            logger.error(f"Video generation request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_video(self, video_filename: str, local_path: str) -> Dict[str, Any]:
        """
        Download generated video from Video Generation Service
        
        Args:
            video_filename: Filename of the generated video
            local_path: Local path to save the video
            
        Returns:
            Download result
        """
        try:
            download_url = f"{self.video_service_url}/download/{video_filename}"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)
                        
                        # Save file
                        async with aiofiles.open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        file_size = os.path.getsize(local_path)
                        logger.info(f"Downloaded video {video_filename} ({file_size} bytes)")
                        
                        return {
                            "success": True,
                            "local_path": local_path,
                            "file_size": file_size
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Download failed: HTTP {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"Video download failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def evaluate_interview(self, video_path: str, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request interview evaluation from Evaluation Agent Service
        
        Args:
            video_path: Path to interview video
            evaluation_data: Additional evaluation context
            
        Returns:
            Evaluation result
        """
        try:
            logger.info(f"Requesting interview evaluation for video: {video_path}")
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            
            # Add video file
            async with aiofiles.open(video_path, 'rb') as f:
                video_data = await f.read()
                data.add_field('video_file', video_data,
                              filename=os.path.basename(video_path),
                              content_type='video/mp4')
            
            # Add evaluation context as JSON
            data.add_field('evaluation_data', 
                          str(evaluation_data),  # Convert to string for form data
                          content_type='application/json')
            
            # Make request to evaluation service
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(f"{self.evaluation_service_url}/evaluate", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("Interview evaluation completed successfully")
                        return {
                            "success": True,
                            "result": result
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Evaluation failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Evaluation service error: {response.status}",
                            "details": error_text
                        }
                        
        except Exception as e:
            logger.error(f"Interview evaluation request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_gpu_files(self, task_ids: list) -> Dict[str, Any]:
        """Clean up temporary files on GPU services"""
        results = {
            "video_cleanup": [],
            "evaluation_cleanup": []
        }
        
        # Cleanup video generation files
        for task_id in task_ids:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.delete(f"{self.video_service_url}/cleanup/{task_id}") as response:
                        if response.status == 200:
                            result = await response.json()
                            results["video_cleanup"].append({
                                "task_id": task_id,
                                "success": True,
                                "result": result
                            })
                        else:
                            results["video_cleanup"].append({
                                "task_id": task_id,
                                "success": False,
                                "error": f"HTTP {response.status}"
                            })
            except Exception as e:
                results["video_cleanup"].append({
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.mp4': 'video/mp4',
            '.avi': 'video/avi',
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg'
        }
        return content_types.get(ext, 'application/octet-stream')

# Global instance
gpu_comm = GPUCommunicationService()