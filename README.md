# MCP GitHub Project Manager

A comprehensive Model Context Protocol (MCP) server built in Python that provides advanced GitHub project management capabilities. Manage your GitHub Projects, issues, milestones, sprints, and more through the MCP interface.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](https://github.com/your-username/git_proj_manger_mcp)

## Overview

This server implements the [Model Context Protocol](https://modelcontextprotocol.io) to provide comprehensive GitHub project management through GitHub's GraphQL API. It offers 40+ tools for managing projects, issues, milestones, sprints, labels, and custom fields while maintaining state and handling errors according to MCP specifications.

The server is built with Python 3.8+ and follows Clean Architecture principles, providing a maintainable and extensible codebase for GitHub project management operations.

### 🚀 Key Features

- **40+ MCP Tools**: Complete CRUD operations for projects, issues, milestones, sprints, labels, and more
- **Roadmap Creation**: Create project roadmaps with milestones and issues
- **Sprint Planning**: Plan and manage development sprints with metrics tracking
- **Project Management**: Full support for GitHub Projects v2 with custom fields and views
- **Clean Architecture**: Well-structured codebase following Clean Architecture principles
- **Type Safety**: Full type hints and Pydantic validation for all tools
- **Error Handling**: Comprehensive error handling with retry mechanisms

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Key Features](#key-features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

### Prerequisites

- Python 3.8 or higher
- GitHub Personal Access Token with appropriate permissions

### Installation

#### Option 1: Install from Source

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

#### Option 2: Install as Package (Coming Soon)

```bash
pip install mcp-github-project-manager
```

**Note**: Package publication is planned for future releases.

### Configuration

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username_or_organization
GITHUB_REPO=your_repository_name
```

**Required GitHub Token Permissions:**
- `repo` (Full repository access)
- `project` (Project access)
- `write:org` (Organization access, if applicable)

### Running the Server

```bash
# Run from source
python -m src

# Or with command line arguments
python -m src --token=your_token --owner=your_username --repo=your_repo

# With verbose logging
python -m src --verbose
```

## Key Features

### 📊 Project Management

- **Create Projects**: Create new GitHub Projects (v2) with custom visibility
- **List Projects**: List all projects for a repository
- **Update Projects**: Update project details, description, and visibility
- **Delete Projects**: Remove projects when no longer needed

### 🎯 Milestone Management

- **Create Milestones**: Create project milestones with due dates
- **List Milestones**: List all milestones with filtering options
- **Update Milestones**: Update milestone details and status
- **Delete Milestones**: Remove milestones
- **Metrics**: Get milestone progress metrics and track overdue/upcoming milestones

### 📋 Issue Management

- **Create Issues**: Create GitHub issues with labels, assignees, and priority
- **List Issues**: List issues with filtering by status, assignee, labels, and milestone
- **Get Issue Details**: Retrieve detailed information about specific issues
- **Update Issues**: Update issue status, description, and metadata

### 🏃 Sprint Planning

- **Create Sprints**: Create development sprints with start/end dates and goals
- **Plan Sprints**: Plan sprints with selected issues
- **List Sprints**: List all sprints with status filtering
- **Get Current Sprint**: Retrieve the currently active sprint
- **Update Sprints**: Update sprint details and status
- **Manage Sprint Issues**: Add or remove issues from sprints
- **Sprint Metrics**: Track sprint progress and completion metrics

### 🗺️ Roadmap Creation

- **Create Roadmaps**: Create comprehensive project roadmaps with milestones and issues
- **Milestone Metrics**: Track milestone progress and completion
- **Overdue Milestones**: Identify and track overdue milestones
- **Upcoming Milestones**: Get upcoming milestones within a time frame

### 🏷️ Labels and Organization

- **Create Labels**: Create repository labels with colors and descriptions
- **List Labels**: List all labels in the repository

### 📐 Custom Fields and Views

- **Project Fields**: Create, list, and update custom project fields
- **Project Views**: Create different views (board, table, timeline, roadmap)
- **Field Values**: Set, get, and clear custom field values for project items

### 🔗 Project Items

- **Add Items**: Add issues or PRs to projects
- **Remove Items**: Remove items from projects
- **List Items**: List all items in a project

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/your-username/git_proj_manger_mcp.git
cd git_proj_manger_mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

The project requires the following core dependencies:

- `mcp>=1.0.0` - Model Context Protocol SDK
- `pydantic>=2.0.0` - Data validation
- `pygithub>=2.0.0` - GitHub API integration
- `click>=8.0.0` - CLI interface
- `httpx>=0.27.0` - HTTP client
- `python-dotenv>=1.0.0` - Environment variable management

See `requirements.txt` for the complete list.

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required GitHub Configuration
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username_or_organization
GITHUB_REPO=your_repository_name

# Optional Configuration
SYNC_ENABLED=true
SYNC_TIMEOUT_MS=5000
CACHE_DIRECTORY=.cache
WEBHOOK_SECRET=your_webhook_secret
WEBHOOK_PORT=3000
SSE_ENABLED=false
```

### Command Line Arguments

You can also provide configuration via command line arguments:

```bash
python -m src --token=your_token --owner=your_username --repo=your_repo --verbose
```

**Available CLI Options:**
- `-t, --token`: GitHub personal access token
- `-o, --owner`: GitHub repository owner
- `-r, --repo`: GitHub repository name
- `-e, --env-file`: Path to .env file (default: .env)
- `-v, --verbose`: Enable verbose logging
- `--version`: Display version information

Command line arguments take precedence over environment variables.

## Usage

### As a Command-Line Tool

```bash
# Basic usage
python -m src

# With environment variables
GITHUB_TOKEN=your_token python -m src

# With command line arguments
python -m src --token=your_token --owner=your_username --repo=your_repo

# Verbose mode
python -m src --verbose
```

### Integration with MCP Clients

The server communicates via stdio transport following the MCP specification. Configure your MCP client to run:

```bash
python -m src
```

### Installing in AI Assistants

#### Install in Cursor

Add this to your Cursor MCP config file (`cursor-mcp-config.json`):

```json
{
  "mcpServers": {
    "github-project-manager": {
      "command": "python",
      "args": ["-m", "src"],
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "GITHUB_OWNER": "your_username",
        "GITHUB_REPO": "your_repo"
      }
    }
  }
}
```

#### Install in Claude Desktop

Add this to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "github-project-manager": {
      "command": "python",
      "args": ["-m", "src"],
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "GITHUB_OWNER": "your_username",
        "GITHUB_REPO": "your_repo"
      }
    }
  }
}
```

#### Install in VS Code

Add this to your VS Code MCP config:

```json
{
  "servers": {
    "github-project-manager": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "src"],
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "GITHUB_OWNER": "your_username",
        "GITHUB_REPO": "your_repo"
      }
    }
  }
}
```

## Available Tools

The server provides 40+ MCP tools organized into the following categories:

### Project Tools
- `create_project` - Create a new GitHub project
- `list_projects` - List all projects
- `get_project` - Get project details
- `update_project` - Update project information
- `delete_project` - Delete a project

### Milestone Tools
- `create_milestone` - Create a new milestone
- `list_milestones` - List all milestones
- `update_milestone` - Update milestone details
- `delete_milestone` - Delete a milestone
- `get_milestone_metrics` - Get milestone progress metrics
- `get_overdue_milestones` - Get overdue milestones
- `get_upcoming_milestones` - Get upcoming milestones

### Issue Tools
- `create_issue` - Create a new issue
- `list_issues` - List issues with filtering
- `get_issue` - Get issue details
- `update_issue` - Update issue information

### Sprint Tools
- `create_sprint` - Create a new sprint
- `list_sprints` - List all sprints
- `get_current_sprint` - Get the active sprint
- `update_sprint` - Update sprint details
- `plan_sprint` - Plan a sprint with issues
- `add_issues_to_sprint` - Add issues to a sprint
- `remove_issues_from_sprint` - Remove issues from a sprint
- `get_sprint_metrics` - Get sprint progress metrics

### Roadmap Tools
- `create_roadmap` - Create a project roadmap with milestones and issues

### Label Tools
- `create_label` - Create a repository label
- `list_labels` - List all labels

### Project Field Tools
- `create_project_field` - Create a custom project field
- `list_project_fields` - List all project fields
- `update_project_field` - Update a project field

### Project View Tools
- `create_project_view` - Create a project view
- `list_project_views` - List all project views
- `update_project_view` - Update a project view
- `delete_project_view` - Delete a project view

### Project Item Tools
- `add_project_item` - Add an item to a project
- `remove_project_item` - Remove an item from a project
- `list_project_items` - List all items in a project

### Field Value Tools
- `set_field_value` - Set a field value for a project item
- `get_field_value` - Get a field value for a project item
- `clear_field_value` - Clear a field value for a project item

## Architecture

The project follows Clean Architecture principles with clear separation of concerns:

- **Domain Layer** (`src/domain/`): Core business entities, types, and interfaces
- **Infrastructure Layer** (`src/infrastructure/`): GitHub API integration, repositories, and MCP implementation
- **Service Layer** (`src/services/`): Business logic and coordination
- **Tools Layer** (`src/infrastructure/tools/`): MCP tool definitions, handlers, and validation

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-username/git_proj_manger_mcp.git
cd git_proj_manger_mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies including dev dependencies
pip install -r requirements.txt
```

