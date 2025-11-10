"""GitHub issue repository."""

from typing import Optional, List
from github import Github
from github.Repository import Repository
from ..github_config import GitHubConfig
from .base_repository import BaseGitHubRepository
from ....domain.types import Issue, CreateIssue, IssueId, MilestoneId
from ....domain.resource_types import ResourceStatus


class GitHubIssueRepository(BaseGitHubRepository):
    """GitHub issue repository."""
    
    async def create(self, data: CreateIssue) -> Issue:
        """Create an issue."""
        # Use PyGithub to create issue
        issue = self.repo.create_issue(
            title=data.title,
            body=data.description,
            assignees=data.assignees or [],
            labels=data.labels or [],
            milestone=None  # Will need to convert milestone ID
        )
        
        return self._convert_issue(issue)
    
    async def update(self, id: IssueId, data: dict) -> Issue:
        """Update an issue."""
        issue = self.repo.get_issue(int(id))
        
        if 'title' in data:
            issue.edit(title=data['title'])
        if 'description' in data:
            issue.edit(body=data['description'])
        if 'assignees' in data:
            issue.edit(assignees=data['assignees'])
        if 'labels' in data:
            issue.edit(labels=data['labels'])
        
        return self._convert_issue(issue)
    
    async def delete(self, id: IssueId) -> None:
        """Delete an issue."""
        issue = self.repo.get_issue(int(id))
        issue.edit(state='closed')
    
    async def find_by_id(self, id: IssueId) -> Optional[Issue]:
        """Find issue by ID."""
        try:
            issue = self.repo.get_issue(int(id))
            return self._convert_issue(issue)
        except Exception:
            return None
    
    async def find_by_milestone(self, milestone_id: MilestoneId) -> List[Issue]:
        """Find issues by milestone."""
        issues = self.repo.get_issues(milestone=milestone_id)
        return [self._convert_issue(issue) for issue in issues]
    
    async def find_all(self, options: Optional[dict] = None) -> List[Issue]:
        """Find all issues."""
        state = options.get('status') if options else None
        if state == ResourceStatus.CLOSED:
            state = 'closed'
        elif state == ResourceStatus.ACTIVE:
            state = 'open'
        else:
            state = 'all'
        
        issues = self.repo.get_issues(state=state)
        return [self._convert_issue(issue) for issue in issues]
    
    def _convert_issue(self, issue) -> Issue:
        """Convert GitHub issue to domain Issue."""
        from ....domain.types import Issue as DomainIssue
        
        return DomainIssue(
            id=str(issue.number),
            number=issue.number,
            title=issue.title,
            description=issue.body or "",
            status=ResourceStatus.CLOSED if issue.state == 'closed' else ResourceStatus.ACTIVE,
            assignees=[assignee.login for assignee in issue.assignees],
            labels=[label.name for label in issue.labels],
            milestone_id=str(issue.milestone.number) if issue.milestone else None,
            created_at=issue.created_at.isoformat() if issue.created_at else "",
            updated_at=issue.updated_at.isoformat() if issue.updated_at else "",
            url=issue.html_url
        )

