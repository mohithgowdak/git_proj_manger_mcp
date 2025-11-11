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
        issue = await self._issue_repo.update(issue_id, data)
        
        # If status is "in_progress", also try to update project item Status field
        if data.get("status") == ResourceStatus.ACTIVE and data.get("_add_in_progress_label"):
            # Try to update project item Status field if issue is in a project
            await self._try_update_project_item_status(issue_id, "in_progress")
        
        return issue
    
    async def _try_update_project_item_status(self, issue_id: IssueId, status_value: str) -> None:
        """Try to update project item Status field for an issue."""
        try:
            # Get all projects
            projects = await self.list_projects()
            
            for project in projects:
                # Get project item ID for this issue
                item_id = await self._project_repo.get_project_item_id_for_issue(project.id, issue_id)
                if item_id:
                    # Find Status field
                    status_field = await self._project_repo.get_field_by_name(project.id, "Status")
                    if status_field:
                        # Update the field value
                        await self._project_repo.set_field_value(
                            project.id,
                            item_id,
                            status_field["id"],
                            status_value
                        )
                        # Only update in the first project found
                        break
        except Exception as e:
            # Log but don't fail the issue update
            if hasattr(self._logger, 'debug'):
                self._logger.debug(f"Could not update project item status: {str(e)}")
    
    async def set_project_item_field_value(
        self,
        project_id: ProjectId,
        item_id: str,
        field_id: str,
        value: Any
    ) -> bool:
        """Set field value for a project item."""
        return await self._project_repo.set_field_value(project_id, item_id, field_id, value)
    
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
        
        # Convert issues to dictionaries if including them
        issues_dict = None
        if include_issues and issues:
            from dataclasses import asdict
            issues_dict = []
            for issue in issues:
                if hasattr(issue, '__dataclass_fields__'):
                    issues_dict.append(asdict(issue))
                elif hasattr(issue, '__dict__'):
                    issues_dict.append(issue.__dict__)
                else:
                    # Fallback: create dict manually
                    issues_dict.append({
                        'id': getattr(issue, 'id', ''),
                        'number': getattr(issue, 'number', 0),
                        'title': getattr(issue, 'title', ''),
                        'description': getattr(issue, 'description', ''),
                        'status': getattr(issue, 'status', '').value if hasattr(getattr(issue, 'status', ''), 'value') else str(getattr(issue, 'status', '')),
                        'assignees': getattr(issue, 'assignees', []),
                        'labels': getattr(issue, 'labels', []),
                        'milestone_id': getattr(issue, 'milestone_id', None),
                        'created_at': getattr(issue, 'created_at', ''),
                        'updated_at': getattr(issue, 'updated_at', ''),
                        'url': getattr(issue, 'url', ''),
                    })
        
        # Calculate days remaining
        days_remaining = None
        is_overdue = False
        try:
            from datetime import datetime
            if milestone.due_date:
                due_date = datetime.fromisoformat(milestone.due_date.replace('Z', '+00:00'))
                now = datetime.now(due_date.tzinfo) if due_date.tzinfo else datetime.now()
                days_remaining = (due_date - now).days
                is_overdue = days_remaining < 0
        except:
            pass
        
        return {
            'id': milestone.id,
            'title': milestone.title,
            'due_date': milestone.due_date,
            'open_issues': len(open_issues),
            'closed_issues': len(closed_issues),
            'total_issues': total_issues,
            'completion_percentage': round(completion_percentage, 2),
            'status': milestone.status.value if hasattr(milestone.status, 'value') else str(milestone.status),
            'issues': issues_dict,
            'is_overdue': is_overdue,
            'days_remaining': days_remaining
        }
    
    async def get_overdue_milestones(self, limit: int, include_issues: bool = False) -> List[Dict[str, Any]]:
        """Get overdue milestones."""
        from datetime import datetime
        
        # Get all active milestones
        all_milestones = await self.list_milestones(status=ResourceStatus.ACTIVE)
        
        overdue_milestones = []
        now = datetime.now()
        
        for milestone in all_milestones:
            if not milestone.due_date:
                continue
            
            try:
                due_date = datetime.fromisoformat(milestone.due_date.replace('Z', '+00:00'))
                days_overdue = (now - due_date).days
                
                if days_overdue > 0:  # Overdue
                    # Get metrics for this milestone
                    metrics = await self.get_milestone_metrics(milestone.id, include_issues)
                    metrics['days_overdue'] = days_overdue
                    overdue_milestones.append(metrics)
            except:
                continue
        
        # Sort by days overdue (most overdue first)
        overdue_milestones.sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
        
        # Apply limit
        return overdue_milestones[:limit]
    
    async def get_upcoming_milestones(self, days_ahead: int, limit: int, include_issues: bool = False) -> List[Dict[str, Any]]:
        """Get upcoming milestones."""
        from datetime import datetime, timedelta
        
        # Get all active milestones
        all_milestones = await self.list_milestones(status=ResourceStatus.ACTIVE)
        
        upcoming_milestones = []
        now = datetime.now()
        
        for milestone in all_milestones:
            if not milestone.due_date:
                continue
            
            try:
                # Parse due date - handle both Z and +00:00 formats
                due_date_str = milestone.due_date.replace('Z', '+00:00')
                # If it doesn't have timezone info, add UTC
                if '+' not in due_date_str and 'Z' not in due_date_str:
                    due_date_str += '+00:00'
                
                due_date = datetime.fromisoformat(due_date_str)
                days_remaining = (due_date - now).days
                
                # Check if milestone is upcoming (due date is in the future and within the specified days ahead)
                # Include milestones that are due today (0 days) up to days_ahead days in the future
                if 0 <= days_remaining <= days_ahead:
                    # Get metrics for this milestone
                    metrics = await self.get_milestone_metrics(milestone.id, include_issues)
                    metrics['days_remaining'] = days_remaining
                    upcoming_milestones.append(metrics)
            except Exception as e:
                # Log error but continue
                if hasattr(self._logger, 'debug'):
                    self._logger.debug(f"Error processing milestone {milestone.id}: {str(e)}")
                continue
        
        # Sort by days remaining (soonest first)
        upcoming_milestones.sort(key=lambda x: x.get('days_remaining', 999))
        
        # Apply limit
        return upcoming_milestones[:limit]
    
    # Sprint methods
    async def create_sprint(self, data: CreateSprint, project_id: Optional[ProjectId] = None) -> Sprint:
        """Create a sprint."""
        return await self._sprint_repo.create(data, project_id)
    
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
    
    async def plan_sprint(self, data: Dict[str, Any]) -> Sprint:
        """Plan a sprint - creates a sprint with issues."""
        from ...domain.types import CreateSprint as DomainCreateSprint
        
        sprint_data = data.get("sprint", {})
        issue_ids = data.get("issue_ids", [])
        
        create_sprint = DomainCreateSprint(
            title=sprint_data.get("title", ""),
            description=sprint_data.get("description", ""),
            start_date=sprint_data.get("start_date", ""),
            end_date=sprint_data.get("end_date", ""),
            issues=issue_ids,
            goals=sprint_data.get("goals", [])
        )
        
        project_id = data.get("project_id")
        return await self.create_sprint(create_sprint, project_id)
    
    async def get_sprint_metrics(self, sprint_id: SprintId, include_issues: bool = False) -> Dict[str, Any]:
        """Get sprint metrics."""
        # Try to find sprint by ID
        sprint = await self._sprint_repo.find_by_id(sprint_id)
        if not sprint:
            raise ValueError(f"Sprint {sprint_id} not found")
        
        # Get issues for the sprint
        try:
            issues = await self._sprint_repo.get_issues(sprint_id)
        except NotImplementedError:
            # If get_issues is not implemented, try to get issues from sprint.issues if available
            if hasattr(sprint, 'issues') and sprint.issues:
                from .github_issue_repository import GitHubIssueRepository
                issue_repo = GitHubIssueRepository(self._github, self._repo, self._config)
                issues = []
                for issue_id in sprint.issues:
                    try:
                        issue = await issue_repo.find_by_id(issue_id)
                        if issue:
                            issues.append(issue)
                    except:
                        continue
            else:
                issues = []
        
        open_issues = [i for i in issues if i.status == ResourceStatus.ACTIVE]
        closed_issues = [i for i in issues if i.status == ResourceStatus.CLOSED]
        
        total_issues = len(issues)
        completion_percentage = (len(closed_issues) / total_issues * 100) if total_issues > 0 else 0
        
        # Calculate days remaining
        days_remaining = None
        try:
            from datetime import datetime
            if sprint.end_date:
                end_date = datetime.fromisoformat(sprint.end_date.replace('Z', '+00:00'))
                now = datetime.now(end_date.tzinfo) if end_date.tzinfo else datetime.now()
                days_remaining = (end_date - now).days
        except:
            pass
        
        # Convert issues to dictionaries if including them
        issues_dict = None
        if include_issues and issues:
            from dataclasses import asdict
            issues_dict = []
            for issue in issues:
                if hasattr(issue, '__dataclass_fields__'):
                    issues_dict.append(asdict(issue))
                elif hasattr(issue, '__dict__'):
                    issues_dict.append(issue.__dict__)
                else:
                    # Fallback: create dict manually
                    issues_dict.append({
                        'id': getattr(issue, 'id', ''),
                        'number': getattr(issue, 'number', 0),
                        'title': getattr(issue, 'title', ''),
                        'description': getattr(issue, 'description', ''),
                        'status': getattr(issue, 'status', '').value if hasattr(getattr(issue, 'status', ''), 'value') else str(getattr(issue, 'status', '')),
                        'assignees': getattr(issue, 'assignees', []),
                        'labels': getattr(issue, 'labels', []),
                        'milestone_id': getattr(issue, 'milestone_id', None),
                        'created_at': getattr(issue, 'created_at', ''),
                        'updated_at': getattr(issue, 'updated_at', ''),
                        'url': getattr(issue, 'url', ''),
                    })
        
        return {
            'sprint': {
                'id': sprint.id,
                'title': sprint.title,
                'description': sprint.description,
                'start_date': sprint.start_date,
                'end_date': sprint.end_date,
                'status': sprint.status.value if hasattr(sprint.status, 'value') else str(sprint.status),
            },
            'open_issues': len(open_issues),
            'closed_issues': len(closed_issues),
            'total_issues': total_issues,
            'completion_percentage': round(completion_percentage, 2),
            'days_remaining': days_remaining,
            'issues': issues_dict,
        }
    
    async def add_issue_to_sprint(self, sprint_id: SprintId, issue_id: IssueId) -> Sprint:
        """Add an issue to a sprint."""
        return await self._sprint_repo.add_issue(sprint_id, issue_id)
    
    async def create_roadmap(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a roadmap."""
        # This method is now handled by the tool handler directly
        # Keeping for backward compatibility but implementation is in tool_handlers.py
        raise NotImplementedError("Roadmap creation should be handled via create_roadmap tool handler")
    
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

