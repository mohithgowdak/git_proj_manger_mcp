"""Domain types for GitHub Project Manager."""

from typing import Optional, Protocol, Dict, Any, List
from dataclasses import dataclass
from .resource_types import ResourceStatus, ResourceType

# Type aliases
ProjectId = str
FieldId = str
ItemId = str
IssueId = str
MilestoneId = str
SprintId = str

# Field types supported by GitHub Projects v2
FieldType = str  # 'text' | 'number' | 'date' | 'single_select' | 'iteration' | 'milestone' | 'assignees' | 'labels' | 'repository' | 'tracked_by' | 'tracks'

# View layouts supported by GitHub Projects v2
ViewLayout = str  # 'board' | 'table' | 'timeline' | 'roadmap'


@dataclass
class Issue:
    """Issue type."""
    id: IssueId
    number: int
    title: str
    description: str
    status: ResourceStatus
    assignees: List[str]
    labels: List[str]
    milestone_id: Optional[MilestoneId] = None
    created_at: str = ""
    updated_at: str = ""
    url: str = ""


@dataclass
class CreateIssue:
    """Create issue data."""
    title: str
    description: str
    assignees: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    milestone_id: Optional[MilestoneId] = None
    status: Optional[ResourceStatus] = None
    priority: Optional[str] = None
    issue_type: Optional[str] = None


# Type alias for comment ID
CommentId = str


@dataclass
class IssueComment:
    """Issue comment type."""
    id: CommentId
    body: str
    author: str
    created_at: str = ""
    updated_at: str = ""
    url: str = ""


@dataclass
class CreateIssueComment:
    """Create issue comment data."""
    body: str


class IssueRepository(Protocol):
    """Issue repository protocol."""
    
    async def create(self, data: CreateIssue) -> Issue:
        """Create issue."""
        ...
    
    async def update(self, id: IssueId, data: Dict[str, Any]) -> Issue:
        """Update issue."""
        ...
    
    async def delete(self, id: IssueId) -> None:
        """Delete issue."""
        ...
    
    async def find_by_id(self, id: IssueId) -> Optional[Issue]:
        """Find issue by ID."""
        ...
    
    async def find_by_milestone(self, milestone_id: MilestoneId) -> List[Issue]:
        """Find issues by milestone."""
        ...
    
    async def find_all(self, options: Optional[Dict[str, Any]] = None) -> List[Issue]:
        """Find all issues."""
        ...
    
    async def search(self, query: str) -> List[Issue]:
        """Search issues using GitHub search API query syntax."""
        ...
    
    async def create_comment(self, issue_id: IssueId, data: CreateIssueComment) -> IssueComment:
        """Create a comment on an issue."""
        ...
    
    async def list_comments(self, issue_id: IssueId) -> List[IssueComment]:
        """List all comments on an issue."""
        ...
    
    async def update_comment(self, issue_id: IssueId, comment_id: CommentId, body: str) -> IssueComment:
        """Update a comment on an issue."""
        ...
    
    async def delete_comment(self, issue_id: IssueId, comment_id: CommentId) -> None:
        """Delete a comment on an issue."""
        ...


@dataclass
class Milestone:
    """Milestone type."""
    id: MilestoneId
    number: int
    title: str
    description: str
    due_date: Optional[str] = None
    status: ResourceStatus = ResourceStatus.ACTIVE
    created_at: str = ""
    updated_at: str = ""
    url: str = ""
    progress: Optional[Dict[str, int]] = None


@dataclass
class CreateMilestone:
    """Create milestone data."""
    title: str
    description: str
    due_date: Optional[str] = None
    status: Optional[ResourceStatus] = None
    goals: Optional[List[str]] = None


class MilestoneRepository(Protocol):
    """Milestone repository protocol."""
    
    async def create(self, data: CreateMilestone) -> Milestone:
        """Create milestone."""
        ...
    
    async def update(self, id: MilestoneId, data: Dict[str, Any]) -> Milestone:
        """Update milestone."""
        ...
    
    async def delete(self, id: MilestoneId) -> None:
        """Delete milestone."""
        ...
    
    async def find_by_id(self, id: MilestoneId) -> Optional[Milestone]:
        """Find milestone by ID."""
        ...
    
    async def find_all(self, options: Optional[Dict[str, Any]] = None) -> List[Milestone]:
        """Find all milestones."""
        ...
    
    async def get_issues(self, id: MilestoneId) -> List[Issue]:
        """Get issues for milestone."""
        ...


@dataclass
class Sprint:
    """Sprint type."""
    id: SprintId
    title: str
    description: str
    start_date: str
    end_date: str
    status: ResourceStatus = ResourceStatus.ACTIVE
    issues: List[IssueId] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class CreateSprint:
    """Create sprint data."""
    title: str
    description: str
    start_date: str
    end_date: str
    status: Optional[ResourceStatus] = None
    issues: Optional[List[IssueId]] = None
    goals: Optional[List[str]] = None


