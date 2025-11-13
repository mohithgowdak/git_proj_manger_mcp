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
        import sys
        import json
        
        # Debug logging
        def log_debug(msg: str):
            sys.stderr.write(f"[ToolValidator] {msg}\n")
        
        log_debug(f"=== Validating {tool_name} ===")
        log_debug(f"Args type: {type(args)}")
        log_debug(f"Args: {json.dumps(args, indent=2, default=str) if isinstance(args, dict) else str(args)}")
        
        try:
            # Handle string arguments (JSON strings from MCP client)
            if isinstance(args, str):
                log_debug(f"Args is a string, attempting to parse")
                try:
                    args = json.loads(args)
                    log_debug(f"Parsed JSON string successfully")
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON string for tool {tool_name}: {args}")
            
            # Ensure args is a dict if it's not already
            if not isinstance(args, dict):
                log_debug(f"Args is not a dict, attempting conversion. Type: {type(args)}")
                if hasattr(args, 'model_dump'):
                    args = args.model_dump()
                    log_debug(f"Converted from Pydantic model")
                elif hasattr(args, '__dict__'):
                    args = args.__dict__
                    log_debug(f"Converted from object __dict__")
                else:
                    raise ValueError(f"Invalid arguments type for tool {tool_name}: {type(args)}")
            
            log_debug(f"Args after conversion: {json.dumps(args, indent=2, default=str)}")
            
            # For create_project_field, handle options parameter which might be a string or various formats
            if tool_name == "create_project_field" and isinstance(args, dict) and "options" in args:
                options = args["options"]
                log_debug(f"Processing options: type={type(options)}, value={options}")
                
                # If options is None or empty, skip processing
                if options is None:
                    log_debug("Options is None, skipping")
                elif isinstance(options, str):
                    log_debug(f"Options is a string, attempting to parse: {options}")
                    try:
                        # Try JSON parsing first
                        parsed_options = json.loads(options)
                        args["options"] = parsed_options
                        log_debug(f"Parsed options as JSON successfully: {parsed_options}")
                    except json.JSONDecodeError:
                        # Try ast.literal_eval for Python list syntax
                        try:
                            import ast
                            parsed_options = ast.literal_eval(options)
                            args["options"] = parsed_options
                            log_debug(f"Parsed options using ast.literal_eval successfully: {parsed_options}")
                        except (ValueError, SyntaxError):
                            # Try to parse as a simple list of strings
                            try:
                                # Remove common prefixes/suffixes
                                cleaned = options.strip()
                                
                                # Check if it contains " -> " (arrow notation from user prompt)
                                if " -> " in cleaned:
                                    # Extract the part after the arrow
                                    parts = cleaned.split(" -> ", 1)
                                    if len(parts) > 1:
                                        cleaned = parts[1].strip()
                                
                                # Check if it contains " or " or " and " - common separator in natural language
                                if " or " in cleaned.lower() or " and " in cleaned.lower():
                                    # Split by " or " or " and "
                                    separator = " or " if " or " in cleaned.lower() else " and "
                                    items = [item.strip().strip('"').strip("'") for item in cleaned.split(separator)]
                                    args["options"] = [{"name": item} for item in items if item]
                                    log_debug(f"Parsed options with 'or/and' separator: {args['options']}")
                                elif "," in cleaned:
                                    # Split by comma (handles "High, Medium, Low" or "High,Medium,Low")
                                    items = [item.strip().strip('"').strip("'") for item in cleaned.split(',')]
                                    args["options"] = [{"name": item} for item in items if item]
                                    log_debug(f"Parsed options as comma-separated list: {args['options']}")
                                else:
                                    # Single option or no separator - treat as single option
                                    cleaned = cleaned.strip('[]').strip().strip('"').strip("'")
                                    if cleaned:
                                        args["options"] = [{"name": cleaned}]
                                        log_debug(f"Parsed options as single option: {args['options']}")
                                    else:
                                        log_debug(f"Empty options string, setting to None")
                                        args["options"] = None
                            except Exception as parse_error:
                                log_debug(f"Could not parse options: {parse_error}, setting to None")
                                args["options"] = None
                elif isinstance(options, list):
                    # Options is already a list, but ensure it's in the right format
                    log_debug(f"Options is already a list: {options}")
                    processed_options = []
                    for opt in options:
                        if isinstance(opt, dict):
                            # Already a dict, ensure it has 'name' key
                            if "name" in opt:
                                processed_options.append(opt)
                            else:
                                # Convert dict to have 'name' key
                                processed_options.append({"name": str(opt)})
                        elif isinstance(opt, str):
                            # String in list, convert to dict
                            processed_options.append({"name": opt})
                        else:
                            # Other type, convert to string
                            processed_options.append({"name": str(opt)})
                    args["options"] = processed_options
                    log_debug(f"Processed list options: {args['options']}")
                else:
                    # Other type, try to convert
                    log_debug(f"Options is unexpected type {type(options)}, attempting conversion")
                    try:
                        options_str = str(options)
                        if options_str.strip():
                            args["options"] = [{"name": options_str.strip()}]
                        else:
                            args["options"] = None
                    except Exception:
                        args["options"] = None
                
                log_debug(f"Final options after processing: {args.get('options')}")
            
            # For create_roadmap, handle nested structures BEFORE Pydantic validation
            # This is critical because Pydantic will fail if it sees string representations
            if tool_name == "create_roadmap" and isinstance(args, dict):
                log_debug("=== Processing create_roadmap ===")
                from .tool_schemas import CreateRoadmapProject, CreateRoadmapMilestoneData
                import ast
                import copy
                
                # Create a copy of args to avoid modifying the original
                processed_args = copy.deepcopy(args)
                
                # Handle project - might be a string representation of a dict
                if "project" in processed_args:
                    project_data = processed_args["project"]
                    log_debug(f"Project data type: {type(project_data)}")
                    log_debug(f"Project data value: {project_data}")
                    log_debug(f"Project data repr: {repr(project_data)}")
                    # If it's already a Pydantic model, skip
                    if not isinstance(project_data, BaseModel):
                        # If it's not already a dict, try to parse it
                        if not isinstance(project_data, dict):
                            # Convert to string for parsing attempts
                            project_str = str(project_data)
                            
                            # Try to parse string representation of dict
                            # First try ast.literal_eval for Python dict syntax
                            try:
                                project_data = ast.literal_eval(project_str)
                            except (ValueError, SyntaxError) as e:
                                # If that fails, try JSON parsing
                                try:
                                    import json
                                    # Replace single quotes with double quotes for JSON
                                    json_str = project_str.replace("'", '"')
                                    project_data = json.loads(json_str)
                                except json.JSONDecodeError:
                                    # Last resort: try eval (less safe but might work)
                                    try:
                                        project_data = eval(project_str)
                                    except Exception as eval_error:
                                        raise ValueError(f"Could not parse project data. Type: {type(project_data).__name__}, String: {project_str[:200]}, Error: {str(eval_error)}")
                        
                        # Ensure project_data is a dict before constructing the model
                        if not isinstance(project_data, dict):
                            raise ValueError(f"Project data must be a dict after parsing, got {type(project_data).__name__}: {str(project_data)[:200]}")
                        
                        # Now construct the Pydantic model
                        try:
                            log_debug(f"Creating CreateRoadmapProject from dict: {project_data}")
                            processed_args["project"] = CreateRoadmapProject(**project_data)
                            log_debug(f"Successfully created CreateRoadmapProject")
                        except Exception as e:
                            log_debug(f"Failed to create CreateRoadmapProject: {str(e)}")
                            import traceback
                            log_debug(f"Traceback: {traceback.format_exc()}")
                            raise ValueError(f"Failed to create CreateRoadmapProject from dict {project_data}: {str(e)}")
                    else:
                        log_debug(f"Project is already a BaseModel, skipping")
                        processed_args["project"] = project_data
                
                # Use processed_args instead of args for the rest of validation
                args = processed_args
                log_debug(f"Final processed args project type: {type(args.get('project'))}")
            
            # Use Pydantic for validation
            if issubclass(schema, BaseModel):
                # For create_roadmap, manual construction already done above
                # Just proceed with normal Pydantic validation
                try:
                    # Try Pydantic v2 model_validate first
                    if hasattr(schema, 'model_validate'):
                        return schema.model_validate(args)
                    else:
                        # Fallback for Pydantic v1
                        return schema(**args)
                except (AttributeError, TypeError, PydanticValidationError) as e:
                    # If model_validate fails, try Pydantic v1 syntax
                    try:
                        return schema(**args)
                    except Exception as e2:
                        # Provide more detailed error
                        error_details = str(e2)
                        if isinstance(e2, PydanticValidationError):
                            error_details = "; ".join([f"{err['loc']}: {err['msg']}" for err in e2.errors()])
                        raise ValueError(f"Failed to validate {tool_name} arguments: {error_details}")
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




