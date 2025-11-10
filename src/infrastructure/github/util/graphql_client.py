"""GraphQL client for GitHub API."""

import json
import asyncio
from typing import Any, Dict, Optional
import httpx
from ..github_config import GitHubConfig
from ..github_error_handler import GitHubErrorHandler


class GraphQLClient:
    """GraphQL client for GitHub API."""
    
    def __init__(self, config: GitHubConfig):
        """Initialize GraphQL client."""
        self.config = config
        self.error_handler = GitHubErrorHandler()
        self.base_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json"
        }
    
    async def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute GraphQL query."""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "errors" in result:
                    # Check if errors are about nullable fields (like organization not existing)
                    # In GraphQL, nullable fields can fail without failing the entire query
                    errors = result.get("errors", [])
                    fatal_errors = []
                    nullable_field_errors = []
                    
                    for err in errors:
                        error_msg = err.get("message", "")
                        # Check if error is about resolving to an organization/user that doesn't exist
                        # These are typically non-fatal for nullable fields
                        if "Could not resolve to an Organization" in error_msg or "Could not resolve to a User" in error_msg:
                            nullable_field_errors.append(err)
                        else:
                            fatal_errors.append(err)
                    
                    # If we have data (even if some fields are null) and only nullable field errors, return the data
                    data = result.get("data")
                    if data is not None and not fatal_errors:
                        # Check if we have at least some non-null data
                        # Even if organization is null, user might have data
                        if isinstance(data, dict) and len(data) > 0:
                            return data
                    
                    # Otherwise, raise exception with all errors
                    error_messages = [err.get("message", "Unknown error") for err in errors]
                    raise Exception(f"GraphQL errors: {', '.join(error_messages)}")
                
                return result.get("data", {})
            except httpx.HTTPStatusError as e:
                raise self.error_handler.handle_error(e, "GraphQL operation")
            except Exception as e:
                raise self.error_handler.handle_error(e, "GraphQL operation")

