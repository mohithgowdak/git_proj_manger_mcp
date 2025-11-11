# GitHub Projects MCP Integration

## Overview

This document details how the MCP server interfaces with GitHub's Projects API (v2) and implements the Model Context Protocol for project management functionality.

## Architecture

### Integration Layers

```
┌─────────────────┐
│   MCP Layer     │ ← Tool definitions, request/response handling
├─────────────────┤
│ Service Layer   │ ← Business logic, coordination
├─────────────────┤
│    Domain       │ ← Core entities, interfaces
├─────────────────┤
│ Infrastructure  │ ← GitHub API integration, repositories
└─────────────────┘
```

### Core Components

1. **Repository Layer**
   - `GitHubProjectRepository`: Project CRUD operations
   - `GitHubIssueRepository`: Issue management
   - `GitHubMilestoneRepository`: Milestone operations
   - `GitHubSprintRepository`: Sprint planning

2. **Service Layer**
   - `ProjectManagementService`: Business logic coordination
   - Resource caching and state management
   - Error handling and retry logic

3. **MCP Layer**
   - Tool definitions and registration
   - Request validation with Pydantic
   - Response formatting
   - Error handling

## GitHub API Integration

### GraphQL API Usage

The server uses GitHub's GraphQL API for most operations. Here's how it's implemented:

```python
# Example GraphQL Mutations
CREATE_PROJECT_MUTATION = """
  mutation($input: CreateProjectV2Input!) {
    createProjectV2(input: $input) {
      projectV2 {
        id
        title
        shortDescription
        closed
        createdAt
        updatedAt
      }
    }
  }
"""

UPDATE_PROJECT_MUTATION = """
  mutation($input: UpdateProjectV2Input!) {
    updateProjectV2(input: $input) {
      projectV2 {
        id
        title
        shortDescription
        closed
        createdAt
        updatedAt
      }
    }
  }
"""

# Python implementation
class GitHubProjectRepository(BaseGitHubRepository):
    async def create(self, data: CreateProject) -> Project:
        # Step 1: Create project (without description - schema compliance)
        create_input = {
            "ownerId": self.owner,
            "title": data.title,
        }
        
        if self.repository:
            create_input["repositoryId"] = self.repository
        
        create_response = await self.graphql(
            CREATE_PROJECT_MUTATION,
            {"input": create_input}
        )
        
        project = create_response["data"]["createProjectV2"]["projectV2"]
        
        # Step 2: Update with description if provided (separate mutation)
        if data.description:
            update_response = await self.graphql(
                UPDATE_PROJECT_MUTATION,
                {
                    "input": {
                        "projectId": project["id"],
                        "shortDescription": data.description,
                    }
                }
            )
            project = update_response["data"]["updateProjectV2"]["projectV2"]
        
        return self._map_to_project(project)
```

### Schema Compliance Notes

**Important**: GitHub's `CreateProjectV2Input` schema does NOT accept description fields:
- ❌ `description` - Not a valid field
- ❌ `shortDescription` - Not a valid field in create mutation

Valid `CreateProjectV2Input` fields:
- ✅ `ownerId` (required)
- ✅ `title` (required) 
- ✅ `repositoryId` (optional)
- ✅ `teamId` (optional)
- ✅ `clientMutationId` (optional)

To set a project description, use a separate `UpdateProjectV2Input` mutation after creation.

### API Features

1. **Projects API (v2)**
   - Project creation and configuration
   - Custom field management
   - View configuration
   - Item management

2. **Issues API**
   - Issue CRUD operations
   - Label management
   - Milestone association
   - Status updates

3. **Milestones API**
   - Milestone management
   - Progress tracking
   - Due date handling

## MCP Implementation

### Tool Definitions

Tools are defined using Pydantic models for validation:

1. **Project Management Tools**

```python
from pydantic import BaseModel, Field

class CreateProjectArgs(BaseModel):
    """Create project arguments."""
    title: str = Field(..., min_length=1, description="Project title")
    owner: str = Field(..., min_length=1, description="Project owner")
    visibility: str = Field("private", description="Project visibility")
    short_description: Optional[str] = Field(None, description="Project description")

class UpdateProjectArgs(BaseModel):
    """Update project arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    title: Optional[str] = Field(None, description="Project title")
    short_description: Optional[str] = Field(None, description="Project description")
    visibility: Optional[str] = Field(None, description="Project visibility")
```

2. **Resource Management Tools**

```python
class AddProjectItemArgs(BaseModel):
    """Add project item arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    content_id: str = Field(..., min_length=1, description="Content ID (issue or PR)")
    content_type: str = Field(..., description="Content type")

class SetFieldValueArgs(BaseModel):
    """Set field value arguments."""
    project_id: str = Field(..., min_length=1, description="Project ID")
    item_id: str = Field(..., min_length=1, description="Item ID")
    field_id: str = Field(..., min_length=1, description="Field ID")
    value: Any = Field(..., description="Field value")
```

### Resource Management

1. **Caching**

```python
from src.infrastructure.cache.resource_cache import ResourceCache, ResourceCacheOptions
from src.domain.resource_types import ResourceType

# Cache a resource
cache = ResourceCache.get_instance()
await cache.set(
    ResourceType.ISSUE,
    issue_id,
    issue,
    ResourceCacheOptions(ttl=3600000)  # 1 hour
)

# Retrieve from cache
cached_issue = await cache.get(ResourceType.ISSUE, issue_id)
```

