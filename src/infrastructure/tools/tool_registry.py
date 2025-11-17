"""Tool registry for managing MCP tools."""

from typing import Dict, Any, Optional, List
from .tool_validator import ToolDefinition


class ToolRegistry:
    """Central registry of all available tools."""
    
    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, ToolDefinition]
    
    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._register_built_in_tools()
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a new tool."""
        if tool.name in self._tools:
            import sys
            sys.stderr.write(f"Tool '{tool.name}' is already registered and will be overwritten.\n")
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_tools_for_mcp(self) -> List[Dict[str, Any]]:
        """Convert tools to MCP format for list_tools response."""
        tools_list = []
        for tool in self.get_all_tools():
            try:
                schema = self._convert_pydantic_to_json_schema(tool.schema)
                # Debug: log schema for create_project_field
                if tool.name == "create_project_field":
                    import sys
                    import json
                    sys.stderr.write(f"[ToolRegistry] Schema for {tool.name}:\n{json.dumps(schema, indent=2)}\n")
                tools_list.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": schema,
                })
            except Exception as e:
                import sys
                sys.stderr.write(f"Error generating schema for tool {tool.name}: {e}\n")
                # Add tool with basic schema if generation fails
                tools_list.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": {"type": "object", "properties": {}},
                })
        return tools_list
    
    def _register_built_in_tools(self) -> None:
        """Register all built-in tools."""
        from .tool_schemas import (
            # Roadmap and planning tools
            create_roadmap_tool,
            plan_sprint_tool,
            get_milestone_metrics_tool,
            get_sprint_metrics_tool,
            get_overdue_milestones_tool,
            get_upcoming_milestones_tool,
            
            # Project tools
            create_project_tool,
            list_projects_tool,
            get_project_tool,
            update_project_tool,
            delete_project_tool,
            
            # Milestone tools
            create_milestone_tool,
            list_milestones_tool,
            update_milestone_tool,
            delete_milestone_tool,
            
            # Issue tools
            create_issue_tool,
            list_issues_tool,
            get_issue_tool,
            update_issue_tool,
            
            # Issue comment tools
            add_issue_comment_tool,
            list_issue_comments_tool,
            update_issue_comment_tool,
            delete_issue_comment_tool,
            
            # Issue search tools
            search_issues_tool,
            
            # Project item filtering tools
            filter_project_items_tool,
            find_issues_by_field_tool,
            
            # Sprint tools
            create_sprint_tool,
            list_sprints_tool,
            get_current_sprint_tool,
            update_sprint_tool,
            add_issues_to_sprint_tool,
            remove_issues_from_sprint_tool,
            
            # Project field tools
            create_project_field_tool,
            list_project_fields_tool,
            update_project_field_tool,
            
            # Project view tools
            create_project_view_tool,
            list_project_views_tool,
            update_project_view_tool,
            delete_project_view_tool,
            
            # Project item tools
            add_project_item_tool,
            remove_project_item_tool,
            list_project_items_tool,
            
            # Field value tools
            set_field_value_tool,
            get_field_value_tool,
            clear_field_value_tool,
            
            # Label tools
            create_label_tool,
            list_labels_tool,
        )
        
        # Register roadmap and planning tools
        self.register_tool(create_roadmap_tool)
        self.register_tool(plan_sprint_tool)
        self.register_tool(get_milestone_metrics_tool)
        self.register_tool(get_sprint_metrics_tool)
        self.register_tool(get_overdue_milestones_tool)
        self.register_tool(get_upcoming_milestones_tool)
        
        # Register project tools
        self.register_tool(create_project_tool)
        self.register_tool(list_projects_tool)
        self.register_tool(get_project_tool)
        self.register_tool(update_project_tool)
        self.register_tool(delete_project_tool)
        
        # Register milestone tools
        self.register_tool(create_milestone_tool)
        self.register_tool(list_milestones_tool)
        self.register_tool(update_milestone_tool)
        self.register_tool(delete_milestone_tool)
        
        # Register issue tools
        self.register_tool(create_issue_tool)
        self.register_tool(list_issues_tool)
        self.register_tool(get_issue_tool)
        self.register_tool(update_issue_tool)
        
        # Register issue comment tools
        self.register_tool(add_issue_comment_tool)
        self.register_tool(list_issue_comments_tool)
        self.register_tool(update_issue_comment_tool)
        self.register_tool(delete_issue_comment_tool)
        
        # Register issue search tools
        self.register_tool(search_issues_tool)
        
        # Register project item filtering tools
        self.register_tool(filter_project_items_tool)
        self.register_tool(find_issues_by_field_tool)
        
        # Register sprint tools
        self.register_tool(create_sprint_tool)
        self.register_tool(list_sprints_tool)
        self.register_tool(get_current_sprint_tool)
        self.register_tool(update_sprint_tool)
        self.register_tool(add_issues_to_sprint_tool)
        self.register_tool(remove_issues_from_sprint_tool)
        
        # Register project field tools
        self.register_tool(create_project_field_tool)
        self.register_tool(list_project_fields_tool)
        self.register_tool(update_project_field_tool)
        
        # Register project view tools
        self.register_tool(create_project_view_tool)
        self.register_tool(list_project_views_tool)
        self.register_tool(update_project_view_tool)
        self.register_tool(delete_project_view_tool)
        
        # Register project item tools
        self.register_tool(add_project_item_tool)
        self.register_tool(remove_project_item_tool)
        self.register_tool(list_project_items_tool)
        
        # Register field value tools
        self.register_tool(set_field_value_tool)
        self.register_tool(get_field_value_tool)
        self.register_tool(clear_field_value_tool)
        
        # Register label tools
        self.register_tool(create_label_tool)
        self.register_tool(list_labels_tool)
    
    def _convert_pydantic_to_json_schema(self, schema: type) -> Dict[str, Any]:
        """Convert Pydantic model to JSON schema."""
        try:
            from pydantic import BaseModel
            if issubclass(schema, BaseModel):
                json_schema = schema.model_json_schema()
                
                # Special handling for create_project_field to make options more flexible
                # Check by schema name or by checking if it has the expected fields
                schema_name = getattr(schema, '__name__', '')
                is_create_field = (schema_name == "CreateProjectFieldArgs" or 
                                 ("properties" in json_schema and 
                                  "project_id" in json_schema.get("properties", {}) and
                                  "name" in json_schema.get("properties", {}) and
                                  "type" in json_schema.get("properties", {}) and
                                  "options" in json_schema.get("properties", {})))
                
                if is_create_field and "properties" in json_schema:
                    if "options" in json_schema["properties"]:
                        # Make options accept literally any format - we'll parse it in the validator
                        # This is the most permissive schema possible
                        json_schema["properties"]["options"] = {
                            "description": "Field options. Can be: array of objects like [{\"name\": \"High\"}], array of strings like [\"High\", \"Medium\"], comma-separated string like \"High, Medium, Low\", or JSON string. The validator will parse any format.",
                            "oneOf": [
                                {"type": "array"},
                                {"type": "string"},
                                {"type": "null"}
                            ]
                        }
                        # Also add to definitions if needed
                        if "definitions" not in json_schema:
                            json_schema["definitions"] = {}
                
                return json_schema
            else:
                # Fallback to basic schema
                return {"type": "object", "properties": {}}
        except Exception as e:
            import sys
            sys.stderr.write(f"Error converting schema to JSON: {e}\n")
            import traceback
            sys.stderr.write(f"Traceback: {traceback.format_exc()}\n")
            # Fallback to basic schema
            return {"type": "object", "properties": {}}

