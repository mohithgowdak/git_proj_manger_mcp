"""GitHub repository factory."""

from typing import Optional, Dict, Any
from github import Github
from .github_config import GitHubConfig
from .github_error_handler import GitHubErrorHandler
from .repositories.base_repository import BaseGitHubRepository
from .repositories.github_project_repository import GitHubProjectRepository
from .repositories.github_issue_repository import GitHubIssueRepository
from .repositories.github_milestone_repository import GitHubMilestoneRepository
from .repositories.github_sprint_repository import GitHubSprintRepository


class RepositoryFactoryOptions:
    """Repository factory options."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        previews: Optional[list[str]] = None
    ):
        self.base_url = base_url or "https://api.github.com"
        self.previews = previews or ["inertia-preview"]


class GitHubRepositoryFactory:
    """GitHub repository factory."""
    
    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        options: Optional[RepositoryFactoryOptions] = None
    ):
        """Initialize GitHub repository factory."""
        self.config = GitHubConfig.create(owner, repo, token)
        self.error_handler = GitHubErrorHandler()
        
        # Initialize PyGithub client
        self.github = Github(token)
        self.repo = self.github.get_repo(f"{owner}/{repo}")
        
        if options is None:
            options = RepositoryFactoryOptions()
        self.options = options
    
    def get_error_handler(self) -> GitHubErrorHandler:
        """Get error handler."""
        return self.error_handler
    
    def get_config(self) -> GitHubConfig:
        """Get configuration."""
        return self.config
    
    def create_project_repository(self) -> GitHubProjectRepository:
        """Create project repository."""
        return GitHubProjectRepository(self.github, self.repo, self.config)
    
    def create_issue_repository(self) -> GitHubIssueRepository:
        """Create issue repository."""
        return GitHubIssueRepository(self.github, self.repo, self.config)
    
    def create_milestone_repository(self) -> GitHubMilestoneRepository:
        """Create milestone repository."""
        return GitHubMilestoneRepository(self.github, self.repo, self.config)
    
    def create_sprint_repository(self) -> GitHubSprintRepository:
        """Create sprint repository."""
        return GitHubSprintRepository(self.github, self.repo, self.config)
    
    @classmethod
    def create(
        cls,
        env: Dict[str, str],
        options: Optional[RepositoryFactoryOptions] = None
    ) -> "GitHubRepositoryFactory":
        """Create factory from environment variables."""
        if not env.get("GITHUB_TOKEN") or not env.get("GITHUB_OWNER") or not env.get("GITHUB_REPO"):
            raise ValueError("Missing required GitHub configuration")
        
        return cls(
            env["GITHUB_TOKEN"],
            env["GITHUB_OWNER"],
            env["GITHUB_REPO"],
            options
        )




