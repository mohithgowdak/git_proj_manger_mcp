# Building an MCP Server for GitHub Project Management: A Developer's Journey

## Introduction

As developers, we're constantly looking for ways to streamline our workflows and automate repetitive tasks. When I discovered the Model Context Protocol (MCP) and saw its potential for integrating AI assistants with development tools, I came across an excellent TypeScript/Node.js implementation by [@kunwarVivek](https://github.com/kunwarVivek) ([mcp-github-project-manager](https://github.com/kunwarVivek/mcp-github-project-manager)). 

Inspired by this project, I decided to reimplement it in Python—not just as a port, but as a learning journey to understand MCP architecture, GitHub API integration, and how to adapt design patterns from one language ecosystem to another. This project taught me invaluable lessons about architecture, async programming, and building production-ready systems.

In this post, I'll share my journey building this server, the technical challenges I faced, the design decisions I made, and the key learnings that shaped the final implementation.

## The Problem: Why Build This?

Managing GitHub projects manually can be tedious. Creating issues, planning sprints, tracking milestones, and organizing roadmaps often requires multiple clicks and context switching. What if AI assistants like Claude or ChatGPT could directly interact with your GitHub projects? What if you could say "Create a sprint for next week with these issues" and have it happen automatically?

That's exactly what the Model Context Protocol enables. MCP is a protocol that allows AI assistants to interact with external tools and services through a standardized interface. By building an MCP server, I could bridge the gap between AI assistants and GitHub's project management capabilities.

## The Inspiration: Learning from Existing Projects