2. **Error Handling**

```python
from src.infrastructure.github.github_error_handler import GitHubErrorHandler
from src.domain.errors import GitHubAPIError, RateLimitError

class BaseGitHubRepository:
    async def with_retry(self, operation, context: Optional[str] = None) -> Any:
        """Execute operation with automatic retries."""
        error_handler = GitHubErrorHandler()
        
        for attempt in range(self._retry_attempts):
            try:
                return await operation()
            except Exception as error:
                if not error_handler.is_retryable_error(error) or attempt == self._retry_attempts - 1:
                    raise error_handler.handle_error(error, context)
                
                # Exponential backoff
                delay = 1000 * (2 ** attempt)
                await asyncio.sleep(delay / 1000)
```

### Retry Strategy

The server implements automatic retry with exponential backoff:

```python
class BaseGitHubRepository:
    def __init__(self, ...):
        self._retry_attempts = 3
    
    async def with_retry(self, operation, context: Optional[str] = None) -> Any:
        """Execute operation with automatic retries."""
        last_error = None
        
        for attempt in range(self._retry_attempts):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation()
                else:
                    return operation()
            except Exception as error:
                last_error = error
                
                is_retryable = self._error_handler.is_retryable_error(error)
                is_last_attempt = attempt == self._retry_attempts - 1
                
                if not is_retryable or is_last_attempt:
                    raise self._error_handler.handle_error(
                        error,
                        f"{context} (max retries exceeded)" if is_last_attempt else context
                    )
                
                # Exponential backoff: 1s, 2s, 4s
                delay = 1000 * (2 ** attempt)
                await asyncio.sleep(delay / 1000)
```

## Best Practices

1. **API Usage**
   - The server automatically handles rate limits with retry
   - Use request batching for multiple operations when possible
   - Handle API errors gracefully (errors are automatically mapped)
   - Validate inputs before API calls (Pydantic validation)

2. **Resource Management**
   - Resources are automatically cached with TTL
   - Cache is invalidated on updates
   - Use appropriate cache TTLs for different resource types

3. **Error Handling**
   - All GitHub API errors are mapped to domain errors
   - Retry logic is automatic for retryable errors
   - Error context is preserved for debugging

4. **Async Operations**
   - All I/O operations use async/await
   - Use `asyncio.gather()` for concurrent operations
   - Proper exception handling in async functions

## Examples

### Creating a Project with Items

```python
from src.services.project_management_service import ProjectManagementService
from src.domain.types import CreateProject

async def create_project_with_items(
    title: str,
    owner: str
) -> Project:
    """Create a project and add items."""
    service = ProjectManagementService(owner, repo, token)
    
    # Create project
    project_data = CreateProject(
        title=title,
        owner=owner,
        short_description="Created via MCP",
        visibility="private"
    )
    
    project = await service.create_project(project_data)
    
    # Add items (issues) to project
    # This would be done via add_project_item tool
    return project
```

### Handling Field Updates

```python
async def update_field_value(
    project_id: str,
    item_id: str,
    field_id: str,
    value: Any
) -> None:
    """Update field value with error handling."""
    service = ProjectManagementService(owner, repo, token)
    
    try:
        await service.set_project_item_field_value(
            project_id,
            item_id,
            field_id,
            value
        )
    except ValidationError as e:
        print(f"Validation error: {e}")
    except GitHubAPIError as e:
        print(f"GitHub API error: {e}")
        # Retry logic is automatic
```

### Using MCP Tools

```python
from src.infrastructure.tools.tool_handlers import execute_tool
from src.services.project_management_service import ProjectManagementService

async def use_tool_example():
    """Example of using MCP tools."""
    service = ProjectManagementService(owner, repo, token)
    
    # Create project via tool
    result = await execute_tool(
        "create_project",
        service,
        {
            "title": "My Project",
            "owner": owner,
            "visibility": "private"
        }
    )
    
    if result.status == "success":
        print(f"Project created: {result.output}")
    else:
        print(f"Error: {result.error}")
```

## Testing

1. **Unit Tests**
   - Test individual components in isolation
   - Mock GitHub API responses
   - Validate error handling

2. **Integration Tests**
   - Test complete workflows
   - Verify API integration
   - Check resource management

3. **E2E Tests**
   - Test full system functionality
   - Verify real API interactions (optional)
   - Validate error scenarios

Example test:

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.services.project_management_service import ProjectManagementService

@pytest.mark.asyncio
async def test_create_project():
    """Test project creation."""
    service = ProjectManagementService("owner", "repo", "token")
    
    with patch('src.infrastructure.github.repositories.github_project_repository.GitHubProjectRepository.create') as mock_create:
        mock_create.return_value = Project(...)
        
        result = await service.create_project(CreateProject(...))
        
        assert result.title == "Test Project"
        mock_create.assert_called_once()
```

## References

- [GitHub Projects API Documentation](https://docs.github.com/en/rest/projects)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- [MCP Specification](https://modelcontextprotocol.io)
- [Architecture Documentation](../../ARCHITECTURE.md)
- [User Guide](../user-guide.md)