### Code Quality

```bash
# Format code with black
black src/

# Lint code with ruff
ruff check src/

# Type check with mypy
mypy src/
```

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html
```

## Troubleshooting

### Common Issues

1. **Module Not Found Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify your virtual environment is activated

2. **GitHub Token Issues**
   - Verify your token has the required permissions (`repo`, `project`, `write:org`)
   - Check that the token is set correctly in your `.env` file or environment variables

3. **Import Errors**
   - Make sure you're running from the project root directory
   - Verify Python version is 3.8 or higher: `python --version`

4. **Connection Issues**
   - Check your internet connection
   - Verify GitHub API is accessible
   - Check for rate limiting issues

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- [Model Context Protocol](https://modelcontextprotocol.io)
- [GitHub Projects API](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)

## Acknowledgments

This project was inspired by and uses [mcp-github-project-manager](https://github.com/kunwarVivek/mcp-github-project-manager) by [@kunwarVivek](https://github.com/kunwarVivek) as a reference. The original TypeScript/Node.js implementation provided valuable insights into MCP server architecture, GitHub Projects API integration, and tool design patterns.

### Changes in This Project

This Python implementation adapts the concepts and architecture from the original project with the following key changes:

- **Language Migration**: Reimplemented from TypeScript/Node.js to Python 3.8+
- **Type Validation**: Replaced Zod schemas with Pydantic models for Python-native validation
- **Async Patterns**: Implemented Python async/await patterns throughout
- **MCP SDK**: Integrated with Python MCP SDK instead of TypeScript SDK
- **Architecture**: Maintained Clean Architecture principles adapted for Python
- **Dependencies**: Uses Python ecosystem (pygithub, httpx, aiohttp) instead of Node.js packages
- **Tool System**: Reimplemented 40+ MCP tools using Python patterns
- **Error Handling**: Python-specific error handling with domain error types
- **Caching**: In-memory caching implementation using Python dataclasses
- **Documentation**: Updated all documentation for Python developers

We extend our gratitude to the original project maintainers and contributors for their excellent work and for making their codebase available as open source.

## Current Status

### ✅ Implemented Features

- **40+ MCP Tools**: All core project management tools are fully implemented
- **Project Management**: Complete CRUD operations for GitHub Projects v2
- **Issue Management**: Full issue lifecycle management
- **Milestone Management**: Create, update, delete, and track milestones
- **Sprint Planning**: Sprint creation, planning, and metrics tracking
- **Roadmap Creation**: Automated roadmap generation with milestones and issues
- **Custom Fields & Views**: Support for custom project fields and views
- **Error Handling**: Comprehensive error handling with retry mechanisms
- **Caching**: In-memory resource caching with TTL support
- **Event System**: Event store for tracking resource changes

### 🔄 Future Enhancements

- AI-powered task generation and analysis (infrastructure ready)
- Webhook integration for real-time updates
- Persistent caching (Redis/database-backed)
- Advanced metrics and reporting
- Multi-repository support

## Documentation

- [Architecture](ARCHITECTURE.md) - System architecture and design
- [User Guide](docs/user-guide.md) - Detailed usage instructions
- [Tutorials](docs/tutorials/getting-started.md) - Step-by-step guides
- [GitHub Projects Integration](docs/mcp/github-projects-integration.md) - Integration details

## Utilities

### Cleanup Script

A utility script is provided for bulk operations:

```bash
# Delete all projects and close all issues
python delete_all_projects_and_issues.py
```

**Note**: The script requires confirmation before performing destructive operations. GitHub does not allow deleting issues, only closing them.
