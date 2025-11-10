"""GraphQL types for GitHub API."""

from typing import Optional, List, Dict, Any
from ...domain.types import ViewLayout, FieldType


class GraphQLResponse:
    """GraphQL response wrapper."""
    
    def __init__(self, data: Optional[Dict[str, Any]] = None, errors: Optional[List[Dict[str, Any]]] = None):
        self.data = data
        self.errors = errors


GraphQLViewLayout = str  # 'BOARD_LAYOUT' | 'TABLE_LAYOUT' | 'TIMELINE_LAYOUT' | 'ROADMAP_LAYOUT'
GraphQLFieldType = str  # 'TEXT' | 'NUMBER' | 'DATE' | 'SINGLE_SELECT' | 'ITERATION' | 'MILESTONE' | 'ASSIGNEES' | 'LABELS' | 'REPOSITORY' | 'TRACKED_BY' | 'TRACKS'


def map_to_graphql_view_layout(layout: ViewLayout) -> GraphQLViewLayout:
    """Map domain view layout to GitHub GraphQL layout."""
    mapping = {
        'board': 'BOARD_LAYOUT',
        'table': 'TABLE_LAYOUT',
        'timeline': 'TIMELINE_LAYOUT',
        'roadmap': 'ROADMAP_LAYOUT'
    }
    return mapping.get(layout, 'BOARD_LAYOUT')


def map_to_graphql_field_type(field_type: FieldType) -> GraphQLFieldType:
    """Map domain field type to GitHub GraphQL field type."""
    mapping = {
        'text': 'TEXT',
        'number': 'NUMBER',
        'date': 'DATE',
        'single_select': 'SINGLE_SELECT',
        'iteration': 'ITERATION',
        'milestone': 'MILESTONE',
        'assignees': 'ASSIGNEES',
        'labels': 'LABELS',
        'repository': 'REPOSITORY',
        'tracked_by': 'TRACKED_BY',
        'tracks': 'TRACKS'
    }
    return mapping.get(field_type, 'TEXT')


def map_from_graphql_field_type(field_type: GraphQLFieldType) -> FieldType:
    """Map GitHub GraphQL field type to domain field type."""
    mapping = {
        'TEXT': 'text',
        'NUMBER': 'number',
        'DATE': 'date',
        'SINGLE_SELECT': 'single_select',
        'ITERATION': 'iteration',
        'MILESTONE': 'milestone',
        'ASSIGNEES': 'assignees',
        'LABELS': 'labels',
        'REPOSITORY': 'repository',
        'TRACKED_BY': 'tracked_by'
    }
    return mapping.get(field_type, 'text')


class CreateProjectV2ViewResponse:
    """Create project view response."""
    
    def __init__(self, project_v2_view: Dict[str, Any]):
        self.create_project_v2_view = {
            "projectV2View": project_v2_view
        }


class UpdateProjectV2ViewResponse:
    """Update project view response."""
    
    def __init__(self, project_v2_view: Dict[str, Any]):
        self.update_project_v2_view = {
            "projectV2View": project_v2_view
        }




