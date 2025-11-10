"""Tool result formatter."""

import json
from datetime import datetime
from typing import Any, Dict, Optional
from ..mcp.mcp_response_formatter import MCPResponseFormatter
from ...domain.mcp_types import MCPContentType, MCPResponse


class FormattingOptions:
    """Formatting options."""
    
    def __init__(
        self,
        content_type: Optional[MCPContentType] = None,
        request_id: Optional[str] = None,
        include_raw_data: bool = False
    ):
        self.content_type = content_type or MCPContentType.JSON
        self.request_id = request_id
        self.include_raw_data = include_raw_data


class ToolResultFormatter:
    """Tool result formatter."""
    
    @staticmethod
    def format_success(
        tool_name: str,
        result: Any,
        options: Optional[FormattingOptions] = None
    ) -> MCPResponse:
        """Format a tool result as a successful MCP response."""
        if options is None:
            options = FormattingOptions()
        
        content_type = options.content_type or MCPContentType.JSON
        
        # Determine the right content format based on the result type and requested content type
        if content_type == MCPContentType.MARKDOWN:
            return ToolResultFormatter._format_as_markdown(tool_name, result, options)
        elif content_type == MCPContentType.HTML:
            return ToolResultFormatter._format_as_html(tool_name, result, options)
        elif content_type == MCPContentType.TEXT:
            return ToolResultFormatter._format_as_text(tool_name, result, options)
        else:
            return ToolResultFormatter._format_as_json(tool_name, result, options)
    
    @staticmethod
    def _format_as_json(
        tool_name: str,
        result: Any,
        options: FormattingOptions
    ) -> MCPResponse:
        """Format result as JSON."""
        metadata = {
            "tool": tool_name,
            "timestamp": str(datetime.now()),
            "requestId": options.request_id,
        }
        
        return MCPResponseFormatter.format(result, MCPContentType.JSON, metadata)
    
    @staticmethod
    def _format_as_markdown(
        tool_name: str,
        result: Any,
        options: FormattingOptions
    ) -> MCPResponse:
        """Format result as Markdown."""
        # Add a title based on the tool name
        markdown = f"# {ToolResultFormatter._format_tool_name(tool_name)} Result\n\n"
        
        # Handle different types of results
        if isinstance(result, list):
            # Format array results as a table if possible
            if result and isinstance(result[0], dict):
                markdown += MCPResponseFormatter.format_as_markdown_table(result)
            else:
                # Simple list for arrays of primitives
                markdown += "\n".join(f"- {json.dumps(item)}" for item in result)
        elif isinstance(result, dict):
            # Format key properties as headers with details
            sections = []
            for key, value in result.items():
                formatted_key = key.replace("_", " ").title()
                
                if isinstance(value, list):
                    # Format arrays as lists
                    sections.append(f"## {formatted_key}\n" + "\n".join(f"- {json.dumps(item)}" for item in value))
                elif isinstance(value, dict):
                    # Format objects with nested details
                    sections.append(f"## {formatted_key}\n\n```json\n{json.dumps(value, indent=2)}\n```")
                else:
                    sections.append(f"## {formatted_key}\n{value}")
            markdown += "\n\n".join(sections)
        else:
            # Simple value
            markdown += str(result)
        
        # Include raw JSON data if requested
        if options.include_raw_data:
            markdown += f'\n\n## Raw Data\n\n```json\n{json.dumps(result)}\n```'
        
        metadata = {
            "tool": tool_name,
            "timestamp": str(datetime.now()),
            "requestId": options.request_id,
        }
        
        return MCPResponseFormatter.format(markdown, MCPContentType.MARKDOWN, metadata)
    
    @staticmethod
    def _format_as_html(
        tool_name: str,
        result: Any,
        options: FormattingOptions
    ) -> MCPResponse:
        """Format result as HTML."""
        html = f"<h1>{ToolResultFormatter._format_tool_name(tool_name)} Result</h1>\n"
        
        if isinstance(result, dict):
            for key, value in result.items():
                formatted_key = key.replace("_", " ").title()
                html += f"<h3>{formatted_key}</h3>"
                if isinstance(value, (dict, list)):
                    html += f"<pre>{json.dumps(value, indent=2)}</pre>"
                else:
                    html += f"<p>{value}</p>"
        elif isinstance(result, list):
            html += "<ul>"
            for item in result:
                html += f"<li>{json.dumps(item)}</li>"
            html += "</ul>"
        else:
            html += f"<p>{result}</p>"
        
        metadata = {
            "tool": tool_name,
            "timestamp": str(datetime.now()),
            "requestId": options.request_id,
        }
        
        return MCPResponseFormatter.format(html, MCPContentType.HTML, metadata)
    
    @staticmethod
    def _format_as_text(
        tool_name: str,
        result: Any,
        options: FormattingOptions
    ) -> MCPResponse:
        """Format result as plain text."""
        text = f"{ToolResultFormatter._format_tool_name(tool_name)} Result\n\n"
        text += str(result)
        
        metadata = {
            "tool": tool_name,
            "timestamp": str(datetime.now()),
            "requestId": options.request_id,
        }
        
        return MCPResponseFormatter.format(text, MCPContentType.TEXT, metadata)
    
    @staticmethod
    def _format_tool_name(tool_name: str) -> str:
        """Format tool name for display."""
        return tool_name.replace("_", " ").title()

