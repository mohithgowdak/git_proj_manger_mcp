"""GitHub milestone repository."""

from typing import Optional, List
from github import Github
from github.Repository import Repository
from ..github_config import GitHubConfig
from .base_repository import BaseGitHubRepository
from ....domain.types import Milestone, CreateMilestone, MilestoneId
from ....domain.resource_types import ResourceStatus


class GitHubMilestoneRepository(BaseGitHubRepository):
    """GitHub milestone repository."""
    
    async def create(self, data: CreateMilestone) -> Milestone:
        """Create a milestone."""
        milestone = self.repo.create_milestone(
            title=data.title,
            description=data.description,
            due_on=data.due_date if data.due_date else None,
            state='open' if data.status != ResourceStatus.CLOSED else 'closed'
        )
        
        return self._convert_milestone(milestone)
    
    async def update(self, id: MilestoneId, data: dict) -> Milestone:
        """Update a milestone."""
        milestone = self.repo.get_milestone(int(id))
        
        milestone.edit(
            title=data.get('title', milestone.title),
            description=data.get('description', milestone.description),
            due_on=data.get('due_date', milestone.due_on),
            state='open' if data.get('status') != ResourceStatus.CLOSED else 'closed'
        )
        
        return self._convert_milestone(milestone)
    
    async def delete(self, id: MilestoneId) -> None:
        """Delete a milestone."""
        milestone = self.repo.get_milestone(int(id))
        milestone.delete()
    
    async def find_by_id(self, id: MilestoneId) -> Optional[Milestone]:
        """Find milestone by ID."""
        try:
            milestone = self.repo.get_milestone(int(id))
            return self._convert_milestone(milestone)
        except Exception:
            return None
    
    async def find_all(self, options: Optional[dict] = None) -> List[Milestone]:
        """Find all milestones."""
        state = options.get('status') if options else None
        if state == ResourceStatus.CLOSED:
            state = 'closed'
        elif state == ResourceStatus.ACTIVE:
            state = 'open'
        else:
            state = 'all'
        
        milestones = self.repo.get_milestones(state=state)
        return [self._convert_milestone(milestone) for milestone in milestones]
    
    async def get_issues(self, id: MilestoneId) -> List:
        """Get issues for milestone."""
        from .github_issue_repository import GitHubIssueRepository
        issue_repo = GitHubIssueRepository(self.github, self.repo, self.config)
        return await issue_repo.find_by_milestone(id)
    
    def _convert_milestone(self, milestone) -> Milestone:
        """Convert GitHub milestone to domain Milestone."""
        from ....domain.types import Milestone as DomainMilestone
        
        return DomainMilestone(
            id=str(milestone.number),
            number=milestone.number,
            title=milestone.title,
            description=milestone.description or "",
            due_date=milestone.due_on.isoformat() if milestone.due_on else None,
            status=ResourceStatus.CLOSED if milestone.state == 'closed' else ResourceStatus.ACTIVE,
            created_at=milestone.created_at.isoformat() if milestone.created_at else "",
            updated_at=milestone.updated_at.isoformat() if milestone.updated_at else "",
            url=milestone.url,
            progress=None  # Will need to calculate from issues
        )

