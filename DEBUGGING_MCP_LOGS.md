# Debugging MCP Server Logs

This guide explains how to check MCP server logs to debug argument serialization issues.

## Where Logs Are Written

The MCP server writes all logs to **stderr** (standard error). Cursor should capture these logs automatically.

## How to View Logs in Cursor

### Method 1: Check Cursor's MCP Output Panel

1. Open Cursor
2. Look for an **MCP** or **Output** panel (usually at the bottom)
3. Select the MCP server output channel
4. You should see debug messages prefixed with `[ToolValidator]` and `[MCP]`

### Method 2: Check Cursor's Developer Console

1. In Cursor, open the Developer Tools:
   - **Windows/Linux**: `Ctrl+Shift+I` or `F12`
   - **Mac**: `Cmd+Option+I`
2. Look for the **Console** tab
3. Filter for MCP-related messages

### Method 3: Run Server Manually (Advanced)

If you want to see logs directly in a terminal:

```bash
# Navigate to your project directory
cd D:\New folder\git_proj_manger_mcp

# Run the MCP server directly (this will show stderr output)
python -m src.__main__
```

## What to Look For

When you call `create_roadmap`, you should see logs like:

```
[ToolValidator] === Validating create_roadmap ===
[ToolValidator] Args type: <class 'dict'>
[ToolValidator] Args: {
  "project": {...},
  "milestones": [...]
}
[MCP] === Tool Call: create_roadmap ===
[MCP] Raw arguments type: <class 'dict'>
[MCP] Raw arguments: {...}
[MCP] Project type: <class 'str'>  <-- THIS IS THE PROBLEM!
[MCP] Project value: {'title': '...', ...}
```

## Key Information to Check

1. **Project Type**: Look for `Project type: <class 'str'>` - this indicates the project is being sent as a string
2. **Project Value**: Check what the actual value looks like
3. **Project repr**: The `repr()` output shows the exact representation

## Expected vs Actual

### Expected (Working):
```
Project type: <class 'dict'>
Project value: {'title': '...', 'visibility': 'private'}
```

### Actual (Current Issue):
```
Project type: <class 'str'>
Project value: "{'title': '...', 'visibility': 'private'}"
```

## What the Logs Will Show

The enhanced logging will show:

1. **Raw arguments received** from Cursor/MCP client
2. **Type of each argument** (dict, str, etc.)
3. **Value and representation** of nested structures
4. **Parsing attempts** and their results
5. **Validation errors** with full tracebacks

## Next Steps After Viewing Logs

Once you see the logs:

1. **If project is a string**: The MCP client (Cursor) is serializing nested dicts as strings
   - Solution: The parsing code should handle this (already implemented)
   - Check if `ast.literal_eval()` or `eval()` is working

2. **If project is a dict**: The issue is elsewhere
   - Check if Pydantic validation is the problem
   - Verify the dict structure matches the schema

3. **If project type is unexpected**: There might be a custom type
   - Check the `__dict__` or `__class__` attributes
   - See if it needs special handling

## Testing the Logging

To test the logging:

1. Restart the MCP server
2. Try creating a roadmap again:
   ```
   Create a roadmap for project "Test" with milestones: ...
   ```
3. Check the logs immediately after the call
4. Look for the debug messages starting with `[ToolValidator]` and `[MCP]`

## Log Format

All debug logs follow this format:
- `[ToolValidator]` - Messages from the validator
- `[MCP]` - Messages from the main server handler
- Error logs include full tracebacks

## Troubleshooting

If you don't see logs:

1. **Check Cursor settings**: Make sure MCP logging is enabled
2. **Check server is running**: Verify the MCP server is active
3. **Check log level**: Debug logs might be filtered out
4. **Try manual run**: Run the server manually to see direct output

## Example Log Output

Here's what you should see when debugging:

```
[MCP] === Tool Call: create_roadmap ===
[MCP] Raw arguments type: <class 'dict'>
[MCP] Raw arguments: {
  "project": "{'title': 'Test', 'visibility': 'private'}",
  "milestones": [...]
}
[MCP] Project type: <class 'str'>
[MCP] Project value: {'title': 'Test', 'visibility': 'private'}
[ToolValidator] === Validating create_roadmap ===
[ToolValidator] Args type: <class 'dict'>
[ToolValidator] === Processing create_roadmap ===
[ToolValidator] Project data type: <class 'str'>
[ToolValidator] Project data value: {'title': 'Test', 'visibility': 'private'}
[ToolValidator] Creating CreateRoadmapProject from dict: {'title': 'Test', 'visibility': 'private'}
[ToolValidator] Successfully created CreateRoadmapProject
```

This will help identify exactly where the issue occurs!





