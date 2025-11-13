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
    try:
        from ...domain.types import CreateIssue
        from dataclasses import asdict
        
        # Handle both dict and Pydantic model inputs
        if hasattr(args, 'model_dump'):
            # Pydantic model - convert to dict
            args_dict = args.model_dump()
        elif isinstance(args, dict):
            args_dict = args
        else:
            # Try to convert to dict
            args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
        
        create_issue = CreateIssue(
            title=get_arg_value(args_dict, "title"),
            description=get_arg_value(args_dict, "description"),
            milestone_id=get_arg_value(args_dict, "milestone_id"),
            assignees=get_arg_value(args_dict, "assignees", []),
            labels=get_arg_value(args_dict, "labels", []),
            priority=get_arg_value(args_dict, "priority"),
            issue_type=get_arg_value(args_dict, "type")
        )
        
        issue = await service.create_issue(create_issue)
        
        # Convert dataclass to dict properly
        issue_dict = asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue.__dict__
        
        # Ensure we have a valid dict with all fields
        if not issue_dict or not isinstance(issue_dict, dict):
            raise ValueError(f"Failed to serialize issue: {type(issue)}")
        
        return ToolResultFormatter.format_success(
            "create_issue",
            issue_dict,
            FormattingOptions(content_type=None)
        )
    except Exception as e:
        from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
        import traceback
        error_msg = str(e)
        error_type = type(e).__name__
        # Get more details if available
        if hasattr(e, 'args') and e.args:
            error_details = f"{error_type}: {error_msg}"
        else:
            error_details = f"{error_type}: {error_msg}"
        
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message=f"Error creating issue: {error_details}"
            )
        )


async def execute_create_milestone(
    service: ProjectManagementService,
    args: Dict[str, Any]
) -> MCPResponse:
    """Execute create_milestone tool."""
    from ...domain.types import CreateMilestone
    from dataclasses import asdict
    
    try:
        # Handle both dict and Pydantic model inputs
        if hasattr(args, 'model_dump'):
            # Pydantic model - convert to dict
            args_dict = args.model_dump()
        elif isinstance(args, dict):
            args_dict = args
        else:
            # Try to convert to dict
            args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
        
        create_milestone = CreateMilestone(
            title=get_arg_value(args_dict, "title"),
            description=get_arg_value(args_dict, "description"),
            due_date=get_arg_value(args_dict, "due_date"),
            status=None
        )
        
        milestone = await service.create_milestone(create_milestone)
        
        # Convert dataclass to dict properly
        if hasattr(milestone, '__dataclass_fields__'):
            milestone_dict = asdict(milestone)
        elif hasattr(milestone, '__dict__'):
            milestone_dict = milestone.__dict__
        else:
            # Fallback: create dict from milestone attributes
            milestone_dict = {
                'id': getattr(milestone, 'id', None),
                'title': getattr(milestone, 'title', None),
                'description': getattr(milestone, 'description', None),
                'due_date': getattr(milestone, 'due_date', None),
                'status': str(getattr(milestone, 'status', None)) if hasattr(milestone, 'status') else None,
                'created_at': getattr(milestone, 'created_at', None),
                'updated_at': getattr(milestone, 'updated_at', None),
                'url': getattr(milestone, 'url', None),
                'number': getattr(milestone, 'number', None),
                'progress': getattr(milestone, 'progress', None)
            }
        
        # Ensure we have a valid dict with all fields
        if not milestone_dict or not isinstance(milestone_dict, dict):
            raise ValueError(f"Failed to serialize milestone: {type(milestone)}")
        
        return ToolResultFormatter.format_success(
            "create_milestone",
            milestone_dict,
            FormattingOptions(content_type=None)
        )
    except Exception as e:
        from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
        import traceback
        error_msg = str(e)
        error_type = type(e).__name__
        # Get more details if available
        if hasattr(e, 'args') and e.args:
            error_details = f"{error_type}: {error_msg}"
        else:
            error_details = f"{error_type}: {error_msg}"
        
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message=f"Error creating milestone: {error_details}"
            )
        )


