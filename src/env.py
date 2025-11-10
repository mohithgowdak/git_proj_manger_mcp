"""Environment configuration module."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from .cli import CliOptions, parse_command_line_args

# Parse command line arguments only if not in test environment
cli_options: CliOptions = (
    CliOptions(verbose=False, env_file=None, token=None, owner=None, repo=None)
    if os.getenv("NODE_ENV") == "test"
    else parse_command_line_args()
)

# Load environment variables from .env file
env_path = (
    Path.cwd() / cli_options.env_file
    if cli_options.env_file
    else Path.cwd() / ".env"
)

load_dotenv(dotenv_path=env_path)

if cli_options.verbose:
    print(f"Loading environment from: {env_path}", file=os.sys.stderr)


def get_config_value(name: str, cli_value: Optional[str] = None) -> str:
    """Get a required configuration value from command line args or environment variables."""
    # First check CLI arguments
    if cli_value:
        return cli_value
    
    # Then check environment variables
    value = os.getenv(name)
    if not value:
        raise ValueError(
            f"{name} is required. Provide it via command line argument "
            f"(--{name.lower()}) or environment variable."
        )
    return value


def get_optional_config_value(name: str, default_value: str, cli_value: Optional[str] = None) -> str:
    """Get an optional configuration value with a default."""
    # First check CLI arguments
    if cli_value:
        return cli_value
    
    # Then check environment variables
    return os.getenv(name, default_value)


def get_boolean_config_value(name: str, default_value: bool) -> bool:
    """Get a boolean configuration value."""
    value = os.getenv(name)
    if not value:
        return default_value
    return value.lower() in ("true", "1")


def get_numeric_config_value(name: str, default_value: int) -> int:
    """Get a numeric configuration value."""
    value = os.getenv(name)
    if not value:
        return default_value
    try:
        return int(value)
    except ValueError:
        return default_value


# Export configuration values with CLI arguments taking precedence over environment variables
GITHUB_TOKEN = (
    "test-token"
    if os.getenv("NODE_ENV") == "test"
    else get_config_value("GITHUB_TOKEN", cli_options.token)
)
GITHUB_OWNER = (
    "test-owner"
    if os.getenv("NODE_ENV") == "test"
    else get_config_value("GITHUB_OWNER", cli_options.owner)
)
GITHUB_REPO = (
    "test-repo"
    if os.getenv("NODE_ENV") == "test"
    else get_config_value("GITHUB_REPO", cli_options.repo)
)

# Sync configuration
SYNC_ENABLED = get_boolean_config_value("SYNC_ENABLED", True)
SYNC_TIMEOUT_MS = get_numeric_config_value("SYNC_TIMEOUT_MS", 30000)
SYNC_INTERVAL_MS = get_numeric_config_value("SYNC_INTERVAL_MS", 0)  # 0 = disabled
CACHE_DIRECTORY = get_optional_config_value("CACHE_DIRECTORY", ".mcp-cache")
SYNC_RESOURCES = get_optional_config_value("SYNC_RESOURCES", "PROJECT,MILESTONE,ISSUE,SPRINT").split(",")

# Event system configuration
WEBHOOK_SECRET = get_optional_config_value("WEBHOOK_SECRET", "")
WEBHOOK_PORT = get_numeric_config_value("WEBHOOK_PORT", 3001)
SSE_ENABLED = get_boolean_config_value("SSE_ENABLED", True)
EVENT_RETENTION_DAYS = get_numeric_config_value("EVENT_RETENTION_DAYS", 7)
MAX_EVENTS_IN_MEMORY = get_numeric_config_value("MAX_EVENTS_IN_MEMORY", 1000)
WEBHOOK_TIMEOUT_MS = get_numeric_config_value("WEBHOOK_TIMEOUT_MS", 5000)

# AI Provider configuration
ANTHROPIC_API_KEY = get_optional_config_value("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = get_optional_config_value("OPENAI_API_KEY", "")
GOOGLE_API_KEY = get_optional_config_value("GOOGLE_API_KEY", "")
PERPLEXITY_API_KEY = get_optional_config_value("PERPLEXITY_API_KEY", "")

# AI Model configuration
AI_MAIN_MODEL = get_optional_config_value("AI_MAIN_MODEL", "claude-3-5-sonnet-20241022")
AI_RESEARCH_MODEL = get_optional_config_value("AI_RESEARCH_MODEL", "perplexity-llama-3.1-sonar-large-128k-online")
AI_FALLBACK_MODEL = get_optional_config_value("AI_FALLBACK_MODEL", "gpt-4o")
AI_PRD_MODEL = get_optional_config_value("AI_PRD_MODEL", "claude-3-5-sonnet-20241022")

# AI Task Generation configuration
MAX_TASKS_PER_PRD = get_numeric_config_value("MAX_TASKS_PER_PRD", 50)
DEFAULT_COMPLEXITY_THRESHOLD = get_numeric_config_value("DEFAULT_COMPLEXITY_THRESHOLD", 7)
MAX_SUBTASK_DEPTH = get_numeric_config_value("MAX_SUBTASK_DEPTH", 3)
AUTO_DEPENDENCY_DETECTION = get_boolean_config_value("AUTO_DEPENDENCY_DETECTION", True)
AUTO_EFFORT_ESTIMATION = get_boolean_config_value("AUTO_EFFORT_ESTIMATION", True)

# Enhanced Task Generation configuration
ENHANCED_TASK_GENERATION = get_boolean_config_value("ENHANCED_TASK_GENERATION", True)
AUTO_CREATE_TRACEABILITY = get_boolean_config_value("AUTO_CREATE_TRACEABILITY", True)
AUTO_GENERATE_USE_CASES = get_boolean_config_value("AUTO_GENERATE_USE_CASES", True)
AUTO_CREATE_LIFECYCLE = get_boolean_config_value("AUTO_CREATE_LIFECYCLE", True)
ENHANCED_CONTEXT_LEVEL = get_optional_config_value("ENHANCED_CONTEXT_LEVEL", "standard")  # minimal, standard, full
INCLUDE_BUSINESS_CONTEXT = get_boolean_config_value("INCLUDE_BUSINESS_CONTEXT", False)  # Default: traceability only
INCLUDE_TECHNICAL_CONTEXT = get_boolean_config_value("INCLUDE_TECHNICAL_CONTEXT", False)  # Default: traceability only
INCLUDE_IMPLEMENTATION_GUIDANCE = get_boolean_config_value("INCLUDE_IMPLEMENTATION_GUIDANCE", False)  # Default: traceability only

# GitHub AI Integration
AUTO_CREATE_PROJECT_FIELDS = get_boolean_config_value("AUTO_CREATE_PROJECT_FIELDS", True)
AI_BATCH_SIZE = get_numeric_config_value("AI_BATCH_SIZE", 10)

# Export CLI options for use in other modules
CLI_OPTIONS = cli_options




