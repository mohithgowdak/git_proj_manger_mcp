"""GitHub issue repository."""

import json
import traceback
from typing import Optional, List
from github import Github
from github.Repository import Repository
from ..github_config import GitHubConfig
from .base_repository import BaseGitHubRepository
from ....domain.types import Issue, CreateIssue, IssueId, MilestoneId, IssueComment, CreateIssueComment, CommentId
from ....domain.resource_types import ResourceStatus
import httpx


class GitHubIssueRepository(BaseGitHubRepository):
    """GitHub issue repository."""
    
    async def _create_issue_via_api(self, data: CreateIssue) -> Issue:
        """Create issue using direct GitHub API call as fallback."""
        try:
            # Prepare issue data
            issue_data = {
                "title": data.title,
                "body": data.description or "",
            }
            
            # Add milestone if provided
            if data.milestone_id:
                try:
                    milestone_number = int(data.milestone_id)
                    issue_data["milestone"] = milestone_number
                except (ValueError, TypeError):
                    pass
            
            # Add assignees if provided
            if data.assignees:
                issue_data["assignees"] = data.assignees
            
            # Add labels if provided
            if data.labels:
                issue_data["labels"] = data.labels
            
            # Make direct API call
            url = f"https://api.github.com/repos/{self.owner}/{self.repository}/issues"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=issue_data, headers=headers, timeout=30.0)
                
                # Log the response for debugging
                self._logger.debug(f"GitHub API Response Status: {response.status_code}")
                self._logger.debug(f"GitHub API Response Headers: {dict(response.headers)}")
                
                if response.status_code == 201:
                    issue_json = response.json()
                    self._logger.debug(f"GitHub API Response Body: {json.dumps(issue_json, indent=2)}")
                    
                    # Convert JSON response to Issue domain object
                    from ....domain.types import Issue as DomainIssue
                    return DomainIssue(
                        id=str(issue_json["number"]),
                        number=issue_json["number"],
                        title=issue_json["title"],
                        description=issue_json["body"] or "",
                        status=ResourceStatus.CLOSED if issue_json["state"] == "closed" else ResourceStatus.ACTIVE,
                        assignees=[assignee["login"] for assignee in issue_json.get("assignees", [])],
                        labels=[label["name"] for label in issue_json.get("labels", [])],
                        milestone_id=str(issue_json["milestone"]["number"]) if issue_json.get("milestone") else None,
                        created_at=issue_json["created_at"],
                        updated_at=issue_json["updated_at"],
                        url=issue_json["html_url"]
                    )
                else:
                    error_body = response.text
                    self._logger.error(f"GitHub API Error Response: {error_body}")
                    raise ValueError(f"GitHub API error ({response.status_code}): {error_body}")
        except httpx.HTTPError as e:
            self._logger.error(f"HTTP error creating issue via API: {str(e)}")
            raise ValueError(f"HTTP error creating issue: {str(e)}")
        except Exception as e:
            self._logger.error(f"Error creating issue via API: {str(e)}")
            self._logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def create(self, data: CreateIssue) -> Issue:
        """Create an issue."""
        try:
            # Validate repository object
            if not self.repo:
                raise ValueError("Repository object is not initialized")
            
            # Validate required fields
            if not data.title or not data.title.strip():
                raise ValueError("Issue title is required")
            
            # Log PyGithub version for debugging
            try:
                import github
                pygithub_version = github.__version__
                self._logger.debug(f"PyGithub version: {pygithub_version}")
            except Exception:
                self._logger.warn("Could not determine PyGithub version")
            
            # Convert milestone ID to milestone object if provided
            milestone_obj = None
            if data.milestone_id:
                try:
                    milestone_obj = self.repo.get_milestone(int(data.milestone_id))
                except Exception as e:
                    self._logger.debug(f"Could not get milestone {data.milestone_id}: {str(e)}")
                    pass
            
            # Try PyGithub first
            try:
                self._logger.debug("Attempting to create issue via PyGithub...")
                
                # Use PyGithub to create issue - wrap in retry logic
                def _create_issue():
                    return self.repo.create_issue(
                        title=data.title,
                        body=data.description or "",
                        assignees=data.assignees or [],
                        labels=data.labels or [],
                        milestone=milestone_obj
                    )
                
                # Execute with retry logic
                issue = await self.with_retry(_create_issue, "creating issue")
                
                # Validate issue was created
                if not issue:
                    raise ValueError("GitHub API returned None when creating issue")
                
                self._logger.debug(f"Issue created successfully via PyGithub: {issue.number}")
                return self._convert_issue(issue)
                
            except AssertionError as e:
                # PyGithub AssertionError - log details and fallback to direct API
                error_msg = str(e)
                error_traceback = traceback.format_exc()
                self._logger.warn(f"PyGithub AssertionError: {error_msg}")
                self._logger.debug(f"PyGithub AssertionError traceback: {error_traceback}")
                self._logger.info("Falling back to direct GitHub API call...")
                
                # Fallback to direct API call
                return await self._create_issue_via_api(data)
                
            except Exception as e:
                # Log the error details
                error_msg = str(e)
                error_type = type(e).__name__
                error_traceback = traceback.format_exc()
                
                self._logger.error(f"PyGithub error ({error_type}): {error_msg}")
                self._logger.debug(f"PyGithub error traceback: {error_traceback}")
                
                # Check if it's a retryable error - if not, try direct API
                if not self._error_handler.is_retryable_error(e):
                    self._logger.info("Non-retryable error, falling back to direct GitHub API call...")
                    return await self._create_issue_via_api(data)
                else:
                    # Re-raise retryable errors
                    raise
                    
        except Exception as e:
            # Final error handling
            error_msg = str(e)
            error_type = type(e).__name__
            error_traceback = traceback.format_exc()
            
            self._logger.error(f"Final error creating issue ({error_type}): {error_msg}")
            self._logger.debug(f"Final error traceback: {error_traceback}")
            
            # Check for common GitHub API errors
            if "Bad credentials" in error_msg or "401" in error_msg:
                raise ValueError(f"GitHub authentication failed: {error_msg}")
            elif "Not Found" in error_msg or "404" in error_msg:
                raise ValueError(f"Repository or resource not found: {error_msg}")
            elif "Forbidden" in error_msg or "403" in error_msg:
                raise ValueError(f"Permission denied: {error_msg}")
            else:
                raise ValueError(f"Failed to create issue: {error_type}: {error_msg}")
    
    async def update(self, id: IssueId, data: dict) -> Issue:
        """Update an issue."""
        issue = self.repo.get_issue(int(id))
        
        # Track if we need to add in-progress label
        add_in_progress_label = False
        
        if 'title' in data:
            issue.edit(title=data['title'])
        if 'description' in data:
            issue.edit(body=data['description'])
        if 'assignees' in data:
            issue.edit(assignees=data['assignees'])
        
        # Handle milestone updates
        if 'milestone_id' in data:
            milestone_id = data['milestone_id']
            if milestone_id:
                try:
                    milestone_number = int(milestone_id)
                    milestone_obj = self.repo.get_milestone(milestone_number)
                    issue.edit(milestone=milestone_obj)
                except (ValueError, TypeError) as e:
                    self._logger.warn(f"Could not set milestone {milestone_id}: {str(e)}")
            else:
                # Remove milestone if milestone_id is None or empty
                issue.edit(milestone=None)
        
        # Handle status updates
        # GitHub issues only support "open" and "closed" states
        # "in_progress" is not a valid GitHub issue status, but we handle it via labels
        if 'status' in data:
            status = data['status']
            # Convert ResourceStatus to GitHub state
            if status == ResourceStatus.CLOSED:
                issue.edit(state='closed')
            elif status == ResourceStatus.ACTIVE:
                issue.edit(state='open')
                # Check if this was meant to be "in_progress" by checking the original status string
                # We'll handle this via labels below
        
        # Handle labels - if status was "in_progress", add the label
        should_add_in_progress = data.get('_add_in_progress_label', False)
        
        if 'labels' in data:
            labels = data['labels']
            # Ensure labels is a list of strings
            if not isinstance(labels, list):
                labels = list(labels) if labels else []
            labels = [str(l) for l in labels]  # Convert to strings
            
            # Add in-progress label if needed
            if should_add_in_progress:
                label_names = [l.lower() for l in labels]
                if "in-progress" not in label_names and "in_progress" not in label_names:
                    labels.append("in-progress")
            issue.edit(labels=labels)
        elif should_add_in_progress or ('status' in data and data['status'] == ResourceStatus.ACTIVE):
            # If no labels specified but we need to add in-progress label
            # Get current labels and add in-progress if not present
            current_labels = [label.name for label in issue.labels]
            if "in-progress" not in current_labels and "in_progress" not in current_labels:
                current_labels.append("in-progress")
                issue.edit(labels=current_labels)
        
        return self._convert_issue(issue)
    
    async def delete(self, id: IssueId) -> None:
        """Delete an issue."""
        issue = self.repo.get_issue(int(id))
        issue.edit(state='closed')
    
    async def find_by_id(self, id: IssueId) -> Optional[Issue]:
        """Find issue by ID."""
        try:
            issue = self.repo.get_issue(int(id))
            return self._convert_issue(issue)
        except Exception:
            return None
    
    async def find_by_milestone(self, milestone_id: MilestoneId) -> List[Issue]:
        """Find issues by milestone."""
        try:
            # PyGithub expects milestone as an integer or milestone object
            milestone_number = int(milestone_id)
            milestone_obj = self.repo.get_milestone(milestone_number)
            issues = self.repo.get_issues(milestone=milestone_obj)
            return [self._convert_issue(issue) for issue in issues]
        except (ValueError, TypeError) as e:
            # If milestone_id is not a valid integer, return empty list
            return []
        except Exception as e:
            # Log error but return empty list
            if hasattr(self._logger, 'warn'):
                self._logger.warn(f"Failed to get issues for milestone {milestone_id}: {str(e)}")
            return []
    
    async def find_all(self, options: Optional[dict] = None) -> List[Issue]:
        """Find all issues."""
        state = options.get('status') if options else None
        if state == ResourceStatus.CLOSED:
            state = 'closed'
        elif state == ResourceStatus.ACTIVE:
            state = 'open'
        else:
            state = 'all'
        
        issues = self.repo.get_issues(state=state)
        return [self._convert_issue(issue) for issue in issues]
    
    async def search(self, query: str) -> List[Issue]:
        """Search issues using GitHub search API query syntax.
        
        Examples:
        - "is:issue is:open label:bug"
        - "is:issue author:username"
        - "is:issue assignee:username"
        - "is:issue milestone:v1.0"
        """
        try:
            # GitHub search API format: repo:owner/repo query
            search_query = f"repo:{self.owner}/{self.repository} {query}"
            
            # Use GitHub search API
            def _search_issues():
                return self.github.search_issues(search_query)
            
            search_results = await self.with_retry(_search_issues, "searching issues")
            
            # Convert search results to issues
            issues = []
            for result in search_results:
                # Get full issue details
                try:
                    issue = self.repo.get_issue(result.number)
                    issues.append(self._convert_issue(issue))
                except Exception as e:
                    self._logger.warn(f"Could not get issue {result.number}: {str(e)}")
                    continue
            
            return issues
        except Exception as e:
            self._logger.error(f"Error searching issues with query '{query}': {str(e)}")
            raise ValueError(f"Failed to search issues: {str(e)}")
    
    def _convert_issue(self, issue) -> Issue:
        """Convert GitHub issue to domain Issue."""
        from ....domain.types import Issue as DomainIssue
        
        return DomainIssue(
            id=str(issue.number),
            number=issue.number,
            title=issue.title,
            description=issue.body or "",
            status=ResourceStatus.CLOSED if issue.state == 'closed' else ResourceStatus.ACTIVE,
            assignees=[assignee.login for assignee in issue.assignees],
            labels=[label.name for label in issue.labels],
            milestone_id=str(issue.milestone.number) if issue.milestone else None,
            created_at=issue.created_at.isoformat() if issue.created_at else "",
            updated_at=issue.updated_at.isoformat() if issue.updated_at else "",
            url=issue.html_url
        )
    
    def _convert_comment(self, comment) -> IssueComment:
        """Convert GitHub comment to domain IssueComment."""
        return IssueComment(
            id=str(comment.id),
            body=comment.body or "",
            author=comment.user.login if comment.user else "",
            created_at=comment.created_at.isoformat() if comment.created_at else "",
            updated_at=comment.updated_at.isoformat() if comment.updated_at else "",
            url=comment.html_url if hasattr(comment, 'html_url') else ""
        )
    
    async def create_comment(self, issue_id: IssueId, data: CreateIssueComment) -> IssueComment:
        """Create a comment on an issue."""
        try:
            issue = self.repo.get_issue(int(issue_id))
            
            def _create_comment():
                return issue.create_comment(data.body)
            
            comment = await self.with_retry(_create_comment, "creating comment")
            return self._convert_comment(comment)
        except Exception as e:
            self._logger.error(f"Error creating comment on issue {issue_id}: {str(e)}")
            raise ValueError(f"Failed to create comment: {str(e)}")
    
    async def list_comments(self, issue_id: IssueId) -> List[IssueComment]:
        """List all comments on an issue."""
        try:
            issue = self.repo.get_issue(int(issue_id))
            
            def _get_comments():
                return list(issue.get_comments())
            
            comments = await self.with_retry(_get_comments, "listing comments")
            return [self._convert_comment(comment) for comment in comments]
        except Exception as e:
            self._logger.error(f"Error listing comments for issue {issue_id}: {str(e)}")
            raise ValueError(f"Failed to list comments: {str(e)}")
    
    async def update_comment(self, issue_id: IssueId, comment_id: CommentId, body: str) -> IssueComment:
        """Update a comment on an issue."""
        try:
            issue = self.repo.get_issue(int(issue_id))
            comment = issue.get_comment(int(comment_id))
            
            def _update_comment():
                comment.edit(body)
                return comment
            
            updated_comment = await self.with_retry(_update_comment, "updating comment")
            return self._convert_comment(updated_comment)
        except Exception as e:
            self._logger.error(f"Error updating comment {comment_id} on issue {issue_id}: {str(e)}")
            raise ValueError(f"Failed to update comment: {str(e)}")
    
    async def delete_comment(self, issue_id: IssueId, comment_id: CommentId) -> None:
        """Delete a comment on an issue."""
        try:
            issue = self.repo.get_issue(int(issue_id))
            comment = issue.get_comment(int(comment_id))
            
            def _delete_comment():
                comment.delete()
            
            await self.with_retry(_delete_comment, "deleting comment")
        except Exception as e:
            self._logger.error(f"Error deleting comment {comment_id} on issue {issue_id}: {str(e)}")
            raise ValueError(f"Failed to delete comment: {str(e)}")

