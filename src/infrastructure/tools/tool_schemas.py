"""Tool schemas and definitions for MCP tools."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from .tool_validator import ToolDefinition


# ============================================================================
# Pydantic Schemas for Tool Arguments
# ============================================================================

class CreateRoadmapProject(BaseModel):
    """Create roadmap project."""
    title: str = Field(..., min_length=1, description="Project title")
    short_description: Optional[str] = Field(None, description="Project short description")
    visibility: str = Field(..., description="Project visibility")


class CreateRoadmapMilestone(BaseModel):
    """Create roadmap milestone."""
    title: str = Field(..., min_length=1, description="Milestone title")
    description: str = Field(..., min_length=1, description="Milestone description")
    due_date: Optional[str] = Field(None, description="Due date (ISO format)")


class CreateRoadmapIssue(BaseModel):
    """Create roadmap issue."""
    title: str = Field(..., min_length=1, description="Issue title")
    description: str = Field(..., min_length=1, description="Issue description")
    priority: str = Field("medium", description="Priority")
    type: str = Field("feature", description="Issue type")
    assignees: List[str] = Field(default_factory=list, description="Assignees")
    labels: List[str] = Field(default_factory=list, description="Labels")


class CreateRoadmapMilestoneData(BaseModel):
    """Create roadmap milestone data."""
    milestone: CreateRoadmapMilestone
    issues: List[CreateRoadmapIssue] = Field(default_factory=list, description="Issues")


class CreateRoadmapArgs(BaseModel):
    """Create roadmap arguments."""
    project: CreateRoadmapProject
    milestones: List[CreateRoadmapMilestoneData]


class PlanSprintSprint(BaseModel):
    """Plan sprint sprint."""
    title: str = Field(..., min_length=1, description="Sprint title")
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")
    goals: List[str] = Field(default_factory=list, description="Sprint goals")


class PlanSprintArgs(BaseModel):
    """Plan sprint arguments."""
    sprint: PlanSprintSprint
    issue_ids: List[str] = Field(default_factory=list, description="Issue IDs")


class GetMilestoneMetricsArgs(BaseModel):
    """Get milestone metrics arguments."""
    milestone_id: str = Field(..., min_length=1, description="Milestone ID")
    include_issues: bool = Field(False, description="Include issues")


class GetSprintMetricsArgs(BaseModel):
    """Get sprint metrics arguments."""
    sprint_id: str = Field(..., min_length=1, description="Sprint ID")
    include_issues: bool = Field(False, description="Include issues")


class GetOverdueMilestonesArgs(BaseModel):
    """Get overdue milestones arguments."""
    limit: int = Field(..., gt=0, description="Limit")
    include_issues: bool = Field(False, description="Include issues")


class GetUpcomingMilestonesArgs(BaseModel):
    """Get upcoming milestones arguments."""
    days_ahead: int = Field(..., gt=0, description="Days ahead")
    limit: int = Field(..., gt=0, description="Limit")
    include_issues: bool = Field(False, description="Include issues")


class CreateProjectArgs(BaseModel):
    """Create project arguments."""
    title: str = Field(..., min_length=1, description="Project title")
    short_description: Optional[str] = Field(None, description="Project short description")
    owner: str = Field(..., min_length=1, description="Project owner")
    visibility: str = Field("private", description="Project visibility")


class ListProjectsArgs(BaseModel):
    """List projects arguments."""
    status: str = Field("active", description="Project status")
    limit: Optional[int] = Field(None, gt=0, description="Limit")


class GetProjectArgs(BaseModel):
    """Get project arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")


class UpdateProjectArgs(BaseModel):
    """Update project arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    title: Optional[str] = Field(None, description="Project title")
    description: Optional[str] = Field(None, description="Project description")
    visibility: Optional[str] = Field(None, description="Project visibility")
    status: Optional[str] = Field(None, description="Project status")


class DeleteProjectArgs(BaseModel):
    """Delete project arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")


class CreateMilestoneArgs(BaseModel):
    """Create milestone arguments."""
    title: str = Field(..., min_length=1, description="Milestone title")
    description: str = Field(..., min_length=1, description="Milestone description")
    due_date: Optional[str] = Field(None, description="Due date (ISO format)")


