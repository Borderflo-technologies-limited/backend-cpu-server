#!/usr/bin/env python3
"""
Interview Agent Service
Handles question generation using Groq's Llama-3.3-70b and TTS
"""

import os
import logging
import json
import hashlib
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from pathlib import Path

from app.core.config import settings
from app.core.database import get_db, Question, MonthlyQuestionSet

logger = logging.getLogger(__name__)

class InterviewAgent:
    """Interview Agent for question generation and TTS"""
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
        
    async def generate_questions(self, user_data: Dict[str, Any], count: int = 30) -> List[Dict[str, Any]]:
        """Generate interview questions based on user profile"""
        if not self.groq_api_key:
            logger.warning("Groq API key not found, using mock questions")
            return self._generate_mock_questions(count)
        
        try:
            # Prepare user context for question generation
            context = self._prepare_user_context(user_data)
            
            # Generate questions in batches to avoid token limits
            batch_size = 5
            all_questions = []
            
            for i in range(0, count, batch_size):
                batch_count = min(batch_size, count - i)
                batch_questions = await self._generate_question_batch(context, batch_count, i + 1)
                all_questions.extend(batch_questions)
                
                # Small delay between batches to avoid rate limiting
                await asyncio.sleep(1)
            
            logger.info(f"Generated {len(all_questions)} questions for user")
            return all_questions
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return self._generate_mock_questions(count)
    
    def _prepare_user_context(self, user_data: Dict[str, Any]) -> str:
        """Prepare user context for question generation"""
        context_parts = []
        
        if user_data.get('visa_type'):
            context_parts.append(f"Visa Type: {user_data['visa_type']}")
        if user_data.get('purpose_of_visit'):
            context_parts.append(f"Purpose: {user_data['purpose_of_visit']}")
        if user_data.get('country_of_residence'):
            context_parts.append(f"Country: {user_data['country_of_residence']}")
        if user_data.get('occupation'):
            context_parts.append(f"Occupation: {user_data['occupation']}")
            
        return " | ".join(context_parts) if context_parts else "General visa interview"
    
    def _generate_mock_questions(self, count: int, start_number: int = 1) -> List[Dict[str, Any]]:
        """Generate mock questions when API is not available"""
        mock_questions = [
            {"text": "What is the purpose of your visit?", "category": "purpose", "difficulty": "easy"},
            {"text": "How long do you plan to stay?", "category": "travel", "difficulty": "easy"},
            {"text": "Do you have family or friends in the destination country?", "category": "ties", "difficulty": "medium"},
            {"text": "What is your current occupation?", "category": "background", "difficulty": "easy"},
            {"text": "How will you finance your trip?", "category": "financial", "difficulty": "medium"},
            {"text": "Have you traveled internationally before?", "category": "travel", "difficulty": "easy"},
            {"text": "What ties do you have to your home country?", "category": "ties", "difficulty": "medium"},
        ]
        
        questions = []
        for i in range(count):
            base_question = mock_questions[i % len(mock_questions)]
            question = {
                "id": start_number + i,
                "text": base_question["text"],
                "category": base_question["category"],
                "difficulty": base_question["difficulty"],
                "expected_duration": 30
            }
            questions.append(question)
        
        return questions
    
    async def _generate_question_batch(self, context: str, count: int, start_number: int) -> List[Dict[str, Any]]:
        """Generate a batch of questions using Groq API"""
        # For now, return mock questions
        # In production, this would call Groq API
        return self._generate_mock_questions(count, start_number)
    
    async def process_monthly_generation(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate and save monthly question set for a user"""
        try:
            # Generate questions
            questions = await self.generate_questions(user_data, count=30)
            
            logger.info(f"Generated {len(questions)} questions for user {user_id}")
            
            return {
                "success": True,
                "questions_generated": len(questions),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Monthly generation failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }

# Global instance
interview_agent = InterviewAgent()