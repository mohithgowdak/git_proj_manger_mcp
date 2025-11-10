"""Domain error types and error handling utilities."""

from typing import Optional, Any


class DomainError(Exception):
    """Base domain error."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.name = self.__class__.__name__


class ValidationError(Exception):
    """Validation error."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.name = "ValidationError"


class ResourceNotFoundError(Exception):
    """Resource not found error."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.name = "ResourceNotFoundError"


class UnauthorizedError(Exception):
    """Unauthorized access error."""
    
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message)
        self.name = "UnauthorizedError"


class RateLimitError(Exception):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str = "Rate limit exceeded", reset_time: Optional[Any] = None):
        super().__init__(message)
        self.name = "RateLimitError"
        self.reset_time = reset_time


class ConfigurationError(Exception):
    """Configuration error."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.name = "ConfigurationError"


class IntegrationError(Exception):
    """Integration error."""
    
    def __init__(self, message: str, source: Optional[str] = None):
        super().__init__(message)
        self.name = "IntegrationError"
        self.source = source


class GitHubAPIError(Exception):
    """GitHub API error."""
    
    def __init__(self, message: str, status: Optional[int] = None, response: Optional[Any] = None):
        super().__init__(message)
        self.name = "GitHubAPIError"
        self.status = status
        self.response = response


class MCPProtocolError(Exception):
    """MCP protocol error."""
    
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.name = "MCPProtocolError"
        self.code = code


def is_error_type(error: Exception, error_type: type) -> bool:
    """Check if error is of a specific type."""
    return isinstance(error, error_type)


def unwrap_error(error: Any) -> Exception:
    """Unwrap error to Exception type."""
    if isinstance(error, Exception):
        return error
    return Exception(str(error))