class ListMilestonesArgs(BaseModel):
    """List milestones arguments."""
    status: str = Field("open", description="Milestone status")
    sort: Optional[str] = Field(None, description="Sort field")
    direction: Optional[str] = Field(None, description="Sort direction")


class UpdateMilestoneArgs(BaseModel):
    """Update milestone arguments."""
    milestone_id: str = Field(..., min_length=1, description="Milestone ID")
    title: Optional[str] = Field(None, description="Milestone title")
    description: Optional[str] = Field(None, description="Milestone description")
    due_date: Optional[str] = Field(None, description="Due date (ISO format)")
    state: Optional[str] = Field(None, description="Milestone state")


class DeleteMilestoneArgs(BaseModel):
    """Delete milestone arguments."""
    milestone_id: str = Field(..., min_length=1, description="Milestone ID")


class CreateIssueArgs(BaseModel):
    """Create issue arguments."""
    title: str = Field(..., min_length=1, description="Issue title")
    description: str = Field(..., min_length=1, description="Issue description")
    milestone_id: Optional[str] = Field(None, description="Milestone ID")
    assignees: List[str] = Field(default_factory=list, description="Assignees")
    labels: List[str] = Field(default_factory=list, description="Labels")
    priority: Optional[str] = Field(None, description="Priority")
    type: Optional[str] = Field(None, description="Issue type")


class ListIssuesArgs(BaseModel):
    """List issues arguments."""
    status: str = Field("open", description="Issue status")
    milestone: Optional[str] = Field(None, description="Milestone")
    labels: Optional[List[str]] = Field(None, description="Labels")
    assignee: Optional[str] = Field(None, description="Assignee")
    sort: Optional[str] = Field(None, description="Sort field")
    direction: Optional[str] = Field(None, description="Sort direction")
    limit: Optional[int] = Field(None, gt=0, description="Limit")


class GetIssueArgs(BaseModel):
    """Get issue arguments."""
    issue_id: str = Field(..., min_length=1, description="Issue ID")


class UpdateIssueArgs(BaseModel):
    """Update issue arguments."""
    issue_id: str = Field(..., min_length=1, description="Issue ID")
    title: Optional[str] = Field(None, description="Issue title")
    description: Optional[str] = Field(None, description="Issue description")
    status: Optional[str] = Field(None, description="Issue status")
    milestone_id: Optional[str] = Field(None, description="Milestone ID")
    assignees: Optional[List[str]] = Field(None, description="Assignees")
    labels: Optional[List[str]] = Field(None, description="Labels")


class AddIssueCommentArgs(BaseModel):
    """Add issue comment arguments."""
    issue_id: str = Field(..., min_length=1, description="Issue ID")
    body: str = Field(..., min_length=1, description="Comment body")


class ListIssueCommentsArgs(BaseModel):
    """List issue comments arguments."""
    issue_id: str = Field(..., min_length=1, description="Issue ID")


class UpdateIssueCommentArgs(BaseModel):
    """Update issue comment arguments."""
    issue_id: str = Field(..., min_length=1, description="Issue ID")
    comment_id: str = Field(..., min_length=1, description="Comment ID")
    body: str = Field(..., min_length=1, description="Updated comment body")


class DeleteIssueCommentArgs(BaseModel):
    """Delete issue comment arguments."""
    issue_id: str = Field(..., min_length=1, description="Issue ID")
    comment_id: str = Field(..., min_length=1, description="Comment ID")


class SearchIssuesArgs(BaseModel):
    """Search issues arguments."""
    query: str = Field(..., min_length=1, description="GitHub search query syntax. Examples: 'is:issue is:open label:bug', 'is:issue author:username', 'is:issue assignee:username'")


class FilterProjectItemsArgs(BaseModel):
    """Filter project items arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    field_filters: Dict[str, Any] = Field(..., description="Dictionary mapping field names to values. Example: {'Priority': 'High', 'Status': 'In Progress'}")


class FindIssuesByFieldArgs(BaseModel):
    """Find issues by field arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    field_name: str = Field(..., min_length=1, description="Name of the field to filter by")
    field_value: Any = Field(..., description="Value to match")


