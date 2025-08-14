
"""
RunPod Manager - Handles RunPod API interactions
Starts/stops GPU servers based on demand
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

class RunPodManager:
    def __init__(self):
        self.config = self.load_config()
        self.api_key = self.config["runpod"]["api_key"]
        self.base_url = self.config["runpod"]["base_url"]
        self.video_template_id = self.config["pod_templates"]["video_generation"]["template_id"]
        self.eval_template_id = self.config["pod_templates"]["evaluation_agent"]["template_id"]
        
        # Track running pods
        self.video_pod_id = None
        self.eval_pod_id = None
    
    def load_config(self) -> Dict:
        """Load RunPod configuration"""
        # For now, return default config - will be replaced with actual config later
        return {
            "runpod": {
                "api_key": "your-runpod-api-key",
                "base_url": "https://api.runpod.io/v2"
            },
            "pod_templates": {
                "video_generation": {
                    "template_id": "video-gen-template"
                },
                "evaluation_agent": {
                    "template_id": "eval-template"
                }
            }
        }
    
    async def start_gpu_server(self, task_type) -> Optional[str]:
        """Start GPU server on RunPod (simplified for testing)"""
        if task_type.value == "video_generation":
            if self.video_pod_id:
                return self.video_pod_id  # Already running
        else:
            if self.eval_pod_id:
                return self.eval_pod_id  # Already running
        
        # For now, just simulate starting a server
        pod_id = f"pod_{task_type.value}_{datetime.now().timestamp()}"
        
        if task_type.value == "video_generation":
            self.video_pod_id = pod_id
        else:
            self.eval_pod_id = pod_id
        
        print(f"Started {task_type.value} server: {pod_id}")
        return pod_id
    
    async def stop_gpu_server(self, task_type) -> bool:
        """Stop GPU server on RunPod (simplified for testing)"""
        if task_type.value == "video_generation":
            pod_id = self.video_pod_id
        else:
            pod_id = self.eval_pod_id
        
        if not pod_id:
            return True  # Already stopped
        
        # For now, just simulate stopping a server
        if task_type.value == "video_generation":
            self.video_pod_id = None
        else:
            self.eval_pod_id = None
        
        print(f"Stopped {task_type.value} server: {pod_id}")
        return True
    
    async def get_video_server_status(self) -> str:
        """Get video generation server status"""
        if not self.video_pod_id:
            return "stopped"
        
        return await self.get_pod_status(self.video_pod_id)
    
    async def get_eval_server_status(self) -> str:
        """Get evaluation server status"""
        if not self.eval_pod_id:
            return "stopped"
        
        return await self.get_pod_status(self.eval_pod_id)
    
    async def get_pod_status(self, pod_id: str) -> str:
        """Get specific pod status (simplified for testing)"""
        # For now, just return running if pod_id exists
        if pod_id:
            return "running"
        return "stopped"
