---
name: HLD LLD System Design
overview: Complete High-Level Design and Low-Level Design documentation for the MCP GitHub Project Manager, covering system context, component architecture, data flows, module design, state machines, data models, API contracts, error handling, storage schemas, dependency graph, and infrastructure topology.
todos: []
isProject: false
---

# STEP 6: System Design -- HLD + LLD

# GitForge MCP -- Complete System Design Document

---

# PART A: HIGH-LEVEL DESIGN (HLD)

---

## 1. System Context

The system is an MCP (Model Context Protocol) server that sits between AI assistants and GitHub's API. It receives structured tool calls from AI clients over stdio, translates them into GitHub API operations, and returns structured responses.

```mermaid
graph TB
    subgraph actors [Human Actors]
        Dev[Developer using AI Assistant]
    end

    subgraph aiclients [AI Clients]
        Cursor[Cursor IDE]
        Claude[Claude Desktop]
        VSCode[VS Code Copilot]
    end

    subgraph system ["GitForge MCP Server (This System)"]
        MCPServer["MCP Protocol Server\nPython 3.8+ / asyncio"]
    end

    subgraph external [External Dependencies]
        GitHubGQL["GitHub GraphQL API\napi.github.com/graphql"]
        GitHubREST["GitHub REST API\napi.github.com"]
    end

    Dev -->|natural language| Cursor
    Dev -->|natural language| Claude
    Dev -->|natural language| VSCode
    Cursor -->|"stdio JSON-RPC\n(list_tools, call_tool)"| MCPServer
    Claude -->|"stdio JSON-RPC\n(list_tools, call_tool)"| MCPServer
    VSCode -->|"stdio JSON-RPC\n(list_tools, call_tool)"| MCPServer
    MCPServer -->|"HTTPS + Bearer Token\nGraphQL mutations/queries"| GitHubGQL
    MCPServer -->|"HTTPS + Bearer Token\nREST endpoints"| GitHubREST
```



**Key constraint:** The server is a child process spawned by the AI client. Communication is strictly over stdin/stdout using JSON-RPC. There is no HTTP server, no port binding, no network listener.

---

## 2. Component Architecture

```mermaid
graph TB
    subgraph boundary ["System Boundary -- GitForge MCP"]
        subgraph entrypoint [Entry Point]
            MainModule["__main__.py\nServer bootstrap"]
            CLI["cli.py\nArg parsing"]
            Env["env.py\nConfig loading"]
        end

        subgraph protocol [Protocol Layer]
            MCPServer2["GitHubProjectManagerServer\n- list_tools handler\n- call_tool handler"]
            StdioTransport["MCP stdio Transport\nJSON-RPC over stdin/stdout"]
        end

        subgraph tools [Tool Layer]
            Registry["ToolRegistry\nSingleton, 47 tools"]
            Schemas["ToolSchemas\n40+ Pydantic models"]
            Validator["ToolValidator\nInput validation"]
            Handlers["ToolHandlers\nDispatch map"]
            Formatter["ResultFormatter\nJSON/MD/HTML/Text"]
        end

        subgraph business [Business Logic Layer]
            PMService["ProjectManagementService\nOrchestrator"]
        end

        subgraph data [Data Access Layer]
            Factory["GitHubRepositoryFactory"]
            BaseRepo2["BaseGitHubRepository\nRetry + error handling"]
            ProjRepo["ProjectRepository\nGraphQL mutations"]
            IssueRepo2["IssueRepository\nREST + GraphQL"]
            MileRepo["MilestoneRepository\nREST via PyGithub"]
            SprintRepo2["SprintRepository\nGraphQL iterations"]
        end

        subgraph infra [Infrastructure Layer]
            GQLClient["GraphQLClient\nhttpx async"]
            PyGH["PyGithub Client\nREST sync wrapper"]
            ErrHandler["GitHubErrorHandler"]
            Cache2["ResourceCache\nIn-memory TTL"]
            Events["EventStore\nMemory + disk"]
            Log["Logger"]
        end
    end

    MainModule --> MCPServer2
    CLI --> Env
    Env --> MainModule
    StdioTransport --> MCPServer2
    MCPServer2 --> Registry
    MCPServer2 --> Handlers
    Registry --> Schemas
    Handlers --> Validator
    Handlers --> PMService
    Handlers --> Formatter
    PMService --> Factory
    Factory --> ProjRepo
    Factory --> IssueRepo2
    Factory --> MileRepo
    Factory --> SprintRepo2
    BaseRepo2 -.-> ProjRepo
    BaseRepo2 -.-> IssueRepo2
    BaseRepo2 -.-> MileRepo
    BaseRepo2 -.-> SprintRepo2
    ProjRepo --> GQLClient
    IssueRepo2 --> PyGH
    IssueRepo2 --> GQLClient
    MileRepo --> PyGH
    SprintRepo2 --> GQLClient
    BaseRepo2 --> ErrHandler
    PMService --> Cache2
    PMService --> Events
```



