"""GraphQL helpers for GitHub API."""

from typing import Dict, Any, Optional
from ....domain.types import FieldType


def map_to_graphql_field_type(field_type: FieldType) -> str:
    """Map a domain field type to a GraphQL field type."""
    mapping = {
        'text': 'TEXT',
        'number': 'NUMBER',
        'date': 'DATE',
        'single_select': 'SINGLE_SELECT',
        'iteration': 'ITERATION',
        'milestone': 'MILESTONE',
        'assignees': 'ASSIGNEES',
        'labels': 'LABELS',
        'tracked_by': 'TRACKED_BY',
        'repository': 'REPOSITORY',
        'tracks': 'TRACKS'
    }
    return mapping.get(field_type, 'TEXT')


def map_from_graphql_field_type(field_type: str) -> FieldType:
    """Map a GraphQL field type to a domain field type."""
    mapping = {
        'TEXT': 'text',
        'NUMBER': 'number',
        'DATE': 'date',
        'SINGLE_SELECT': 'single_select',
        'ITERATION': 'iteration',
        'MILESTONE': 'milestone',
        'ASSIGNEES': 'assignees',
        'LABELS': 'labels',
        'TRACKED_BY': 'tracked_by',
        'REPOSITORY': 'repository'
    }
    return mapping.get(field_type, 'text')


class GraphQLResponse:
    """GraphQL response wrapper."""
    
    def __init__(self, data: Optional[Dict[str, Any]] = None, errors: Optional[list] = None):
        self.data = data
        self.errors = errors


class CreateProjectV2FieldResponse:
    """Create project field response."""
    
    def __init__(self, project_v2_field: Dict[str, Any]):
        self.create_project_v2_field = {
            "projectV2Field": project_v2_field
        }


class UpdateProjectV2FieldResponse:
    """Update project field response."""
    
    def __init__(self, project_v2_field: Dict[str, Any]):
        self.update_project_v2_field = {
            "projectV2Field": project_v2_field
        }