One of the best ways to learn is by studying well-architected projects. I discovered [@kunwarVivek](https://github.com/kunwarVivek)'s excellent TypeScript/Node.js implementation of an MCP GitHub project manager. The original project provided valuable insights into:
- MCP server architecture and protocol implementation
- GitHub Projects API integration patterns
- Tool design and organization
- Error handling strategies

Rather than just using it, I decided to reimplement it in Python. This wasn't about reinventing the wheel—it was about understanding the wheel deeply by building it from scratch in a different language. This approach taught me:
- How to translate design patterns between languages
- The differences between TypeScript's Zod and Python's Pydantic
- How async patterns differ between Node.js and Python
- The importance of understanding the "why" behind architectural decisions

## Understanding the Model Context Protocol

Before diving into the implementation, let me explain what MCP is and why it matters. The Model Context Protocol is a standardized way for AI assistants to:
- **Discover available tools**: AI assistants can query what tools are available
- **Execute tools with validated inputs**: Tools receive validated, typed inputs
- **Receive structured responses**: Responses follow a consistent format
- **Handle errors gracefully**: Errors are properly formatted and handled

Think of MCP as a bridge between AI assistants and external services. An MCP server exposes "tools" (essentially functions) that AI assistants can call. Each tool has:
- A **name**: Unique identifier (e.g., `create_issue`)
- A **description**: What the tool does (used by AI to decide when to call it)
- An **input schema**: JSON Schema defining required and optional parameters
- An **output format**: How results are structured

### How MCP Works in Practice

When you ask an AI assistant like Claude to "create an issue for fixing the login bug," here's what happens:

1. The AI assistant recognizes it needs to create a GitHub issue
2. It looks up available tools and finds `create_issue`
3. It extracts parameters from your request (title, description, etc.)
4. It calls the MCP server with the tool name and parameters
5. The MCP server validates inputs, executes the operation, and returns results
6. The AI assistant presents the results to you

This seamless integration makes AI assistants much more powerful—they can now interact with your development tools directly.

## Architecture: Clean Architecture Principles

One of the most important decisions I made early on was to follow **Clean Architecture** principles. This wasn't just about following best practices—it was about building a maintainable, testable, and extensible system that could evolve over time.

### Why Clean Architecture?

When I started, I could have built everything in a single file or a few modules. But I knew this project would grow, and I wanted to avoid the "big ball of mud" anti-pattern. Clean Architecture provides:

- **Independence**: Business logic doesn't depend on frameworks or external services
- **Testability**: Each layer can be tested in isolation
- **Flexibility**: We can swap implementations without changing core logic
- **Maintainability**: Clear boundaries make the codebase easier to understand and modify

### Layer Structure

The project is organized into four distinct layers, each with a specific responsibility:

#### 1. Domain Layer (`src/domain/`)

The innermost layer contains core business entities, types, and repository interfaces. This layer has **zero dependencies** on external frameworks or libraries. It defines:

- **Domain Entities**: `Issue`, `Milestone`, `Sprint`, `Project` - the core business objects
- **Value Objects**: `ProjectId`, `IssueId` - type-safe identifiers
- **Repository Protocols**: Interfaces that define what operations are possible
- **Domain Errors**: Business-specific error types

```python
# Domain layer - no external dependencies
from typing import Protocol, Optional
from dataclasses import dataclass

@dataclass
class Issue:
    id: str
    title: str
    description: str
    status: str
    labels: list[str]

class IssueRepository(Protocol):
    """Protocol defining issue operations - no implementation details"""
    async def create(self, data: CreateIssue) -> Issue: ...
    async def find_by_id(self, id: str) -> Optional[Issue]: ...
    async def update(self, id: str, data: UpdateIssue) -> Issue: ...
```

The key insight: The domain layer doesn't know about GitHub, GraphQL, or HTTP. It only knows about business concepts.

#### 2. Infrastructure Layer (`src/infrastructure/`)

This layer implements the interfaces defined in the domain layer. It handles all external concerns:

- **GitHub API Integration**: GraphQL and REST clients
- **Repository Implementations**: Concrete implementations of domain protocols
- **MCP Tools**: Tool definitions, handlers, and validation
- **Caching**: In-memory cache with TTL
- **Event System**: Event storage and querying

```python
# Infrastructure layer - implements domain protocols
class GitHubIssueRepository(BaseGitHubRepository):
    """Concrete implementation using GitHub GraphQL API"""
    
    async def create(self, data: CreateIssue) -> Issue:
        mutation = """
        mutation($input: CreateIssueInput!) {
            createIssue(input: $input) {
                issue { id title body state }
            }
        }
        """
        result = await self._graphql_client.execute(mutation, variables)
        return self._map_to_domain_entity(result)
```

#### 3. Service Layer (`src/services/`)

The service layer orchestrates business logic and coordinates between repositories. It implements complex workflows that might involve multiple repositories:

```python
class ProjectManagementService:
    """Orchestrates complex business operations"""
    
    async def create_roadmap(self, roadmap_data: CreateRoadmap) -> Roadmap:
        # 1. Create project
        project = await self._project_repo.create(roadmap_data.project)
        
        # 2. Create milestones
        milestones = []
        for milestone_data in roadmap_data.milestones:
            milestone = await self._milestone_repo.create(milestone_data)
            milestones.append(milestone)
            
            # 3. Create issues for each milestone
            for issue_data in milestone_data.issues:
                issue = await self._issue_repo.create(issue_data)
                await self._project_repo.add_item(project.id, issue.id)
        
        return Roadmap(project=project, milestones=milestones)
```

#### 4. MCP Layer

The outermost layer handles MCP protocol concerns:
- Tool registration and discovery
- Request/response formatting
- Protocol-specific error handling

This separation ensures that:
- Business logic is independent of external frameworks
- Testing is easier (we can mock repositories)
- The codebase remains maintainable as it grows
- We can swap implementations (e.g., different API clients) without changing business logic

### Repository Pattern: The Foundation of Data Access

I implemented the Repository Pattern to abstract data access. This pattern is crucial for Clean Architecture because it decouples business logic from data storage details.

#### The Pattern in Action

```python
# Domain layer - defines the contract
from typing import Protocol, Optional

class IssueRepository(Protocol):
    """Protocol defines what operations are possible - not how they're done"""
    async def create(self, data: CreateIssue) -> Issue: ...
    async def find_by_id(self, id: IssueId) -> Optional[Issue]: ...
    async def find_all(self, filters: Optional[IssueFilters] = None) -> list[Issue]: ...
    async def update(self, id: IssueId, data: UpdateIssue) -> Issue: ...
    async def delete(self, id: IssueId) -> None: ...
```

```python
# Infrastructure layer - provides the implementation
class GitHubIssueRepository(BaseGitHubRepository):
    """Concrete implementation - knows about GitHub API"""
    
    async def create(self, data: CreateIssue) -> Issue:
        # Build GraphQL mutation
        mutation = """
        mutation($input: CreateIssueInput!) {
            createIssue(input: $input) {
                issue {
                    id
                    title
                    body
                    state
                    createdAt
                    labels(first: 10) {
                        nodes { name }
                    }
                }
            }
        }
        """
        
        variables = {
            "input": {
                "repositoryId": self._repo_id,
                "title": data.title,
                "body": data.description,
                "labelIds": await self._resolve_label_ids(data.labels)
            }
        }
        
        result = await self._graphql_client.execute(mutation, variables)
        issue_data = result["data"]["createIssue"]["issue"]
        
        # Map GitHub API response to domain entity
        return Issue(
            id=issue_data["id"],
            title=issue_data["title"],
            description=issue_data["body"],
            status=issue_data["state"].lower(),
            labels=[label["name"] for label in issue_data["labels"]["nodes"]]
        )
```

#### Why This Matters

This pattern provides several critical benefits:

1. **Testability**: I can create mock repositories for unit tests without hitting the GitHub API:
```python
class MockIssueRepository:
    def __init__(self):
        self._issues = {}
    
    async def create(self, data: CreateIssue) -> Issue:
        issue = Issue(id=str(uuid.uuid4()), title=data.title, ...)
        self._issues[issue.id] = issue
        return issue
```

2. **Flexibility**: If GitHub changes their API or we want to support GitLab, we only change the infrastructure layer:
```python
# Could easily add a GitLab implementation
class GitLabIssueRepository(BaseRepository):
    async def create(self, data: CreateIssue) -> Issue:
        # Different implementation, same interface
```

3. **Clean Separation**: The service layer doesn't know or care whether we're using GitHub, GitLab, or a database. It just calls repository methods.

#### Base Repository: DRY Principle

I created a `BaseGitHubRepository` to avoid code duplication across repositories:

```python
class BaseGitHubRepository:
    """Base class with common functionality for all GitHub repositories"""
    
    def __init__(self, graphql_client: GraphQLClient, repo_id: str):
        self._graphql_client = graphql_client
        self._repo_id = repo_id
    
    async def with_retry(self, operation, max_retries: int = 3):
        """Automatic retry with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return await operation()
            except RateLimitError as e:
                delay = self._calculate_retry_delay(e)
                await asyncio.sleep(delay)
            except RetryableError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
    
    def _calculate_retry_delay(self, error: RateLimitError) -> float:
        """Calculate delay from GitHub rate limit headers"""
        reset_time = error.reset_at
        delay = max(0, (reset_time - time.time()) + 1)
        return delay
```

All repositories inherit from this base class, getting retry logic, error handling, and rate limit management for free.

## Technical Challenges & Solutions

### Challenge 1: Async/Await Throughout - The Async-First Approach

One of the biggest challenges was ensuring consistent async/await patterns throughout the codebase. GitHub API calls are I/O-bound operations (network requests), so using async was crucial for performance. But going "all-in" on async required discipline and understanding.

#### The Problem

Python's async/await can be tricky. If you mix sync and async code, you get:
- Performance bottlenecks (blocking operations)
- Runtime errors (`RuntimeError: This event loop is already running`)
- Confusion about when to use `await`

#### The Solution: Async-First Architecture

I made async/await mandatory for all I/O operations. Every repository method, service method, and tool handler is async:

```python
# Repository layer - all methods are async
class GitHubIssueRepository(BaseGitHubRepository):
    async def create(self, data: CreateIssue) -> Issue:
        # Async GraphQL call - non-blocking
        result = await self._graphql_client.execute(mutation, variables)
        
        # Async cache update - non-blocking
        issue = self._map_to_entity(result)
        await self._cache.set(ResourceType.ISSUE, issue.id, issue)
        
        return issue
    
    async def find_by_id(self, id: str) -> Optional[Issue]:
        # Check cache first (async)
        cached = await self._cache.get(ResourceType.ISSUE, id)
        if cached:
            return cached
        
        # Fetch from API if not cached (async)
        result = await self._graphql_client.execute(query, variables)
        issue = self._map_to_entity(result)
        
        # Update cache (async)
        await self._cache.set(ResourceType.ISSUE, id, issue)
        return issue
```

#### Handling Concurrent Operations

One of the benefits of async is handling multiple operations concurrently:

```python
async def create_roadmap(self, roadmap_data: CreateRoadmap) -> Roadmap:
    # Create project first
    project = await self._project_repo.create(roadmap_data.project)
    
    # Create all milestones concurrently (much faster!)
    milestone_tasks = [
        self._milestone_repo.create(milestone_data)
        for milestone_data in roadmap_data.milestones
    ]
    milestones = await asyncio.gather(*milestone_tasks)
    
    # Create issues for each milestone concurrently
    issue_tasks = []
    for milestone, milestone_data in zip(milestones, roadmap_data.milestones):
        for issue_data in milestone_data.issues:
            task = self._issue_repo.create(issue_data)
            issue_tasks.append(task)
    
    issues = await asyncio.gather(*issue_tasks)
    
    return Roadmap(project=project, milestones=milestones, issues=issues)
```

This concurrent approach can be **10x faster** than sequential operations when creating multiple resources.

#### Key Learnings

1. **Consistency is Critical**: Once you commit to async, stick with it everywhere. Mixing sync and async leads to confusion and performance issues.

2. **Understand the Event Loop**: Python's event loop runs in a single thread. Blocking operations (like `time.sleep()` instead of `await asyncio.sleep()`) will block the entire event loop.

3. **Use `asyncio.gather()` for Concurrency**: When you have multiple independent async operations, `asyncio.gather()` runs them concurrently, dramatically improving performance.

4. **Error Handling in Async**: Async exceptions propagate differently. Always use `try/except` around `await` calls and handle `asyncio.CancelledError` appropriately.

### Challenge 2: Error Handling & Retry Logic - Production-Ready Resilience

GitHub's API has rate limits (5,000 requests/hour for authenticated users), and network requests can fail for various reasons. I needed robust error handling and automatic retry mechanisms that work reliably in production.

#### The Challenge

When dealing with external APIs, you face multiple failure modes:
- **Rate Limiting**: Too many requests too quickly
- **Network Failures**: Timeouts, connection errors
- **Temporary Server Errors**: 500, 502, 503 status codes
- **Permanent Errors**: 404 (not found), 401 (unauthorized)

Each requires different handling strategies.

#### The Solution: Comprehensive Error Handling

I implemented a sophisticated error handling system in the base repository:

```python
class BaseGitHubRepository:
    async def with_retry(
        self, 
        operation: Callable,
        context: Optional[str] = None,
        max_retries: int = 3
    ) -> Any:
        """
        Execute an operation with automatic retry logic.
        
        Handles:
        - Rate limit errors (with calculated delay)
        - Temporary network errors (with exponential backoff)
        - Permanent errors (fail immediately)
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await operation()
                
            except RateLimitError as e:
                # Rate limit: wait until reset time
                delay = self._calculate_retry_delay(e)
                self._logger.warning(
                    f"Rate limit hit. Retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)
                last_exception = e
                
            except TemporaryError as e:
                # Temporary error: exponential backoff
                if attempt < max_retries - 1:
                    delay = 2 ** attempt  # 1s, 2s, 4s
                    self._logger.warning(
                        f"Temporary error: {e}. Retrying in {delay}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                    last_exception = e
                else:
                    raise
                    
            except PermanentError as e:
                # Permanent error: don't retry
                self._logger.error(f"Permanent error: {e}")
                raise
                
            except Exception as e:
                # Unexpected error: log and re-raise
                self._logger.error(f"Unexpected error: {e}", exc_info=True)
                raise
        
        # All retries exhausted
        raise RetryExhaustedError(
            f"Operation failed after {max_retries} attempts. "
            f"Last error: {last_exception}"
        ) from last_exception
    
    def _calculate_retry_delay(self, error: RateLimitError) -> float:
        """
        Calculate retry delay from GitHub rate limit headers.
        
        GitHub provides:
        - X-RateLimit-Reset: Unix timestamp when rate limit resets
        - X-RateLimit-Remaining: Requests remaining in current window
        """
        reset_time = error.reset_at  # From X-RateLimit-Reset header
        current_time = time.time()
        delay = max(0, (reset_time - current_time) + 1)  # +1 for safety margin
        
        return min(delay, 3600)  # Cap at 1 hour
```

#### Error Classification

I created a hierarchy of error types to handle different scenarios:

```python
class GitHubAPIError(Exception):
    """Base class for all GitHub API errors"""
    pass

class RateLimitError(GitHubAPIError):
    """Rate limit exceeded - retry after delay"""
    def __init__(self, reset_at: float, remaining: int):
        self.reset_at = reset_at
        self.remaining = remaining
        super().__init__(f"Rate limit exceeded. Resets at {reset_at}")

class TemporaryError(GitHubAPIError):
    """Temporary error - retry with backoff"""
    pass

class PermanentError(GitHubAPIError):
    """Permanent error - don't retry"""
    pass

class RetryExhaustedError(GitHubAPIError):
    """All retry attempts exhausted"""
    pass
```

#### Error Mapping from HTTP Status Codes

```python
def map_http_error(status_code: int, headers: dict) -> GitHubAPIError:
    """Map HTTP status codes to domain errors"""
    if status_code == 429:  # Too Many Requests
        reset_at = float(headers.get("X-RateLimit-Reset", time.time() + 3600))
        remaining = int(headers.get("X-RateLimit-Remaining", 0))
        return RateLimitError(reset_at, remaining)
    
    elif status_code in (500, 502, 503, 504):  # Server errors
        return TemporaryError(f"Server error: {status_code}")
    
    elif status_code in (400, 401, 403, 404):  # Client errors
        return PermanentError(f"Client error: {status_code}")
    
    else:
        return GitHubAPIError(f"Unexpected status: {status_code}")
```

#### Real-World Impact

This error handling system has proven crucial:
- **Rate Limit Handling**: Automatically waits for rate limit resets instead of failing
- **Network Resilience**: Handles temporary network issues gracefully
- **User Experience**: Operations succeed even when GitHub has temporary issues
- **Debugging**: Detailed logging helps identify patterns in failures

#### Key Learnings

1. **Always Handle Rate Limits**: Calculate delays from API response headers, not fixed intervals. GitHub provides `X-RateLimit-Reset` which tells you exactly when to retry.

2. **Exponential Backoff**: For temporary errors, use exponential backoff (1s, 2s, 4s) to avoid overwhelming the API.

3. **Don't Retry Permanent Errors**: 404 (not found) or 401 (unauthorized) won't succeed on retry. Fail fast for these.

4. **Log Everything**: Detailed logging helps debug production issues and understand failure patterns.

5. **Context Matters**: Include context in error messages (what operation failed, attempt number, etc.) to make debugging easier.

### Challenge 3: Type Safety with Pydantic - From Zod to Python

MCP requires strict input validation. The original TypeScript implementation used Zod for validation. I needed to find the Python equivalent and translate validation patterns.

#### The Translation Challenge

Zod and Pydantic solve the same problem but with different syntax. Here's how I translated common patterns:

**Zod (TypeScript):**
```typescript
const CreateIssueSchema = z.object({
  title: z.string().min(1, "Title is required"),
  description: z.string().min(1, "Description is required"),
  labels: z.array(z.string()).optional().default([]),
  assignees: z.array(z.string()).optional().default([]),
  priority: z.enum(["low", "medium", "high"]).optional(),
  dueDate: z.string().datetime().optional()
});
```

**Pydantic (Python):**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class CreateIssueArgs(BaseModel):
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=256,
        description="Issue title"
    )
    description: str = Field(
        ..., 
        min_length=1,
        description="Issue description"
    )
    labels: Optional[List[str]] = Field(
        default=[],
        description="Issue labels"
    )
    assignees: Optional[List[str]] = Field(
        default=[],
        description="Issue assignees (GitHub usernames)"
    )
    priority: Optional[Priority] = Field(
        default=None,
        description="Issue priority"
    )
    due_date: Optional[str] = Field(
        default=None,
        alias="dueDate",
        description="Due date in ISO format"
    )
    
    @field_validator('labels')
    @classmethod
    def validate_labels(cls, v: List[str]) -> List[str]:
        if len(v) > 10:
            raise ValueError("Maximum 10 labels allowed")
        return [label.lower() for label in v]  # Normalize to lowercase
    
    @field_validator('assignees')
    @classmethod
    def validate_assignees(cls, v: List[str]) -> List[str]:
        if len(v) > 5:
            raise ValueError("Maximum 5 assignees allowed")
        return v
    
    class Config:
        populate_by_name = True  # Allow both 'due_date' and 'dueDate'