class CreateSprintArgs(BaseModel):
    """Create sprint arguments."""
    title: str = Field(..., min_length=1, description="Sprint title")
    description: str = Field(..., min_length=1, description="Sprint description")
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")
    issue_ids: List[str] = Field(default_factory=list, description="Issue IDs")


class ListSprintsArgs(BaseModel):
    """List sprints arguments."""
    status: str = Field("all", description="Sprint status")


class GetCurrentSprintArgs(BaseModel):
    """Get current sprint arguments."""
    include_issues: bool = Field(True, description="Include issues")


class UpdateSprintArgs(BaseModel):
    """Update sprint arguments."""
    sprint_id: str = Field(..., min_length=1, description="Sprint ID")
    title: Optional[str] = Field(None, description="Sprint title")
    description: Optional[str] = Field(None, description="Sprint description")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")
    status: Optional[str] = Field(None, description="Sprint status")


class AddIssuesToSprintArgs(BaseModel):
    """Add issues to sprint arguments."""
    sprint_id: str = Field(..., min_length=1, description="Sprint ID")
    issue_ids: List[str] = Field(..., min_length=1, description="Issue IDs")


class RemoveIssuesFromSprintArgs(BaseModel):
    """Remove issues from sprint arguments."""
    sprint_id: str = Field(..., min_length=1, description="Sprint ID")
    issue_ids: List[str] = Field(..., min_length=1, description="Issue IDs")


class CreateProjectFieldArgs(BaseModel):
    """Create project field arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    name: str = Field(..., min_length=1, description="Field name")
    type: str = Field(..., description="Field type")
    options: Optional[Union[List[Dict[str, Any]], List[str], str]] = Field(None, description="Field options (can be list of dicts, list of strings, or JSON string)")
    description: Optional[str] = Field(None, description="Field description")
    required: Optional[bool] = Field(None, description="Required")


class CreateProjectViewArgs(BaseModel):
    """Create project view arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    name: str = Field(..., min_length=1, description="View name")
    layout: str = Field(..., description="View layout")


class ListProjectFieldsArgs(BaseModel):
    """List project fields arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")


class UpdateProjectFieldArgs(BaseModel):
    """Update project field arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    field_id: str = Field(..., min_length=1, description="Field ID")
    name: Optional[str] = Field(None, description="Field name")
    description: Optional[str] = Field(None, description="Field description")
    options: Optional[List[Dict[str, Any]]] = Field(None, description="Field options")
    required: Optional[bool] = Field(None, description="Required")


class ListProjectViewsArgs(BaseModel):
    """List project views arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")


class UpdateProjectViewArgs(BaseModel):
    """Update project view arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    view_id: str = Field(..., min_length=1, description="View ID")
    name: Optional[str] = Field(None, description="View name")
    layout: Optional[str] = Field(None, description="View layout")


class DeleteProjectViewArgs(BaseModel):
    """Delete project view arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    view_id: str = Field(..., min_length=1, description="View ID")


class AddProjectItemArgs(BaseModel):
    """Add project item arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    content_id: str = Field(..., min_length=1, description="Content ID")
    content_type: str = Field(..., description="Content type")
    priority: Optional[str] = Field(None, description="Priority (optional, will be set on project item if field exists)")
    type: Optional[str] = Field(None, description="Issue type (optional, will be set on project item if field exists)")


class RemoveProjectItemArgs(BaseModel):
    """Remove project item arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    item_id: str = Field(..., min_length=1, description="Item ID")


class ListProjectItemsArgs(BaseModel):
    """List project items arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    limit: Optional[int] = Field(None, gt=0, description="Limit")


class SetFieldValueArgs(BaseModel):
    """Set field value arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    item_id: str = Field(..., min_length=1, description="Item ID")
    field_id: str = Field(..., min_length=1, description="Field ID")
    value: Any = Field(..., description="Field value")


class GetFieldValueArgs(BaseModel):
    """Get field value arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    item_id: str = Field(..., min_length=1, description="Item ID")
    field_id: str = Field(..., min_length=1, description="Field ID")


