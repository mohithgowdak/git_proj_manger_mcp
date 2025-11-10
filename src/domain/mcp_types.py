"""MCP types for GitHub Project Manager."""

from enum import Enum
from typing import Optional, Dict, Any, List, Protocol, Union
from datetime import datetime
from .resource_types import ResourceType


class MCPContentType(str, Enum):
    """MCP content types."""
    JSON = "application/json"
    TEXT = "text/plain"
    MARKDOWN = "text/markdown"
    HTML = "text/html"


class MCPErrorCode(str, Enum):
    """MCP error codes."""
    INTERNAL_ERROR = "MCP-001"
    VALIDATION_ERROR = "MCP-002"
    RESOURCE_NOT_FOUND = "MCP-003"
    INVALID_REQUEST = "MCP-004"
    UNAUTHORIZED = "MCP-005"
    RATE_LIMITED = "MCP-006"


class MCPContent:
    """MCP content interface."""
    
    def __init__(
        self,
        type: str,  # "text" | "json" | "markdown" | "html"
        text: str,
        content_type: MCPContentType
    ):
        self.type = type
        self.text = text
        self.content_type = content_type


class MCPRequest:
    """MCP request interface."""
    
    def __init__(
        self,
        version: str,
        request_id: str,
        inputs: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        self.version = version
        self.correlation_id = correlation_id
        self.request_id = request_id
        self.inputs = inputs


class MCPResponseFormat:
    """MCP response format interface."""
    
    def __init__(self, type: str, schema: Optional[Dict[str, Any]] = None):
        self.type = type
        self.schema = schema


class MCPResource:
    """MCP resource interface."""
    
    def __init__(
        self,
        type: ResourceType,
        id: str,
        properties: Dict[str, Any],
        links: Optional[Dict[str, str]] = None
    ):
        self.type = type
        self.id = id
        self.properties = properties
        self.links = links or {}


class MCPErrorDetail:
    """MCP error detail interface."""
    
    def __init__(
        self,
        code: str,
        message: str,
        target: Optional[str] = None,
        details: Optional[List["MCPErrorDetail"]] = None,
        inner_error: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.target = target
        self.details = details or []
        self.inner_error = inner_error


class MCPSuccessResponse:
    """MCP success response interface."""
    
    def __init__(
        self,
        version: str,
        request_id: str,
        status: str = "success",
        output: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        self.version = version
        self.correlation_id = correlation_id
        self.request_id = request_id
        self.status = status
        self.output = output or {}


class MCPErrorResponse:
    """MCP error response interface."""
    
    def __init__(
        self,
        version: str,
        request_id: str,
        error: MCPErrorDetail,
        correlation_id: Optional[str] = None
    ):
        self.version = version
        self.correlation_id = correlation_id
        self.request_id = request_id
        self.status = "error"
        self.error = error


MCPResponse = Union[MCPSuccessResponse, MCPErrorResponse]


class MCPHandler(Protocol):
    """MCP handler protocol."""
    
    async def handle(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP request."""
        ...


class MCPResourceMapper(Protocol):
    """MCP resource mapper protocol."""
    
    def to_mcp_resource(self, entity: Any) -> MCPResource:
        """Convert entity to MCP resource."""
        ...
    
    def from_mcp_resource(self, resource: MCPResource) -> Any:
        """Convert MCP resource to entity."""
        ...


class MCPSerializer(Protocol):
    """MCP serializer protocol."""
    
    def serialize(self, entity: Any) -> MCPResource:
        """Serialize entity to MCP resource."""
        ...
    
    def deserialize(self, resource: MCPResource) -> Any:
        """Deserialize MCP resource to entity."""
        ...


def create_success_response(
    request_id: str,
    content: Optional[str] = None,
    resources: Optional[List[MCPResource]] = None,
    correlation_id: Optional[str] = None,
    version: str = "1.0"
) -> MCPSuccessResponse:
    """Create success response."""
    return MCPSuccessResponse(
        version=version,
        correlation_id=correlation_id,
        request_id=request_id,
        output={
            "content": content,
            "resources": resources,
        }
    )


def create_error_response(
    request_id: str,
    code: str,
    message: str,
    correlation_id: Optional[str] = None,
    details: Optional[List[MCPErrorDetail]] = None,
    version: str = "1.0"
) -> MCPErrorResponse:
    """Create error response."""
    return MCPErrorResponse(
        version=version,
        correlation_id=correlation_id,
        request_id=request_id,
        error=MCPErrorDetail(
            code=code,
            message=message,
            details=details
        )
    )




