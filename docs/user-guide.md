# GitHub Project Manager MCP Server - User Guide

## Overview

The GitHub Project Manager MCP Server provides a Model Context Protocol (MCP) interface for managing GitHub Projects. This guide explains how to set up, configure, and use the server effectively.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A GitHub account with appropriate permissions
- A GitHub Personal Access Token with the following scopes:
  - `repo` (Full repository access)
  - `project` (Project access)
  - `write:org` (Organization access)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/git_proj_manger_mcp.git
   cd git_proj_manger_mcp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   # Create .env file
   touch .env
   ```

5. Edit `.env` with your GitHub credentials:
   ```env
   GITHUB_TOKEN=your_personal_access_token
   GITHUB_OWNER=repository_owner
   GITHUB_REPO=repository_name
   ```

## Running the Server

### Command Line

```bash
# Basic usage
python -m src

# With command line arguments
python -m src --token=your_token --owner=your_username --repo=your_repo

# With verbose logging
python -m src --verbose
```

### Environment Variables

You can also set environment variables:

```bash
export GITHUB_TOKEN=your_token
export GITHUB_OWNER=your_username
export GITHUB_REPO=your_repo
python -m src
```

## Features

### Project Management

1. **Roadmap Creation**
   - Create project roadmaps with milestones
   - Define project scope and objectives
   - Set project visibility and access controls

2. **Sprint Planning**
   - Create and manage sprints
   - Assign issues to sprints
   - Track sprint progress and metrics

3. **Milestone Management**
   - Create project milestones
   - Track milestone progress
   - Manage milestone deadlines

4. **Issue Tracking**
   - Create and manage issues
   - Track issue status and progress
   - Link related issues
   - Add custom fields

### Resource Types

1. **Projects**
   ```python
   from dataclasses import dataclass
   from typing import Optional
   
   @dataclass
   class Project:
       id: str
       title: str
       description: str
       status: str  # 'active' | 'closed'
       visibility: str  # 'private' | 'public'
       owner: str
       number: int
       url: str
   ```

2. **Milestones**
   ```python
   @dataclass
   class Milestone:
       id: str
       title: str
       description: str
       due_date: Optional[str]
       status: str  # 'active' | 'closed'
       number: int
       url: str
   ```

3. **Sprints**
   ```python
   @dataclass
   class Sprint:
       id: str
       title: str
       description: str
       start_date: str
       end_date: str
       status: str  # 'active' | 'closed'
       issues: List[str]
   ```

## MCP Tool Usage

### Project Operations

1. **Create Project**
   ```python
   # Using MCP tools via client
   result = await mcp_client.call_tool("create_project", {
       "title": "My Project",
       "owner": "repository_owner",
       "visibility": "private",
       "short_description": "Project description"
   })
   ```

2. **List Projects**
   ```python
   result = await mcp_client.call_tool("list_projects", {
       "status": "active",
       "limit": 10
   })
   ```

3. **Create Roadmap**
   ```python
   result = await mcp_client.call_tool("create_roadmap", {
       "project": {
           "title": "Project Name",
           "short_description": "Project Description",
           "visibility": "private"
       },
       "milestones": [
           {
               "milestone": {
                   "title": "Phase 1",
                   "description": "Initial phase",
                   "due_date": "2024-12-31"
               },
               "issues": [
                   {
                       "title": "Task 1",
                       "description": "Task description",
                       "priority": "high",
                       "type": "feature"
                   }
               ]
           }
       ]
   })
   ```

### Sprint Operations

1. **Plan Sprint**
   ```python
   result = await mcp_client.call_tool("plan_sprint", {
       "sprint": {
           "title": "Sprint 1",
           "start_date": "2024-01-01",
           "end_date": "2024-01-14",
           "goals": ["Complete initial setup", "Establish workflow"]
       },
       "issue_ids": ["issue-1", "issue-2"]
   })
   ```

2. **Get Sprint Metrics**
   ```python
   result = await mcp_client.call_tool("get_sprint_metrics", {
       "sprint_id": "sprint-id",
       "include_issues": True
   })
   ```

### Issue Operations

1. **Create Issue**
   ```python
   result = await mcp_client.call_tool("create_issue", {
       "title": "New Issue",
       "description": "Issue description",
       "labels": ["bug", "high-priority"],
       "assignees": ["username"],
       "priority": "high"
   })
   ```

2. **Update Issue**
   ```python
   result = await mcp_client.call_tool("update_issue", {
       "issue_id": "issue-id",
       "status": "closed",
       "description": "Updated description"
   })
   ```

## Error Handling

The server implements comprehensive error handling:

1. **API Errors**
   - Rate limiting with automatic retry
   - Authentication failures
   - Permission issues

2. **Resource Errors**
   - Not found errors
   - Validation errors
   - Resource conflicts

### Error Response Format

```python
{
    "status": "error",
    "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Project with ID 'xxx' not found"
    }
}
```

## Best Practices

1. **Resource Management**
   - Use meaningful titles and descriptions
   - Keep project structure consistent
   - Regularly update status and progress

2. **Performance**
   - Batch related operations when possible
   - Use pagination for large datasets
   - Handle rate limits appropriately (automatic retry is built-in)

3. **Error Handling**
   - Always check for errors in responses
   - Implement proper error handling in your client
   - Validate inputs before submission

4. **Caching**
   - The server uses in-memory caching for frequently accessed resources
   - Cache TTL is configurable (default: 1 hour)
   - Cache is automatically invalidated on updates

## Troubleshooting

Common issues and solutions:

1. **Authentication Errors**
   ```
   Error: Unauthorized: Bad credentials
   ```
   - Verify token permissions
   - Check token expiration
   - Ensure correct environment variables

2. **Rate Limiting**
   ```
   Error: Rate limited: API rate limit exceeded
   ```
   - The server automatically handles rate limits with retry
   - Implement request batching for large operations
   - Monitor rate limit headers in responses

3. **Resource Conflicts**
   ```
   Error: Resource not found: Issue with ID 123 not found
   ```
   - Verify that resource IDs are correct
   - Check that you have access to the resources
   - Ensure you're using the correct owner and repository

4. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'mcp'
   ```
   - Ensure virtual environment is activated
   - Install dependencies: `pip install -r requirements.txt`
   - Verify Python version: `python --version` (should be 3.8+)

5. **Configuration Errors**
   ```
   ValueError: GITHUB_TOKEN is required
   ```
   - Check `.env` file exists and contains required variables
   - Verify environment variables are set correctly
   - Use command line arguments as alternative: `--token`, `--owner`, `--repo`

## Configuration Options

### Environment Variables

```env
# Required
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_username_or_org
GITHUB_REPO=your_repository_name

# Optional
SYNC_ENABLED=true
SYNC_TIMEOUT_MS=5000
CACHE_DIRECTORY=.cache
WEBHOOK_SECRET=your_webhook_secret
WEBHOOK_PORT=3001
SSE_ENABLED=false
EVENT_RETENTION_DAYS=7
MAX_EVENTS_IN_MEMORY=1000
```

### Command Line Arguments

```bash
python -m src \
  --token=your_token \
  --owner=your_username \
  --repo=your_repo \
  --env-file=.env \
  --verbose
```

## Support

For issues and feature requests:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Follow the [contribution guidelines](../CONTRIBUTING.md)

## References

- [GitHub Projects API Documentation](https://docs.github.com/en/rest/projects)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- [MCP Specification](https://modelcontextprotocol.io)
- [Project Architecture](../ARCHITECTURE.md)
- [Getting Started Tutorial](tutorials/getting-started.md)
