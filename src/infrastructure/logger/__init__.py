"""Logger infrastructure module."""

import sys
import json
from typing import Any, Optional


class ILogger:
    """Logger interface."""
    
    def debug(self, message: str, *args: Any) -> None:
        """Log debug message."""
        raise NotImplementedError
    
    def info(self, message: str, *args: Any) -> None:
        """Log info message."""
        raise NotImplementedError
    
    def warn(self, message: str, *args: Any) -> None:
        """Log warning message."""
        raise NotImplementedError
    
    def error(self, message: str, *args: Any) -> None:
        """Log error message."""
        raise NotImplementedError


class ConsoleLogger(ILogger):
    """Default logger implementation that logs to console."""
    
    def __init__(self, prefix: str = ""):
        """Initialize logger with optional prefix."""
        self.prefix = f"[{prefix}] " if prefix else ""
    
    def debug(self, message: str, *args: Any) -> None:
        """Log debug message to stderr."""
        sys.stderr.write(f"{self.prefix}{message}\n")
        if args:
            sys.stderr.write(f"{json.dumps(args, indent=2)}\n")
    
    def info(self, message: str, *args: Any) -> None:
        """Log info message to stderr."""
        sys.stderr.write(f"{self.prefix}{message}\n")
        if args:
            sys.stderr.write(f"{json.dumps(args, indent=2)}\n")
    
    def warn(self, message: str, *args: Any) -> None:
        """Log warning message to stderr."""
        sys.stderr.write(f"{self.prefix}{message}\n")
        if args:
            sys.stderr.write(f"{json.dumps(args, indent=2)}\n")
    
    def error(self, message: str, *args: Any) -> None:
        """Log error message to stderr."""
        sys.stderr.write(f"{self.prefix}{message}\n")
        if args:
            sys.stderr.write(f"{json.dumps(args, indent=2)}\n")


class NoopLogger(ILogger):
    """No-op logger that doesn't do any logging."""
    
    def debug(self, message: str, *args: Any) -> None:
        """No-op debug."""
        pass
    
    def info(self, message: str, *args: Any) -> None:
        """No-op info."""
        pass
    
    def warn(self, message: str, *args: Any) -> None:
        """No-op warn."""
        pass
    
    def error(self, message: str, *args: Any) -> None:
        """No-op error."""
        pass


def create_logger(prefix: Optional[str] = None) -> ILogger:
    """Create a logger instance with optional prefix."""
    return ConsoleLogger(prefix)


def get_logger(prefix: str) -> ILogger:
    """Get a logger instance with a prefix."""
    return create_logger(prefix)


# Default singleton logger instance
logger = create_logger("MCP")


class Logger:
    """Singleton logger class for global access."""
    
    _instance: Optional["Logger"] = None
    
    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = ConsoleLogger("MCP")
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "Logger":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def debug(self, message: str, *args: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, *args)
    
    def info(self, message: str, *args: Any) -> None:
        """Log info message."""
        self.logger.info(message, *args)
    
    def warn(self, message: str, *args: Any) -> None:
        """Log warning message."""
        self.logger.warn(message, *args)
    
    def error(self, message: str, *args: Any) -> None:
        """Log error message."""
        self.logger.error(message, *args)




