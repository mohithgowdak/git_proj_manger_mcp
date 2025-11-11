# Getting Started with GitHub Project Manager MCP

This tutorial will guide you through the process of setting up and using the GitHub Project Manager MCP Server for basic project management tasks.

## Prerequisites

Before you begin, make sure you have:

- Python 3.8 or higher installed
- A GitHub account with appropriate permissions
- A GitHub Personal Access Token with required scopes:
  - `repo` (Full repository access)
  - `project` (Project access)
  - `write:org` (Organization access)

## Step 1: Installation and Setup

First, let's install and configure the server:

```bash
# Clone the repository
git clone https://github.com/your-username/git_proj_manger_mcp.git
cd git_proj_manger_mcp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Now, create a `.env` file with your GitHub credentials:

```env
GITHUB_TOKEN=your_personal_access_token
GITHUB_OWNER=your_github_username_or_org
GITHUB_REPO=your_repository_name
```

## Step 2: Start the Server

Start the MCP server:

```bash
# Start the server
python -m src

# Or with verbose logging
python -m src --verbose
```

You should see output indicating that the server is running:

```
GitHub Project Manager MCP server running on stdio
```

## Step 3: Create Your First Project

Let's create a simple project with one milestone. Create a file named `create_project.py`:

```python
#!/usr/bin/env python3
"""Example script to create a project with milestones and issues."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.env import GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO
from src.services.project_management_service import ProjectManagementService
from src.domain.types import CreateProject, CreateMilestone, CreateIssue
from datetime import datetime, timedelta


async def create_project():
    """Create a project with milestones and issues."""
    # Initialize the service with your GitHub credentials
    service = ProjectManagementService(GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN)

    try:
        # Create a project
        project_data = CreateProject(
            title="My First Project",
            owner=GITHUB_OWNER,
            short_description="A test project created with the MCP API",
            visibility="private"
        )
        
        project = await service.create_project(project_data)
        print(f'✅ Project created successfully!')
        print(f'   Project ID: {project.id}')
        print(f'   Project Title: {project.title}')
        
        # Create a milestone
        milestone_data = CreateMilestone(
            title="Phase 1",
            description="Initial phase of the project",
            due_date=(datetime.now() + timedelta(days=14)).isoformat()
        )
        
        milestone = await service.create_milestone(milestone_data)
        print(f'✅ Milestone created successfully!')
        print(f'   Milestone ID: {milestone.id}')
        print(f'   Milestone Title: {milestone.title}')
        
        # Create an issue
        issue_data = CreateIssue(
            title="Setup project repository",
            description="Create and configure the initial project repository",
            priority="high",
            issue_type="feature"
        )
        
        issue = await service.create_issue(issue_data)
        print(f'✅ Issue created successfully!')
        print(f'   Issue ID: {issue.id}')
        print(f'   Issue #: {issue.number}')
        print(f'   Issue Title: {issue.title}')
        
        return {
            "project": project,
            "milestone": milestone,
            "issue": issue
        }
        
    except Exception as e:
        print(f'❌ Error creating project: {e}')
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(create_project())
```

Run the script:

```bash
python create_project.py
```

You should see output confirming that your project, milestone, and issue were created successfully.

## Step 4: Plan a Sprint

Now, let's plan a sprint with our issues. Create a file named `plan_sprint.py`:

```python
#!/usr/bin/env python3
"""Example script to plan a sprint with issues."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.env import GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO
from src.services.project_management_service import ProjectManagementService
from src.domain.types import CreateSprint


