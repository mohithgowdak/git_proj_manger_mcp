"""GitHub project repository."""

from typing import Optional, List, Dict, Any
from github import Github
from github.Repository import Repository
from ..github_config import GitHubConfig
from .base_repository import BaseGitHubRepository
from ....domain.types import Project, CreateProject, ProjectId, ProjectView, CustomField
from ....domain.resource_types import ResourceType, ResourceStatus


class GitHubProjectRepository(BaseGitHubRepository):
    """GitHub project repository."""
    
    async def create(self, data: CreateProject) -> Project:
        """Create a project."""
        # Step 0: Resolve owner login to node ID
        owner_id = None
        owner_login = data.owner if data.owner else self._config.owner
        
        # Try to get user ID first
        user_query = """
        query($login: String!) {
          user(login: $login) {
            id
          }
        }
        """
        
        # Try to get organization ID
        org_query = """
        query($login: String!) {
          organization(login: $login) {
            id
          }
        }
        """
        
        try:
            user_response = await self.graphql(user_query, {"login": owner_login})
            owner_id = user_response.get("user", {}).get("id")
        except Exception:
            # If user not found, try organization
            try:
                org_response = await self.graphql(org_query, {"login": owner_login})
                owner_id = org_response.get("organization", {}).get("id")
            except Exception as e:
                raise ValueError(f"Could not resolve owner '{owner_login}' to a user or organization: {str(e)}")
        
        if not owner_id:
            raise ValueError(f"Could not resolve owner '{owner_login}' to a node ID")
        
        # Step 1: Create project with valid CreateProjectV2Input schema
        create_mutation = """
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
        
        # Build input according to official GitHub schema
        # ownerId needs to be the node ID of the owner (user or org)
        create_input: Dict[str, Any] = {
            "title": data.title,
            "ownerId": owner_id,
        }
        
        # Execute GraphQL mutation
        create_response = await self.graphql(create_mutation, {
            "input": create_input
        })
        
        project_data = create_response.get("createProjectV2", {}).get("projectV2", {})
        
        # Step 2: Update project with description if provided
        if data.short_description:
            update_mutation = """
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
            
            update_response = await self.graphql(update_mutation, {
                "input": {
                    "projectId": project_data["id"],
                    "shortDescription": data.short_description
                }
            })
            
            project_data = update_response.get("updateProjectV2", {}).get("projectV2", project_data)
        
        return self._convert_to_project(project_data, data)
    
    async def update(self, id: ProjectId, data: dict) -> Project:
        """Update a project."""
        mutation = """
        mutation($input: UpdateProjectV2Input!) {
          updateProjectV2(input: $input) {
            projectV2 {
              id
              title
              shortDescription
              closed
              updatedAt
            }
          }
        }
        """
        
        input_data: Dict[str, Any] = {"projectId": id}
        if "title" in data:
            input_data["title"] = data["title"]
        if "description" in data:
            input_data["shortDescription"] = data["description"]
        if "status" in data:
            input_data["closed"] = data["status"] == ResourceStatus.CLOSED
        
        response = await self.graphql(mutation, {"input": input_data})
        project_data = response.get("updateProjectV2", {}).get("projectV2", {})
        
        return self._convert_to_project(project_data, None)
    
    async def delete(self, id: ProjectId) -> None:
        """Delete a project."""
        mutation = """
        mutation($input: DeleteProjectV2Input!) {
          deleteProjectV2(input: $input) {
            projectV2 {
              id
            }
          }
        }
        """
        
        await self.graphql(mutation, {
            "input": {"projectId": id}
        })
    
    async def find_by_id(self, id: ProjectId) -> Optional[Project]:
        """Find project by ID."""
        query = """
        query($id: ID!) {
          node(id: $id) {
            ... on ProjectV2 {
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
        
        response = await self.graphql(query, {"id": id})
        node = response.get("node")
        if not node:
            return None
        
        return self._convert_to_project(node, None)
    
    async def find_by_owner(self, owner: str) -> List[Project]:
        """Find projects by owner."""
        # Query user and organization separately to handle cases where one doesn't exist
        user_query = """
        query($owner: String!) {
          user(login: $owner) {
            projectsV2(first: 100) {
              nodes {
                id
                title
                shortDescription
                closed
                createdAt
                updatedAt
              }
            }
          }
        }
        """
        
        org_query = """
        query($owner: String!) {
          organization(login: $owner) {
            projectsV2(first: 100) {
              nodes {
                id
                title
                shortDescription
                closed
                createdAt
                updatedAt
              }
            }
          }
        }
        """
        
        user_projects = []
        org_projects = []
        
        # Try to get user projects
        try:
            user_response = await self.graphql(user_query, {"owner": owner})
            user_projects = user_response.get("user", {}).get("projectsV2", {}).get("nodes", []) or []
        except Exception as e:
            error_msg = str(e)
            # If it's a "user not found" error, that's fine - owner might be an org
            # Otherwise, log but continue to try organization query
            if "Could not resolve to a User" not in error_msg and "Could not resolve to an Organization" not in error_msg:
                # For other errors, we'll try org query and then decide
                self._logger.warn(f"Error querying user projects: {error_msg}")
        
        # Try to get organization projects
        try:
            org_response = await self.graphql(org_query, {"owner": owner})
            if org_response and isinstance(org_response, dict):
                org_data = org_response.get("organization")
                if org_data and isinstance(org_data, dict):
                    org_projects = org_data.get("projectsV2", {}).get("nodes", []) or []
                else:
                    org_projects = []
            else:
                org_projects = []
        except Exception as e:
            error_msg = str(e)
            # If it's an "organization not found" error, that's fine - owner might be a user
            if "Could not resolve to an Organization" not in error_msg:
                # For other errors, only fail if we don't have user projects either
                if not user_projects:
                    self._logger.error(f"Error querying organization projects and no user projects found: {error_msg}")
                    raise
                else:
                    self._logger.warn(f"Error querying organization projects (but user projects found): {error_msg}")
            org_projects = []
        
        all_projects = user_projects + org_projects
        return [self._convert_to_project(p, None) for p in all_projects]
    
    async def find_all(self) -> List[Project]:
        """Find all projects."""
        return await self.find_by_owner(self._config.owner)
    
    async def create_field(self, project_id: ProjectId, field: dict) -> CustomField:
        """Create field."""
        from ..util.graphql_helpers import map_to_graphql_field_type
        
        mutation = """
        mutation($input: CreateProjectV2FieldInput!) {
          createProjectV2Field(input: $input) {
            projectV2Field {
              id
              name
              dataType
            }
          }
        }
        """
        
        input_data: Dict[str, Any] = {
            "projectId": project_id,
            "name": field["name"],
            "dataType": map_to_graphql_field_type(field["type"])
        }
        
        if "options" in field and field["options"]:
            input_data["singleSelectOptions"] = [
                {"name": opt["name"]} for opt in field["options"]
            ]
        
        response = await self.graphql(mutation, {"input": input_data})
        field_data = response.get("createProjectV2Field", {}).get("projectV2Field", {})
        
        from ....domain.types import CustomField as DomainCustomField
        return DomainCustomField(
            id=field_data["id"],
            name=field_data["name"],
            type=field["type"],
            options=field.get("options"),
            description=field.get("description"),
            required=field.get("required", False)
        )
    
    async def update_field(self, project_id: ProjectId, field_id: str, data: dict) -> CustomField:
        """Update field."""
        mutation = """
        mutation($input: UpdateProjectV2FieldInput!) {
          updateProjectV2Field(input: $input) {
            projectV2Field {
              id
              name
            }
          }
        }
        """
        
        input_data: Dict[str, Any] = {
            "projectId": project_id,
            "fieldId": field_id
        }
        
        if "name" in data:
            input_data["name"] = data["name"]
        
        response = await self.graphql(mutation, {"input": input_data})
        field_data = response.get("updateProjectV2Field", {}).get("projectV2Field", {})
        
        from ....domain.types import CustomField as DomainCustomField
        return DomainCustomField(
            id=field_data["id"],
            name=field_data.get("name", ""),
            type="text",  # Default, would need to fetch actual type
            options=None,
            description=None,
            required=False
        )
    
    async def delete_field(self, project_id: ProjectId, field_id: str) -> None:
        """Delete field."""
        mutation = """
        mutation($input: DeleteProjectV2FieldInput!) {
          deleteProjectV2Field(input: $input) {
            projectV2Field {
              id
            }
          }
        }
        """
        
        await self.graphql(mutation, {
            "input": {
                "projectId": project_id,
                "fieldId": field_id
            }
        })
    
    async def create_view(self, project_id: ProjectId, name: str, layout: str) -> ProjectView:
        """Create view."""
        from ..graphql_types import map_to_graphql_view_layout
        
        mutation = """
        mutation($input: CreateProjectV2ViewInput!) {
          createProjectV2View(input: $input) {
            projectV2View {
              id
              name
              layout
            }
          }
        }
        """
        
        graphql_layout = map_to_graphql_view_layout(layout)
        response = await self.graphql(mutation, {
            "input": {
                "projectId": project_id,
                "name": name,
                "layout": graphql_layout
            }
        })
        
        view_data = response.get("createProjectV2View", {}).get("projectV2View", {})
        
        from ....domain.types import ProjectView as DomainProjectView
        return DomainProjectView(
            id=view_data["id"],
            name=view_data["name"],
            layout=layout,
            fields=None,
            sort_by=None,
            group_by=None,
            filters=None,
            settings=None
        )
    
    async def update_view(self, project_id: ProjectId, view_id: str, data: dict) -> ProjectView:
        """Update view."""
        mutation = """
        mutation($input: UpdateProjectV2ViewInput!) {
          updateProjectV2View(input: $input) {
            projectV2View {
              id
              name
              layout
            }
          }
        }
        """
        
        input_data: Dict[str, Any] = {
            "projectId": project_id,
            "viewId": view_id
        }
        
        if "name" in data:
            input_data["name"] = data["name"]
        
        response = await self.graphql(mutation, {"input": input_data})
        view_data = response.get("updateProjectV2View", {}).get("projectV2View", {})
        
        from ....domain.types import ProjectView as DomainProjectView
        return DomainProjectView(
            id=view_data["id"],
            name=view_data.get("name", ""),
            layout=data.get("layout", "board"),
            fields=None,
            sort_by=None,
            group_by=None,
            filters=None,
            settings=None
        )
    
    async def delete_view(self, project_id: ProjectId, view_id: str) -> None:
        """Delete view."""
        mutation = """
        mutation($input: DeleteProjectV2ViewInput!) {
          deleteProjectV2View(input: $input) {
            projectV2View {
              id
            }
          }
        }
        """
        
        await self.graphql(mutation, {
            "input": {
                "projectId": project_id,
                "viewId": view_id
            }
        })
    
    def _convert_to_project(self, project_data: Dict[str, Any], create_data: Optional[CreateProject]) -> Project:
        """Convert GitHub project data to domain Project."""
        from ....domain.types import Project as DomainProject
        
        project_id = project_data.get("id", "")
        # GitHub Project V2 IDs are base64-encoded node IDs (e.g., "PVT_kwHOBXXpns4AMPu0")
        # Try to extract a number if possible, otherwise use 0
        number = 0
        if project_id:
            # Try to parse number from ID format like "PVT_kwHOBXXpns4AMPu0" or extract from base64
            try:
                if '_' in project_id:
                    # Try to decode base64 part after underscore
                    parts = project_id.split('_')
                    if len(parts) > 1:
                        # For now, just use 0 as GitHub Project V2 doesn't have simple numeric IDs
                        number = 0
                    else:
                        number = int(parts[-1])
                else:
                    number = int(project_id)
            except (ValueError, IndexError):
                # If parsing fails, use 0
                number = 0
        owner = self._config.owner
        
        return DomainProject(
            id=project_id,
            type=ResourceType.PROJECT,
            title=project_data.get("title", ""),
            description=project_data.get("shortDescription") or "",
            owner=owner,
            number=number,
            url=f"https://github.com/{owner}/projects/{number}",
            fields=[],
            views=None,
            closed=project_data.get("closed", False),
            created_at=project_data.get("createdAt", ""),
            updated_at=project_data.get("updatedAt", ""),
            status=ResourceStatus.CLOSED if project_data.get("closed") else ResourceStatus.ACTIVE,
            visibility=create_data.visibility if create_data else "private",
            version=None
        )

