#!/usr/bin/env python3
"""Script to delete all projects and close all issues in GitHub repository."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.env import GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO
from src.services.project_management_service import ProjectManagementService
from src.domain.resource_types import ResourceStatus


async def delete_all_projects():
    """Delete all projects."""
    print(f"Connecting to GitHub repository: {GITHUB_OWNER}/{GITHUB_REPO}")
    service = ProjectManagementService(GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN)
    
    # List all projects (both active and closed)
    print("\n📋 Listing all projects...")
    active_projects = await service.list_projects(status=ResourceStatus.ACTIVE)
    closed_projects = await service.list_projects(status=ResourceStatus.CLOSED)
    all_projects = active_projects + closed_projects
    
    if not all_projects:
        print("✅ No projects found.")
        return
    
    print(f"Found {len(all_projects)} project(s):")
    for project in all_projects:
        print(f"  - {project.title} (ID: {project.id})")
    
    # Confirm deletion
    print(f"\n⚠️  WARNING: This will delete {len(all_projects)} project(s).")
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Operation cancelled.")
        return
    
    # Delete each project
    print("\n🗑️  Deleting projects...")
    deleted_count = 0
    failed_count = 0
    
    for project in all_projects:
        try:
            print(f"  Deleting: {project.title} (ID: {project.id})...")
            await service.delete_project({"project_id": project.id})
            deleted_count += 1
            print(f"  ✅ Deleted: {project.title}")
        except Exception as e:
            failed_count += 1
            print(f"  ❌ Failed to delete {project.title}: {e}")
    
    print(f"\n✅ Deleted {deleted_count} project(s).")
    if failed_count > 0:
        print(f"❌ Failed to delete {failed_count} project(s).")


async def close_all_issues():
    """Close all open issues."""
    print(f"\n📋 Listing all open issues...")
    service = ProjectManagementService(GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN)
    
    # List all open issues
    open_issues = await service.list_issues(options={"status": "open"})
    
    if not open_issues:
        print("✅ No open issues found.")
        return
    
    print(f"Found {len(open_issues)} open issue(s):")
    for issue in open_issues:
        print(f"  - #{issue.number}: {issue.title} (ID: {issue.id})")
    
    # Confirm closing
    print(f"\n⚠️  WARNING: This will close {len(open_issues)} issue(s).")
    print("Note: GitHub does not allow deleting issues, only closing them.")
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Operation cancelled.")
        return
    
    # Close each issue
    print("\n🔒 Closing issues...")
    closed_count = 0
    failed_count = 0
    
    for issue in open_issues:
        try:
            print(f"  Closing: #{issue.number} - {issue.title}...")
            await service.update_issue(issue.id, {"status": ResourceStatus.CLOSED})
            closed_count += 1
            print(f"  ✅ Closed: #{issue.number}")
        except Exception as e:
            failed_count += 1
            print(f"  ❌ Failed to close #{issue.number}: {e}")
    
    print(f"\n✅ Closed {closed_count} issue(s).")
    if failed_count > 0:
        print(f"❌ Failed to close {failed_count} issue(s).")


async def main():
    """Main function."""
    print("=" * 60)
    print("GitHub Project and Issue Cleanup Script")
    print("=" * 60)
    
    try:
        # Delete all projects
        await delete_all_projects()
        
        # Close all issues
        await close_all_issues()
        
        print("\n" + "=" * 60)
        print("✅ Cleanup completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

