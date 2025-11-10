#!/usr/bin/env python3
"""Main entry point for MCP GitHub Project Manager server."""

import sys
import asyncio
from typing import Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError:
    print("Error: MCP SDK not installed. Please install it with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from .env import (
    GITHUB_TOKEN,
    GITHUB_OWNER,
    GITHUB_REPO,
    CLI_OPTIONS,
    SYNC_ENABLED,
    SYNC_TIMEOUT_MS,
    CACHE_DIRECTORY,
    WEBHOOK_SECRET,
    WEBHOOK_PORT,
    SSE_ENABLED
)
from .infrastructure.logger import Logger
from .infrastructure.tools.tool_registry import ToolRegistry
from .services.project_management_service import ProjectManagementService


class GitHubProjectManagerServer:
    """GitHub Project Manager MCP Server."""
    
    def __init__(self):
        """Initialize the server."""
        self.logger = Logger.get_instance()
        
        # Initialize MCP server
        self.server = Server(
            name="github-project-manager",
            version="1.0.1"
        )
        
        # Initialize project management service
        self.service = ProjectManagementService(
            GITHUB_OWNER,
            GITHUB_REPO,
            GITHUB_TOKEN
        )
        
        # Get the tool registry instance
        self.tool_registry = ToolRegistry.get_instance()
        
        # Setup handlers
        self._setup_handlers()
        
        # Log AI service status
        self._log_ai_service_status()
    
    def _setup_handlers(self):
        """Setup MCP handlers."""
        # Setup list_tools handler
        @self.server.list_tools()
        async def list_tools() -> list:
            """List all available tools."""
            try:
                tools = self.tool_registry.get_tools_for_mcp()
                # Convert to MCP SDK format
                from mcp.types import Tool
                return [
                    Tool(
                        name=tool.get("name", ""),
                        description=tool.get("description", ""),
                        inputSchema=tool.get("inputSchema", {})
                    )
                    for tool in tools
                ]
            except Exception as e:
                self.logger.error(f"Error in list_tools handler: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                raise
        
        # Setup call_tool handler
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list:
            """Call a tool by name."""
            try:
                from .infrastructure.tools.tool_handlers import execute_tool
                from .infrastructure.tools.tool_validator import ToolValidator
                from mcp.types import TextContent
                
                tool = self.tool_registry.get_tool(name)
                if not tool:
                    raise ValueError(f"Unknown tool: {name}")
                
                # Validate arguments
                try:
                    validated_args = ToolValidator.validate(name, arguments, tool.schema)
                except Exception as validation_error:
                    self.logger.error(f"Tool validation error: {validation_error}")
                    raise ValueError(f"Invalid arguments for tool {name}: {validation_error}")
                
                # Execute tool handler
                result = await execute_tool(name, self.service, validated_args)
                
                # Convert MCPResponse to MCP SDK format
                if hasattr(result, 'status') and result.status == "success":
                    content = result.output.get("content", "")
                    if isinstance(content, str):
                        return [TextContent(type="text", text=content)]
                    else:
                        import json
                        return [TextContent(type="text", text=json.dumps(content, indent=2))]
                else:
                    # Error response
                    error_detail = result.error if hasattr(result, 'error') else None
                    error_message = error_detail.message if error_detail else "Unknown error"
                    raise ValueError(f"Tool execution failed: {error_message}")
                    
            except Exception as error:
                self.logger.error(f"Tool execution error: {error}")
                raise
    
    def _log_ai_service_status(self):
        """Log AI service status during startup."""
        try:
            # This will be implemented when AI services are translated
            self.logger.info("🤖 AI Service Status Check")
            self.logger.warn("⚠️  AI services not yet implemented in Python version")
        except Exception as error:
            self.logger.error(f"Failed to check AI service status: {error}")
    
    async def run(self):
        """Run the MCP server."""
        try:
            # Display configuration information if verbose mode is enabled
            if CLI_OPTIONS.verbose:
                print("GitHub Project Manager MCP server configuration:", file=sys.stderr)
                print(f"- Owner: {GITHUB_OWNER}", file=sys.stderr)
                print(f"- Repository: {GITHUB_REPO}", file=sys.stderr)
                token_display = f"{GITHUB_TOKEN[:4]}...{GITHUB_TOKEN[-4:]}" if len(GITHUB_TOKEN) > 8 else "***"
                print(f"- Token: {token_display}", file=sys.stderr)
                print(f"- Environment file: {CLI_OPTIONS.env_file or '.env (default)'}", file=sys.stderr)
                print(f"- Sync enabled: {SYNC_ENABLED}", file=sys.stderr)
                print(f"- Cache directory: {CACHE_DIRECTORY}", file=sys.stderr)
                print(f"- Webhook port: {WEBHOOK_PORT}", file=sys.stderr)
                print(f"- SSE enabled: {SSE_ENABLED}", file=sys.stderr)
            
            print("GitHub Project Manager MCP server running on stdio", file=sys.stderr)
            
            # Run the server with stdio transport
            # The MCP Python SDK uses stdio_server() as a context manager
            async with stdio_server() as (read_stream, write_stream):
                # Create initialization options
                initialization_options = self.server.create_initialization_options()
                await self.server.run(
                    read_stream,
                    write_stream,
                    initialization_options
                )
        except Exception as error:
            self.logger.error(f"Failed to start server: {error}")
            raise


def main():
    """Main entry point."""
    try:
        server = GitHubProjectManagerServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nShutting down...", file=sys.stderr)
        sys.exit(0)
    except Exception as error:
        error_message = str(error)
        import traceback
        error_traceback = traceback.format_exc()
        
        print(f"Error initializing server: {error_message}", file=sys.stderr)
        print(f"\nTraceback:", file=sys.stderr)
        print(error_traceback, file=sys.stderr)
        
        # Provide helpful instructions for common errors
        if "GITHUB_TOKEN" in error_message:
            print("\nPlease provide a GitHub token using one of these methods:", file=sys.stderr)
            print("  - Set the GITHUB_TOKEN environment variable", file=sys.stderr)
            print("  - Use the --token command line argument", file=sys.stderr)
            print("\nExample: python -m src --token=your_token", file=sys.stderr)
        elif "GITHUB_OWNER" in error_message or "GITHUB_REPO" in error_message:
            print("\nPlease provide the required GitHub repository information:", file=sys.stderr)
            print("  - Set the GITHUB_OWNER and GITHUB_REPO environment variables", file=sys.stderr)
            print("  - Use the --owner and --repo command line arguments", file=sys.stderr)
            print("\nExample: python -m src --owner=your_username --repo=your_repo", file=sys.stderr)
        
        print("\nFor more information, run: python -m src --help", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