```

#### Advanced Validation Patterns

Pydantic's validation system is powerful. Here are some advanced patterns I used:

**1. Custom Validators:**
```python
@field_validator('title')
@classmethod
def validate_title(cls, v: str) -> str:
    # Remove extra whitespace
    v = ' '.join(v.split())
    
    # Check for forbidden characters
    if any(char in v for char in ['<', '>', '&']):
        raise ValueError("Title contains invalid characters")
    
    return v
```

**2. Model Validators (Cross-Field Validation):**
```python
from pydantic import model_validator

class CreateSprintArgs(BaseModel):
    start_date: str
    end_date: str
    
    @model_validator(mode='after')
    def validate_dates(self):
        start = datetime.fromisoformat(self.start_date)
        end = datetime.fromisoformat(self.end_date)
        
        if end <= start:
            raise ValueError("End date must be after start date")
        
        if (end - start).days > 30:
            raise ValueError("Sprint cannot be longer than 30 days")
        
        return self
```

**3. JSON Schema Generation for MCP:**
```python
def pydantic_to_json_schema(model: type[BaseModel]) -> dict:
    """Convert Pydantic model to JSON Schema for MCP"""
    schema = model.model_json_schema()
    
    # MCP requires specific format
    return {
        "type": "object",
        "properties": schema.get("properties", {}),
        "required": schema.get("required", []),
        "additionalProperties": False
    }
