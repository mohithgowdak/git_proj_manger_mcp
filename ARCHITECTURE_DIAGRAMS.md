# Architecture Diagrams

This directory contains detailed Mermaid.js architecture diagrams for the MCP GitHub Project Manager project.

## Files

1. **architecture.mmd** - Main system architecture diagram showing all layers and components
2. **architecture-detailed.mmd** - Multiple detailed diagrams including:
   - Component architecture
   - Request flow sequence
   - Error handling flow
   - Caching strategy
   - Tool categories breakdown
3. **architecture-class-diagram.mmd** - UML-style class diagram showing relationships

## How to View

### Option 1: GitHub/GitLab
These diagrams will render automatically when viewed on GitHub or GitLab.

### Option 2: VS Code
Install the "Markdown Preview Mermaid Support" extension:
1. Open VS Code
2. Install extension: `bierner.markdown-mermaid`
3. Open the `.mmd` files and use the preview

### Option 3: Online Editors
- [Mermaid Live Editor](https://mermaid.live/)
- [Mermaid Chart](https://www.mermaidchart.com/)

### Option 4: Command Line
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG
mmdc -i architecture.mmd -o architecture.png

# Generate SVG
mmdc -i architecture.mmd -o architecture.svg
```

## Diagram Descriptions

### Main Architecture (architecture.mmd)
Shows the complete system architecture with:
- **External Layer**: MCP Clients (Cursor, Claude Desktop, VS Code)
- **MCP Server Layer**: Server and transport
- **Tool Layer**: 47+ tools, validation, formatting
- **Service Layer**: Business logic orchestration
- **Infrastructure Layer**: GitHub integration, repositories, caching, events
- **Domain Layer**: Core types, protocols, errors
- **External Systems**: GitHub API

### Detailed Architecture (architecture-detailed.mmd)
Contains 5 sub-diagrams:

1. **System Component Architecture**: Detailed component view with all subsystems
2. **Request Flow Sequence**: Step-by-step flow of a tool execution
3. **Error Handling Flow**: How errors are processed and retried
4. **Caching Strategy**: Cache operations and indexing
5. **Tool Categories**: Breakdown of all 47+ tools by category

### Class Diagram (architecture-class-diagram.mmd)
UML-style class diagram showing:
- Class relationships (inheritance, composition, usage)
- Key methods and properties
- Domain entities and their relationships

## Architecture Layers

### 1. MCP Protocol Layer
- Handles JSON-RPC communication via stdio
- Implements MCP protocol specification
- Manages tool registration and execution

### 2. Tool Layer
- **ToolRegistry**: Singleton managing all 47+ tools
- **Tool Handlers**: Execution logic for each tool
- **Tool Validator**: Pydantic-based validation
- **Result Formatter**: MCP response formatting

### 3. Service Layer
- **ProjectManagementService**: Main orchestrator
- Coordinates between repositories
- Implements complex workflows (roadmaps, sprints)

### 4. Repository Layer
- **Factory Pattern**: Creates repository instances
- **Base Repository**: Common functionality (retry, error handling)
- **Concrete Repositories**: Project, Issue, Milestone, Sprint

### 5. API Integration Layer
- **GraphQL Client**: Async httpx for GraphQL queries
- **PyGithub Client**: REST API operations
- **Error Handler**: Maps GitHub errors to domain errors

### 6. Supporting Systems
- **Resource Cache**: In-memory caching with TTL
- **Event Store**: Tracks resource changes
- **Logger**: Structured logging

### 7. Domain Layer
- **Types**: Core domain entities
- **Protocols**: Repository interfaces
- **Errors**: Domain-specific error types

## Key Design Patterns

1. **Clean Architecture**: Clear separation of concerns, dependency inversion
2. **Repository Pattern**: Abstracts data access
3. **Factory Pattern**: Creates repository instances
4. **Singleton Pattern**: ToolRegistry, Cache, Logger
5. **Retry Pattern**: Exponential backoff for API calls
6. **Cache-Aside Pattern**: Check cache, then API

## Data Flow

1. **Client Request** → MCP Client sends JSON-RPC request
2. **MCP Server** → Routes to appropriate tool handler
3. **Tool Handler** → Validates arguments, calls service
4. **Service** → Orchestrates business logic
5. **Repository** → Checks cache, queries GitHub API
6. **GitHub API** → Returns data
7. **Repository** → Caches result, returns to service
8. **Service** → Returns to handler
9. **Handler** → Formats MCP response
10. **MCP Server** → Sends JSON-RPC response to client

## Error Handling Flow

1. API error occurs
2. GitHubErrorHandler maps to domain error
3. Retry logic checks if error is retryable
4. Exponential backoff (1s, 2s, 4s)
5. Max 3 retry attempts
6. If fails, returns domain error
7. Tool handler formats as MCP error response

## Caching Strategy

- **Storage**: In-memory dictionary
- **TTL**: Default 1 hour (configurable)
- **Indexing**: By type, tag, namespace
- **Hit Rate**: 60-80% for frequently accessed resources
- **Operations**: get, set, get_by_type, get_by_tag, delete, clear

## Performance Characteristics

- **Project Operations**: ~200-500ms
- **Issue Operations**: ~150-400ms
- **Milestone Operations**: ~200-400ms
- **Sprint Operations**: ~300-600ms
- **Roadmap Creation**: ~1-3s

## Technology Stack

- **Python 3.8+**: Core language
- **MCP SDK**: Protocol implementation
- **Pydantic**: Data validation
- **PyGithub**: GitHub REST API
- **httpx**: Async HTTP client for GraphQL
- **aiohttp**: Additional async support
- **Click**: CLI interface