async def plan_sprint():
    """Plan a sprint with issues."""
    service = ProjectManagementService(GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN)

    try:
        # Get the issue ID from the previous step
        # For this example, we'll assume it's "1", but you should replace this with your actual issue ID
        issue_id = "1"

        # Plan a sprint with the issue
        sprint_data = CreateSprint(
            title="Sprint 1",
            description="First sprint for the project",
            start_date=datetime.now().isoformat(),
            end_date=(datetime.now() + timedelta(days=7)).isoformat(),
            issues=[issue_id],
            goals=[
                "Complete initial project setup",
                "Establish development workflow"
            ]
        )
        
        sprint = await service.create_sprint(sprint_data)
        
        print('✅ Sprint planned successfully!')
        print(f'   Sprint ID: {sprint.id}')
        print(f'   Sprint Title: {sprint.title}')
        print(f'   Sprint Start: {sprint.start_date}')
        print(f'   Sprint End: {sprint.end_date}')
        print(f'   Issues: {sprint.issues}')
        
        return sprint
        
    except Exception as e:
        print(f'❌ Error planning sprint: {e}')
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(plan_sprint())
```

Run the script:

```bash
python plan_sprint.py
```

## Step 5: Track Progress

Finally, let's check the progress of our sprint. Create a file named `track_progress.py`:

```python
#!/usr/bin/env python3
"""Example script to track sprint progress."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.env import GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO
from src.services.project_management_service import ProjectManagementService


async def track_progress():
    """Track sprint progress."""
    service = ProjectManagementService(GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN)

    try:
        # Get the sprint ID from the previous step
        # For this example, we'll assume it's "sprint-1", but you should replace this with your actual sprint ID
        sprint_id = "sprint-1"

        # Get sprint metrics
        metrics = await service.get_sprint_metrics(sprint_id, include_issues=True)

        print('📊 Sprint Metrics:')
        print(f'   Title: {metrics["sprint"]["title"]}')
        print(f'   Status: {metrics["sprint"]["status"]}')
        print(f'   Progress: {metrics["completion_percentage"]}%')
        print(f'   Open Issues: {metrics["open_issues"]}')
        print(f'   Closed Issues: {metrics["closed_issues"]}')
        print(f'   Total Issues: {metrics["total_issues"]}')
        
        # Display issues if available
        if metrics.get("issues") and len(metrics["issues"]) > 0:
            print('\n📋 Issues:')
            for issue in metrics["issues"]:
                status = issue.get("status", "unknown")
                title = issue.get("title", "Untitled")
                print(f'   - {title} ({status})')
        
        return metrics
        
    except Exception as e:
        print(f'❌ Error tracking progress: {e}')
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(track_progress())
```

Run the script:

```bash
python track_progress.py
```

## Step 6: Using MCP Tools Directly

You can also use the MCP tools directly through an MCP client. Here's an example using the MCP Python SDK:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_mcp_tools():
    """Use MCP tools directly."""
    # Configure server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src"],
        env={
            "GITHUB_TOKEN": "your_token",
            "GITHUB_OWNER": "your_username",
            "GITHUB_REPO": "your_repo"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Create a project
            result = await session.call_tool(
                "create_project",
                {
                    "title": "MCP Project",
                    "owner": "your_username",
                    "visibility": "private"
                }
            )
            
            print(f"Project created: {result.content}")

if __name__ == "__main__":
    asyncio.run(use_mcp_tools())
```

## Step 7: Explore the API

Now that you've completed the basic workflow, explore the full API capabilities:

1. Check out the [User Guide](../user-guide.md) for all available tools
2. Try creating more complex projects with multiple milestones
3. Experiment with different issue types and priorities
4. Track progress across multiple sprints
5. Use custom fields and views

## Troubleshooting

If you encounter any issues:

### Authentication Errors

```
Error: Unauthorized: Bad credentials
```

- Verify that your GitHub token is correct and has not expired
- Check that your token has the required scopes
- Ensure the token is correctly set in your `.env` file

### Rate Limiting

```
Error: Rate limited: API rate limit exceeded
```

- The server automatically handles rate limits with retry
- Implement request batching for large operations
- Monitor rate limit headers in responses

### Resource Not Found

```
Error: Resource not found: Issue with ID 123 not found
```

- Verify that the resource IDs you're using are correct
- Check that you have access to the resources
- Ensure you're using the correct owner and repository

### Import Errors

```
ModuleNotFoundError: No module named 'mcp'
```

- Ensure your virtual environment is activated
- Install dependencies: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.8+)

## Next Steps

Congratulations! You've completed the getting started tutorial. Here are some next steps:

1. Explore the [User Guide](../user-guide.md) to learn about all available tools
2. Check out the [Architecture Documentation](../../ARCHITECTURE.md) to understand the system design
3. Read the [GitHub Projects Integration Guide](../mcp/github-projects-integration.md) for advanced usage
4. Contribute to the project by following the [Contributing Guide](../../CONTRIBUTING.md)
