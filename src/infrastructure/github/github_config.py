"""GitHub configuration."""

from typing import Optional


class GitHubConfig:
    """GitHub configuration."""
    
    def __init__(self, owner: str, repo: str, token: str, project_id: Optional[str] = None):
        """Initialize GitHub configuration."""
        if not owner:
            raise ValueError("Owner is required")
        if not repo:
            raise ValueError("Repository is required")
        if not token:
            raise ValueError("Token is required")
        
        self._owner = owner
        self._repo = repo
        self._token = token
        self._project_id = project_id
    
    @property
    def owner(self) -> str:
        """Get owner."""
        return self._owner
    
    @property
    def repo(self) -> str:
        """Get repository."""
        return self._repo
    
    @property
    def token(self) -> str:
        """Get token."""
        return self._token
    
    @property
    def project_id(self) -> Optional[str]:
        """Get project ID."""
        return self._project_id
    
    @classmethod
    def create(cls, owner: str, repo: str, token: str, project_id: Optional[str] = None) -> "GitHubConfig":
        """Create GitHub configuration."""
        return cls(owner, repo, token, project_id)




