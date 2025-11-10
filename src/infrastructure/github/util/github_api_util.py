"""GitHub API utilities."""

import time
from typing import Optional
from datetime import datetime
from github import Github


class RateLimitInfo:
    """Rate limit information."""
    
    def __init__(
        self,
        limit: int,
        remaining: int,
        reset: int,
        used: int,
        reset_date: datetime
    ):
        self.limit = limit
        self.remaining = remaining
        self.reset = reset
        self.used = used
        self.reset_date = reset_date


class PaginationOptions:
    """Pagination options."""
    
    def __init__(
        self,
        per_page: Optional[int] = None,
        page: Optional[int] = None,
        max_items: Optional[int] = None,
        max_pages: Optional[int] = None
    ):
        self.per_page = per_page
        self.page = page
        self.max_items = max_items
        self.max_pages = max_pages


class GitHubApiUtil:
    """GitHub API utilities."""
    
    _instance: Optional["GitHubApiUtil"] = None
    _rate_limit_warning_threshold: int = 50
    _min_request_delay: int = 100
    
    def __init__(self):
        """Initialize GitHub API utilities."""
        pass
    
    @classmethod
    def get_instance(cls) -> "GitHubApiUtil":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def get_rate_limit(self, github: Github) -> RateLimitInfo:
        """Get current rate limit information from GitHub."""
        try:
            # PyGithub provides rate limit info
            rate_limit = github.get_rate_limit()
            core = rate_limit.core
            
            return RateLimitInfo(
                limit=core.limit,
                remaining=core.remaining,
                reset=core.reset,
                used=core.limit - core.remaining,
                reset_date=datetime.fromtimestamp(core.reset)
            )
        except Exception as error:
            import sys
            sys.stderr.write(f"Failed to get rate limit info: {error}\n")
            return self._get_default_rate_limit_info()
    
    def _get_default_rate_limit_info(self) -> RateLimitInfo:
        """Get default rate limit information."""
        return RateLimitInfo(
            limit=5000,
            remaining=5000,
            reset=int(time.time()) + 3600,
            used=0,
            reset_date=datetime.fromtimestamp(time.time() + 3600)
        )
    
    async def should_throttle(self, github: Github) -> bool:
        """Check if we should throttle requests."""
        rate_limit_info = await self.get_rate_limit(github)
        return rate_limit_info.remaining < self._rate_limit_warning_threshold
    
    async def calculate_request_delay(self, github: Github) -> int:
        """Calculate delay for next request based on rate limit."""
        rate_limit_info = await self.get_rate_limit(github)
        
        # If we're approaching the limit, calculate time to wait
        if rate_limit_info.remaining < self._rate_limit_warning_threshold:
            reset_time = rate_limit_info.reset_date.timestamp()
            now = time.time()
            
            if reset_time > now:
                time_to_reset = (reset_time - now) * 1000
                requests_left = max(1, rate_limit_info.remaining)
                # Distribute remaining requests over the time until reset
                return max(self._min_request_delay, int(time_to_reset / requests_left))
        
        return self._min_request_delay