---

## 3. Data Flow Diagrams

### 3.1 Tool Execution Flow (Happy Path)

```mermaid
sequenceDiagram
    participant Client as AI Client
    participant Stdio as stdio Transport
    participant Server as MCPServer
    participant Reg as ToolRegistry
    participant Val as ToolValidator
    participant Hand as ToolHandler
    participant Svc as PMService
    participant Repo as Repository
    participant Base as BaseRepo
    participant API as GitHub API
    participant Cache as Cache

    Client->>Stdio: JSON-RPC call_tool
    Stdio->>Server: name + arguments
    Server->>Reg: get_tool by name
    Reg-->>Server: ToolDefinition + schema
    Server->>Val: validate args against schema
    Val-->>Server: Pydantic model instance
    Server->>Hand: execute_tool with validated args
    Hand->>Svc: call business method
    Svc->>Cache: lookup by ResourceType + ID
    alt Cache Hit
        Cache-->>Svc: cached entity
    else Cache Miss
        Svc->>Repo: async data operation
        Repo->>Base: with_retry wrapper
        Base->>API: GraphQL or REST call
        API-->>Base: JSON response
        Base-->>Repo: parsed response
        Repo-->>Svc: Domain entity
        Svc->>Cache: store with TTL
    end
    Svc-->>Hand: Domain entity
    Hand-->>Server: MCPSuccessResponse
    Server-->>Stdio: JSON-RPC response
    Stdio-->>Client: result
```



### 3.2 Roadmap Creation Flow (Complex Multi-Step)

```mermaid
sequenceDiagram
    participant Hand as Handler
    participant Svc as PMService
    participant ProjR as ProjectRepo
    participant MileR as MilestoneRepo
    participant IssR as IssueRepo
    participant API as GitHub API

    Hand->>Svc: create_roadmap args
    Svc->>ProjR: create_project
    ProjR->>API: createProjectV2 mutation
    API-->>ProjR: Project node ID
    ProjR-->>Svc: Project entity

    loop For each milestone in roadmap
        Svc->>MileR: create_milestone
        MileR->>API: create milestone REST
        API-->>MileR: Milestone data
        MileR-->>Svc: Milestone entity

        loop For each issue in milestone
            Svc->>IssR: create_issue
            IssR->>API: create issue REST
            API-->>IssR: Issue data
            IssR-->>Svc: Issue entity
        end
    end

    Svc-->>Hand: Complete roadmap result
```



### 3.3 Retry Flow (Error Path)

```mermaid
sequenceDiagram
    participant Base as BaseRepo
    participant API as GitHub API
    participant EH as ErrorHandler

    Base->>API: API call attempt 1
    API-->>Base: 429 Rate Limited
    Base->>EH: handle_error
    EH-->>Base: RateLimitError, retryable=true
    Base->>Base: sleep 1s
    Base->>API: API call attempt 2
    API-->>Base: 502 Bad Gateway
    Base->>EH: handle_error
    EH-->>Base: GitHubAPIError, retryable=true
    Base->>Base: sleep 2s
    Base->>API: API call attempt 3
    API-->>Base: 200 OK
    Base-->>Base: return parsed data
```



