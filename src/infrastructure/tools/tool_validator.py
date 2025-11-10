"""Tool validator for validating tool arguments."""

from typing import Any, Dict, Optional, TypeVar
from pydantic import BaseModel, ValidationError as PydanticValidationError
from ..mcp.mcp_response_formatter import MCPResponseFormatter
from ...domain.mcp_types import MCPErrorCode

T = TypeVar('T')


class ToolDefinition(BaseModel):
    """Tool definition."""
    
    name: str
    description: str
    schema: type  # Pydantic model type
    examples: Optional[list[Dict[str, Any]]] = None


class ToolValidator:
    """Tool validator for validating tool arguments."""
    
    @staticmethod
    def validate(tool_name: str, args: Any, schema: type) -> Any:
        """Validate tool arguments against the schema."""
        try:
            # Use Pydantic for validation
            if issubclass(schema, BaseModel):
                return schema(**args)
            else:
                # Fallback to dict validation
                return args
        except PydanticValidationError as error:
            # Format Pydantic validation errors
            details = [
                {
                    "path": ".".join(str(p) for p in err["loc"]),
                    "message": err["msg"],
                    "code": err["type"]
                }
                for err in error.errors()
            ]
            
            error_messages = [err["msg"] for err in error.errors()]
            raise ValueError(
                f"Invalid parameters for tool {tool_name}: {', '.join(error_messages)}"
            ) from error
        except Exception as error:
            # Generic validation error
            raise ValueError(
                f"Invalid parameters for tool {tool_name}: {str(error)}"
            ) from error
    
    @staticmethod
    def handle_tool_error(error: Exception, tool_name: str) -> Dict[str, Any]:
        """Handle tool execution error."""
        import sys
        sys.stderr.write(f"[{tool_name}] Error: {error}\n")
        
        # Handle validation errors
        if isinstance(error, ValueError):
            return MCPResponseFormatter.error(
                MCPErrorCode.VALIDATION_ERROR,
                str(error)
            )
        
        # Handle regular errors
        if isinstance(error, Exception):
            return MCPResponseFormatter.error(
                MCPErrorCode.INTERNAL_ERROR,
                f"Error executing tool {tool_name}: {str(error)}",
                {"stack": str(error.__traceback__) if hasattr(error, '__traceback__') else None}
            )
        
        # Handle unknown errors
        return MCPResponseFormatter.error(
            MCPErrorCode.INTERNAL_ERROR,
            f"Unknown error executing tool {tool_name}",
            {"error": str(error)}
        )
    
    @staticmethod
    def map_error_code(error_code: str) -> MCPErrorCode:
        """Map error code to MCP error code."""
        error_code_map = {
            "InvalidParams": MCPErrorCode.VALIDATION_ERROR,
            "MethodNotFound": MCPErrorCode.RESOURCE_NOT_FOUND,
            "InternalError": MCPErrorCode.INTERNAL_ERROR,
            "InvalidRequest": MCPErrorCode.UNAUTHORIZED,
            "ParseError": MCPErrorCode.RATE_LIMITED,
        }
        return error_code_map.get(error_code, MCPErrorCode.INTERNAL_ERROR)




