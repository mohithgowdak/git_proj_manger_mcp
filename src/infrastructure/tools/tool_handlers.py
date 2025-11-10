"""Tool handlers for MCP tools."""

from typing import Any, Dict
from pydantic import BaseModel, Field
from ...domain.mcp_types import MCPResponse
from ..tools.tool_result_formatter import ToolResultFormatter, FormattingOptions
from ...services.project_management_service import ProjectManagementService


def get_arg_value(args: Any, key: str, default: Any = None) -> Any:
    """Get a value from args, supporting both dict and Pydantic model."""
    if hasattr(args, key):
        # Pydantic model - use attribute access
        value = getattr(args, key, default)
        # Only return default if value is None AND default is provided AND default is not None
        if value is None and default is not None:
            return default
        return value
    elif isinstance(args, dict):
        # Dictionary - use .get()
        return args.get(key, default)
    else:
        # Fallback - try attribute access
        try:
            value = getattr(args, key, default)
            if value is None and default is not None:
                return default
            return value
        except AttributeError:
            return default


# Pydantic schemas for tool arguments
class CreateIssueArgs(BaseModel):
    """Create issue arguments."""
    title: str = Field(..., min_length=1, description="Issue title")
    description: str = Field(..., min_length=1, description="Issue description")
    milestone_id: str | None = Field(None, description="Milestone ID")
    assignees: list[str] = Field(default_factory=list, description="Assignees")
    labels: list[str] = Field(default_factory=list, description="Labels")
    priority: str | None = Field(None, description="Priority")
    type: str | None = Field(None, description="Issue type")


class CreateMilestoneArgs(BaseModel):
    """Create milestone arguments."""
    title: str = Field(..., min_length=1, description="Milestone title")
    description: str = Field(..., min_length=1, description="Milestone description")
    due_date: str | None = Field(None, description="Due date (ISO format)")


class GetIssueArgs(BaseModel):
    """Get issue arguments."""
    issue_id: str = Field(..., min_length=1, description="Issue ID")


class GetMilestoneArgs(BaseModel):
    """Get milestone arguments."""
    milestone_id: str = Field(..., min_length=1, description="Milestone ID")


class ListIssuesArgs(BaseModel):
    """List issues arguments."""
    status: str = Field("open", description="Issue status")
    limit: int | None = Field(None, description="Limit")


class ListMilestonesArgs(BaseModel):
    """List milestones arguments."""
    status: str = Field("open", description="Milestone status")
    sort: str | None = Field(None, description="Sort field")
    direction: str | None = Field(None, description="Sort direction")


class GetMilestoneMetricsArgs(BaseModel):
    """Get milestone metrics arguments."""
    milestone_id: str = Field(..., min_length=1, description="Milestone ID")
    include_issues: bool = Field(False, description="Include issues")


# Tool handler functions
async def execute_create_issue(
    service: ProjectManagementService,
    args: Dict[str, Any]
) -> MCPResponse:
    """Execute create_issue tool."""
    from ...domain.types import CreateIssue
    
    create_issue = CreateIssue(
        title=get_arg_value(args, "title"),
        description=get_arg_value(args, "description"),
        milestone_id=get_arg_value(args, "milestone_id"),
        assignees=get_arg_value(args, "assignees", []),
        labels=get_arg_value(args, "labels", []),
        priority=get_arg_value(args, "priority"),
        issue_type=get_arg_value(args, "type")
    )
    
    issue = await service.create_issue(create_issue)
    
    return ToolResultFormatter.format_success(
        "create_issue",
        issue.__dict__,
        FormattingOptions(content_type=None)
    )