---

## 4. Non-Functional Requirements


| Requirement          | Current State                                | Target                                     |
| -------------------- | -------------------------------------------- | ------------------------------------------ |
| **Latency**          | 150-500ms per tool call (API-bound)          | Acceptable -- GitHub API is the bottleneck |
| **Throughput**       | Sequential tool calls only (stdio is serial) | N/A -- inherent MCP limitation             |
| **Availability**     | Process lifecycle tied to AI client          | Acceptable for stdio transport             |
| **Cache Hit Rate**   | 60-80% for repeated reads                    | Good for read-heavy patterns               |
| **Retry Resilience** | 3 attempts, exponential backoff              | Handles transient GitHub failures          |
| **Error Recovery**   | Graceful degradation to error response       | No tool call crashes the server            |
| **Memory**           | 10-50MB depending on cache size              | Acceptable for a child process             |
| **Startup Time**     | <2s (import + GitHub client init)            | Acceptable                                 |
| **Concurrency**      | Single-threaded async event loop             | Matches stdio serial nature                |
| **Security**         | Token in env var, no encryption at rest      | Minimum viable for local tool              |


---

---

# PART B: LOW-LEVEL DESIGN (LLD)

---

## 5. Module Design

### 5.1 Module Dependency Graph

```mermaid
graph TB
    main["__main__.py"] --> env["env.py"]
    main --> cli["cli.py"]
    main --> logger["logger/__init__.py"]
    main --> toolreg["tool_registry.py"]
    main --> pms["project_management_service.py"]
    main --> toolhand["tool_handlers.py"]
    main --> toolval["tool_validator.py"]

    toolreg --> toolschemas["tool_schemas.py"]
    toolhand --> pms
    toolhand --> formatter["tool_result_formatter.py"]
    toolhand --> mcpfmt["mcp_response_formatter.py"]
    toolval --> toolschemas
    toolval --> mcptypes["mcp_types.py"]

    pms --> factory["github_repository_factory.py"]
    pms --> cache["resource_cache.py"]
    pms --> events["event_store.py"]

    factory --> config["github_config.py"]
    factory --> projrepo["github_project_repository.py"]
    factory --> issuerepo["github_issue_repository.py"]
    factory --> milerepo["github_milestone_repository.py"]
    factory --> sprintrepo["github_sprint_repository.py"]

    projrepo --> baserepo["base_repository.py"]
    issuerepo --> baserepo
    milerepo --> baserepo
    sprintrepo --> baserepo

    baserepo --> gqlclient["graphql_client.py"]
    baserepo --> errhandler["github_error_handler.py"]
    baserepo --> config

    gqlclient --> config
    errhandler --> errors["errors.py"]

    toolschemas --> types["types.py"]
    pms --> types
    projrepo --> types
    issuerepo --> types
    milerepo --> types
    sprintrepo --> types

    types --> restypes["resource_types.py"]
    mcptypes --> restypes
```



### 5.2 Module Responsibilities (Single Responsibility)