async def execute_get_issue(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute get_issue tool."""
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    issue = await service.get_issue(get_arg_value(args_dict, "issue_id"))
    
    # Convert dataclass to dict properly
    issue_dict = asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue.__dict__
    
    return ToolResultFormatter.format_success(
        "get_issue",
        issue_dict,
        FormattingOptions(content_type=None)
    )


async def execute_list_issues(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute list_issues tool."""
    from ...domain.resource_types import ResourceStatus
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    options = {}
    status_str = get_arg_value(args_dict, "status")
    if status_str:
        status_map = {
            "open": ResourceStatus.ACTIVE,
            "closed": ResourceStatus.CLOSED
        }
        options["status"] = status_map.get(status_str, ResourceStatus.ACTIVE)
    
    issues = await service.list_issues(options)
    
    # Convert dataclasses to dicts properly
    issues_list = [
        asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue.__dict__
        for issue in issues
    ]
    
    return ToolResultFormatter.format_success(
        "list_issues",
        issues_list,
        FormattingOptions(content_type=None)
    )


async def execute_list_milestones(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute list_milestones tool."""
    from ...domain.resource_types import ResourceStatus
    from dataclasses import asdict
    
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
    
    # Convert dataclasses to dicts properly
    milestones_list = [
        asdict(milestone) if hasattr(milestone, '__dataclass_fields__') else milestone.__dict__
        for milestone in milestones
    ]
    
    return ToolResultFormatter.format_success(
        "list_milestones",
        milestones_list,
        FormattingOptions(content_type=None)
    )


async def execute_get_milestone_metrics(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute get_milestone_metrics tool."""
    try:
        milestone_id = get_arg_value(args, "milestone_id")
        include_issues = get_arg_value(args, "include_issues", False)
        
        metrics = await service.get_milestone_metrics(milestone_id, include_issues)
        
        # Ensure metrics is a dict
        if not isinstance(metrics, dict):
            from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
            return MCPErrorResponse(
                version="1.0",
                request_id="",
                error=MCPErrorDetail(
                    code=MCPErrorCode.INTERNAL_ERROR.value,
                    message=f"Expected dict but got {type(metrics)}: {metrics}"
                )
            )
        
        return ToolResultFormatter.format_success(
            "get_milestone_metrics",
            metrics,
            FormattingOptions(content_type=None)
        )
    except Exception as e:
        from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message=f"Error getting milestone metrics: {str(e)}"
            )
        )