class ClearFieldValueArgs(BaseModel):
    """Clear field value arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    item_id: str = Field(..., min_length=1, description="Item ID")
    field_id: str = Field(..., min_length=1, description="Field ID")


class CreateLabelArgs(BaseModel):
    """Create label arguments."""
    name: str = Field(..., min_length=1, description="Label name")
    color: str = Field(..., description="Label color (hex)")
    description: Optional[str] = Field(None, description="Label description")


class ListLabelsArgs(BaseModel):
    """List labels arguments."""
    limit: Optional[int] = Field(None, gt=0, description="Limit")


# ============================================================================
# Tool Definitions
# ============================================================================

def create_tool_definition(name: str, description: str, schema: type) -> ToolDefinition:
    """Create a tool definition."""
    return ToolDefinition(
        name=name,
        description=description,
        schema=schema,
        examples=None
    )


# Project tools
create_project_tool = create_tool_definition(
    "create_project",
    "Create a new GitHub project",
    CreateProjectArgs
)

list_projects_tool = create_tool_definition(
    "list_projects",
    "List GitHub projects",
    ListProjectsArgs
)

get_project_tool = create_tool_definition(
    "get_project",
    "Get details of a specific GitHub project",
    GetProjectArgs
)

update_project_tool = create_tool_definition(
    "update_project",
    "Update a GitHub project",
    UpdateProjectArgs
)

delete_project_tool = create_tool_definition(
    "delete_project",
    "Delete a GitHub project",
    DeleteProjectArgs
)

# Milestone tools
create_milestone_tool = create_tool_definition(
    "create_milestone",
    "Create a new milestone",
    CreateMilestoneArgs
)

list_milestones_tool = create_tool_definition(
    "list_milestones",
    "List milestones",
    ListMilestonesArgs
)

update_milestone_tool = create_tool_definition(
    "update_milestone",
    "Update a milestone",
    UpdateMilestoneArgs
)

delete_milestone_tool = create_tool_definition(
    "delete_milestone",
    "Delete a milestone",
    DeleteMilestoneArgs
)

# Issue tools
create_issue_tool = create_tool_definition(
    "create_issue",
    "Create a new GitHub issue",
    CreateIssueArgs
)

list_issues_tool = create_tool_definition(
    "list_issues",
    "List GitHub issues",
    ListIssuesArgs
)

get_issue_tool = create_tool_definition(
    "get_issue",
    "Get details of a specific GitHub issue",
    GetIssueArgs
)

update_issue_tool = create_tool_definition(
    "update_issue",
    "Update a GitHub issue",
    UpdateIssueArgs
)

# Issue comment tools
add_issue_comment_tool = create_tool_definition(
    "add_issue_comment",
    "Add a comment to a GitHub issue",
    AddIssueCommentArgs
)

list_issue_comments_tool = create_tool_definition(
    "list_issue_comments",
    "List all comments on a GitHub issue",
    ListIssueCommentsArgs
)

update_issue_comment_tool = create_tool_definition(
    "update_issue_comment",
    "Update a comment on a GitHub issue",
    UpdateIssueCommentArgs
)

delete_issue_comment_tool = create_tool_definition(
    "delete_issue_comment",
    "Delete a comment from a GitHub issue",
    DeleteIssueCommentArgs
)

# Issue search tools
search_issues_tool = create_tool_definition(
    "search_issues",
    "Search issues using GitHub search API query syntax",
    SearchIssuesArgs
)

# Project item filtering tools
filter_project_items_tool = create_tool_definition(
    "filter_project_items",
    "Filter project items by field values",
    FilterProjectItemsArgs
)

find_issues_by_field_tool = create_tool_definition(
    "find_issues_by_field",
    "Find issues by project field values",
    FindIssuesByFieldArgs
)

# Sprint tools
create_sprint_tool = create_tool_definition(
    "create_sprint",
    "Create a new development sprint",
    CreateSprintArgs
)

list_sprints_tool = create_tool_definition(
    "list_sprints",
    "List all sprints",
    ListSprintsArgs
)

get_current_sprint_tool = create_tool_definition(
    "get_current_sprint",
    "Get the currently active sprint",
    GetCurrentSprintArgs
)

update_sprint_tool = create_tool_definition(
    "update_sprint",
    "Update a sprint",
    UpdateSprintArgs
)

add_issues_to_sprint_tool = create_tool_definition(
    "add_issues_to_sprint",
    "Add issues to a sprint",
    AddIssuesToSprintArgs
)

remove_issues_from_sprint_tool = create_tool_definition(
    "remove_issues_from_sprint",
    "Remove issues from a sprint",
    RemoveIssuesFromSprintArgs
)

# Roadmap and planning tools
create_roadmap_tool = create_tool_definition(
    "create_roadmap",
    "Create a project roadmap with milestones and tasks",
    CreateRoadmapArgs
)

plan_sprint_tool = create_tool_definition(
    "plan_sprint",
    "Plan a new sprint with selected issues",
    PlanSprintArgs
)

get_milestone_metrics_tool = create_tool_definition(
    "get_milestone_metrics",
    "Get progress metrics for a specific milestone",
    GetMilestoneMetricsArgs
)

get_sprint_metrics_tool = create_tool_definition(
    "get_sprint_metrics",
    "Get progress metrics for a specific sprint",
    GetSprintMetricsArgs
)

get_overdue_milestones_tool = create_tool_definition(
    "get_overdue_milestones",
    "Get a list of overdue milestones",
    GetOverdueMilestonesArgs
)

get_upcoming_milestones_tool = create_tool_definition(
    "get_upcoming_milestones",
    "Get a list of upcoming milestones within a time frame",
    GetUpcomingMilestonesArgs
)

# Project field tools
create_project_field_tool = create_tool_definition(
    "create_project_field",
    "Create a custom field for a GitHub project",
    CreateProjectFieldArgs
)

list_project_fields_tool = create_tool_definition(
    "list_project_fields",
    "List all fields for a GitHub project",
    ListProjectFieldsArgs
)

update_project_field_tool = create_tool_definition(
    "update_project_field",
    "Update a custom field for a GitHub project",
    UpdateProjectFieldArgs
)

# Project view tools
create_project_view_tool = create_tool_definition(
    "create_project_view",
    "Create a new view for a GitHub project",
    CreateProjectViewArgs
)

list_project_views_tool = create_tool_definition(
    "list_project_views",
    "List all views for a GitHub project",
    ListProjectViewsArgs
)

update_project_view_tool = create_tool_definition(
    "update_project_view",
    "Update a view for a GitHub project",
    UpdateProjectViewArgs
)

delete_project_view_tool = create_tool_definition(
    "delete_project_view",
    "Delete a view from a GitHub project",
    DeleteProjectViewArgs
)

# Project item tools
add_project_item_tool = create_tool_definition(
    "add_project_item",
    "Add an item (issue or PR) to a GitHub project",
    AddProjectItemArgs
)

remove_project_item_tool = create_tool_definition(
    "remove_project_item",
    "Remove an item from a GitHub project",
    RemoveProjectItemArgs
)

list_project_items_tool = create_tool_definition(
    "list_project_items",
    "List all items in a GitHub project",
    ListProjectItemsArgs
)

# Field value tools
set_field_value_tool = create_tool_definition(
    "set_field_value",
    "Set a field value for a project item",
    SetFieldValueArgs
)

get_field_value_tool = create_tool_definition(
    "get_field_value",
    "Get a field value for a project item",
    GetFieldValueArgs
)

clear_field_value_tool = create_tool_definition(
    "clear_field_value",
    "Clear a field value for a project item",
    ClearFieldValueArgs
)

# Label tools
create_label_tool = create_tool_definition(
    "create_label",
    "Create a new label for the repository",
    CreateLabelArgs
)

list_labels_tool = create_tool_definition(
    "list_labels",
    "List all labels in the repository",
    ListLabelsArgs
)