| Module                           | Responsibility                              | Lines (approx) | Dependencies                |
| -------------------------------- | ------------------------------------------- | -------------- | --------------------------- |
| `__main__.py`                    | Bootstrap server, wire handlers             | ~120           | env, cli, registry, service |
| `env.py`                         | Load config from CLI + env + .env file      | ~150           | cli, dotenv                 |
| `tool_registry.py`               | Register + discover 47 tools                | ~150           | tool_schemas                |
| `tool_schemas.py`                | Define 40+ Pydantic input models            | ~900           | domain types                |
| `tool_validator.py`              | Validate + coerce tool arguments            | ~200           | schemas, mcp_types          |
| `tool_handlers.py`               | Execute tool logic, dispatch map            | ~1200          | service, formatter          |
| `tool_result_formatter.py`       | Format results as JSON/MD/HTML              | ~200           | mcp_types                   |
| `project_management_service.py`  | Orchestrate business operations             | ~700           | factory, cache, events      |
| `github_repository_factory.py`   | Create repo instances, validate token       | ~120           | config, repos               |
| `base_repository.py`             | Retry logic, error handling, GraphQL access | ~100           | gql_client, error_handler   |
| `github_project_repository.py`   | GitHub Projects v2 GraphQL CRUD             | ~800           | base_repo, gql_client       |
| `github_issue_repository.py`     | Issue CRUD with REST fallback               | ~500           | base_repo, PyGithub         |
| `github_milestone_repository.py` | Milestone CRUD via REST                     | ~250           | base_repo, PyGithub         |
| `github_sprint_repository.py`    | Sprint/iteration via GraphQL                | ~400           | base_repo, gql_client       |
| `graphql_client.py`              | Execute GraphQL queries async               | ~100           | httpx, config               |
| `github_error_handler.py`        | Map HTTP errors to domain errors            | ~100           | domain errors               |
| `resource_cache.py`              | In-memory cache with TTL + indices          | ~250           | resource_types              |
| `event_store.py`                 | Event storage with memory + disk            | ~300           | resource_types              |


---

## 6. State Machine Transitions

### 6.1 Issue Lifecycle

```mermaid
stateDiagram-v2
    [*] --> ACTIVE: create_issue
    ACTIVE --> IN_PROGRESS: update status
    IN_PROGRESS --> ACTIVE: reopen
    IN_PROGRESS --> CLOSED: close
    ACTIVE --> CLOSED: close
    CLOSED --> ACTIVE: reopen
    CLOSED --> [*]
```



### 6.2 Sprint Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PLANNED: create_sprint
    PLANNED --> ACTIVE: start date reached
    PLANNED --> CANCELLED: cancel
    ACTIVE --> COMPLETED: end date reached
    ACTIVE --> ACTIVE: add/remove issues
    COMPLETED --> [*]
    CANCELLED --> [*]
```



### 6.3 Milestone Lifecycle

```mermaid
stateDiagram-v2
    [*] --> ACTIVE: create_milestone
    ACTIVE --> ACTIVE: update details
    ACTIVE --> CLOSED: close milestone
    CLOSED --> ACTIVE: reopen
    CLOSED --> [*]
```



### 6.4 Project Lifecycle

```mermaid
stateDiagram-v2
    [*] --> ACTIVE: create_project
    ACTIVE --> ACTIVE: update / add items
    ACTIVE --> CLOSED: close project
    CLOSED --> ACTIVE: reopen
    CLOSED --> [*]
```



### 6.5 Cache Entry Lifecycle

```mermaid
stateDiagram-v2
    [*] --> VALID: cache.set with TTL
    VALID --> VALID: cache.get before expiry
    VALID --> EXPIRED: TTL elapsed
    EXPIRED --> VALID: cache.set refreshes
    EXPIRED --> [*]: cleanup removes entry
    VALID --> [*]: cache.delete
```



### 6.6 MCP Request Lifecycle

```mermaid
stateDiagram-v2
    [*] --> RECEIVED: JSON-RPC arrives on stdin
    RECEIVED --> VALIDATING: lookup tool + validate args
    VALIDATING --> REJECTED: validation fails
    VALIDATING --> EXECUTING: validation passes
    EXECUTING --> RETRYING: retryable API error
    RETRYING --> EXECUTING: retry attempt
    RETRYING --> FAILED: max retries exceeded
    EXECUTING --> SUCCESS: API returns data
    SUCCESS --> [*]: MCPSuccessResponse on stdout
    FAILED --> [*]: MCPErrorResponse on stdout
    REJECTED --> [*]: MCPErrorResponse on stdout
```



---

## 7. Complete Data Models

### 7.1 Domain Entities

```python
# Issue
@dataclass
class Issue:
    id: str                          # GitHub node ID (e.g. "I_kwDOAbc123")
    number: int                      # Human-readable number
    title: str
    description: Optional[str]
    status: ResourceStatus           # ACTIVE | IN_PROGRESS | CLOSED
    assignees: List[str]             # GitHub usernames
    labels: List[str]                # Label names
    milestone_id: Optional[str]      # Milestone number as string
    created_at: str                  # ISO 8601
    updated_at: str                  # ISO 8601
    url: str                         # GitHub web URL