async def execute_get_overdue_milestones(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute get_overdue_milestones tool."""
    limit = get_arg_value(args, "limit", 10)
    include_issues = get_arg_value(args, "include_issues", False)
    
    milestones = await service.get_overdue_milestones(limit, include_issues)
    
    return ToolResultFormatter.format_success(
        "get_overdue_milestones",
        milestones,
        FormattingOptions(content_type=None)
    )


async def execute_get_upcoming_milestones(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute get_upcoming_milestones tool."""
    days_ahead = get_arg_value(args, "days_ahead", 30)
    limit = get_arg_value(args, "limit", 5)
    include_issues = get_arg_value(args, "include_issues", False)
    
    milestones = await service.get_upcoming_milestones(days_ahead, limit, include_issues)
    
    return ToolResultFormatter.format_success(
        "get_upcoming_milestones",
        milestones,
        FormattingOptions(content_type=None)
    )


async def execute_get_sprint_metrics(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute get_sprint_metrics tool."""
    metrics = await service.get_sprint_metrics(
        get_arg_value(args, "sprint_id"),
        get_arg_value(args, "include_issues", False)
    )
    
    return ToolResultFormatter.format_success(
        "get_sprint_metrics",
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


async def execute_add_issue_comment(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute add_issue_comment tool."""
    from ...domain.types import CreateIssueComment
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    issue_id = get_arg_value(args_dict, "issue_id")
    body = get_arg_value(args_dict, "body")
    
    create_comment = CreateIssueComment(body=body)
    comment = await service.create_issue_comment(issue_id, create_comment)
    
    # Convert dataclass to dict properly
    comment_dict = asdict(comment) if hasattr(comment, '__dataclass_fields__') else comment.__dict__
    
    return ToolResultFormatter.format_success(
        "add_issue_comment",
        comment_dict,
        FormattingOptions(content_type=None)
    )


async def execute_list_issue_comments(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute list_issue_comments tool."""
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    issue_id = get_arg_value(args_dict, "issue_id")
    comments = await service.list_issue_comments(issue_id)
    
    # Convert dataclasses to dicts properly
    comments_list = [
        asdict(comment) if hasattr(comment, '__dataclass_fields__') else comment.__dict__
        for comment in comments
    ]
    
    return ToolResultFormatter.format_success(
        "list_issue_comments",
        comments_list,
        FormattingOptions(content_type=None)
    )


async def execute_update_issue_comment(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute update_issue_comment tool."""
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    issue_id = get_arg_value(args_dict, "issue_id")
    comment_id = get_arg_value(args_dict, "comment_id")
    body = get_arg_value(args_dict, "body")
    
    comment = await service.update_issue_comment(issue_id, comment_id, body)
    
    # Convert dataclass to dict properly
    comment_dict = asdict(comment) if hasattr(comment, '__dataclass_fields__') else comment.__dict__
    
    return ToolResultFormatter.format_success(
        "update_issue_comment",
        comment_dict,
        FormattingOptions(content_type=None)
    )


async def execute_delete_issue_comment(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute delete_issue_comment tool."""
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    issue_id = get_arg_value(args_dict, "issue_id")
    comment_id = get_arg_value(args_dict, "comment_id")
    
    await service.delete_issue_comment(issue_id, comment_id)
    
    return ToolResultFormatter.format_success(
        "delete_issue_comment",
        {"success": True, "issue_id": issue_id, "comment_id": comment_id},
        FormattingOptions(content_type=None)
    )


async def execute_search_issues(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute search_issues tool."""
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    query = get_arg_value(args_dict, "query")
    issues = await service.search_issues(query)
    
    # Convert dataclasses to dicts properly
    issues_list = [
        asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue.__dict__
        for issue in issues
    ]
    
    return ToolResultFormatter.format_success(
        "search_issues",
        {
            "query": query,
            "count": len(issues_list),
            "issues": issues_list
        },
        FormattingOptions(content_type=None)
    )


async def execute_filter_project_items(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute filter_project_items tool."""
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    project_id = get_arg_value(args_dict, "project_id")
    field_filters = get_arg_value(args_dict, "field_filters")
    
    if not isinstance(field_filters, dict):
        from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.VALIDATION_ERROR.value,
                message="field_filters must be a dictionary"
            )
        )
    
    filtered_items = await service.filter_project_items(project_id, field_filters)
    
    return ToolResultFormatter.format_success(
        "filter_project_items",
        {
            "project_id": project_id,
            "filters": field_filters,
            "count": len(filtered_items),
            "items": filtered_items
        },
        FormattingOptions(content_type=None)
    )


async def execute_find_issues_by_field(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute find_issues_by_field tool."""
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    project_id = get_arg_value(args_dict, "project_id")
    field_name = get_arg_value(args_dict, "field_name")
    field_value = get_arg_value(args_dict, "field_value")
    
    issue_ids = await service.find_issues_by_field(project_id, field_name, field_value)
    
    return ToolResultFormatter.format_success(
        "find_issues_by_field",
        {
            "project_id": project_id,
            "field_name": field_name,
            "field_value": field_value,
            "count": len(issue_ids),
            "issue_ids": issue_ids
        },
        FormattingOptions(content_type=None)
    )


async def execute_update_issue(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute update_issue tool."""
    from ...domain.resource_types import ResourceStatus
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    update_data = {}
    title = get_arg_value(args_dict, "title")
    if title is not None:
        update_data["title"] = title
    description = get_arg_value(args_dict, "description")
    if description is not None:
        update_data["description"] = description
    status_str = get_arg_value(args_dict, "status")
    if status_str is not None:
        # Normalize status string for comparison (lowercase, replace spaces/underscores)
        normalized_status = status_str.lower().replace("_", " ").replace("-", " ").strip()
        
        status_map = {
            "open": ResourceStatus.ACTIVE,
            "closed": ResourceStatus.CLOSED,
            "in progress": ResourceStatus.ACTIVE,  # GitHub doesn't support in_progress, map to ACTIVE
            "in_progress": ResourceStatus.ACTIVE,
            "in-progress": ResourceStatus.ACTIVE
        }
        update_data["status"] = status_map.get(normalized_status, ResourceStatus.ACTIVE)
        
        # If status is "in progress" (in any format), also add/ensure "in-progress" label exists
        if normalized_status in ["in progress", "in_progress", "in-progress"]:
            # Get current labels or initialize empty list
            current_labels = get_arg_value(args_dict, "labels") or []
            # Convert to list of strings if needed
            if isinstance(current_labels, list):
                label_names = [str(l).lower() for l in current_labels]
            else:
                label_names = []
            
            # Add in-progress label if not already present
            if "in-progress" not in label_names and "in_progress" not in label_names:
                if isinstance(current_labels, list):
                    current_labels.append("in-progress")
                else:
                    current_labels = ["in-progress"]
                update_data["labels"] = current_labels
                # Also mark that we want to add this label
                update_data["_add_in_progress_label"] = True
    milestone_id = get_arg_value(args_dict, "milestone_id")
    if milestone_id is not None:
        update_data["milestone_id"] = milestone_id
    assignees = get_arg_value(args_dict, "assignees")
    if assignees is not None:
        update_data["assignees"] = assignees
    labels = get_arg_value(args_dict, "labels")
    if labels is not None:
        update_data["labels"] = labels
    
    issue_id = get_arg_value(args_dict, "issue_id")
    issue = await service.update_issue(issue_id, update_data)
    
    # Convert dataclass to dict properly
    issue_dict = asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue.__dict__
    
    return ToolResultFormatter.format_success(
        "update_issue",
        issue_dict,
        FormattingOptions(content_type=None)
    )


async def execute_update_milestone(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute update_milestone tool."""
    from dataclasses import asdict
    
    # Convert Pydantic model to dict if needed
    if hasattr(args, 'model_dump'):
        update_dict = args.model_dump(exclude_unset=True)
    elif isinstance(args, dict):
        update_dict = args
    else:
        update_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    milestone = await service.update_milestone(update_dict)
    
    # Convert dataclass to dict properly
    milestone_dict = asdict(milestone) if hasattr(milestone, '__dataclass_fields__') else milestone.__dict__
    
    return ToolResultFormatter.format_success(
        "update_milestone",
        milestone_dict,
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


async def execute_create_roadmap(
    service: ProjectManagementService,
    args: Dict[str, Any]
) -> MCPResponse:
    """Execute create_roadmap tool."""
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        # Pydantic model - convert to dict
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        # Try to convert to dict
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    # Extract project data
    project_data = get_arg_value(args_dict, "project")
    
    # Get owner from environment if not provided
    import os
    from ...env import GITHUB_OWNER
    default_owner = GITHUB_OWNER
    
    # Convert project_data to dict if it's a Pydantic model
    if hasattr(project_data, 'model_dump'):
        project_data = project_data.model_dump()
    elif not isinstance(project_data, dict):
        # Try to convert to dict
        project_data = {k: getattr(project_data, k) for k in dir(project_data) if not k.startswith('_')}
    
    if isinstance(project_data, dict):
        project_title = project_data.get("title")
        project_description = project_data.get("short_description")
        project_visibility = project_data.get("visibility", "private")
        project_owner = get_arg_value(args_dict, "owner") or default_owner
    else:
        # Handle Pydantic model
        project_title = getattr(project_data, "title", None)
        project_description = getattr(project_data, "short_description", None)
        project_visibility = getattr(project_data, "visibility", "private")
        project_owner = get_arg_value(args_dict, "owner") or default_owner
    
    if not project_title:
        from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INVALID_PARAMS.value,
                message="Project title is required"
            )
        )
    
    # Create the project first
    from ...domain.types import CreateProject
    create_project = CreateProject(
        title=project_title,
        owner=project_owner,
        short_description=project_description,
        visibility=project_visibility
    )
    
    project = await service.create_project(create_project)
    project_dict = asdict(project) if hasattr(project, '__dataclass_fields__') else project.__dict__
    
    # Extract milestones data
    milestones_data = get_arg_value(args_dict, "milestones", [])
    created_milestones = []
    created_issues = []
    
    for milestone_data in milestones_data:
        # Convert milestone_data to dict if it's a Pydantic model
        if hasattr(milestone_data, 'model_dump'):
            milestone_data = milestone_data.model_dump()
        elif not isinstance(milestone_data, dict):
            milestone_data = {k: getattr(milestone_data, k) for k in dir(milestone_data) if not k.startswith('_')}
        
        # Extract milestone info
        if isinstance(milestone_data, dict):
            milestone_info = milestone_data.get("milestone", {})
            issues_data = milestone_data.get("issues", [])
        else:
            milestone_info = getattr(milestone_data, "milestone", None)
            issues_data = getattr(milestone_data, "issues", [])
            if milestone_info:
                if hasattr(milestone_info, 'model_dump'):
                    milestone_info = milestone_info.model_dump()
                else:
                    milestone_info = milestone_info.__dict__ if hasattr(milestone_info, '__dict__') else milestone_info
        
        # Convert milestone_info to dict if needed
        if hasattr(milestone_info, 'model_dump'):
            milestone_info = milestone_info.model_dump()
        elif not isinstance(milestone_info, dict):
            milestone_info = {k: getattr(milestone_info, k) for k in dir(milestone_info) if not k.startswith('_')}
        
        if isinstance(milestone_info, dict):
            milestone_title = milestone_info.get("title")
            milestone_description = milestone_info.get("description")
            milestone_due_date = milestone_info.get("due_date")
        else:
            milestone_title = getattr(milestone_info, "title", None)
            milestone_description = getattr(milestone_info, "description", None)
            milestone_due_date = getattr(milestone_info, "due_date", None)
        
        if milestone_title:
            # Create milestone
            from ...domain.types import CreateMilestone
            create_milestone = CreateMilestone(
                title=milestone_title,
                description=milestone_description or "",
                due_date=milestone_due_date,
                status=None
            )
            
            milestone = await service.create_milestone(create_milestone)
            milestone_dict = asdict(milestone) if hasattr(milestone, '__dataclass_fields__') else milestone.__dict__
            created_milestones.append(milestone_dict)
            
            # Create issues for this milestone
            for issue_data in issues_data:
                # Convert issue_data to dict if it's a Pydantic model
                if hasattr(issue_data, 'model_dump'):
                    issue_data = issue_data.model_dump()
                elif not isinstance(issue_data, dict):
                    issue_data = {k: getattr(issue_data, k) for k in dir(issue_data) if not k.startswith('_')}
                
                if isinstance(issue_data, dict):
                    issue_title = issue_data.get("title")
                    issue_description = issue_data.get("description")
                    issue_priority = issue_data.get("priority", "medium")
                    issue_type = issue_data.get("type", "feature")
                    issue_assignees = issue_data.get("assignees", [])
                    issue_labels = issue_data.get("labels", [])
                else:
                    issue_title = getattr(issue_data, "title", None)
                    issue_description = getattr(issue_data, "description", None)
                    issue_priority = getattr(issue_data, "priority", "medium")
                    issue_type = getattr(issue_data, "type", "feature")
                    issue_assignees = getattr(issue_data, "assignees", [])
                    issue_labels = getattr(issue_data, "labels", [])
                
                if issue_title:
                    from ...domain.types import CreateIssue
                    create_issue = CreateIssue(
                        title=issue_title,
                        description=issue_description or "",
                        milestone_id=milestone.id,
                        assignees=issue_assignees,
                        labels=issue_labels,
                        priority=issue_priority,
                        issue_type=issue_type
                    )
                    
                    issue = await service.create_issue(create_issue)
                    issue_dict = asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue.__dict__
                    created_issues.append(issue_dict)
    
    result = {
        "project": project_dict,
        "milestones": created_milestones,
        "issues": created_issues,
        "summary": {
            "project_created": True,
            "milestones_created": len(created_milestones),
            "issues_created": len(created_issues)
        }
    }
    
    return ToolResultFormatter.format_success(
        "create_roadmap",
        result,
        FormattingOptions(content_type=None)
    )


async def execute_create_sprint(
    service: ProjectManagementService,
    args: Dict[str, Any]
) -> MCPResponse:
    """Execute create_sprint tool."""
    from ...domain.types import CreateSprint
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    create_sprint = CreateSprint(
        title=get_arg_value(args_dict, "title"),
        description=get_arg_value(args_dict, "description"),
        start_date=get_arg_value(args_dict, "start_date"),
        end_date=get_arg_value(args_dict, "end_date"),
        issues=get_arg_value(args_dict, "issue_ids", []),
        status=None
    )
    
    project_id = get_arg_value(args_dict, "project_id")
    sprint = await service.create_sprint(create_sprint, project_id)
    
    sprint_dict = asdict(sprint) if hasattr(sprint, '__dataclass_fields__') else sprint.__dict__
    
    return ToolResultFormatter.format_success(
        "create_sprint",
        sprint_dict,
        FormattingOptions(content_type=None)
    )


async def execute_plan_sprint(
    service: ProjectManagementService,
    args: Dict[str, Any]
) -> MCPResponse:
    """Execute plan_sprint tool."""
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    # Extract sprint data
    sprint_data = args_dict.get("sprint", {})
    if hasattr(sprint_data, 'model_dump'):
        sprint_data = sprint_data.model_dump()
    
    issue_ids = args_dict.get("issue_ids", [])
    project_id = args_dict.get("project_id")
    
    plan_data = {
        "sprint": sprint_data,
        "issue_ids": issue_ids,
        "project_id": project_id
    }
    
    sprint = await service.plan_sprint(plan_data)
    
    sprint_dict = asdict(sprint) if hasattr(sprint, '__dataclass_fields__') else sprint.__dict__
    
    return ToolResultFormatter.format_success(
        "plan_sprint",
        sprint_dict,
        FormattingOptions(content_type=None)
    )


async def execute_list_sprints(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute list_sprints tool."""
    from dataclasses import asdict
    
    status = get_arg_value(args, "status")
    
    sprints = await service.list_sprints(status)
    
    # Convert sprints to dictionaries
    sprints_list = []
    for sprint in sprints:
        sprint_dict = asdict(sprint) if hasattr(sprint, '__dataclass_fields__') else sprint.__dict__
        sprints_list.append(sprint_dict)
    
    return ToolResultFormatter.format_success(
        "list_sprints",
        sprints_list,
        FormattingOptions(content_type=None)
    )


async def execute_add_issues_to_sprint(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute add_issues_to_sprint tool."""
    sprint_id = get_arg_value(args, "sprint_id")
    issue_ids = get_arg_value(args, "issue_ids", [])
    
    if not sprint_id:
        from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INVALID_REQUEST.value,
                message="Sprint ID is required"
            )
        )
    
    if not issue_ids:
        from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INVALID_REQUEST.value,
                message="At least one issue ID is required"
            )
        )
    
    # Add each issue to the sprint
    results = []
    for issue_id in issue_ids:
        try:
            sprint = await service.add_issue_to_sprint(sprint_id, issue_id)
            results.append({
                "issue_id": issue_id,
                "status": "success",
                "sprint_id": sprint.id if hasattr(sprint, 'id') else sprint_id
            })
        except Exception as e:
            results.append({
                "issue_id": issue_id,
                "status": "error",
                "error": str(e)
            })
    
    return ToolResultFormatter.format_success(
        "add_issues_to_sprint",
        {
            "sprint_id": sprint_id,
            "results": results,
            "total_issues": len(issue_ids),
            "successful": len([r for r in results if r.get("status") == "success"]),
            "failed": len([r for r in results if r.get("status") == "error"])
        },
        FormattingOptions(content_type=None)
    )


async def execute_set_field_value(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute set_field_value tool."""
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    project_id = get_arg_value(args_dict, "project_id")
    item_id = get_arg_value(args_dict, "item_id")
    field_id = get_arg_value(args_dict, "field_id")
    value = get_arg_value(args_dict, "value")
    
    if not project_id or not item_id or not field_id:
        from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.VALIDATION_ERROR.value,
                message="project_id, item_id, and field_id are required"
            )
        )
    
    success = await service.set_project_item_field_value(project_id, item_id, field_id, value)
    
    return ToolResultFormatter.format_success(
        "set_field_value",
        {
            "success": success,
            "project_id": project_id,
            "item_id": item_id,
            "field_id": field_id,
            "value": value
        },
        FormattingOptions(content_type=None)
    )


async def execute_add_project_item(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute add_project_item tool."""
    from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    project_id = get_arg_value(args_dict, "project_id")
    content_id = get_arg_value(args_dict, "content_id")
    content_type = get_arg_value(args_dict, "content_type")
    
    if not project_id or not content_id or not content_type:
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.VALIDATION_ERROR.value,
                message="project_id, content_id, and content_type are required"
            )
        )
    
    try:
        project_repo = service.get_repository_factory().create_project_repository()
        
        # If content_type is "Issue" and content_id is a number, we need to get the node ID
        if content_type.lower() == "issue":
            try:
                # Try to parse as integer (issue number)
                issue_number = int(content_id)
                # Get issue node ID
                issue_node_query = """
                query($owner: String!, $repo: String!, $number: Int!) {
                  repository(owner: $owner, name: $repo) {
                    issue(number: $number) {
                      id
                    }
                  }
                }
                """
                
                issue_node_response = await project_repo.graphql(issue_node_query, {
                    "owner": project_repo.owner,
                    "repo": project_repo.repository,
                    "number": issue_number
                })
                
                issue_node_id = issue_node_response.get("repository", {}).get("issue", {}).get("id")
                if not issue_node_id:
                    return MCPErrorResponse(
                        version="1.0",
                        request_id="",
                        error=MCPErrorDetail(
                            code=MCPErrorCode.RESOURCE_NOT_FOUND.value,
                            message=f"Issue {content_id} not found"
                        )
                    )
                
                content_id = issue_node_id
            except ValueError:
                # content_id is already a node ID, use it as is
                pass
        
        # Add item to project
        add_item_mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {
            projectId: $projectId
            contentId: $contentId
          }) {
            item {
              id
            }
          }
        }
        """
        
        response = await project_repo.graphql(add_item_mutation, {
            "projectId": project_id,
            "contentId": content_id
        })
        
        item = response.get("addProjectV2ItemById", {}).get("item", {})
        if not item:
            return MCPErrorResponse(
                version="1.0",
                request_id="",
                error=MCPErrorDetail(
                    code=MCPErrorCode.INTERNAL_ERROR.value,
                    message="Failed to add item to project"
                )
            )
        
        item_id = item.get("id")
        
        # If this is an issue, try to set priority and type fields if they exist
        if content_type.lower() == "issue":
            try:
                # Get the issue to check if it has priority/type stored
                issue_number = int(content_id) if content_id.isdigit() else None
                if issue_number:
                    # Try to get issue details - but priority/type aren't stored in GitHub issues
                    # They need to be set as project fields
                    # For now, we'll try to set them if provided in the args
                    priority = get_arg_value(args_dict, "priority")
                    issue_type = get_arg_value(args_dict, "type")
                    
                    # Try to set Priority field if provided
                    if priority:
                        priority_field = await project_repo.get_field_by_name(project_id, "Priority")
                        if priority_field:
                            try:
                                await project_repo.set_field_value(
                                    project_id,
                                    item_id,
                                    priority_field["id"],
                                    priority
                                )
                            except Exception as e:
                                # Log but don't fail
                                project_repo._logger.debug(f"Could not set Priority field: {str(e)}")
                    
                    # Try to set Type field if provided
                    if issue_type:
                        type_field = await project_repo.get_field_by_name(project_id, "Type")
                        if not type_field:
                            # Try "Issue Type" as alternative name
                            type_field = await project_repo.get_field_by_name(project_id, "Issue Type")
                        if type_field:
                            try:
                                await project_repo.set_field_value(
                                    project_id,
                                    item_id,
                                    type_field["id"],
                                    issue_type
                                )
                            except Exception as e:
                                # Log but don't fail
                                project_repo._logger.debug(f"Could not set Type field: {str(e)}")
            except Exception as e:
                # Log but don't fail the operation
                project_repo._logger.debug(f"Could not set priority/type fields: {str(e)}")
        
        return ToolResultFormatter.format_success(
            "add_project_item",
            {
                "success": True,
                "project_id": project_id,
                "item_id": item_id,
                "content_id": content_id,
                "content_type": content_type
            },
            FormattingOptions(content_type=None)
        )
    except Exception as e:
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message=f"Error adding item to project: {str(e)}"
            )
        )


async def execute_create_project_field(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute create_project_field tool."""
    from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    project_id = get_arg_value(args_dict, "project_id")
    name = get_arg_value(args_dict, "name")
    field_type = get_arg_value(args_dict, "type")
    options = get_arg_value(args_dict, "options")
    description = get_arg_value(args_dict, "description")
    required = get_arg_value(args_dict, "required")
    
    if not project_id or not name or not field_type:
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.VALIDATION_ERROR.value,
                message="project_id, name, and type are required"
            )
        )
    
    try:
        project_repo = service.get_repository_factory().create_project_repository()
        
        field_data = {
            "name": name,
            "type": field_type
        }
        
        # Handle options - might come as string or list
        if options:
            if isinstance(options, str):
                # Try to parse as JSON first
                import json
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    # If not JSON, try ast.literal_eval for Python list syntax
                    try:
                        import ast
                        options = ast.literal_eval(options)
                    except (ValueError, SyntaxError):
                        # If that fails, treat as single option
                        options = [{"name": options}]
            
            # Ensure options is a list
            if not isinstance(options, list):
                options = [options]
            
            # Ensure all items are dicts with required fields
            processed_options = []
            for opt in options:
                if isinstance(opt, dict):
                    # Ensure color and description are present
                    processed_opt = {
                        "name": opt.get("name", str(opt)),
                        "color": opt.get("color", "GRAY"),
                        "description": opt.get("description", "")
                    }
                    processed_options.append(processed_opt)
                else:
                    # Convert to dict
                    processed_options.append({
                        "name": str(opt),
                        "color": "GRAY",
                        "description": ""
                    })
            
            field_data["options"] = processed_options
        elif field_type.lower() == "single_select":
            # For single_select fields, GitHub requires at least one option
            # Add a generic default option if none provided
            field_data["options"] = [{"name": "Option 1", "color": "GRAY", "description": ""}]
        if description:
            field_data["description"] = description
        if required is not None:
            field_data["required"] = required
        
        field = await project_repo.create_field(project_id, field_data)
        
        # Convert dataclass to dict properly
        if hasattr(field, '__dataclass_fields__'):
            field_dict = asdict(field)
            # Convert FieldOption objects to dicts if they exist
            if 'options' in field_dict and field_dict['options']:
                field_dict['options'] = [
                    {'id': opt.id, 'name': opt.name, 'color': opt.color, 'description': opt.description}
                    if hasattr(opt, 'id') else {'name': str(opt)}
                    for opt in field_dict['options']
                ]
        else:
            field_dict = field.__dict__ if hasattr(field, '__dict__') else {}
        
        return ToolResultFormatter.format_success(
            "create_project_field",
            field_dict,
            FormattingOptions(content_type=None)
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_msg = f"Error creating project field: {str(e)}\nTraceback:\n{error_traceback}"
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message=error_msg
            )
        )


