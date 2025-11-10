"""Domain resource types and enums."""

from enum import Enum
from typing import Optional, Dict, Any, Protocol, Generic, TypeVar
from datetime import datetime

T = TypeVar('T', bound='Resource')


class ResourceType(str, Enum):
    """Resource type enumeration."""
    PROJECT = "project"
    ISSUE = "issue"
    MILESTONE = "milestone"
    SPRINT = "sprint"
    RELATIONSHIP = "relationship"
    PULL_REQUEST = "pull_request"
    LABEL = "label"
    VIEW = "view"
    FIELD = "field"
    COMMENT = "comment"
    # AI-related resource types
    PRD = "prd"
    AI_TASK = "ai_task"
    FEATURE_REQUEST = "feature_request"
    TASK_LIFECYCLE = "task_lifecycle"
    PROJECT_ROADMAP = "project_roadmap"
    # Requirements traceability types
    REQUIREMENT = "requirement"
    USE_CASE = "use_case"
    TRACEABILITY_MATRIX = "traceability_matrix"
    TRACEABILITY_LINK = "traceability_link"


class ResourceStatus(str, Enum):
    """Resource status enumeration."""
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PLANNED = "planned"
    COMPLETED = "completed"


class RelationshipType(str, Enum):
    """Relationship type enumeration."""
    LINKED = "linked"
    DEPENDENCY_OF = "dependency_of"
    BLOCKED_BY = "blocked_by"
    PARENT_CHILD = "parent_child"
    DEPENDENCY = "dependency"


class ResourceEventType(str, Enum):
    """Resource event type enumeration."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ARCHIVED = "archived"
    RESTORED = "restored"
    RELATIONSHIP_CREATED = "relationship_created"
    RELATIONSHIP_DELETED = "relationship_deleted"
    RELATIONSHIP_REMOVED = "relationship_removed"


class Resource:
    """Base resource interface."""
    
    def __init__(
        self,
        id: str,
        type: ResourceType,
        created_at: str,
        updated_at: Optional[str] = None,
        deleted_at: Optional[str] = None,
        version: Optional[int] = None,
        status: Optional[ResourceStatus] = None
    ):
        self.id = id
        self.type = type
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at
        self.version = version
        self.status = status


class Relationship(Resource):
    """Relationship resource."""
    
    def __init__(
        self,
        id: str,
        source_id: str,
        source_type: ResourceType,
        target_id: str,
        target_type: ResourceType,
        relationship_type: RelationshipType,
        created_at: str,
        updated_at: Optional[str] = None,
        deleted_at: Optional[str] = None,
        version: Optional[int] = None,
        status: Optional[ResourceStatus] = None
    ):
        super().__init__(id, ResourceType.RELATIONSHIP, created_at, updated_at, deleted_at, version, status)
        self.source_id = source_id
        self.source_type = source_type
        self.target_id = target_id
        self.target_type = target_type
        self.relationship_type = relationship_type


class ResourceEvent:
    """Resource event."""
    
    def __init__(
        self,
        id: str,
        resource_id: str,
        resource_type: ResourceType,
        event_type: ResourceEventType,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.event_type = event_type
        self.timestamp = timestamp
        self.metadata = metadata or {}


class ResourceNotFoundError(Exception):
    """Resource not found error."""
    
    def __init__(self, resource_type: ResourceType, resource_id: str):
        super().__init__(f"{resource_type} with ID {resource_id} not found")
        self.name = "ResourceNotFoundError"
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceVersionError(Exception):
    """Resource version error."""
    
    def __init__(
        self,
        resource_type: ResourceType,
        resource_id: str,
        current_version: int,
        expected_version: int
    ):
        super().__init__(
            f"Version mismatch for {resource_type} with ID {resource_id}: "
            f"current={current_version}, expected={expected_version}"
        )
        self.name = "ResourceVersionError"
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.current_version = current_version
        self.expected_version = expected_version


class ResourceValidationError(Exception):
    """Resource validation error."""
    
    def __init__(self, resource_type: ResourceType, details: str):
        super().__init__(f"Validation failed for {resource_type}: {details}")
        self.name = "ResourceValidationError"
        self.resource_type = resource_type
        self.details = details


class ResourceValidationRule:
    """Resource validation rule."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
    
    def validate(self, resource: Any) -> bool:
        """Validate resource."""
        raise NotImplementedError
    
    def get_error_message(self, resource: Any) -> str:
        """Get error message."""
        return self.message


class ResourceCacheOptions:
    """Resource cache options."""
    
    def __init__(
        self,
        ttl: Optional[int] = None,
        refresh_interval: Optional[int] = None,
        max_size: Optional[int] = None,
        tags: Optional[list[str]] = None,
        namespaces: Optional[list[str]] = None,
        include_deleted: bool = False
    ):
        self.ttl = ttl
        self.refresh_interval = refresh_interval
        self.max_size = max_size
        self.tags = tags or []
        self.namespaces = namespaces or []
        self.include_deleted = include_deleted


class ResourceUpdateOptions:
    """Resource update options."""
    
    def __init__(
        self,
        expected_version: Optional[int] = None,
        validate: bool = True,
        optimistic_lock: bool = True,
        tags: Optional[list[str]] = None,
        namespaces: Optional[list[str]] = None
    ):
        self.expected_version = expected_version
        self.validate = validate
        self.optimistic_lock = optimistic_lock
        self.tags = tags or []
        self.namespaces = namespaces or []


class ResourceRepository(Protocol, Generic[T]):
    """Resource repository protocol."""
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create resource."""
        ...
    
    async def update(self, id: str, data: Dict[str, Any]) -> T:
        """Update resource."""
        ...
    
    async def delete(self, id: str) -> None:
        """Delete resource."""
        ...
    
    async def find_by_id(self, id: str) -> Optional[T]:
        """Find resource by ID."""
        ...
    
    async def find_all(self, options: Optional[Dict[str, Any]] = None) -> list[T]:
        """Find all resources."""
        ...




