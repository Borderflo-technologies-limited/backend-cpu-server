
"""
GPU Queue Manager - Handles requests to GPU servers
Queues requests and triggers RunPod auto-scaling
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import redis
from sqlalchemy.orm import Session
from app.core.database import get_db
from .runpod_manager import RunPodManager

class TaskType(Enum):
    VIDEO_GENERATION = "video_generation"
    EVALUATION = "evaluation"

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class GPUQueueManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.runpod_manager = RunPodManager()
        self.scaling_enabled = True
        
    async def queue_video_generation(self, audio_data: bytes, session_id: str) -> str:
        """Queue video generation task"""
        task_id = f"video_{session_id}_{datetime.now().timestamp()}"
        
        task_data = {
            "task_id": task_id,
            "type": TaskType.VIDEO_GENERATION.value,
            "session_id": session_id,
            "audio_data": audio_data.hex(),  # Convert bytes to hex string
            "created_at": datetime.now().isoformat(),
            "status": TaskStatus.PENDING.value,
            "priority": "high"
        }
        
        # Add to Redis queue
        self.redis_client.lpush("video_generation_queue", json.dumps(task_data))
        
        # Trigger scaling check
        await self.check_scaling_needs(TaskType.VIDEO_GENERATION)
        
        return task_id
    
    async def queue_evaluation(self, video_data: bytes, session_id: str, question_id: str) -> str:
        """Queue evaluation task"""
        task_id = f"eval_{session_id}_{question_id}_{datetime.now().timestamp()}"
        
        task_data = {
            "task_id": task_id,
            "type": TaskType.EVALUATION.value,
            "session_id": session_id,
            "question_id": question_id,
            "video_data": video_data.hex(),  # Convert bytes to hex string
            "created_at": datetime.now().isoformat(),
            "status": TaskStatus.PENDING.value,
            "priority": "medium"
        }
        
        # Add to Redis queue
        self.redis_client.lpush("evaluation_queue", json.dumps(task_data))
        
        # Trigger scaling check
        await self.check_scaling_needs(TaskType.EVALUATION)
        
        return task_id
    
    async def check_scaling_needs(self, task_type: TaskType):
        """Check if GPU servers need to be scaled up"""
        if not self.scaling_enabled:
            return
            
        queue_name = f"{task_type.value}_queue"
        queue_length = self.redis_client.llen(queue_name)
        
        # Get current GPU server status
        if task_type == TaskType.VIDEO_GENERATION:
            server_status = await self.runpod_manager.get_video_server_status()
            threshold = 1  # Start after 1 request
        else:
            server_status = await self.runpod_manager.get_eval_server_status()
            threshold = 2  # Start after 2 requests
        
        # Scale up if needed
        if queue_length >= threshold and server_status == "stopped":
            await self.runpod_manager.start_gpu_server(task_type)
    
    async def get_task_status(self, task_id: str) -> Dict:
        """Get task status from queue or completed tasks"""
        # Check completed tasks first
        completed_task = self.redis_client.get(f"completed_{task_id}")
        if completed_task:
            return json.loads(completed_task)
        
        # Check pending queues
        for queue_name in ["video_generation_queue", "evaluation_queue"]:
            queue_items = self.redis_client.lrange(queue_name, 0, -1)
            for item in queue_items:
                task_data = json.loads(item)
                if task_data["task_id"] == task_id:
                    return task_data
        
        return {"error": "Task not found"}
    
    async def mark_task_completed(self, task_id: str, result: Dict):
        """Mark task as completed and store result"""
        result_data = {
            "task_id": task_id,
            "status": TaskStatus.COMPLETED.value,
            "result": result,
            "completed_at": datetime.now().isoformat()
        }
        
        # Store completed task (expire after 24 hours)
        self.redis_client.setex(
            f"completed_{task_id}", 
            86400,  # 24 hours
            json.dumps(result_data)
        )
    
    async def process_queue(self):
        """Process GPU queue (simplified for testing)"""
        # For now, just log that we're processing
        print("Processing GPU queue...")
        await asyncio.sleep(1)  # Simulate processing time
