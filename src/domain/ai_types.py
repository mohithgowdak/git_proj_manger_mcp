"""AI-related domain types."""

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


class TaskPriority(str, Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


TaskComplexity = int  # 1-10 scale


@dataclass
class AIGenerationMetadata:
    """AI generation metadata."""
    generated_by: str  # AI model used
    generated_at: str  # ISO timestamp
    prompt: str  # Prompt used for generation
    confidence: float  # 0-1 confidence score
    version: str  # AI system version


@dataclass
class TaskDependency:
    """Task dependency."""
    id: str
    type: str  # "blocks" | "depends_on" | "related_to"
    description: Optional[str] = None


@dataclass
class AcceptanceCriteria:
    """Acceptance criteria."""
    id: str
    description: str
    completed: bool = False


@dataclass
class AITask:
    """AI enhanced task."""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    complexity: TaskComplexity
    estimated_hours: float
    actual_hours: Optional[float] = None
    
    # AI-specific metadata
    ai_generated: bool = False
    ai_metadata: Optional[AIGenerationMetadata] = None
    
    # Task relationships
    parent_task_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)  # IDs of subtasks
    dependencies: List[TaskDependency] = field(default_factory=list)
    
    # Acceptance criteria
    acceptance_criteria: List[AcceptanceCriteria] = field(default_factory=list)
    
    # GitHub integration
    github_project_item_id: Optional[str] = None
    github_issue_id: Optional[int] = None
    
    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    due_date: Optional[str] = None
    
    # Additional metadata
    tags: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    source_prd: Optional[str] = None  # Reference to source PRD


@dataclass
class SubTask:
    """Subtask (simplified version of AITask)."""
    id: str
    title: str
    description: str
    status: TaskStatus
    complexity: TaskComplexity
    estimated_hours: float
    parent_task_id: str
    ai_generated: bool = False
    created_at: str = ""
    updated_at: str = ""


@dataclass
class UserPersona:
    """User persona."""
    id: str
    name: str
    description: str
    goals: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    technical_level: str = "intermediate"  # "beginner" | "intermediate" | "advanced"


@dataclass
class FeatureRequirement:
    """Feature requirement."""
    id: str
    title: str
    description: str
    priority: TaskPriority
    user_stories: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    estimated_complexity: TaskComplexity = 5
    dependencies: List[str] = field(default_factory=list)  # IDs of other features


@dataclass
class TechnicalRequirement:
    """Technical requirement."""
    id: str
    category: str  # "performance" | "security" | "scalability" | "integration" | "infrastructure"
    requirement: str
    rationale: str
    priority: TaskPriority


@dataclass
class ProjectScope:
    """Project scope."""
    in_scope: List[str] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class PRDDocument:
    """PRD Document."""
    id: str
    title: str
    version: str
    
    # Core content
    overview: str
    objectives: List[str] = field(default_factory=list)
    scope: Optional[ProjectScope] = None
    
    # User-focused
    target_users: List[UserPersona] = field(default_factory=list)
    user_journey: str = ""
    
    # Features and requirements
    features: List[FeatureRequirement] = field(default_factory=list)
    technical_requirements: List[TechnicalRequirement] = field(default_factory=list)
    
    # Market research (optional)
    market_research: Optional[Dict[str, Any]] = None
    
    # Project details
    timeline: str = ""
    milestones: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    
    # Metadata
    author: str = ""
    stakeholders: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class FeatureAdditionRequest:
    """Feature addition request."""
    feature_idea: str
    description: str
    existing_prd: Optional[PRDDocument] = None
    project_state: Optional[Dict[str, Any]] = None
    business_justification: Optional[str] = None
    target_users: List[str] = field(default_factory=list)
    requested_by: str = ""


@dataclass
class FeatureExpansionResult:
    """Feature expansion result."""
    analysis: str
    recommendation: str  # "approve" | "reject" | "modify"
    priority: TaskPriority
    complexity: TaskComplexity
    estimated_effort: float
    risks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    suggested_features: List[FeatureRequirement] = field(default_factory=list)
    suggested_tasks: List[AITask] = field(default_factory=list)




