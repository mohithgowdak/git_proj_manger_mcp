"""GitHub sprint repository."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from github import Github
from github.Repository import Repository
from ..github_config import GitHubConfig
from .base_repository import BaseGitHubRepository
from ....domain.types import Sprint, CreateSprint, SprintId, IssueId, ProjectId
from ....domain.resource_types import ResourceStatus


class GitHubSprintRepository(BaseGitHubRepository):
    """GitHub sprint repository."""
    
    async def _get_or_create_iteration_field(self, project_id: ProjectId) -> str:
        """Get or create an iteration field for the project."""
        # First, try to find existing iteration field
        query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              fields(first: 50) {
                nodes {
                  ... on ProjectV2IterationField {
                    id
                    name
                  }
                  ... on ProjectV2Field {
                    id
                    name
                    dataType
                  }
                }
              }
            }
          }
        }
        """
        
        response = await self.graphql(query, {"projectId": project_id})
        node = response.get("node", {})
        fields = node.get("fields", {}).get("nodes", [])
        
        # Find iteration field - check both iteration fields and regular fields with ITERATION dataType
        for field in fields:
            field_id = field.get("id")
            if not field_id:
                continue
            
            # Check if it's an iteration field by dataType
            if field.get("dataType") == "ITERATION":
                return field_id
            
            # Check by name (common names for iteration fields)
            field_name = field.get("name", "").lower()
            if field_name in ["iteration", "sprint", "iterations", "sprints"]:
                # Double-check it's actually an iteration field by querying it
                try:
                    check_query = """
                    query($fieldId: ID!) {
                      node(id: $fieldId) {
                        ... on ProjectV2IterationField {
                          id
                        }
                      }
                    }
                    """
                    check_response = await self.graphql(check_query, {"fieldId": field_id})
                    if check_response.get("node", {}).get("id"):
                        return field_id
                except:
                    continue
        
        # If no iteration field exists, try to create one
        # Note: Some projects may have iteration fields that aren't returned in the query
        # or iteration fields might need special permissions
        try:
            from ..util.graphql_helpers import map_to_graphql_field_type
            create_field_mutation = """
            mutation($input: CreateProjectV2FieldInput!) {
              createProjectV2Field(input: $input) {
                projectV2Field {
                  ... on ProjectV2IterationField {
                    id
                    name
                  }
                }
              }
            }
            """
            
            input_data = {
                "projectId": project_id,
                "name": "Sprint",
                "dataType": "ITERATION"
            }
            
            create_response = await self.graphql(create_field_mutation, {
                "input": input_data
            })
            
            field = create_response.get("createProjectV2Field", {}).get("projectV2Field", {})
            field_id = field.get("id")
            if field_id:
                return field_id
        except Exception as e:
            # If creation fails, try to find any iteration field (might be a system field)
            if hasattr(self._logger, 'warn'):
                self._logger.warn(f"Failed to create iteration field: {str(e)}")
            else:
                print(f"Warning: Failed to create iteration field: {str(e)}", file=__import__('sys').stderr)
        
        # If creation failed, provide helpful error message
        raise ValueError(
            "No iteration field found and unable to create one.\n\n"
            "Iteration fields in GitHub Projects v2 may need to be enabled manually:\n"
            "1. Go to your project: https://github.com/mohithgowdak/projects/0\n"
            "2. Click on the project settings (gear icon)\n"
            "3. Go to 'Fields' section\n"
            "4. Click 'New field' → Select 'Iteration'\n"
            "5. Name it 'Sprint' or 'Iteration'\n"
            "6. Save the field\n\n"
            "Alternatively, ensure your GitHub token has 'project' scope with write permissions."
        )
    
    async def create(self, data: CreateSprint, project_id: Optional[ProjectId] = None) -> Sprint:
        """Create a sprint (iteration)."""
        # Get project ID - use provided one or get from config
        if not project_id:
            project_id = self._config.project_id
        
        if not project_id:
            # Try to get the first active project
            from .github_project_repository import GitHubProjectRepository
            project_repo = GitHubProjectRepository(self.github, self.repo, self._config)
            projects = await project_repo.find_all()
            if projects:
                project_id = projects[0].id
            else:
                raise ValueError("No project ID provided and no projects found")
        
        # Get or create iteration field
        iteration_field_id = await self._get_or_create_iteration_field(project_id)
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(data.start_date.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data.end_date.replace('Z', '+00:00'))
        except ValueError:
            # Try other date formats
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']:
                try:
                    start_date = datetime.strptime(data.start_date[:10], fmt)
                    end_date = datetime.strptime(data.end_date[:10], fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Invalid date format: {data.start_date} or {data.end_date}")
        
        # First, get existing iterations to preserve them
        get_iterations_query = """
        query($fieldId: ID!) {
          node(id: $fieldId) {
            ... on ProjectV2IterationField {
              id
              name
              configuration {
                ... on ProjectV2IterationFieldConfiguration {
                  iterations {
                    id
                    title
                    startDate
                    duration
                  }
                }
              }
            }
          }
        }
        """
        
        existing_response = await self.graphql(get_iterations_query, {"fieldId": iteration_field_id})
        existing_field = existing_response.get("node", {})
        existing_config_raw = existing_field.get("configuration")
        
        # Handle case where configuration might be None or a different structure
        if existing_config_raw is None:
            existing_config = {}
        elif isinstance(existing_config_raw, dict):
            existing_config = existing_config_raw
        else:
            existing_config = {}
        
        existing_iterations = existing_config.get("iterations") or []
        
        # Calculate duration in days for the new iteration
        iteration_duration = (end_date - start_date).days + 1
        
        # Format existing iterations (DO NOT include IDs - GitHub API doesn't allow them in updates)
        formatted_existing = []
        for iter in existing_iterations:
            if not isinstance(iter, dict):
                continue
            # GitHub API doesn't accept 'id' field when updating iterations
            # We only need title, startDate, and duration - ensure no None values
            iter_title = iter.get("title", "")
            iter_start_date = iter.get("startDate", "")
            iter_duration = iter.get("duration", 7)
            
            # Skip if critical fields are missing
            if not iter_title or not iter_start_date or not iter_duration:
                continue
                
            formatted_iter = {
                "title": str(iter_title),
                "startDate": str(iter_start_date),
                "duration": int(iter_duration)
            }
            formatted_existing.append(formatted_iter)
        
        # Prepare new iteration (no ID for new iterations)
        new_iteration = {
            "title": str(data.title),
            "startDate": str(start_date.strftime("%Y-%m-%d")),
            "duration": int(iteration_duration)
        }
        
        # Validate new iteration
        if not new_iteration["title"] or not new_iteration["startDate"] or new_iteration["duration"] <= 0:
            raise ValueError(f"Invalid iteration data: {new_iteration}")
        
        # Combine existing iterations with new one
        # Make sure we're appending the new iteration, not replacing
        all_iterations = formatted_existing + [new_iteration]
        
        # Debug: Log what we're sending
        import sys
        print(f"Total iterations to send: {len(all_iterations)}", file=sys.stderr)
        print(f"Existing: {len(formatted_existing)}, New: 1", file=sys.stderr)
        
        # Validate all iterations
        for idx, iter in enumerate(all_iterations):
            if not iter.get("title") or not iter.get("startDate") or iter.get("duration", 0) <= 0:
                raise ValueError(f"Invalid iteration at index {idx}: {iter}")
        
        # Update iteration field with all iterations
        update_iteration_mutation = """
        mutation($input: UpdateProjectV2FieldInput!) {
          updateProjectV2Field(input: $input) {
            projectV2Field {
              ... on ProjectV2IterationField {
                id
                name
                configuration {
                  ... on ProjectV2IterationFieldConfiguration {
                    iterations {
                      id
                      title
                      startDate
                      duration
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        # Calculate configuration-level startDate and duration
        # Use the earliest start date from all iterations
        all_start_dates = [iter.get("startDate", "") for iter in all_iterations if iter.get("startDate")]
        if all_start_dates:
            config_start_date = min(all_start_dates)
        else:
            config_start_date = start_date.strftime("%Y-%m-%d")
        
        # Use a default duration (typically the most common sprint duration)
        # GitHub requires this to be a positive integer
        config_duration = 14  # Default to 2 weeks
        
        # Ensure we have valid non-null values
        if not config_start_date or config_start_date == "None":
            config_start_date = start_date.strftime("%Y-%m-%d")
        if not config_duration or config_duration <= 0:
            config_duration = 14
        
        # Build iteration configuration with required fields
        # GitHub API requires startDate and duration at configuration level (non-null)
        iteration_config_dict = {
            "startDate": str(config_start_date),
            "duration": int(config_duration),
            "iterations": all_iterations
        }
        
        input_data = {
            "fieldId": iteration_field_id,
            "iterationConfiguration": iteration_config_dict
        }
        
        # Debug: Print what we're sending (for troubleshooting)
        import json
        try:
            input_json_str = json.dumps(input_data, indent=2, default=str)
            # Check for null values
            if "null" in input_json_str.lower():
                raise ValueError(f"Found null in serialized input: {input_json_str}")
        except Exception as json_err:
            raise ValueError(f"JSON serialization error: {json_err}, input_data: {input_data}")
        
        response = await self.graphql(update_iteration_mutation, {"input": input_data})
        
        field_data = response.get("updateProjectV2Field", {}).get("projectV2Field", {})
        config = field_data.get("configuration", {})
        iterations = config.get("iterations", [])
        
        if not iterations:
            raise ValueError("Failed to create iteration")
        
        iteration = iterations[-1]  # Get the newly created iteration
        
        # Assign issues to the iteration if provided
        if data.issues:
            await self._assign_issues_to_iteration(project_id, iteration_field_id, iteration["id"], data.issues)
        
        # Convert to Sprint domain object
        return self._convert_to_sprint(iteration, data)
    
    async def _assign_issues_to_iteration(
        self, 
        project_id: ProjectId, 
        iteration_field_id: str, 
        iteration_id: str, 
        issue_ids: List[IssueId]
    ) -> None:
        """Assign issues to an iteration."""
        from .github_issue_repository import GitHubIssueRepository
        from .github_project_repository import GitHubProjectRepository
        
        issue_repo = GitHubIssueRepository(self.github, self.repo, self._config)
        project_repo = GitHubProjectRepository(self.github, self.repo, self._config)
        
        # Get project items for issues
        for issue_id in issue_ids:
            try:
                issue = await issue_repo.find_by_id(issue_id)
                if not issue:
                    continue
                
                # Get the project item ID for this issue
                # First, we need to add the issue to the project if not already added
                # Then get the item ID and update its iteration field
                
                # We need the issue node ID, not just the number
                # Get issue node ID first
                issue_node_query = """
                query($owner: String!, $repo: String!, $number: Int!) {
                  repository(owner: $owner, name: $repo) {
                    issue(number: $number) {
                      id
                    }
                  }
                }
                """
                
                issue_node_response = await self.graphql(issue_node_query, {
                    "owner": self._config.owner,
                    "repo": self._config.repo,
                    "number": int(issue_id)
                })
                
                issue_node_id = issue_node_response.get("repository", {}).get("issue", {}).get("id")
                if not issue_node_id:
                    raise Exception(f"Issue {issue_id} not found in repository")
                
                # Add issue to project if not already added
                add_item_mutation = """
                mutation($projectId: ID!, $contentId: ID!) {
                  addProjectV2ItemById(input: {
                    projectId: $projectId
                    contentId: $contentId
                  }) {
                    item {
                      id
                    }
                  }
                }
                """
                
                project_item_id = None
                try:
                    add_response = await self.graphql(add_item_mutation, {
                        "projectId": project_id,
                        "contentId": issue_node_id
                    })
                    # If successfully added, get the item ID from response
                    if add_response.get("addProjectV2ItemById", {}).get("item", {}).get("id"):
                        project_item_id = add_response["addProjectV2ItemById"]["item"]["id"]
                    # Wait a moment for GitHub to process
                    import asyncio
                    await asyncio.sleep(0.5)
                except Exception as add_err:
                    # Item might already be in project, that's okay - we'll query for it
                    if hasattr(self._logger, 'debug'):
                        self._logger.debug(f"Issue {issue_id} might already be in project: {str(add_err)}")
                
                # If we don't have the item ID yet, query for it
                if not project_item_id:
                    all_items_query = """
                    query($projectId: ID!) {
                      node(id: $projectId) {
                        ... on ProjectV2 {
                          items(first: 100) {
                            nodes {
                              id
                              content {
                                ... on Issue {
                                  id
                                  number
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    """
                    all_items_response = await self.graphql(all_items_query, {"projectId": project_id})
                    all_items = all_items_response.get("node", {}).get("items", {}).get("nodes", [])
                    for item in all_items:
                        content = item.get("content", {})
                        if content.get("id") == issue_node_id:
                            project_item_id = item.get("id")
                            break
                
                if project_item_id:
                    # Update the iteration field for this project item
                    update_field_mutation = """
                    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $iterationId: String!) {
                      updateProjectV2ItemFieldValue(input: {
                        projectId: $projectId
                        itemId: $itemId
                        fieldId: $fieldId
                        value: {
                          iterationId: $iterationId
                        }
                      }) {
                        projectV2Item {
                          id
                        }
                      }
                    }
                    """
                    
                    response = await self.graphql(update_field_mutation, {
                        "projectId": project_id,
                        "itemId": project_item_id,
                        "fieldId": iteration_field_id,
                        "iterationId": iteration_id
                    })
                    
                    # Check for errors in response
                    if response.get("errors"):
                        error_msg = str(response.get("errors"))
                        raise Exception(f"GraphQL errors: {error_msg}")
                    
                    # Verify the update was successful
                    updated_item = response.get("updateProjectV2ItemFieldValue", {}).get("projectV2Item")
                    if not updated_item:
                        raise Exception(f"Failed to update field - no item returned in response: {response}")
                    
                else:
                    raise Exception(f"Project item ID not found for issue {issue_id}")
            except Exception as e:
                # Re-raise the exception so it can be caught by the caller
                error_msg = f"Failed to assign issue {issue_id} to iteration {iteration_id}: {str(e)}"
                if hasattr(self._logger, 'error'):
                    self._logger.error(error_msg)
                else:
                    print(f"Error: {error_msg}", file=__import__('sys').stderr)
                raise Exception(error_msg)
    
    def _convert_to_sprint(self, iteration_data: Dict[str, Any], create_data: CreateSprint) -> Sprint:
        """Convert GitHub iteration data to domain Sprint."""
        from ....domain.types import Sprint as DomainSprint
        
        iteration_id = iteration_data.get("id", "")
        title = iteration_data.get("title", create_data.title)
        start_date = iteration_data.get("startDate", create_data.start_date)
        duration = iteration_data.get("duration", 7)
        
        # Calculate end date from start date and duration
        try:
            from datetime import timedelta
            start = datetime.fromisoformat(start_date)
            end = start + timedelta(days=duration - 1)
            end_date = end.strftime("%Y-%m-%d")
        except:
            end_date = create_data.end_date
        
        return DomainSprint(
            id=iteration_id,
            title=title,
            description=create_data.description,
            start_date=start_date,
            end_date=end_date,
            status=create_data.status or ResourceStatus.ACTIVE,
            issues=create_data.issues or [],
            created_at="",
            updated_at=""
        )
    
    async def update(self, id: SprintId, data: dict) -> Sprint:
        """Update a sprint."""
        # TODO: Implement sprint update
        raise NotImplementedError("Sprint update via GraphQL not yet implemented")
    
    async def delete(self, id: SprintId) -> None:
        """Delete a sprint."""
        # TODO: Implement sprint deletion
        raise NotImplementedError("Sprint deletion via GraphQL not yet implemented")
    
    async def find_by_id(self, id: SprintId) -> Optional[Sprint]:
        """Find sprint by ID."""
        # Get all sprints and find the one with matching ID
        all_sprints = await self.find_all()
        for sprint in all_sprints:
            if sprint.id == id:
                return sprint
        return None
    
    async def find_all(self, options: Optional[dict] = None) -> List[Sprint]:
        """Find all sprints."""
        # Get project ID
        project_id = self._config.project_id
        if not project_id:
            from .github_project_repository import GitHubProjectRepository
            project_repo = GitHubProjectRepository(self.github, self.repo, self._config)
            projects = await project_repo.find_all()
            if projects:
                project_id = projects[0].id
            else:
                raise ValueError("No project ID found")
        
        # Get iteration field ID
        iteration_field_id = await self._get_or_create_iteration_field(project_id)
        
        # Query all iterations
        get_iterations_query = """
        query($fieldId: ID!) {
          node(id: $fieldId) {
            ... on ProjectV2IterationField {
              id
              name
              configuration {
                ... on ProjectV2IterationFieldConfiguration {
                  iterations {
                    id
                    title
                    startDate
                    duration
                  }
                }
              }
            }
          }
        }
        """
        
        response = await self.graphql(get_iterations_query, {"fieldId": iteration_field_id})
        node = response.get("node", {})
        config = node.get("configuration", {})
        iterations = config.get("iterations", [])
        
        # Convert iterations to Sprint objects
        sprints = []
        for iter_data in iterations:
            if not isinstance(iter_data, dict):
                continue
            
            iteration_id = iter_data.get("id", "")
            title = iter_data.get("title", "")
            start_date = iter_data.get("startDate", "")
            duration = iter_data.get("duration", 7)
            
            if not iteration_id or not title:
                continue
            
            # Calculate end date
            try:
                from datetime import timedelta
                start = datetime.fromisoformat(start_date)
                end = start + timedelta(days=duration - 1)
                end_date = end.strftime("%Y-%m-%d")
            except:
                end_date = ""
            
            from ....domain.types import Sprint as DomainSprint
            sprint = DomainSprint(
                id=iteration_id,
                title=title,
                description="",
                start_date=start_date,
                end_date=end_date,
                status=ResourceStatus.ACTIVE,
                issues=[],
                created_at="",
                updated_at=""
            )
            sprints.append(sprint)
        
        return sprints
    
    async def find_current(self) -> Optional[Sprint]:
        """Find current sprint."""
        # TODO: Implement find current
        raise NotImplementedError("Sprint find current via GraphQL not yet implemented")
    
    async def add_issue(self, sprint_id: SprintId, issue_id: IssueId) -> Sprint:
        """Add issue to sprint."""
        # Get project ID
        project_id = self._config.project_id
        if not project_id:
            from .github_project_repository import GitHubProjectRepository
            project_repo = GitHubProjectRepository(self.github, self.repo, self._config)
            projects = await project_repo.find_all()
            if projects:
                project_id = projects[0].id
            else:
                raise ValueError("No project ID found")
        
        # Get iteration field ID
        iteration_field_id = await self._get_or_create_iteration_field(project_id)
        
        # The sprint_id might be the iteration ID, or we need to query it
        # Try using sprint_id as iteration ID first, if it fails, query for it
        iteration_id = sprint_id
        
        # Try to assign the issue
        await self._assign_issues_to_iteration(project_id, iteration_field_id, iteration_id, [issue_id])
        
        # Return the sprint (we'll need to query it to get full details)
        # For now, return a basic sprint object
        from ....domain.types import Sprint as DomainSprint
        return DomainSprint(
            id=sprint_id,
            title="",
            description="",
            start_date="",
            end_date="",
            status=ResourceStatus.ACTIVE,
            issues=[issue_id],
            created_at="",
            updated_at=""
        )
    
    async def remove_issue(self, sprint_id: SprintId, issue_id: IssueId) -> Sprint:
        """Remove issue from sprint."""
        # TODO: Implement remove issue
        raise NotImplementedError("Sprint remove issue via GraphQL not yet implemented")
    
    async def get_issues(self, sprint_id: SprintId) -> List:
        """Get issues for sprint."""
        # Get project ID
        project_id = self._config.project_id
        if not project_id:
            from .github_project_repository import GitHubProjectRepository
            project_repo = GitHubProjectRepository(self.github, self.repo, self._config)
            projects = await project_repo.find_all()
            if projects:
                project_id = projects[0].id
            else:
                raise ValueError("No project ID found")
        
        # Query all project items and filter by iteration
        get_items_query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: 100) {
                nodes {
                  id
                  fieldValues(first: 20) {
                    nodes {
                      ... on ProjectV2ItemFieldIterationValue {
                        iterationId
                        field {
                          ... on ProjectV2IterationField {
                            id
                          }
                        }
                      }
                    }
                  }
                  content {
                    ... on Issue {
                      id
                      number
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        response = await self.graphql(get_items_query, {"projectId": project_id})
        items = response.get("node", {}).get("items", {}).get("nodes", [])
        
        # Filter items that belong to this sprint
        sprint_issues = []
        from .github_issue_repository import GitHubIssueRepository
        issue_repo = GitHubIssueRepository(self.github, self.repo, self._config)
        
        for item in items:
            field_values = item.get("fieldValues", {}).get("nodes", [])
            content = item.get("content", {})
            
            # Check if this item is assigned to our sprint
            # The iterationId in fieldValues should match our sprint_id
            item_belongs_to_sprint = False
            for field_value in field_values:
                iteration_id = field_value.get("iterationId")
                if iteration_id == sprint_id:
                    item_belongs_to_sprint = True
                    break
            
            if item_belongs_to_sprint:
                # This item belongs to our sprint
                # Check if content is an Issue
                if content and content.get("number"):
                    issue_number = content.get("number")
                    try:
                        issue = await issue_repo.find_by_id(str(issue_number))
                        if issue:
                            sprint_issues.append(issue)
                    except Exception as e:
                        # Log but continue
                        if hasattr(self._logger, 'debug'):
                            self._logger.debug(f"Failed to get issue {issue_number}: {str(e)}")
                        pass
        
        return sprint_issues