class SprintRepository(Protocol):
    """Sprint repository protocol."""
    
    async def create(self, data: CreateSprint) -> Sprint:
        """Create sprint."""
        ...
    
    async def update(self, id: SprintId, data: Dict[str, Any]) -> Sprint:
        """Update sprint."""
        ...
    
    async def delete(self, id: SprintId) -> None:
        """Delete sprint."""
        ...
    
    async def find_by_id(self, id: SprintId) -> Optional[Sprint]:
        """Find sprint by ID."""
        ...
    
    async def find_all(self, options: Optional[Dict[str, Any]] = None) -> List[Sprint]:
        """Find all sprints."""
        ...
    
    async def find_current(self) -> Optional[Sprint]:
        """Find current sprint."""
        ...
    
    async def add_issue(self, sprint_id: SprintId, issue_id: IssueId) -> Sprint:
        """Add issue to sprint."""
        ...
    
    async def remove_issue(self, sprint_id: SprintId, issue_id: IssueId) -> Sprint:
        """Remove issue from sprint."""
        ...
    
    async def get_issues(self, sprint_id: SprintId) -> List[Issue]:
        """Get issues for sprint."""
        ...


@dataclass
class FieldOption:
    """Field option."""
    id: Optional[str] = None
    name: str = ""
    color: Optional[str] = None
    description: Optional[str] = None


@dataclass
class CustomField:
    """Custom field."""
    id: FieldId
    name: str
    type: FieldType
    options: Optional[List[FieldOption]] = None
    description: Optional[str] = None
    required: bool = False
    default_value: Optional[Any] = None
    validation: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


@dataclass
class CreateField:
    """Create field data."""
    name: str
    type: FieldType
    options: Optional[List[FieldOption]] = None
    description: Optional[str] = None
    required: bool = False
    default_value: Optional[Any] = None
    validation: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


@dataclass
class UpdateField:
    """Update field data."""
    name: Optional[str] = None
    options: Optional[List[FieldOption]] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    default_value: Optional[Any] = None
    validation: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


@dataclass
class SortBy:
    """Sort by configuration."""
    field: str
    direction: str  # 'ASC' | 'DESC'


@dataclass
class Filter:
    """Filter configuration."""
    field: str
    operator: str
    value: Any


@dataclass
class ProjectView:
    """Project view."""
    id: str
    name: str
    layout: ViewLayout
    fields: Optional[List[CustomField]] = None
    sort_by: Optional[List[SortBy]] = None
    group_by: Optional[str] = None
    filters: Optional[List[Filter]] = None
    settings: Optional[Dict[str, Any]] = None


@dataclass
class ProjectItem:
    """Project item."""
    id: ItemId
    content_id: str
    content_type: ResourceType
    project_id: ProjectId
    field_values: Dict[FieldId, Any]
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Project:
    """Project type."""
    id: ProjectId
    type: ResourceType
    title: str
    description: str
    owner: str
    number: int
    url: str
    fields: List[CustomField]
    views: Optional[List[ProjectView]] = None
    closed: bool = False
    created_at: str = ""
    updated_at: str = ""
    status: Optional[ResourceStatus] = None
    visibility: Optional[str] = None
    version: Optional[int] = None


@dataclass
class CreateProject:
    """Create project data."""
    title: str
    owner: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[str] = None  # 'private' | 'public'
    views: Optional[List[ProjectView]] = None
    fields: Optional[List[CustomField]] = None
    team_id: Optional[str] = None
    client_mutation_id: Optional[str] = None
    status: Optional[ResourceStatus] = None
    goals: Optional[List[str]] = None


class ProjectRepository(Protocol):
    """Project repository protocol."""
    
    async def create(self, project: CreateProject) -> Project:
        """Create project."""
        ...
    
    async def update(self, id: ProjectId, data: Dict[str, Any]) -> Project:
        """Update project."""
        ...
    
    async def delete(self, id: ProjectId) -> None:
        """Delete project."""
        ...
    
    async def find_by_id(self, id: ProjectId) -> Optional[Project]:
        """Find project by ID."""
        ...
    
    async def find_by_owner(self, owner: str) -> List[Project]:
        """Find projects by owner."""
        ...
    
    async def find_all(self) -> List[Project]:
        """Find all projects."""
        ...
    
    # Field operations
    async def create_field(self, project_id: ProjectId, field: CreateField) -> CustomField:
        """Create field."""
        ...
    
    async def update_field(self, project_id: ProjectId, field_id: FieldId, data: UpdateField) -> CustomField:
        """Update field."""
        ...
    
    async def delete_field(self, project_id: ProjectId, field_id: FieldId) -> None:
        """Delete field."""
        ...
    
    # View operations
    async def create_view(self, project_id: ProjectId, name: str, layout: ViewLayout) -> ProjectView:
        """Create view."""
        ...
    
    async def update_view(self, project_id: ProjectId, view_id: str, data: Dict[str, Any]) -> ProjectView:
        """Update view."""
        ...
    
    async def delete_view(self, project_id: ProjectId, view_id: str) -> None:
        """Delete view."""
        ...


def create_resource(type: ResourceType, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create resource with type."""
    return {**data, "type": type}