# Project
@dataclass
class Project:
    id: str                          # GitHub node ID (e.g. "PVT_kwDO...")
    type: str                        # Always "ProjectV2"
    title: str
    description: Optional[str]
    owner: str                       # GitHub username or org
    number: int
    url: str
    fields: List[CustomField]
    views: List[ProjectView]
    closed: bool
    created_at: str
    updated_at: str
    status: ResourceStatus
    visibility: str                  # "public" | "private"
    version: int

# Milestone
@dataclass
class Milestone:
    id: str
    number: int
    title: str
    description: Optional[str]
    due_date: Optional[str]          # ISO 8601 date
    status: ResourceStatus
    created_at: str
    updated_at: str
    url: str
    progress: Dict[str, Any]         # {open_issues, closed_issues, completion_percentage}

# Sprint
@dataclass
class Sprint:
    id: str
    title: str
    description: Optional[str]
    start_date: str                  # ISO 8601
    end_date: str                    # ISO 8601
    status: ResourceStatus           # PLANNED | ACTIVE | COMPLETED
    issues: List[str]                # Issue IDs
    created_at: str
    updated_at: str

# CustomField
@dataclass
class CustomField:
    id: str
    name: str
    type: FieldType                  # text | number | date | single_select | iteration
    options: List[FieldOption]       # For single_select fields
    description: Optional[str]
    required: bool
    default_value: Optional[Any]
    validation: Optional[Dict]
    config: Optional[Dict]

# IssueComment
@dataclass
class IssueComment:
    id: str
    body: str
    author: str
    created_at: str
    updated_at: str
```

### 7.2 Creation DTOs (Data Transfer Objects)

```python
@dataclass
class CreateIssue:
    title: str
    description: Optional[str] = None
    assignees: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    milestone_id: Optional[str] = None

@dataclass
class CreateProject:
    title: str
    owner: str
    description: Optional[str] = None
    visibility: str = "private"

@dataclass
class CreateMilestone:
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None

@dataclass
class CreateSprint:
    title: str
    description: Optional[str] = None
    start_date: str = ""
    end_date: str = ""
    project_id: Optional[str] = None
    issue_ids: List[str] = field(default_factory=list)
```

---

## 8. API Contracts (All 47+ MCP Tools)

### 8.1 Project Tools

```
create_project
  IN:  { title: str, owner: str, visibility?: "public"|"private", short_description?: str }
  OUT: { id, title, owner, url, visibility, status }

list_projects
  IN:  { status?: "active"|"closed", limit?: int }
  OUT: [ { id, title, status, url } ... ]

get_project
  IN:  { project_id: str }
  OUT: { id, title, description, owner, fields, views, status }

update_project
  IN:  { project_id: str, title?: str, description?: str, visibility?: str, status?: str }
  OUT: { id, title, status }

delete_project
  IN:  { project_id: str }
  OUT: { success: true }
```

### 8.2 Issue Tools

```
create_issue
  IN:  { title: str, description?: str, labels?: [str], assignees?: [str],
         milestone_id?: str, priority?: str, type?: str }
  OUT: { id, number, title, status, url }

list_issues
  IN:  { status?: "open"|"closed"|"all", assignee?: str, labels?: [str],
         milestone?: str, sort?: str, direction?: str, limit?: int }
  OUT: [ { id, number, title, status, labels } ... ]

get_issue
  IN:  { issue_id: str }
  OUT: { id, number, title, description, status, assignees, labels, url }

update_issue
  IN:  { issue_id: str, title?: str, description?: str, status?: str,
         labels?: [str], assignees?: [str], milestone_id?: str,
         project_id?: str, project_field_values?: dict }
  OUT: { id, number, title, status }

search_issues
  IN:  { query: str }  // GitHub search syntax: "is:open label:bug"
  OUT: [ { id, number, title, status, labels } ... ]