async def execute_create_label(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute create_label tool."""
    from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    name = get_arg_value(args_dict, "name")
    color = get_arg_value(args_dict, "color")
    description = get_arg_value(args_dict, "description")
    
    if not name or not color:
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.VALIDATION_ERROR.value,
                message="name and color are required"
            )
        )
    
    try:
        # Get the repository to create labels
        issue_repo = service.get_repository_factory().create_issue_repository()
        repo = issue_repo.repo
        
        # Convert color name to hex if needed
        color_map = {
            "red": "d73a4a",
            "blue": "0366d6",
            "green": "28a745",
            "purple": "6f42c1",
            "yellow": "ffc107",
            "orange": "fd7e14",
            "pink": "e83e8c",
            "gray": "6c757d",
            "grey": "6c757d"
        }
        
        # If color is a name, convert to hex
        if color.lower() in color_map:
            color_hex = color_map[color.lower()]
        elif color.startswith("#"):
            # Remove # if present
            color_hex = color[1:]
        else:
            # Assume it's already hex
            color_hex = color
        
        # Check if label already exists
        label = None
        action = None
        try:
            # Try to get existing label
            existing_label = repo.get_label(name)
            # Label exists - update it
            def _update_label():
                existing_label.edit(
                    name=name,
                    color=color_hex,
                    description=description or ""
                )
                return existing_label
            
            label = await issue_repo.with_retry(_update_label, "updating label")
            action = "updated"
        except Exception as get_error:
            # Label doesn't exist or couldn't be retrieved - try to create it
            try:
                def _create_label():
                    return repo.create_label(
                        name=name,
                        color=color_hex,
                        description=description or ""
                    )
                
                label = await issue_repo.with_retry(_create_label, "creating label")
                action = "created"
            except Exception as create_error:
                # If creation also fails with "already_exists", try to get and update again
                if "already_exists" in str(create_error).lower():
                    try:
                        existing_label = repo.get_label(name)
                        def _update_label():
                            existing_label.edit(
                                name=name,
                                color=color_hex,
                                description=description or ""
                            )
                            return existing_label
                        
                        label = await issue_repo.with_retry(_update_label, "updating label")
                        action = "updated"
                    except Exception:
                        # Re-raise the original create error if update also fails
                        raise create_error
                else:
                    raise create_error
        
        return ToolResultFormatter.format_success(
            "create_label",
            {
                "name": label.name,
                "color": f"#{label.color}",
                "description": label.description or "",
                "url": label.url,
                "action": action
            },
            FormattingOptions(content_type=None)
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_msg = f"Error creating label: {str(e)}\nTraceback:\n{error_traceback}"
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message=error_msg
            )
        )


async def execute_list_labels(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute list_labels tool."""
    from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    limit = get_arg_value(args_dict, "limit")
    
    try:
        # Get the repository to list labels
        issue_repo = service.get_repository_factory().create_issue_repository()
        repo = issue_repo.repo
        
        # Get all labels
        def _get_labels():
            return list(repo.get_labels())
        
        labels = await issue_repo.with_retry(_get_labels, "listing labels")
        
        # Convert labels to dict format
        labels_list = []
        for label in labels:
            labels_list.append({
                "name": label.name,
                "color": f"#{label.color}",
                "description": label.description or "",
                "url": label.url
            })
        
        # Apply limit if specified
        if limit and limit > 0:
            labels_list = labels_list[:limit]
        
        return ToolResultFormatter.format_success(
            "list_labels",
            labels_list,
            FormattingOptions(content_type=None)
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_msg = f"Error listing labels: {str(e)}\nTraceback:\n{error_traceback}"
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message=error_msg
            )
        )