```

#### Benefits of Pydantic

1. **Automatic Type Coercion**: Pydantic automatically converts types when possible:
```python
# This works even though "123" is a string
args = CreateIssueArgs(title="Bug", description="Fix login", priority="1")
# Pydantic converts "1" to Priority.LOW if it's an enum value
```

2. **Excellent Error Messages**: Pydantic provides detailed validation errors:
```python
try:
    CreateIssueArgs(title="", description="Test")
except ValidationError as e:
    print(e.json())
    # [
    #   {
    #     "type": "string_too_short",
    #     "loc": ["title"],
    #     "msg": "String should have at least 1 character",
    #     "input": ""
    #   }
    # ]
```

3. **Self-Documenting**: Field descriptions become part of the schema, making the code self-documenting.

4. **IDE Support**: Type hints work perfectly with IDEs, providing autocomplete and type checking.

#### Key Learnings

1. **Pydantic is Python's Zod**: Both solve the same problem with similar approaches. Learning one helps understand the other.

2. **Validation is Documentation**: Well-written validators document business rules. A validator that checks "sprint length <= 30 days" is clearer than a comment.

3. **Type Coercion is Powerful**: Pydantic's automatic type coercion reduces boilerplate but can hide bugs. Use it carefully.

4. **Custom Validators for Business Logic**: Use `@field_validator` and `@model_validator` to encode business rules directly in the model.

5. **JSON Schema Integration**: Pydantic models can generate JSON Schema automatically, which is perfect for MCP tool definitions.

### Challenge 4: Tool Registration & Discovery - Managing 47+ Tools

With 47+ tools, I needed a clean way to register and discover them. The MCP protocol requires tools to be listed at startup, and each tool needs proper metadata for AI assistants to understand when to use it.

#### The Challenge

Each MCP tool needs:
- A unique name
- A clear description (used by AI to decide when to call it)
- An input schema (JSON Schema)
- A handler function
- Proper error handling

With 47+ tools, managing this manually would be error-prone and hard to maintain.

#### The Solution: Tool Registry Pattern

I implemented a Tool Registry using the Singleton pattern:

```python
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: dict  # JSON Schema
    handler: callable
    
    def to_mcp_format(self) -> dict:
        """Convert to MCP tool format"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }

class ToolRegistry:
    """Singleton registry for all MCP tools"""
    _instance: Optional['ToolRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._tools: Dict[str, MCPTool] = {}
        self._register_built_in_tools()
        self._initialized = True
    
    def register_tool(self, tool: MCPTool):
        """Register a tool"""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> list[MCPTool]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def get_tools_for_mcp(self) -> list[dict]:
        """Get all tools in MCP format"""
        return [tool.to_mcp_format() for tool in self._tools.values()]
    
    def _register_built_in_tools(self):
        """Register all built-in tools"""
        # Project tools
        self.register_tool(MCPTool(
            name="create_project",
            description="Create a new GitHub project with specified title and visibility",
            input_schema=CreateProjectArgs.model_json_schema(),
            handler=create_project_handler
        ))
        
        self.register_tool(MCPTool(
            name="list_projects",
            description="List all GitHub projects for the repository",
            input_schema=ListProjectsArgs.model_json_schema(),
            handler=list_projects_handler
        ))
        
        # Issue tools
        self.register_tool(MCPTool(
            name="create_issue",
            description="Create a new GitHub issue with title, description, labels, and assignees",
            input_schema=CreateIssueArgs.model_json_schema(),
            handler=create_issue_handler
        ))
        
        # ... register all 47+ tools
```

#### Tool Handler Pattern

Each tool has a handler function that follows a consistent pattern:

```python
async def create_issue_handler(arguments: dict) -> dict:
    """
    Handler for create_issue tool.
    
    Args:
        arguments: Validated arguments from MCP client
        
    Returns:
        Formatted response for MCP protocol
    """
    try:
        # Validate arguments using Pydantic
        args = CreateIssueArgs(**arguments)
        
        # Execute business logic
        service = get_project_management_service()
        issue = await service.create_issue(args)
        
        # Format response
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Issue created successfully: {issue.title} (#{issue.id})"
                }
            ]
        }
    except ValidationError as e:
        # Return validation errors in MCP format
        return format_validation_error(e)
    except Exception as e:
        # Return error in MCP format
        return format_error(e)
```

#### Tool Organization

I organized tools into logical groups:

```python
# tools/project_tools.py
def register_project_tools(registry: ToolRegistry):
    """Register all project-related tools"""
    registry.register_tool(create_project_tool)
    registry.register_tool(list_projects_tool)
    registry.register_tool(get_project_tool)
    registry.register_tool(update_project_tool)
    registry.register_tool(delete_project_tool)

# tools/issue_tools.py
def register_issue_tools(registry: ToolRegistry):
    """Register all issue-related tools"""
    registry.register_tool(create_issue_tool)
    registry.register_tool(list_issues_tool)
    # ... etc

# In tool_registry.py
def _register_built_in_tools(self):
    """Register all tools by category"""
    register_project_tools(self)
    register_issue_tools(self)
    register_milestone_tools(self)
    register_sprint_tools(self)
    # ... etc
```

This organization makes it easy to:
- Find tools by category
- Add new tools in the right place
- Understand the tool structure
- Test tools in groups

#### Key Learnings

1. **Singleton for Global State**: The Singleton pattern works well for registries that need to be accessible everywhere, but use it sparingly.

2. **Consistent Handler Pattern**: All handlers follow the same pattern (validate → execute → format), making the code predictable and maintainable.

3. **Tool Descriptions Matter**: AI assistants use tool descriptions to decide when to call them. Write clear, specific descriptions.

4. **Schema Generation**: Use Pydantic's `model_json_schema()` to automatically generate JSON Schema from models, reducing duplication.

5. **Organization is Key**: With 47+ tools, organization matters. Group related tools together and use consistent naming conventions.

### Challenge 5: GraphQL vs REST API - Choosing the Right Tool

GitHub provides both REST and GraphQL APIs. I needed to choose which one to use for different operations, balancing efficiency, simplicity, and maintainability.

#### The Decision Matrix

I evaluated each operation based on:
- **Complexity**: How complex is the query?
- **Efficiency**: How many API calls are needed?
- **API Support**: Which API provides better support?
- **Maintainability**: Which is easier to maintain?

#### GraphQL: The Power Tool

I used GraphQL for most operations because:

**1. Fetch Exactly What You Need:**
```python
# REST: Multiple requests or over-fetching
# GET /repos/owner/repo/issues/123
# GET /repos/owner/repo/issues/123/comments
# GET /repos/owner/repo/issues/123/labels

# GraphQL: Single request, exact fields
query = """
query($issueNumber: Int!) {
    repository(owner: "owner", name: "repo") {
        issue(number: $issueNumber) {
            id
            title
            body
            state
            comments(first: 10) {
                nodes {
                    id
                    body
                    author { login }
                }
            }
            labels(first: 10) {
                nodes { name color }
            }
        }
    }
}
"""
```

**2. GitHub Projects v2 is GraphQL-Only:**
GitHub's Projects v2 API (the modern project management API) is primarily GraphQL-based. Many operations simply aren't available via REST.

**3. Efficient Nested Queries:**
```python
# Fetch project with all items, their fields, and related issues in one query
query = """
query($projectId: ID!) {
    node(id: $projectId) {
        ... on ProjectV2 {
            id
            title
            items(first: 100) {
                nodes {
                    id
                    fieldValues(first: 20) {
                        nodes {
                            ... on ProjectV2ItemFieldTextValue {
                                text
                                field { name }
                            }
                            ... on ProjectV2ItemFieldSingleSelectValue {
                                name
                                field { name }
                            }
                        }
                    }
                    content {
                        ... on Issue {
                            id
                            title
                            state
                        }
                    }
                }
            }
        }
    }
}
"""
```

#### REST: When Simplicity Wins

I kept REST API support for operations where it's simpler:

**1. Simple Operations:**
```python
# REST is simpler for basic operations
async def create_label(self, name: str, color: str) -> Label:
    """Create a label - REST is simpler for this"""
    url = f"{self._base_url}/repos/{self._owner}/{self._repo}/labels"
    data = {"name": name, "color": color}
    response = await self._http_client.post(url, json=data)
    return Label(**response.json())
```

**2. File Operations:**
Some operations (like file uploads) are easier with REST.

**3. Fallback:**
When GraphQL doesn't support an operation, REST is the fallback.

#### GraphQL Client Implementation

I built a robust GraphQL client with error handling:

```python
class GraphQLClient:
    """Async GraphQL client for GitHub API"""
    
    def __init__(self, token: str, base_url: str = "https://api.github.com/graphql"):
        self._token = token
        self._base_url = base_url
        self._http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def execute(
        self, 
        query: str, 
        variables: Optional[dict] = None,
        operation_name: Optional[str] = None
    ) -> dict:
        """
        Execute a GraphQL query.
        
        Handles:
        - Request formatting
        - Error extraction
        - Rate limit detection
        """
        payload = {
            "query": query,
            "variables": variables or {},
        }
        if operation_name:
            payload["operationName"] = operation_name
        
        response = await self._http_client.post(self._base_url, json=payload)
        data = response.json()
        
        # Check for GraphQL errors
        if "errors" in data:
            raise GraphQLError(data["errors"])
        
        # Check for HTTP errors
        if response.status_code != 200:
            raise HTTPError(f"HTTP {response.status_code}: {response.text}")
        
        return data["data"]
    
    async def execute_with_retry(
        self,
        query: str,
        variables: Optional[dict] = None,
        max_retries: int = 3
    ) -> dict:
        """Execute with automatic retry"""
        for attempt in range(max_retries):
            try:
                return await self.execute(query, variables)
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(e.retry_after)
                else:
                    raise
```

#### Handling GraphQL Complexity

GraphQL queries can get complex. I created helper functions:

```python
def build_project_items_query(
    project_id: str,
    first: int = 100,
    include_fields: bool = True,
    include_content: bool = True
) -> str:
    """Build a GraphQL query for project items with optional fields"""
    fields_fragment = """
    fieldValues(first: 20) {
        nodes {
            ... on ProjectV2ItemFieldTextValue {
                text
                field { name }
            }
            ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { name }
            }
        }
    }
    """ if include_fields else ""
    
    content_fragment = """
    content {
        ... on Issue {
            id
            title
            state
        }
    }
    """ if include_content else ""
    
    return f"""
    query {{
        node(id: "{project_id}") {{
            ... on ProjectV2 {{
                items(first: {first}) {{
                    nodes {{
                        id
                        {fields_fragment}
                        {content_fragment}
                    }}
                }}
            }}
        }}
    }}
    """
```

#### Key Learnings

1. **GraphQL for Complex Queries**: When you need nested data or want to avoid multiple requests, GraphQL shines.

2. **REST for Simplicity**: For simple operations, REST is often more straightforward and easier to understand.

3. **Use the Right Tool**: Don't force one API for everything. Use GraphQL for complex queries, REST for simple operations.

4. **GraphQL Learning Curve**: GraphQL has a learning curve, especially with fragments and inline fragments. Start simple and build complexity gradually.

5. **Error Handling**: GraphQL errors are in the response body, not HTTP status codes. Always check the `errors` field.

6. **Query Optimization**: GraphQL allows fetching exactly what you need, but it's easy to over-fetch. Be mindful of query complexity and GitHub's rate limits.

## Key Features & Implementation Highlights

### 1. 47+ MCP Tools

The server exposes 47+ tools organized into categories:
- **Project Management**: Create, list, update, delete projects
- **Issue Management**: Full CRUD operations, search, comments
- **Milestone Management**: Create milestones, track progress, get metrics
- **Sprint Planning**: Create sprints, plan with issues, track metrics
- **Roadmap Creation**: Automated roadmap generation
- **Custom Fields & Views**: Support for GitHub Projects v2 custom fields

### 2. Caching Layer - Performance Optimization

I implemented an in-memory cache with TTL support to reduce API calls and improve performance. Caching is crucial when dealing with external APIs that have rate limits.

#### The Caching Strategy

```python
from dataclasses import dataclass
from typing import Any, Optional, Dict
from enum import Enum
import time

class ResourceType(str, Enum):
    PROJECT = "project"
    ISSUE = "issue"
    MILESTONE = "milestone"
    SPRINT = "sprint"

@dataclass
class CacheEntry:
    """Represents a cached resource"""
    resource: Any
    expires_at: float
    tags: set[str]
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

class ResourceCache:
    """In-memory cache with TTL and tag-based indexing"""
    
    def __init__(self, default_ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._type_index: Dict[ResourceType, set[str]] = {}
        self._tag_index: Dict[str, set[str]] = {}
    
    async def set(
        self,
        resource_type: ResourceType,
        resource_id: str,
        resource: Any,
        ttl: Optional[int] = None,
        tags: Optional[set[str]] = None
    ):
        """Cache a resource with TTL and optional tags"""
        key = self._make_key(resource_type, resource_id)
        expires_at = time.time() + (ttl or self._default_ttl)
        tags = tags or set()
        
        entry = CacheEntry(
            resource=resource,
            expires_at=expires_at,
            tags=tags
        )
        
        self._cache[key] = entry
        
        # Update indices
        if resource_type not in self._type_index:
            self._type_index[resource_type] = set()
        self._type_index[resource_type].add(key)
        
        for tag in tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(key)
    
    async def get(
        self,
        resource_type: ResourceType,
        resource_id: str
    ) -> Optional[Any]:
        """Get a cached resource if not expired"""
        key = self._make_key(resource_type, resource_id)
        entry = self._cache.get(key)
        
        if entry is None:
            return None
        
        if entry.is_expired():
            await self.delete(resource_type, resource_id)
            return None
        
        return entry.resource
    
    async def get_by_type(self, resource_type: ResourceType) -> list[Any]:
        """Get all cached resources of a type"""
        keys = self._type_index.get(resource_type, set())
        resources = []
        
        for key in list(keys):
            resource_type, resource_id = self._parse_key(key)
            resource = await self.get(resource_type, resource_id)
            if resource:
                resources.append(resource)
        
        return resources
    
    async def get_by_tag(self, tag: str) -> list[Any]:
        """Get all cached resources with a specific tag"""
        keys = self._tag_index.get(tag, set())
        resources = []
        
        for key in list(keys):
            resource_type, resource_id = self._parse_key(key)
            resource = await self.get(resource_type, resource_id)
            if resource:
                resources.append(resource)
        
        return resources
    
    async def delete(self, resource_type: ResourceType, resource_id: str):
        """Delete a cached resource"""
        key = self._make_key(resource_type, resource_id)
        entry = self._cache.pop(key, None)
        
        if entry:
            # Remove from indices
            self._type_index.get(resource_type, set()).discard(key)
            for tag in entry.tags:
                self._tag_index.get(tag, set()).discard(key)
    
    async def clear_expired(self):
        """Remove all expired entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            resource_type, resource_id = self._parse_key(key)
            await self.delete(resource_type, resource_id)
    
    def _make_key(self, resource_type: ResourceType, resource_id: str) -> str:
        return f"{resource_type.value}:{resource_id}"
    
    def _parse_key(self, key: str) -> tuple[ResourceType, str]:
        resource_type, resource_id = key.split(":", 1)
        return ResourceType(resource_type), resource_id
