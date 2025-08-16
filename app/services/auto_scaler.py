
"""
Auto Scaler - Monitors queues and manages GPU server lifecycle
Automatically starts/stops RunPod instances based on demand
"""

import asyncio
from datetime import datetime, timedelta
from .gpu_queue_manager import GPUQueueManager, TaskType
from .runpod_manager import RunPodManager

class AutoScaler:
    def __init__(self):
        self.queue_manager = GPUQueueManager()
        self.runpod_manager = RunPodManager()
        self.enabled = True
        self.cost_tracker = CostTracker()
        
        # Scaling thresholds
        self.video_scale_up_threshold = 1
        self.eval_scale_up_threshold = 2
        self.idle_timeout = 300  # 5 minutes
        
        # Track last activity
        self.last_video_activity = None
        self.last_eval_activity = None
    
    async def monitor_and_scale(self):
        """Main monitoring loop"""
        while self.enabled:
            try:
                await self.check_video_scaling()
                await self.check_eval_scaling()
                await self.check_scale_down()
                await self.update_cost_tracking()
                
                # Wait 30 seconds between checks
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"Error in auto-scaler: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def check_video_scaling(self):
        """Check if video generation needs scaling"""
        queue_length = self.queue_manager.redis_client.llen("video_generation_queue")
        server_status = await self.runpod_manager.get_video_server_status()
        
        # Scale up if needed
        if queue_length >= self.video_scale_up_threshold and server_status == "stopped":
            if await self.cost_tracker.can_start_instance():
                await self.runpod_manager.start_gpu_server(TaskType.VIDEO_GENERATION)
                self.last_video_activity = datetime.now()
        
        # Update activity if queue has items
        if queue_length > 0:
            self.last_video_activity = datetime.now()
    
    async def check_eval_scaling(self):
        """Check if evaluation needs scaling"""
        queue_length = self.queue_manager.redis_client.llen("evaluation_queue")
        server_status = await self.runpod_manager.get_eval_server_status()
        
        # Scale up if needed
        if queue_length >= self.eval_scale_up_threshold and server_status == "stopped":
            if await self.cost_tracker.can_start_instance():
                await self.runpod_manager.start_gpu_server(TaskType.EVALUATION)
                self.last_eval_activity = datetime.now()
        
        # Update activity if queue has items
        if queue_length > 0:
            self.last_eval_activity = datetime.now()
    
    async def check_scale_down(self):
        """Check if servers should be scaled down due to inactivity"""
        now = datetime.now()
        
        # Check video server
        if self.last_video_activity:
            idle_time = (now - self.last_video_activity).total_seconds()
            if idle_time > self.idle_timeout:
                video_queue_empty = self.queue_manager.redis_client.llen("video_generation_queue") == 0
                if video_queue_empty:
                    await self.runpod_manager.stop_gpu_server(TaskType.VIDEO_GENERATION)
                    self.last_video_activity = None
        
        # Check eval server
        if self.last_eval_activity:
            idle_time = (now - self.last_eval_activity).total_seconds()
            if idle_time > self.idle_timeout:
                eval_queue_empty = self.queue_manager.redis_client.llen("evaluation_queue") == 0
                if eval_queue_empty:
                    await self.runpod_manager.stop_gpu_server(TaskType.EVALUATION)
                    self.last_eval_activity = None
    
    async def update_cost_tracking(self):
        """Update cost tracking and check limits"""
        await self.cost_tracker.update_usage()
        
        if await self.cost_tracker.approaching_limit():
            print("WARNING: Approaching cost limit, scaling will be restricted")
        
        if await self.cost_tracker.limit_exceeded():
            print("ALERT: Cost limit exceeded, stopping all instances")
            await self.emergency_shutdown()
    
    async def check_and_scale(self):
        """Check and scale GPU instances (simplified for testing)"""
        # For now, just log that we're checking scaling
        print("Checking GPU scaling...")
        await asyncio.sleep(1)  # Simulate processing time
    
    async def emergency_shutdown(self):
        """Emergency shutdown all GPU servers"""
        await self.runpod_manager.stop_gpu_server(TaskType.VIDEO_GENERATION)
        await self.runpod_manager.stop_gpu_server(TaskType.EVALUATION)
        self.enabled = False

class CostTracker:
    def __init__(self):
        self.daily_limit = 50.00  # $50/day
        self.monthly_limit = 500.00  # $500/month
        self.current_daily_cost = 0.0
        self.current_monthly_cost = 0.0
    
    async def can_start_instance(self) -> bool:
        """Check if we can start a new instance within cost limits"""
        estimated_hourly_cost = 0.27  # RTX A5000 cost per hour
        
        # Check if starting would exceed daily limit
        if self.current_daily_cost + estimated_hourly_cost > self.daily_limit:
            return False
        
        # Check if starting would exceed monthly limit
        if self.current_monthly_cost + estimated_hourly_cost > self.monthly_limit:
            return False
        
        return True
    
    async def update_usage(self):
        """Update cost tracking based on RunPod usage"""
        # This would integrate with RunPod billing API
        # For now, estimate based on running time
        pass
    
    async def approaching_limit(self) -> bool:
        """Check if approaching cost limits (80% threshold)"""
        daily_threshold = self.daily_limit * 0.8
        monthly_threshold = self.monthly_limit * 0.8
        
        return (self.current_daily_cost > daily_threshold or 
                self.current_monthly_cost > monthly_threshold)
    
    async def limit_exceeded(self) -> bool:
        """Check if cost limits exceeded"""
        return (self.current_daily_cost > self.daily_limit or 
                self.current_monthly_cost > self.monthly_limit)