async def execute_create_milestone(
    service: ProjectManagementService,
    args: Dict[str, Any]
) -> MCPResponse:
    """Execute create_milestone tool."""
    from ...domain.types import CreateMilestone
    
    create_milestone = CreateMilestone(
        title=get_arg_value(args, "title"),
        description=get_arg_value(args, "description"),
        due_date=get_arg_value(args, "due_date"),
        status=None
    )
    
    milestone = await service.create_milestone(create_milestone)
    
    return ToolResultFormatter.format_success(
        "create_milestone",
        milestone.__dict__,
        FormattingOptions(content_type=None)
    )


async def execute_get_issue(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute get_issue tool."""
    issue = await service.get_issue(get_arg_value(args, "issue_id"))
    
    return ToolResultFormatter.format_success(
        "get_issue",
        issue.__dict__,
        FormattingOptions(content_type=None)
    )


async def execute_list_issues(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute list_issues tool."""
    from ...domain.resource_types import ResourceStatus
    
    options = {}
    status_str = get_arg_value(args, "status")
    if status_str:
        status_map = {
            "open": ResourceStatus.ACTIVE,
            "closed": ResourceStatus.CLOSED
        }
        options["status"] = status_map.get(status_str, ResourceStatus.ACTIVE)
    
    issues = await service.list_issues(options)
    
    return ToolResultFormatter.format_success(
        "list_issues",
        [issue.__dict__ for issue in issues],
        FormattingOptions(content_type=None)
    )


async def execute_list_milestones(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute list_milestones tool."""
    from ...domain.resource_types import ResourceStatus
    
    status_map = {
        "open": ResourceStatus.ACTIVE,
        "closed": ResourceStatus.CLOSED
    }
    status_str = get_arg_value(args, "status", "open")
    status = status_map.get(status_str, ResourceStatus.ACTIVE)
    
    milestones = await service.list_milestones(
        status=status,
        sort=get_arg_value(args, "sort"),
        direction=get_arg_value(args, "direction")
    )
    
    return ToolResultFormatter.format_success(
        "list_milestones",
        [milestone.__dict__ for milestone in milestones],
        FormattingOptions(content_type=None)
    )


async def execute_get_milestone_metrics(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute get_milestone_metrics tool."""
    metrics = await service.get_milestone_metrics(
        get_arg_value(args, "milestone_id"),
        get_arg_value(args, "include_issues", False)
    )
    
    return ToolResultFormatter.format_success(
        "get_milestone_metrics",
        metrics,
        FormattingOptions(content_type=None)
    )


# Additional tool handlers
async def execute_create_project(
    service: ProjectManagementService,
    args: Dict[str, Any]
) -> MCPResponse:
    """Execute create_project tool."""
    from ...domain.types import CreateProject
    
    create_project = CreateProject(
        title=get_arg_value(args, "title"),
        owner=get_arg_value(args, "owner"),
        short_description=get_arg_value(args, "short_description"),
        visibility=get_arg_value(args, "visibility", "private")
    )
    
    project = await service.create_project(create_project)
    
    return ToolResultFormatter.format_success(
        "create_project",
        project.__dict__ if hasattr(project, '__dict__') else project,
        FormattingOptions(content_type=None)
    )


async def execute_list_projects(
    service: ProjectManagementService,
    args: Any  # Can be Dict or Pydantic model
) -> MCPResponse:
    """Execute list_projects tool."""
    from ...domain.resource_types import ResourceStatus
    
    status_str = get_arg_value(args, "status", "active")
    limit = get_arg_value(args, "limit")
    
    status_map = {
        "active": ResourceStatus.ACTIVE,
        "closed": ResourceStatus.CLOSED
    }
    status = status_map.get(status_str, ResourceStatus.ACTIVE)
    
    projects = await service.list_projects(status=status, limit=limit)
    
    return ToolResultFormatter.format_success(
        "list_projects",
        [project.__dict__ if hasattr(project, '__dict__') else project for project in projects],
        FormattingOptions(content_type=None)
    )


async def execute_get_project(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute get_project tool."""
    project = await service.get_project(get_arg_value(args, "project_id"))
    
    return ToolResultFormatter.format_success(
        "get_project",
        project.__dict__,
        FormattingOptions(content_type=None)
    )


async def execute_update_project(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute update_project tool."""
    # Convert Pydantic model to dict if needed
    if hasattr(args, 'model_dump'):
        update_dict = args.model_dump(exclude_unset=True)
    elif isinstance(args, dict):
        update_dict = args
    else:
        update_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    project = await service.update_project(update_dict)
    
    return ToolResultFormatter.format_success(
        "update_project",
        project.__dict__ if hasattr(project, '__dict__') else project,
        FormattingOptions(content_type=None)
    )


async def execute_delete_project(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute delete_project tool."""
    project_id = get_arg_value(args, "project_id")
    await service.delete_project({"project_id": project_id})
    
    return ToolResultFormatter.format_success(
        "delete_project",
        {"success": True, "project_id": project_id},
        FormattingOptions(content_type=None)
    )


async def execute_update_issue(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute update_issue tool."""
    from ...domain.resource_types import ResourceStatus
    
    update_data = {}
    title = get_arg_value(args, "title")
    if title is not None:
        update_data["title"] = title
    description = get_arg_value(args, "description")
    if description is not None:
        update_data["description"] = description
    status_str = get_arg_value(args, "status")
    if status_str is not None:
        status_map = {"open": ResourceStatus.ACTIVE, "closed": ResourceStatus.CLOSED}
        update_data["status"] = status_map.get(status_str, ResourceStatus.ACTIVE)
    milestone_id = get_arg_value(args, "milestone_id")
    if milestone_id is not None:
        update_data["milestone_id"] = milestone_id
    assignees = get_arg_value(args, "assignees")
    if assignees is not None:
        update_data["assignees"] = assignees
    labels = get_arg_value(args, "labels")
    if labels is not None:
        update_data["labels"] = labels
    
    issue_id = get_arg_value(args, "issue_id")
    issue = await service.update_issue(issue_id, update_data)
    
    return ToolResultFormatter.format_success(
        "update_issue",
        issue.__dict__,
        FormattingOptions(content_type=None)
    )


async def execute_update_milestone(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute update_milestone tool."""
    # Convert Pydantic model to dict if needed
    if hasattr(args, 'model_dump'):
        update_dict = args.model_dump(exclude_unset=True)
    elif isinstance(args, dict):
        update_dict = args
    else:
        update_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    milestone = await service.update_milestone(update_dict)
    
    return ToolResultFormatter.format_success(
        "update_milestone",
        milestone.__dict__,
        FormattingOptions(content_type=None)
    )


async def execute_delete_milestone(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute delete_milestone tool."""
    milestone_id = get_arg_value(args, "milestone_id")
    await service.delete_milestone({"milestone_id": milestone_id})
    
    return ToolResultFormatter.format_success(
        "delete_milestone",
        {"success": True, "milestone_id": milestone_id},
        FormattingOptions(content_type=None)
    )


# Tool handler registry
TOOL_HANDLERS: Dict[str, callable] = {
    # Project tools
    "create_project": execute_create_project,
    "list_projects": execute_list_projects,
    "get_project": execute_get_project,
    "update_project": execute_update_project,
    "delete_project": execute_delete_project,
    
    # Issue tools
    "create_issue": execute_create_issue,
    "get_issue": execute_get_issue,
    "list_issues": execute_list_issues,
    "update_issue": execute_update_issue,
    
    # Milestone tools
    "create_milestone": execute_create_milestone,
    "list_milestones": execute_list_milestones,
    "get_milestone_metrics": execute_get_milestone_metrics,
    "update_milestone": execute_update_milestone,
    "delete_milestone": execute_delete_milestone,
}


async def execute_tool(
    tool_name: str,
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute a tool by name."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.RESOURCE_NOT_FOUND.value,
                message=f"Tool '{tool_name}' not found"
            )
        )
    
    return await handler(service, args)

