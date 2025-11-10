"""Project management service."""

from typing import Optional, List, Dict, Any
from ..infrastructure.github.github_repository_factory import GitHubRepositoryFactory
from ..infrastructure.github.repositories.github_issue_repository import GitHubIssueRepository
from ..infrastructure.github.repositories.github_milestone_repository import GitHubMilestoneRepository
from ..infrastructure.github.repositories.github_project_repository import GitHubProjectRepository
from ..infrastructure.github.repositories.github_sprint_repository import GitHubSprintRepository
from ..domain.types import (
    Issue,
    CreateIssue,
    Milestone,
    CreateMilestone,
    Project,
    CreateProject,
    Sprint,
    CreateSprint,
    CustomField,
    ProjectView,
    CreateField,
    UpdateField,
    ProjectId,
    IssueId,
    MilestoneId,
    SprintId
)
from ..domain.resource_types import ResourceStatus


class ProjectManagementService:
    """Project management service."""
    
    def __init__(self, owner: str, repo: str, token: str):
        """Initialize project management service."""
        self._factory = GitHubRepositoryFactory(token, owner, repo)
    
    def get_repository_factory(self) -> GitHubRepositoryFactory:
        """Get the repository factory instance."""
        return self._factory
    
    @property
    def _issue_repo(self) -> GitHubIssueRepository:
        """Get issue repository."""
        return self._factory.create_issue_repository()
    
    @property
    def _milestone_repo(self) -> GitHubMilestoneRepository:
        """Get milestone repository."""
        return self._factory.create_milestone_repository()
    
    @property
    def _project_repo(self) -> GitHubProjectRepository:
        """Get project repository."""
        return self._factory.create_project_repository()
    
    @property
    def _sprint_repo(self) -> GitHubSprintRepository:
        """Get sprint repository."""
        return self._factory.create_sprint_repository()
    
    # Project methods
    async def create_project(self, data: CreateProject) -> Project:
        """Create a project."""
        return await self._project_repo.create(data)
    
    async def list_projects(self, status: Optional[ResourceStatus] = None, limit: Optional[int] = None) -> List[Project]:
        """List projects."""
        projects = await self._project_repo.find_all()
        if status:
            projects = [p for p in projects if p.status == status]
        if limit:
            projects = projects[:limit]
        return projects
    
    async def get_project(self, project_id: ProjectId) -> Project:
        """Get a project."""
        project = await self._project_repo.find_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        return project
    
    async def update_project(self, data: Dict[str, Any]) -> Project:
        """Update a project."""
        project_id = data.get('project_id') or data.get('id')
        if not project_id:
            raise ValueError("Project ID is required")
        return await self._project_repo.update(project_id, data)
    
    async def delete_project(self, data: Dict[str, Any]) -> None:
        """Delete a project."""
        project_id = data.get('project_id') or data.get('id')
        if not project_id:
            raise ValueError("Project ID is required")
        await self._project_repo.delete(project_id)
    
    # Issue methods
    async def create_issue(self, data: CreateIssue) -> Issue:
        """Create an issue."""
        return await self._issue_repo.create(data)
    
    async def list_issues(self, options: Optional[Dict[str, Any]] = None) -> List[Issue]:
        """List issues."""
        return await self._issue_repo.find_all(options)
    
    async def get_issue(self, issue_id: IssueId) -> Issue:
        """Get an issue."""
        issue = await self._issue_repo.find_by_id(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        return issue
    
    async def update_issue(self, issue_id: IssueId, data: Dict[str, Any]) -> Issue:
        """Update an issue."""
        return await self._issue_repo.update(issue_id, data)
    
    # Milestone methods
    async def create_milestone(self, data: CreateMilestone) -> Milestone:
        """Create a milestone."""
        return await self._milestone_repo.create(data)
    
    async def list_milestones(self, status: Optional[ResourceStatus] = None, sort: Optional[str] = None, direction: Optional[str] = None) -> List[Milestone]:
        """List milestones."""
        options = {'status': status} if status else None
        milestones = await self._milestone_repo.find_all(options)
        # TODO: Implement sorting
        return milestones
    
    async def update_milestone(self, data: Dict[str, Any]) -> Milestone:
        """Update a milestone."""
        milestone_id = data.get('milestone_id') or data.get('id')
        if not milestone_id:
            raise ValueError("Milestone ID is required")
        return await self._milestone_repo.update(milestone_id, data)
    
    async def delete_milestone(self, data: Dict[str, Any]) -> None:
        """Delete a milestone."""
        milestone_id = data.get('milestone_id') or data.get('id')
        if not milestone_id:
            raise ValueError("Milestone ID is required")
        await self._milestone_repo.delete(milestone_id)
    
    async def get_milestone_metrics(self, milestone_id: MilestoneId, include_issues: bool = False) -> Dict[str, Any]:
        """Get milestone metrics."""
        milestone = await self._milestone_repo.find_by_id(milestone_id)
        if not milestone:
            raise ValueError(f"Milestone {milestone_id} not found")
        
        issues = await self._milestone_repo.get_issues(milestone_id)
        open_issues = [i for i in issues if i.status == ResourceStatus.ACTIVE]
        closed_issues = [i for i in issues if i.status == ResourceStatus.CLOSED]
        
        total_issues = len(issues)
        completion_percentage = (len(closed_issues) / total_issues * 100) if total_issues > 0 else 0
        
        return {
            'id': milestone.id,
            'title': milestone.title,
            'due_date': milestone.due_date,
            'open_issues': len(open_issues),
            'closed_issues': len(closed_issues),
            'total_issues': total_issues,
            'completion_percentage': completion_percentage,
            'status': milestone.status,
            'issues': issues if include_issues else None,
            'is_overdue': False,  # TODO: Calculate overdue status
            'days_remaining': None  # TODO: Calculate days remaining
        }
    
    # Sprint methods
    async def create_sprint(self, data: CreateSprint) -> Sprint:
        """Create a sprint."""
        return await self._sprint_repo.create(data)
    
    async def list_sprints(self, status: Optional[ResourceStatus] = None) -> List[Sprint]:
        """List sprints."""
        options = {'status': status} if status else None
        return await self._sprint_repo.find_all(options)
    
    async def get_current_sprint(self, include_issues: bool = False) -> Optional[Sprint]:
        """Get current sprint."""
        return await self._sprint_repo.find_current()
    
    async def update_sprint(self, data: Dict[str, Any]) -> Sprint:
        """Update a sprint."""
        sprint_id = data.get('id')
        if not sprint_id:
            raise ValueError("Sprint ID is required")
        return await self._sprint_repo.update(sprint_id, data)
    
    async def plan_sprint(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a sprint."""
        # TODO: Implement sprint planning logic
        raise NotImplementedError("Sprint planning not yet implemented")
    
    async def create_roadmap(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a roadmap."""
        # TODO: Implement roadmap creation logic
        raise NotImplementedError("Roadmap creation not yet implemented")
    
    # Field methods
    async def create_field(self, project_id: ProjectId, field: CreateField) -> CustomField:
        """Create a field."""
        return await self._project_repo.create_field(project_id, field.__dict__)
    
    async def update_field(self, project_id: ProjectId, field_id: str, data: UpdateField) -> CustomField:
        """Update a field."""
        return await self._project_repo.update_field(project_id, field_id, data.__dict__)
    
    async def list_project_fields(self, data: Dict[str, Any]) -> List[CustomField]:
        """List project fields."""
        project_id = data.get('projectId')
        if not project_id:
            raise ValueError("Project ID is required")
        project = await self.get_project(project_id)
        return project.fields
    
    # View methods
    async def create_view(self, project_id: ProjectId, name: str, layout: str) -> ProjectView:
        """Create a view."""
        return await self._project_repo.create_view(project_id, name, layout)
    
    async def list_project_views(self, data: Dict[str, Any]) -> List[ProjectView]:
        """List project views."""
        project_id = data.get('projectId')
        if not project_id:
            raise ValueError("Project ID is required")
        project = await self.get_project(project_id)
        return project.views or []
    
    async def update_project_view(self, data: Dict[str, Any]) -> ProjectView:
        """Update a project view."""
        project_id = data.get('projectId')
        view_id = data.get('viewId')
        if not project_id or not view_id:
            raise ValueError("Project ID and View ID are required")
        return await self._project_repo.update_view(project_id, view_id, data)
    
    async def delete_project_view(self, data: Dict[str, Any]) -> None:
        """Delete a project view."""
        project_id = data.get('projectId')
        view_id = data.get('viewId')
        if not project_id or not view_id:
            raise ValueError("Project ID and View ID are required")
        await self._project_repo.delete_view(project_id, view_id)