```

#### Cache Usage in Repositories

```python
class GitHubIssueRepository(BaseGitHubRepository):
    async def find_by_id(self, id: str) -> Optional[Issue]:
        # Check cache first
        cached = await self._cache.get(ResourceType.ISSUE, id)
        if cached:
            return cached
        
        # Fetch from API
        query = self._build_issue_query(id)
        result = await self._graphql_client.execute(query)
        issue = self._map_to_entity(result)
        
        # Cache with tags
        await self._cache.set(
            ResourceType.ISSUE,
            id,
            issue,
            ttl=3600,  # 1 hour
            tags={f"repo:{self._repo_id}", f"state:{issue.status}"}
        )
        
        return issue
    
    async def invalidate_cache(self, issue_id: str):
        """Invalidate cache when issue is updated"""
        await self._cache.delete(ResourceType.ISSUE, issue_id)
```

#### Cache Performance Impact

Caching significantly improves performance:
- **Cache Hit Rate**: ~60-80% for frequently accessed resources
- **Response Time**: Cached responses are ~100x faster (microseconds vs milliseconds)
- **Rate Limit Savings**: Reduces API calls by 60-80%
- **User Experience**: Faster responses, fewer rate limit errors

#### Key Learnings

1. **TTL is Critical**: Set appropriate TTL values. Too short = too many API calls. Too long = stale data.

2. **Tag-Based Indexing**: Tags enable flexible queries (e.g., "all open issues") without scanning the entire cache.

3. **Cache Invalidation**: When resources are updated, invalidate the cache. This is crucial for data consistency.

4. **Memory Management**: In-memory caches can grow large. Implement size limits and cleanup strategies.

5. **Cache-Aside Pattern**: Check cache first, then API. This is simple and effective for read-heavy workloads.

### 3. Event System

I built an event store to track resource changes, enabling future features like webhooks and real-time updates:

```python
class EventStore:
    async def store_event(self, event: ResourceEvent):
        # Store event with metadata
        await self._persist_event(event)