async def execute_list_project_fields(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute list_project_fields tool."""
    from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    project_id = get_arg_value(args_dict, "project_id")
    
    if not project_id:
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.VALIDATION_ERROR.value,
                message="project_id is required"
            )
        )
    
    try:
        project_repo = service.get_repository_factory().create_project_repository()
        
        # Get all fields for the project
        fields = await project_repo.list_fields(project_id)
        
        # Convert fields to dict format
        fields_list = []
        for field in fields:
            if hasattr(field, '__dataclass_fields__'):
                field_dict = asdict(field)
                # Convert FieldOption objects to dicts if they exist
                if 'options' in field_dict and field_dict['options']:
                    field_dict['options'] = [
                        {'id': opt.id, 'name': opt.name, 'color': opt.color, 'description': opt.description}
                        if hasattr(opt, 'id') else {'name': str(opt)}
                        for opt in field_dict['options']
                    ]
            else:
                field_dict = field.__dict__ if hasattr(field, '__dict__') else {}
            
            fields_list.append(field_dict)
        
        return ToolResultFormatter.format_success(
            "list_project_fields",
            fields_list,
            FormattingOptions(content_type=None)
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_msg = f"Error listing project fields: {str(e)}\nTraceback:\n{error_traceback}"
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message=error_msg
            )
        )


async def execute_create_project_view(
    service: ProjectManagementService,
    args: Any
) -> MCPResponse:
    """Execute create_project_view tool."""
    from ...domain.mcp_types import MCPErrorCode, MCPErrorDetail, MCPErrorResponse
    from dataclasses import asdict
    
    # Handle both dict and Pydantic model inputs
    if hasattr(args, 'model_dump'):
        args_dict = args.model_dump()
    elif isinstance(args, dict):
        args_dict = args
    else:
        args_dict = {k: getattr(args, k) for k in dir(args) if not k.startswith('_')}
    
    project_id = get_arg_value(args_dict, "project_id")
    name = get_arg_value(args_dict, "name")
    layout = get_arg_value(args_dict, "layout")
    
    if not project_id or not name or not layout:
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.VALIDATION_ERROR.value,
                message="project_id, name, and layout are required"
            )
        )
    
    try:
        project_repo = service.get_repository_factory().create_project_repository()
        
        # Map layout string to ViewLayout (it's a type alias, not an enum)
        # ViewLayout = str  # 'board' | 'table' | 'timeline' | 'roadmap'
        layout_map = {
            "board": "board",
            "table": "table",
            "timeline": "timeline",
            "roadmap": "roadmap"
        }
        
        view_layout = layout_map.get(layout.lower(), "board")
        
        # Create view
        view = await project_repo.create_view(project_id, name, view_layout)
        
        # Convert dataclass to dict properly
        if hasattr(view, '__dataclass_fields__'):
            view_dict = asdict(view)
        else:
            view_dict = view.__dict__ if hasattr(view, '__dict__') else {}
        
        return ToolResultFormatter.format_success(
            "create_project_view",
            view_dict,
            FormattingOptions(content_type=None)
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_msg = f"Error creating project view: {str(e)}\nTraceback:\n{error_traceback}"
        return MCPErrorResponse(
            version="1.0",
            request_id="",
            error=MCPErrorDetail(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message=error_msg
            )
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
    
    # Issue comment tools
    "add_issue_comment": execute_add_issue_comment,
    "list_issue_comments": execute_list_issue_comments,
    "update_issue_comment": execute_update_issue_comment,
    "delete_issue_comment": execute_delete_issue_comment,
    
    # Issue search tools
    "search_issues": execute_search_issues,
    
    # Project item filtering tools
    "filter_project_items": execute_filter_project_items,
    "find_issues_by_field": execute_find_issues_by_field,
    
    # Milestone tools
    "create_milestone": execute_create_milestone,
    "list_milestones": execute_list_milestones,
    "get_milestone_metrics": execute_get_milestone_metrics,
    "get_overdue_milestones": execute_get_overdue_milestones,
    "get_upcoming_milestones": execute_get_upcoming_milestones,
    "update_milestone": execute_update_milestone,
    "delete_milestone": execute_delete_milestone,
    
    # Roadmap tools
    "create_roadmap": execute_create_roadmap,
    
    # Sprint tools
    "create_sprint": execute_create_sprint,
    "plan_sprint": execute_plan_sprint,
    "get_sprint_metrics": execute_get_sprint_metrics,
    "list_sprints": execute_list_sprints,
    "add_issues_to_sprint": execute_add_issues_to_sprint,
    
    # Field value tools
    "set_field_value": execute_set_field_value,
    
    # Project item tools
    "add_project_item": execute_add_project_item,
    
    # Project field tools
    "create_project_field": execute_create_project_field,
    
    # Label tools
    "create_label": execute_create_label,
    "list_labels": execute_list_labels,
    
    # Project field tools
    "list_project_fields": execute_list_project_fields,
    
    # Project view tools
    "create_project_view": execute_create_project_view,
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

