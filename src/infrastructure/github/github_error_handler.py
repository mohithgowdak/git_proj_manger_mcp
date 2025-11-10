"""GitHub error handler."""

from typing import Any, Dict, Optional
from ...domain.errors import (
    GitHubAPIError,
    RateLimitError,
    UnauthorizedError,
    ResourceNotFoundError
)


class GitHubErrorHandler:
    """GitHub error handler."""
    
    def handle_error(self, error: Any, context: Optional[str] = None) -> Exception:
        """Handle GitHub API error."""
        error_message = str(error)
        context_str = f" ({context})" if context else ""
        
        # Check for specific error types
        if hasattr(error, 'status'):
            status = error.status
            
            if status == 401:
                return UnauthorizedError(f"Unauthorized access to GitHub API{context_str}")
            elif status == 403:
                # Check if it's a rate limit error
                if hasattr(error, 'response') and hasattr(error.response, 'headers'):
                    headers = error.response.headers
                    if 'x-ratelimit-remaining' in headers and int(headers.get('x-ratelimit-remaining', 0)) == 0:
                        reset_time = headers.get('x-ratelimit-reset')
                        return RateLimitError(
                            f"GitHub API rate limit exceeded{context_str}",
                            reset_time=reset_time
                        )
                return UnauthorizedError(f"Forbidden access to GitHub API{context_str}")
            elif status == 404:
                return ResourceNotFoundError(f"Resource not found on GitHub{context_str}")
            elif status == 429:
                reset_time = None
                if hasattr(error, 'response') and hasattr(error.response, 'headers'):
                    reset_time = error.response.headers.get('x-ratelimit-reset')
                return RateLimitError(
                    f"GitHub API rate limit exceeded{context_str}",
                    reset_time=reset_time
                )
            else:
                return GitHubAPIError(
                    f"GitHub API error (status {status}): {error_message}{context_str}",
                    status=status,
                    response=error.response if hasattr(error, 'response') else None
                )
        
        # Generic error
        return GitHubAPIError(f"GitHub API error: {error_message}{context_str}")
    
    def is_retryable_error(self, error: Any) -> bool:
        """Check if error is retryable."""
        if hasattr(error, 'status'):
            status = error.status
            # Retry on 429 (rate limit), 500, 502, 503, 504
            return status in (429, 500, 502, 503, 504)
        
        # Check for network errors
        error_str = str(error).lower()
        network_errors = ['timeout', 'connection', 'network', 'econnreset']
        return any(err in error_str for err in network_errors)
    
    def calculate_retry_delay(self, headers: Dict[str, Any]) -> int:
        """Calculate retry delay from headers."""
        # Default delay
        delay = 1000
        
        # Check for rate limit reset time
        if 'x-ratelimit-reset' in headers:
            reset_time = int(headers['x-ratelimit-reset'])
            import time
            current_time = int(time.time())
            if reset_time > current_time:
                delay = (reset_time - current_time) * 1000
        
        # Check for retry-after header
        if 'retry-after' in headers:
            retry_after = int(headers['retry-after'])
            delay = max(delay, retry_after * 1000)
        
        return min(delay, 60000)  # Max 60 seconds