```

### 8.3 Comment Tools

```
add_issue_comment
  IN:  { issue_id: str, body: str }
  OUT: { id, body, author, created_at }

list_issue_comments
  IN:  { issue_id: str }
  OUT: [ { id, body, author, created_at } ... ]

update_issue_comment
  IN:  { issue_id: str, comment_id: str, body: str }
  OUT: { id, body, updated_at }

delete_issue_comment
  IN:  { issue_id: str, comment_id: str }
  OUT: { success: true }
```

### 8.4 Milestone Tools

```
create_milestone
  IN:  { title: str, description?: str, due_date?: str }
  OUT: { id, number, title, due_date, status }

list_milestones
  IN:  { status?: "open"|"closed"|"all", sort?: str, direction?: str }
  OUT: [ { id, number, title, due_date, status } ... ]

update_milestone
  IN:  { milestone_id: str, title?: str, description?: str, due_date?: str, state?: str }
  OUT: { id, number, title, status }

delete_milestone
  IN:  { milestone_id: str }
  OUT: { success: true }

get_milestone_metrics
  IN:  { milestone_id: str, include_issues?: bool }
  OUT: { open_issues, closed_issues, completion_percentage, days_remaining, issues? }

get_overdue_milestones
  IN:  { limit: int, include_issues?: bool }
  OUT: [ { id, title, due_date, days_overdue, metrics } ... ]

get_upcoming_milestones
  IN:  { days_ahead: int, limit: int, include_issues?: bool }
  OUT: [ { id, title, due_date, days_until_due, metrics } ... ]
```

### 8.5 Sprint Tools

```
create_sprint
  IN:  { title: str, description: str, start_date: str, end_date: str, issue_ids?: [str] }
  OUT: { id, title, start_date, end_date, status }

plan_sprint
  IN:  { sprint: { title, start_date, end_date, goals?: [str] }, issue_ids?: [str] }
  OUT: { sprint, assigned_issues }

list_sprints
  IN:  { status?: "all"|"active"|"completed"|"planned" }
  OUT: [ { id, title, start_date, end_date, status } ... ]

get_current_sprint
  IN:  { include_issues?: bool }
  OUT: { id, title, start_date, end_date, issues? }

update_sprint
  IN:  { sprint_id: str, title?: str, description?: str, status?: str,
         start_date?: str, end_date?: str }
  OUT: { id, title, status }

add_issues_to_sprint
  IN:  { sprint_id: str, issue_ids: [str] }
  OUT: { sprint_id, added_issues }

remove_issues_from_sprint
  IN:  { sprint_id: str, issue_ids: [str] }
  OUT: { sprint_id, removed_issues }

get_sprint_metrics
  IN:  { sprint_id: str, include_issues?: bool }
  OUT: { total_issues, completed, in_progress, completion_percentage }
```

### 8.6 Roadmap Tool

```
create_roadmap
  IN:  {
    project: { title: str, visibility: str, short_description?: str },
    milestones: [
      {
        milestone: { title: str, description: str, due_date?: str },
        issues?: [ { title: str, description: str, labels?: [str],
                     assignees?: [str], priority?: str, type?: str } ]
      }
    ]
  }
  OUT: { project, milestones: [ { milestone, issues } ] }
```

### 8.7 Field, View, Item, Label Tools

```
create_project_field
  IN:  { project_id: str, name: str, type: str, options?: any, description?: str }
  OUT: { id, name, type, options }

list_project_fields
  IN:  { project_id: str }
  OUT: [ { id, name, type, options } ... ]

create_project_view
  IN:  { project_id: str, name: str, layout: "board"|"table"|"timeline"|"roadmap" }
  OUT: { id, name, layout }

add_project_item
  IN:  { project_id: str, content_id: str, content_type: str, priority?: str, type?: str }
  OUT: { item_id, content_id }

set_field_value
  IN:  { project_id: str, item_id: str, field_id: str, value: any }
  OUT: { item_id, field_id, value }

