"""Base GitHub repository."""

import asyncio
from typing import Any, Dict, Optional, Protocol
from github import Github
from github.Repository import Repository
from ..github_config import GitHubConfig
from ..github_error_handler import GitHubErrorHandler
from ..util.graphql_client import GraphQLClient
from ....infrastructure.logger import get_logger


class IGitHubRepository(Protocol):
    """GitHub repository interface."""
    
    @property
    def github(self) -> Github:
        """Get GitHub client."""
        ...
    
    @property
    def config(self) -> GitHubConfig:
        """Get configuration."""
        ...


class BaseGitHubRepository:
    """Base GitHub repository."""
    
    def __init__(
        self,
        github: Github,
        repo: Repository,
        config: GitHubConfig
    ):
        """Initialize base repository."""
        self._github = github
        self._repo = repo
        self._config = config
        self._error_handler = GitHubErrorHandler()
        self._retry_attempts = 3
        self._logger = get_logger(self.__class__.__name__)
        self._graphql_client = GraphQLClient(config)
    
    @property
    def github(self) -> Github:
        """Get GitHub client."""
        return self._github
    
    @property
    def repo(self) -> Repository:
        """Get repository."""
        return self._repo
    
    @property
    def config(self) -> GitHubConfig:
        """Get configuration."""
        return self._config
    
    @property
    def owner(self) -> str:
        """Get owner."""
        return self._config.owner
    
    @property
    def repository(self) -> str:
        """Get repository name."""
        return self._config.repo
    
    @property
    def token(self) -> str:
        """Get token."""
        return self._config.token
    
    async def with_retry(
        self,
        operation,
        context: Optional[str] = None
    ) -> Any:
        """Execute operation with automatic retries and rate limit handling."""
        last_error: Optional[Exception] = None
        
        for attempt in range(self._retry_attempts):
            try:
                # Execute operation (may be async or sync)
                if asyncio.iscoroutinefunction(operation):
                    result = await operation()
                else:
                    result = operation()
                return result
            except Exception as error:
                last_error = error
                
                is_retryable = self._error_handler.is_retryable_error(error)
                is_last_attempt = attempt == self._retry_attempts - 1
                
                if not is_retryable or is_last_attempt:
                    raise self._error_handler.handle_error(
                        error,
                        f"{context} (max retries exceeded)" if is_last_attempt else context
                    )
                
                # Calculate retry delay
                delay = 1000 * (2 ** attempt)  # Exponential backoff
                await asyncio.sleep(delay / 1000)
        
        if last_error:
            raise self._error_handler.handle_error(last_error, context)
    
    def _handle_pagination(self, items: list, limit: Optional[int] = None) -> list:
        """Handle pagination."""
        if limit is None:
            return items
        return items[:limit]
    
    async def graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Any:
        """Execute GraphQL query with rate limiting support."""
        async def _execute():
            return await self._graphql_client.execute(query, variables)
        return await self.with_retry(_execute, 'executing GraphQL query')