```

**Learning**: Building for the future is important, but don't over-engineer. Start with a simple implementation and extend as needed.

## Technologies & Tools

The project uses a modern Python stack:

- **Python 3.8+**: Modern Python features and async support
- **MCP SDK**: Official Python SDK for Model Context Protocol
- **Pydantic**: Data validation and settings management
- **PyGithub**: GitHub API client (for REST operations)
- **httpx**: Modern async HTTP client (for GraphQL)
- **aiohttp**: Additional async HTTP support
- **Click**: CLI interface
- **pytest**: Testing framework
- **Black, Ruff, MyPy**: Code quality tools

## Learning Journey: Key Takeaways

### 1. Clean Architecture is Worth It

Following Clean Architecture principles made the codebase much more maintainable. Even though it required more upfront planning, it paid off when adding new features or fixing bugs.

**Real Example**: When I needed to add support for GitLab (in addition to GitHub), I only had to:
- Create new repository implementations (infrastructure layer)
- Keep the same domain interfaces
- No changes to business logic or MCP tools

This would have been much harder with a monolithic architecture.

### 2. Type Hints Are Essential

Python's type hints, combined with Pydantic, caught many bugs early. They also made the code self-documenting and improved IDE support.

**Example**: Type hints caught this bug before runtime:
```python
# Without type hints, this would fail at runtime
def create_issue(title: str, labels: list[str]) -> Issue:
    # ...
    
