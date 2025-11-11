"""
Google AI (Gemini) API client for RAG system with free tier rate limiting.
Falls back to Ollama when daily limits are reached.
"""

import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from django.core.cache import cache


class GoogleAIRateLimiter:
    """Rate limiter for Google AI API free tier limits"""
    
    # Free tier limits: 15 requests per minute, 1500 requests per day
    RATE_LIMIT_RPM = 15  # Requests per minute
    RATE_LIMIT_RPD = 1500  # Requests per day
    
    def __init__(self):
        self.cache_prefix = "google_ai_rate_limit"
    
    def _get_minute_key(self) -> str:
        """Get cache key for current minute"""
        now = datetime.now()
        minute_key = now.strftime("%Y%m%d%H%M")
        return f"{self.cache_prefix}:minute:{minute_key}"
    
    def _get_day_key(self) -> str:
        """Get cache key for current day"""
        now = datetime.now()
        day_key = now.strftime("%Y%m%d")
        return f"{self.cache_prefix}:day:{day_key}"
    
    def can_make_request(self) -> tuple[bool, Optional[str]]:
        """
        Check if we can make a request within rate limits.
        
        Returns:
            (can_request, reason_if_not)
        """
        minute_key = self._get_minute_key()
        day_key = self._get_day_key()
        
        # Check minute limit
        minute_count = cache.get(minute_key, 0)
        if minute_count >= self.RATE_LIMIT_RPM:
            return False, f"Rate limit exceeded: {self.RATE_LIMIT_RPM} requests per minute"
        
        # Check daily limit
        day_count = cache.get(day_key, 0)
        if day_count >= self.RATE_LIMIT_RPD:
            return False, f"Daily limit exceeded: {self.RATE_LIMIT_RPD} requests per day"
        
        return True, None
    
    def record_request(self):
        """Record that a request was made"""
        minute_key = self._get_minute_key()
        day_key = self._get_day_key()
        
        # Increment minute counter (expires in 2 minutes)
        minute_count = cache.get(minute_key, 0)
        cache.set(minute_key, minute_count + 1, timeout=120)
        
        # Increment daily counter (expires in 25 hours to be safe)
        day_count = cache.get(day_key, 0)
        cache.set(day_key, day_count + 1, timeout=90000)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        minute_key = self._get_minute_key()
        day_key = self._get_day_key()
        
        minute_count = cache.get(minute_key, 0)
        day_count = cache.get(day_key, 0)
        
        return {
            "minute_usage": minute_count,
            "minute_limit": self.RATE_LIMIT_RPM,
            "day_usage": day_count,
            "day_limit": self.RATE_LIMIT_RPD,
            "minute_remaining": max(0, self.RATE_LIMIT_RPM - minute_count),
            "day_remaining": max(0, self.RATE_LIMIT_RPD - day_count),
        }


class GoogleAIClient:
    """Google AI (Gemini) API client for text generation"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google AI client.
        
        Args:
            api_key: Google AI API key (or from GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        self.rate_limiter = GoogleAIRateLimiter()
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Google AI client"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel('gemini-pro')
            print("✓ Google AI (Gemini) client initialized")
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        except Exception as e:
            raise ValueError(f"Failed to initialize Google AI client: {e}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Generate text using Google AI API.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (prepended to prompt)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Returns:
            Generated text
        """
        # Check rate limits
        can_request, reason = self.rate_limiter.can_make_request()
        if not can_request:
            raise RateLimitError(reason)
        
        try:
            import google.generativeai as genai
            
            # Combine system and user prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Generate response
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            response = self._client.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Record request
            self.rate_limiter.record_request()
            
            return response.text
        
        except Exception as e:
            # Don't record failed requests
            raise Exception(f"Google AI API error: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get rate limit usage statistics"""
        return self.rate_limiter.get_usage_stats()


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass


def create_google_ai_client(api_key: Optional[str] = None) -> GoogleAIClient:
    """
    Create Google AI client instance.
    
    Args:
        api_key: Google AI API key (optional, uses GEMINI_API_KEY env var)
    
    Returns:
        GoogleAIClient instance
    """
    return GoogleAIClient(api_key=api_key)