filter_project_items
  IN:  { project_id: str, field_filters: dict }
  OUT: [ { item_id, content_id, field_values } ... ]

create_label
  IN:  { name: str, color: str, description?: str }
  OUT: { name, color, description }

list_labels
  IN:  { limit?: int }
  OUT: [ { name, color, description } ... ]
```

---

## 9. Error Handling Flows

### 9.1 Error Hierarchy

```mermaid
graph TB
    Exception --> DomainError
    DomainError --> ValidationError
    DomainError --> ResourceNotFoundError
    DomainError --> UnauthorizedError
    DomainError --> RateLimitError
    DomainError --> ConfigurationError
    DomainError --> IntegrationError
    DomainError --> GitHubAPIError
    DomainError --> MCPProtocolError
```



### 9.2 Error Mapping Table

```
GitHub HTTP 401   --> UnauthorizedError     --> MCPErrorCode.UNAUTHORIZED
GitHub HTTP 403   --> UnauthorizedError     --> MCPErrorCode.UNAUTHORIZED
  (if rate limit) --> RateLimitError        --> MCPErrorCode.RATE_LIMITED
GitHub HTTP 404   --> ResourceNotFoundError --> MCPErrorCode.RESOURCE_NOT_FOUND
GitHub HTTP 429   --> RateLimitError        --> MCPErrorCode.RATE_LIMITED
GitHub HTTP 5xx   --> GitHubAPIError        --> MCPErrorCode.INTERNAL_ERROR
Pydantic failure  --> ValidationError       --> MCPErrorCode.VALIDATION_ERROR
Network timeout   --> IntegrationError      --> MCPErrorCode.INTERNAL_ERROR
Unknown exception --> DomainError           --> MCPErrorCode.INTERNAL_ERROR
```

### 9.3 Retry Decision Matrix

```
Error Code  | Retryable | Max Attempts | Backoff
------------|-----------|--------------|--------
429         | YES       | 3            | Rate-limit reset header or 2^n seconds
500         | YES       | 3            | 1s, 2s, 4s
502         | YES       | 3            | 1s, 2s, 4s
503         | YES       | 3            | 1s, 2s, 4s
504         | YES       | 3            | 1s, 2s, 4s
Network err | YES       | 3            | 1s, 2s, 4s
400         | NO        | 0            | --
401         | NO        | 0            | --
403         | NO        | 0            | --
404         | NO        | 0            | --
422         | NO        | 0            | --
```

---

## 10. Storage Schemas

### 10.1 In-Memory Cache Schema

```
Storage: Dict[str, CacheEntry]

Key format: "{ResourceType}:{ResourceId}"
Examples:
  "PROJECT:PVT_kwDOAbc123"
  "ISSUE:I_kwDOXyz789"
  "MILESTONE:42"
  "SPRINT:iter_abc"

CacheEntry[T]:
  value: T                    # Domain entity (Issue, Project, etc.)
  expires_at: float           # Unix timestamp = now + TTL
  tags: List[str]             # ["sprint-1", "high-priority", "bug"]
  namespace: Optional[str]    # Multi-tenant isolation key
  last_modified: float        # Unix timestamp of last write
  version: int                # Optimistic concurrency version

Indices (derived, kept in sync):
  _type_index:      Dict[ResourceType, Set[cache_key]]
  _tag_index:       Dict[str, Set[cache_key]]
  _namespace_index: Dict[str, Set[cache_key]]

Default TTL: 3,600,000ms (1 hour)
Eviction: Lazy on read (check expires_at) + periodic cleanup
```

### 10.2 Event Store Schema

```
Memory Buffer: List[ResourceEvent] (max 10,000, FIFO overflow)

ResourceEvent:
  id: str                     # UUID v4
  type: str                   # "CREATED" | "UPDATED" | "DELETED"
  resource_type: str           # "PROJECT" | "ISSUE" | "MILESTONE" | "SPRINT"
  resource_id: str             # Entity ID
  source: str                  # "mcp-tool" | "webhook" | "system"
  timestamp: str               # ISO 8601
  data: Dict[str, Any]         # Event payload (before/after state)
  metadata: Dict[str, Any]     # Context (user, tool_name, request_id)

