"""MCP response formatter."""

import json
from typing import Any, Dict, Optional
from datetime import datetime
from ...domain.mcp_types import (
    MCPContentType,
    MCPResponse,
    MCPSuccessResponse,
    MCPErrorResponse,
    MCPErrorDetail
)


class MCPResponseFormatter:
    """MCP response formatter."""
    
    @staticmethod
    def format(
        data: Any,
        content_type: MCPContentType = MCPContentType.JSON,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPSuccessResponse:
        """Format data as MCP response."""
        # Convert data to appropriate format
        if content_type == MCPContentType.JSON:
            content = json.dumps(data, indent=2)
        elif content_type == MCPContentType.MARKDOWN:
            content = MCPResponseFormatter._format_as_markdown(data)
        elif content_type == MCPContentType.HTML:
            content = MCPResponseFormatter._format_as_html(data)
        else:
            content = str(data)
        
        # Create response
        return MCPSuccessResponse(
            version="1.0",
            request_id=metadata.get("requestId", "") if metadata else "",
            output={
                "content": content,
                "format": {
                    "type": content_type.value
                }
            },
            correlation_id=metadata.get("correlationId") if metadata else None
        )
    
    @staticmethod
    def error(
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> MCPErrorResponse:
        """Format error as MCP error response."""
        error_detail = MCPErrorDetail(
            code=code,
            message=message,
            inner_error=details
        )
        
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=error_detail
        )
    
    @staticmethod
    def _format_as_markdown(data: Any) -> str:
        """Format data as markdown."""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                formatted_key = key.replace("_", " ").title()
                if isinstance(value, list):
                    lines.append(f"## {formatted_key}\n")
                    for item in value:
                        lines.append(f"- {json.dumps(item)}")
                elif isinstance(value, dict):
                    lines.append(f"## {formatted_key}\n\n```json\n{json.dumps(value, indent=2)}\n```")
                else:
                    lines.append(f"## {formatted_key}\n{value}")
            return "\n\n".join(lines)
        elif isinstance(data, list):
            return "\n".join(f"- {json.dumps(item)}" for item in data)
        else:
            return str(data)
    
    @staticmethod
    def _format_as_html(data: Any) -> str:
        """Format data as HTML."""
        if isinstance(data, dict):
            html = "<div>"
            for key, value in data.items():
                formatted_key = key.replace("_", " ").title()
                html += f"<h3>{formatted_key}</h3>"
                if isinstance(value, (dict, list)):
                    html += f"<pre>{json.dumps(value, indent=2)}</pre>"
                else:
                    html += f"<p>{value}</p>"
            html += "</div>"
            return html
        elif isinstance(data, list):
            html = "<ul>"
            for item in data:
                html += f"<li>{json.dumps(item)}</li>"
            html += "</ul>"
            return html
        else:
            return f"<p>{data}</p>"
    
    @staticmethod
    def format_as_markdown_table(data: list[Dict[str, Any]]) -> str:
        """Format data as markdown table."""
        if not data:
            return ""
        
        # Get all keys from all items
        keys = set()
        for item in data:
            keys.update(item.keys())
        keys = sorted(keys)
        
        # Create table header
        header = "| " + " | ".join(keys) + " |"
        separator = "| " + " | ".join(["---"] * len(keys)) + " |"
        
        # Create table rows
        rows = []
        for item in data:
            row = "| " + " | ".join(str(item.get(key, "")) for key in keys) + " |"
            rows.append(row)
        
        return "\n".join([header, separator] + rows)

