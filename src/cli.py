"""CLI module for parsing command line arguments."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class CliOptions:
    """CLI options."""
    token: Optional[str] = None
    owner: Optional[str] = None
    repo: Optional[str] = None
    env_file: Optional[str] = None
    verbose: bool = False


def get_version() -> str:
    """Get version from pyproject.toml or package.json."""
    version = "1.0.1"
    
    # Try pyproject.toml first
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        try:
            import tomli
            with open(pyproject_path, "rb") as f:
                data = tomli.load(f)
                version = data.get("project", {}).get("version", version)
        except Exception:
            pass
    
    # Fallback to package.json
    package_json_path = Path(__file__).parent.parent / "package.json"
    if package_json_path.exists():
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                version = data.get("version", version)
        except Exception:
            pass
    
    return version


def parse_command_line_args() -> CliOptions:
    """Parse command line arguments using argparse."""
    parser = argparse.ArgumentParser(
        prog="mcp-github-project-manager",
        description="A Model Context Protocol (MCP) server for managing GitHub Projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-github-project-manager --token=your_token --owner=your_username --repo=your_repo
  mcp-github-project-manager -t your_token -o your_username -r your_repo
  mcp-github-project-manager --env-file=.env.production
  GITHUB_TOKEN=your_token mcp-github-project-manager

Environment variables:
  GITHUB_TOKEN     GitHub personal access token
  GITHUB_OWNER     GitHub repository owner
  GITHUB_REPO      GitHub repository name
        """
    )
    
    parser.add_argument(
        "-t", "--token",
        help="GitHub personal access token"
    )
    parser.add_argument(
        "-o", "--owner",
        help="GitHub repository owner (username or organization)"
    )
    parser.add_argument(
        "-r", "--repo",
        help="GitHub repository name"
    )
    parser.add_argument(
        "-e", "--env-file",
        help="Path to .env file (default: .env in project root)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}"
    )
    
    args = parser.parse_args()
    
    return CliOptions(
        token=args.token,
        owner=args.owner,
        repo=args.repo,
        env_file=args.env_file,
        verbose=args.verbose
    )


def main():
    """Main CLI entry point."""
    options = parse_command_line_args()
    # This is just for testing - the actual server is started from __main__.py
    print(f"CLI Options: {options}", file=sys.stderr)


if __name__ == "__main__":
    main()