Disk Storage (planned):
  Directory: .mcp-cache/events/
  Files: events_YYYY-MM-DD.jsonl (one JSON per line)
  Rotation: 10,000 events per file
  Retention: 30 days (configurable)
  Compression: Optional gzip
```

### 10.3 Configuration Schema

```
Required:
  GITHUB_TOKEN: str           # "ghp_..." or "github_pat_..."
  GITHUB_OWNER: str           # Username or org name
  GITHUB_REPO: str            # Repository name

Optional (with defaults):
  SYNC_ENABLED: bool          # true
  SYNC_TIMEOUT_MS: int        # 5000
  CACHE_DIRECTORY: str        # ".cache"
  WEBHOOK_SECRET: str         # ""
  WEBHOOK_PORT: int           # 3000
  SSE_ENABLED: bool           # false
  EVENT_RETENTION_DAYS: int   # 30
  MAX_EVENTS_IN_MEMORY: int   # 10000

AI Config (all optional):
  ANTHROPIC_API_KEY: str
  OPENAI_API_KEY: str
  GOOGLE_API_KEY: str
  PERPLEXITY_API_KEY: str
  AI_MAIN_MODEL: str
  AI_RESEARCH_MODEL: str
```

---

## 11. Infrastructure Topology

### 11.1 Current (Local/Dev)

```mermaid
graph LR
    subgraph devmachine [Developer Machine]
        AIClient["AI Client\ne.g. Cursor"]
        subgraph childproc [Child Process]
            MCPProc["GitForge MCP\nPython 3.8+"]
            InMemCache["In-Memory Cache"]
            EventBuf["Event Buffer"]
        end
    end

    subgraph github [GitHub Cloud]
        GHAPI["api.github.com"]
    end

    AIClient -->|"stdin/stdout\nJSON-RPC"| MCPProc
    MCPProc -->|"HTTPS\nBearer Token"| GHAPI
    MCPProc --- InMemCache
    MCPProc --- EventBuf
```



### 11.2 Future (Containerized/Production)

```mermaid
graph TB
    subgraph clients2 [AI Clients]
        C1["Cursor"]
        C2["Claude Desktop"]
        C3["VS Code"]
    end

    subgraph infra2 [Infrastructure]
        subgraph container [Docker Container]
            MCPSvr["GitForge MCP Server"]
        end
        Redis["Redis Cache"]
        Postgres["PostgreSQL\nEvent Store"]
        Monitoring["Prometheus + Grafana"]
    end

    subgraph ext [External]
        GH2["GitHub API"]
    end

    C1 -->|stdio| container
    C2 -->|stdio| container
    C3 -->|stdio| container
    MCPSvr --> Redis
    MCPSvr --> Postgres
    MCPSvr --> GH2
    MCPSvr --> Monitoring
```



---

## 12. Key Design Constraints

1. **stdio-only transport**: The server cannot expose HTTP endpoints. All communication is stdin/stdout JSON-RPC. This means no webhooks can be received directly -- they would need a sidecar process.
2. **Single-threaded async**: Python's asyncio event loop is single-threaded. All I/O is non-blocking but CPU-bound operations block the loop. GraphQL response parsing is the heaviest CPU operation.
3. **GitHub API rate limits**: 5,000 requests/hour for authenticated users. With 47 tools and potential AI chaining, a single conversation could burn through hundreds of requests. The cache is the primary mitigation.
4. **GitHub Projects v2 is GraphQL-only**: Cannot use REST for project operations. Must maintain complex GraphQL queries for field types, views, items, and iterations.
5. **Sprints are not a GitHub primitive**: Sprints are implemented as iteration fields on Projects v2. This means sprint operations require multiple GraphQL calls (find/create iteration field, then set values on items).
6. **No persistent state**: The server is stateless across restarts. Cache, events, and sprint state are all volatile. This is acceptable for the current use case but limits advanced features.

