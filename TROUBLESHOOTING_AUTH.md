# Troubleshooting: GitHub Authentication Error (401 Bad Credentials)

## Error Description

```
github.GithubException.BadCredentialsException: 401 {"message": "Bad credentials", ...}
```

This error occurs when the GitHub Personal Access Token is invalid, expired, or missing required permissions.

## Quick Fix Steps

### Step 1: Verify Your .env File

Check that your `.env` file exists and contains:

```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_OWNER=your_username_or_org
GITHUB_REPO=your_repository_name
```

### Step 2: Create a New GitHub Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a descriptive name (e.g., "MCP Server Token")
4. Select these scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `project` (Full control of organization projects)
   - ✅ `write:org` (if using organization repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

### Step 3: Update Your .env File

```env
GITHUB_TOKEN=ghp_your_new_token_here
GITHUB_OWNER=your_username
GITHUB_REPO=your_repo_name
```

### Step 4: Verify Token Format

Your token should:
- Start with `ghp_` (classic token) or `github_pat_` (fine-grained token)
- Be at least 40 characters long
- Not have any spaces or line breaks

### Step 5: Test Your Token

You can test your token manually:

```powershell
# Test with PowerShell
$token = "ghp_your_token_here"
$headers = @{Authorization = "token $token"}
Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers
```

If successful, you'll see your GitHub user information.

### Step 6: Restart the Server

```powershell
python -m src
```

## Common Issues

### Issue 1: Token Expired
**Solution:** Generate a new token and update your `.env` file

### Issue 2: Missing Permissions
**Solution:** Ensure your token has `repo` and `project` scopes

### Issue 3: Wrong Repository
**Solution:** Verify `GITHUB_OWNER` and `GITHUB_REPO` are correct:
- Owner: Your username or organization name
- Repo: Repository name (not the full URL)

### Issue 4: Token Format Issues
**Solution:** 
- Remove any spaces or quotes around the token
- Ensure the token starts with `ghp_` or `github_pat_`
- Don't include `Bearer` prefix

### Issue 5: Environment Variables Not Loading
**Solution:**
- Ensure `.env` file is in the project root
- Check for typos in variable names
- Try using command line arguments instead:
  ```powershell
  python -m src --token=your_token --owner=your_username --repo=your_repo
  ```

## Verification Checklist

- [ ] `.env` file exists in project root
- [ ] `GITHUB_TOKEN` is set and starts with `ghp_` or `github_pat_`
- [ ] `GITHUB_OWNER` matches your GitHub username/org
- [ ] `GITHUB_REPO` matches your repository name
- [ ] Token has `repo` and `project` permissions
- [ ] Token is not expired
- [ ] You have access to the repository

## Still Having Issues?

1. **Check token permissions:**
   - Go to https://github.com/settings/tokens
   - Find your token and verify scopes

2. **Test token manually:**
   ```powershell
   $token = "your_token"
   Invoke-RestMethod -Uri "https://api.github.com/user" -Headers @{Authorization = "token $token"}
   ```

3. **Check repository access:**
   - Verify you can access the repository in GitHub
   - Check if it's private and you have access
   - Verify owner and repo names are correct

4. **Use verbose mode:**
   ```powershell
   python -m src --verbose
   ```

5. **Check for typos:**
   - Ensure no extra spaces in `.env` file
   - Variable names are exactly: `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`

## Example .env File

```env
# GitHub Configuration
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_OWNER=mohithgowdak
GITHUB_REPO=AI_ML_LEARNING

# Optional Configuration
SYNC_ENABLED=true
CACHE_DIRECTORY=.cache
```

## Need Help?

If you're still experiencing issues:
1. Check the error message for specific details
2. Verify all steps above
3. Try creating a fresh token
4. Test with a simple repository first

