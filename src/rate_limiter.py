"""
Rate Limiter for combined Gemini API usage
"""
import time
import threading
from collections import deque
from datetime import datetime, timedelta
from typing import Dict

# API Limits configuration
INDIVIDUAL_LIMITS = {
    'gemini-2.0-flash': {
        'rpm': 15,         # Requests per minute
        'tpm': 1000000,    # Tokens per minute
        'rpd': 200         # Requests per day
    },
    'gemini-2.5-flash': {
        'rpm': 10,         # Requests per minute
        'tpm': 250000,     # Tokens per minute
        'rpd': 250         # Requests per day
    }
}

# Combined limits (most restrictive)
COMBINED_LIMITS = {
    'rpm': min(INDIVIDUAL_LIMITS['gemini-2.0-flash']['rpm'],
               INDIVIDUAL_LIMITS['gemini-2.5-flash']['rpm']),  # 10 (from Gemini 2.5)
    'tpm': min(INDIVIDUAL_LIMITS['gemini-2.0-flash']['tpm'],
               INDIVIDUAL_LIMITS['gemini-2.5-flash']['tpm']),  # 250,000 (from Gemini 2.5)
    'rpd': min(INDIVIDUAL_LIMITS['gemini-2.0-flash']['rpd'],
               INDIVIDUAL_LIMITS['gemini-2.5-flash']['rpd'])   # 200 (from Gemini 2.0)
}


class RateLimiter:
    """Combined rate limit control for two-agent system"""

    def __init__(self):
        # Use combined limits for complete system
        self.request_times = deque()
        self.daily_requests = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
        self.lock = threading.Lock()

        # Per-model tracking for statistics
        self.model_requests = {
            'gemini-2.0-flash': 0,
            'gemini-2.5-flash': 0
        }

    def wait_if_needed(self, model_name: str = "gemini-2.5-flash"):
        """Wait if necessary to respect combined limits"""
        with self.lock:
            now = datetime.now()

            # Daily reset
            if now >= self.daily_reset_time:
                self.daily_requests = 0
                self.daily_reset_time = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
                self.model_requests = {k: 0 for k in self.model_requests.keys()}
                print(f"🔄 Combined rate limits reset for new day")

            # Check daily combined limit
            if self.daily_requests >= COMBINED_LIMITS['rpd']:
                wait_until = self.daily_reset_time
                wait_seconds = (wait_until - now).total_seconds()
                print(f"⚠️ Daily combined limit reached ({COMBINED_LIMITS['rpd']} requests). "
                      f"Waiting {wait_seconds/3600:.1f} hours...")
                raise Exception(f"Daily combined limit reached. Resets tomorrow at "
                              f"{self.daily_reset_time.strftime('%H:%M')}")

            # Clean old requests (older than 1 minute)
            cutoff_time = now - timedelta(minutes=1)
            while self.request_times and self.request_times[0] < cutoff_time:
                self.request_times.popleft()

            # Check combined per-minute limit
            if len(self.request_times) >= COMBINED_LIMITS['rpm']:
                wait_time = 60 - (now - self.request_times[0]).total_seconds()
                if wait_time > 0:
                    print(f"⏳ Combined rate limit: waiting {wait_time:.1f}s "
                          f"({len(self.request_times)}/{COMBINED_LIMITS['rpm']} RPM)")
                    time.sleep(wait_time + 1)  # +1 second buffer

            # Register new request
            self.request_times.append(now)
            self.daily_requests += 1

            # Track by model
            if model_name in self.model_requests:
                self.model_requests[model_name] += 1

            print(f"📊 Combined system: {len(self.request_times)}/{COMBINED_LIMITS['rpm']} RPM, "
                  f"{self.daily_requests}/{COMBINED_LIMITS['rpd']} RPD")
            print(f"    By model: 2.0={self.model_requests['gemini-2.0-flash']}, "
                  f"2.5={self.model_requests['gemini-2.5-flash']}")

    def get_usage_summary(self) -> Dict:
        """Get combined system usage summary"""
        # Clean old requests
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=1)
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()

        return {
            'combined': {
                'rpm_used': len(self.request_times),
                'rpm_limit': COMBINED_LIMITS['rpm'],
                'rpd_used': self.daily_requests,
                'rpd_limit': COMBINED_LIMITS['rpd'],
                'tpm_limit': COMBINED_LIMITS['tpm']  # Informational only
            },
            'by_model': self.model_requests.copy()
        }