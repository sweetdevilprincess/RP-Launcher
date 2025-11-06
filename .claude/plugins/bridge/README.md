# Claude Code Bridge Plugin

This plugin enables the Claude Code Bridge MCP server, which allows multiple Claude Code instances to coordinate their work across different git worktrees/branches.

## Purpose

When working on a large refactor with multiple parallel workstreams, this bridge allows different Claude instances to:
- Send messages to each other
- Share status updates
- Coordinate dependencies
- Avoid conflicts

## MCP Tools Provided

Once enabled, this plugin provides these tools:

1. **send_message** - Send a message to another Claude instance
   - `from_instance`: Your workstream identifier (e.g., "workstream-d")
   - `to_instance`: Target workstream identifier (e.g., "workstream-e")
   - `message`: Message content

2. **get_messages** - Receive messages for your instance
   - `instance`: Your workstream identifier

3. **clear_messages** - Mark messages as read
   - `instance`: Your workstream identifier

4. **update_status** - Share your work progress
   - `instance`: Your workstream identifier
   - `status`: Current status (e.g., "completed", "in-progress", "blocked")
   - `details`: Additional details object

5. **get_status** - Check another instance's status
   - `instance`: Instance identifier to query

6. **get_all_statuses** - See all instances at once

## Usage Example

```python
# From Workstream D (Automation Pipeline)
send_message(
    from_instance="workstream-d",
    to_instance="workstream-e",
    message="Completed BackgroundAgentStrategy. Ready for agent migration."
)

update_status(
    instance="workstream-d",
    status="completed",
    details={
        "components": ["CounterService", "TimeService", "AgentStrategies"],
        "tests_passing": True
    }
)

# From Workstream E (Agent System)
get_messages(instance="workstream-e")
get_status(instance="workstream-d")
```

## Shared State

All instances share state through:
```
C:\Users\green\Desktop\RP_Claude_Code_Bridge\shared_state.json
```

This file contains:
- `messages`: Array of inter-instance messages
- `status`: Object mapping instance names to their current status

## Activation

1. Restart Claude Code after creating this plugin
2. The MCP server should auto-start with the plugin
3. Verify with `/mcp` command in Claude Code
4. Look for tools prefixed with `mcp__claude_code_bridge__`

## Troubleshooting

If the MCP server doesn't appear:
- Ensure Python is in your PATH
- Verify the MCP Python SDK is installed: `pip install mcp`
- Check Claude Code logs for errors
- Try `/doctor` command to diagnose issues