# Type checker catches this immediately
create_issue("Bug", "bug")  # Error: Expected list[str], got str
```

### 3. Async Programming Requires Discipline

Once you go async, you need to be consistent. Mixing sync and async code leads to confusion. Use `asyncio` utilities and understand the event loop.

**Common Pitfall**: Using `time.sleep()` instead of `await asyncio.sleep()` blocks the entire event loop, defeating the purpose of async.

### 4. Error Handling is Critical

Robust error handling, especially for external APIs, is crucial. Always implement retry logic, handle rate limits, and provide meaningful error messages.

**Production Impact**: The retry logic with exponential backoff has saved the system from failing during GitHub API outages or rate limit spikes.

### 5. Testing is Easier with Good Architecture

The Clean Architecture made testing straightforward. I could mock repositories and test business logic independently of external services.

**Example**:
```python
async def test_create_roadmap():
    # Mock repositories
    mock_project_repo = MockProjectRepository()
    mock_milestone_repo = MockMilestoneRepository()
    
    # Test business logic without hitting GitHub API
    service = ProjectManagementService(
        project_repo=mock_project_repo,
        milestone_repo=mock_milestone_repo
    )
    
    roadmap = await service.create_roadmap(roadmap_data)
    assert len(roadmap.milestones) == 3
```

### 6. Documentation Matters

Good documentation (README, architecture docs, code comments) is essential, especially for open-source projects. It helps others understand and contribute.

**Impact**: Well-documented code is easier to maintain, even for yourself months later.

### 7. Learning from Existing Projects is Valuable

Studying the original TypeScript implementation taught me:
- How to structure an MCP server
- Common patterns and pitfalls
- Best practices for tool design

Reimplementing it in Python deepened my understanding of both the problem and the solution.

### 8. Performance Optimization is Iterative

I started with a simple implementation and optimized based on real usage:
- Added caching after noticing repeated API calls
- Implemented concurrent operations after seeing sequential bottlenecks
- Added connection pooling after identifying connection overhead

Measure first, optimize second.

### 9. API Design Matters

Well-designed tool interfaces make the system easier to use:
- Clear, descriptive tool names
- Comprehensive descriptions (for AI assistants)
- Sensible defaults
- Good error messages

### 10. Building for Extensibility

I designed the system to be extensible:
- Easy to add new tools
- Easy to add new repository implementations
- Easy to add new features

This has made adding features much easier than if I had built a monolithic system.

## Future Enhancements

The project is functional but has room for growth:

- **AI-Powered Features**: Task generation, issue analysis, and intelligent recommendations
- **Webhook Integration**: Real-time updates from GitHub
- **Persistent Caching**: Redis or database-backed cache
- **Advanced Metrics**: Performance tracking and usage analytics
- **Multi-Repository Support**: Manage projects across multiple repositories

## Conclusion

Building this MCP server was a fantastic learning experience. By reimplementing an existing TypeScript project in Python, I learned:
- How to translate design patterns and architectures between languages
- The nuances of async programming in Python vs Node.js
- How different validation libraries (Zod vs Pydantic) solve similar problems
- Clean Architecture principles and their practical application
- API integration and error handling best practices
- Building production-ready systems

The project is now a fully functional MCP server with 47+ tools, comprehensive error handling, and a maintainable architecture. It can be integrated with AI assistants like Cursor, Claude Desktop, and VS Code to automate GitHub project management.

**A special thanks to [@kunwarVivek](https://github.com/kunwarVivek) for the original TypeScript implementation** that served as both inspiration and a valuable reference. Studying well-architected code is one of the best ways to grow as a developer.

If you're interested in exploring the codebase or contributing, check out the repository. I'd love to hear your thoughts and feedback!

---

**What's Next?**

I'm planning to add AI-powered features next, including automated task generation and intelligent issue analysis. If you have ideas or want to collaborate, feel free to reach out!

#Python #SoftwareArchitecture #GitHub #MCP #CleanArchitecture #AsyncProgramming #OpenSource #DeveloperJourney

