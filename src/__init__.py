"""
Metaphor Analysis System

A two-agent system for detecting conceptual metaphors in financial texts
using Google Gemini models.
"""

from .metaphor_analyzer import MetaphorAnalyzer
from .database import MetaphorDatabase
from .rate_limiter import RateLimiter
from .gemini_client import GeminiClient

__version__ = "1.0.0"
__all__ = ["MetaphorAnalyzer", "MetaphorDatabase", "RateLimiter", "GeminiClient"]