"""
Gemini API client with rate limiting
"""
import os
import google.generativeai as genai
from typing import Optional
from .rate_limiter import RateLimiter


class GeminiClient:
    """Gemini API client with rate limiting support"""
    
    def __init__(self, api_key: Optional[str] = None, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google API key (if None, will try to get from environment)
            rate_limiter: RateLimiter instance (if None, will create new one)
        """
        # Configure API key
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("API key not provided and not found in environment variables. "
                               "Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
        
        genai.configure(api_key=api_key)
        
        # Initialize models
        self.agent1_model = genai.GenerativeModel('gemini-2.0-flash')  # Better for detection
        self.agent2_model = genai.GenerativeModel('gemini-2.5-flash')  # Better for validation
        
        # Rate limiter
        self.rate_limiter = rate_limiter or RateLimiter()
    
    def safe_gemini_request(self, model, prompt: str, agent_name: str = "Agent", 
                          model_name: Optional[str] = None):
        """Make request to Gemini respecting rate limits"""
        try:
            # Determine model name if not provided
            if model_name is None:
                model_name = getattr(model, 'model_name', "gemini-2.5-flash")
            
            # Wait if necessary due to rate limits
            self.rate_limiter.wait_if_needed(model_name)
            
            print(f"🔄 {agent_name}: Sending request to {model_name}...")
            response = model.generate_content(prompt)
            
            print(f"✅ {agent_name}: Response received successfully")
            return response
            
        except Exception as e:
            print(f"❌ {agent_name}: Error in request: {e}")
            raise
    
    def get_usage_summary(self):
        """Get API usage summary"""
        return self.rate_limiter.get_usage_summary()