# How to Check and Enable GitHub Token Permissions

## Required Permissions for Sprint Creation

Your GitHub Personal Access Token needs the following scopes:
- ✅ **`repo`** - Full repository access (read/write)
- ✅ **`project`** - Project access (read/write) 
- ✅ **`write:org`** - Organization access (if working with organization projects)

## Step 1: Check Current Token Permissions

### Method 1: Via GitHub Website

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Direct link: https://github.com/settings/tokens

2. Find your token in the list (or check if you have one)

3. Look at the "Scopes" column to see what permissions it has

### Method 2: Test via API

You can test your token permissions by making an API call:

```bash
# Test if token works and check scopes
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/user
```

The response headers will show what scopes your token has.

## Step 2: Create a New Token with Required Permissions

### Option A: Classic Personal Access Token (Recommended)

1. **Go to GitHub Settings:**
   - Visit: https://github.com/settings/tokens/new
   - Or: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)

2. **Configure Token:**
   - **Note**: Give it a descriptive name like "MCP GitHub Project Manager"
   - **Expiration**: Choose expiration (90 days, 1 year, or no expiration)
   - **Scopes**: Check the following boxes:
     - ✅ **repo** (Full control of private repositories)
       - This includes: repo:status, repo_deployment, public_repo, repo:invite, security_events
     - ✅ **project** (Full control of user projects)
     - ✅ **write:org** (Write org and team membership) - Only if using organization projects

3. **Generate Token:**
   - Click "Generate token" at the bottom
   - **IMPORTANT**: Copy the token immediately - you won't be able to see it again!

4. **Update Your Configuration:**
   - Update your `.env` file or MCP config with the new token:
   ```env
   GITHUB_TOKEN=your_new_token_here
   ```

### Option B: Fine-Grained Personal Access Token (New)

1. **Go to GitHub Settings:**
   - Visit: https://github.com/settings/tokens/new
   - Select "Fine-grained tokens" tab

2. **Configure Token:**
   - **Token name**: "MCP GitHub Project Manager"
   - **Expiration**: Choose expiration
   - **Repository access**: 
     - Select "Only select repositories" and choose your repository
     - Or "All repositories" if you want broader access
   
3. **Set Permissions:**
   - **Repository permissions**:
     - ✅ **Contents**: Read and write
     - ✅ **Issues**: Read and write
     - ✅ **Metadata**: Read (automatically selected)
     - ✅ **Pull requests**: Read and write (if needed)
   
   - **Account permissions**:
     - ✅ **Projects**: Read and write
     - ✅ **Organization permissions** (if using org projects):
       - ✅ **Projects**: Read and write

4. **Generate and Save Token**

## Step 3: Verify Token Permissions

After creating/updating your token, verify it works:

```bash
# Test repository access
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.github.com/repos/YOUR_OWNER/YOUR_REPO

# Test project access (GraphQL)
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "query { viewer { login } }"}' \
  https://api.github.com/graphql
```

## Step 4: Update Your MCP Configuration

Update your token in your MCP config file (e.g., `cursor-mcp-config.json`):

```json
{
  "mcpServers": {
    "github-project-manager": {
      "command": "python",
      "args": ["-m", "src"],
      "env": {
        "GITHUB_TOKEN": "your_new_token_here",
        "GITHUB_OWNER": "your_username",
        "GITHUB_REPO": "your_repo"
      }
    }
  }
}
```

## Troubleshooting

### Error: "Bad credentials"
- Token is invalid or expired
- Solution: Generate a new token

### Error: "Resource not accessible by integration"
- Token doesn't have required scopes
- Solution: Regenerate token with all required scopes

### Error: "GraphQL errors: Argument 'dataType'..."
- Token might not have `project` scope
- Solution: Ensure `project` scope is enabled

### Error: "Insufficient permissions"
- Token lacks write permissions
- Solution: Check that `repo` and `project` scopes include write access

## Security Best Practices

1. **Never commit tokens to git** - Use environment variables or config files excluded from git
2. **Use token expiration** - Set reasonable expiration dates
3. **Limit repository access** - Only grant access to repositories you need
4. **Rotate tokens regularly** - Generate new tokens periodically
5. **Use fine-grained tokens** - When possible, use fine-grained tokens for better security

## Quick Reference

- **Token Settings**: https://github.com/settings/tokens
- **Create Classic Token**: https://github.com/settings/tokens/new
- **Create Fine-Grained Token**: https://github.com/settings/tokens/new (select Fine-grained tab)
- **GitHub API Docs**: https://docs.github.com/en/rest
- **GraphQL API Docs**: https://docs.github.com/en/graphql


