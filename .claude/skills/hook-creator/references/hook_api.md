# Claude Code Hooks API Reference

This document provides a comprehensive reference for Claude Code hooks API.

## Hook Configuration Schema

```yaml
hooks:
  - name: string           # Required: Unique hook identifier
    event: string          # Required: Event type (see Events section)
    command: string        # Required: Command or script to execute
    tool: string           # Optional: Tool name to filter on
    enabled: boolean       # Optional: Enable/disable hook (default: true)
    interactive: boolean   # Optional: Allow user interaction (default: false)
    timeout: integer       # Optional: Timeout in seconds (default: 30)
    conditions: object     # Optional: Execution conditions
    depends_on: string     # Optional: Name of prerequisite hook
```

## Events

### Tool Events
- `before`: Before tool execution
- `after`: After tool completion

### Lifecycle Events
- `session_start`: When Claude initializes
- `session_end`: When Claude shuts down
- `agent_created`: When a new agent is created
- `agent_destroyed`: When an agent is destroyed

### Command Events
- `slash_command`: When slash commands are executed

## Environment Variables

Hooks have access to the following environment variables:

```bash
BASH_COMMAND      # The command being executed (bash hooks only)
TOOL_NAME         # Name of the tool being used
FILE_PATH         # Path of file being operated on (if applicable)
CLAUDE_SESSION_ID # Current session identifier
HOOK_NAME         # Name of the current hook
PWD               # Current working directory
HOME              # User home directory
```

## Supported Tools

- `bash` - Shell command execution
- `write` - File writing operations
- `read` - File reading operations
- `edit` - File editing operations
- `glob` - File pattern matching
- `grep` - Text searching
- `webfetch` - Web content fetching
- `task` - Task agent execution
- `slashcommand` - Slash command execution
- `killshell` - Shell termination
- `git` - Git operations
- `mcp` - MCP server operations

## Conditions

Hooks can be conditionally executed based on:

### File Conditions
```yaml
conditions:
  file_extension: "py"        # File extension (without dot)
  file_path: "src/"           # Path pattern
  file_size: "< 1MB"          # Size comparison
```

### Tool Conditions
```yaml
conditions:
  tool: "bash"                # Specific tool name
  tools: ["bash", "write"]    # Multiple tools
```

### Command Pattern Matching
```yaml
conditions:
  match: "git push"          # Command pattern
  match_regex: "^git.*"      # Regular expression
```

## Hook Return Codes

Hooks should follow these return code conventions:

- `0` - Success (continue execution)
- `1` - Error/Warning (may halt execution depending on context)
- `2` - Skipped (hook didn't apply)

## Security Considerations

### Input Validation
Always validate input parameters in hooks:

```bash
#!/bin/bash
# Validate file path
if [[ "$FILE_PATH" =~ \.\./ ]]; then
    echo "Error: Directory traversal detected"
    exit 1
fi
```

### Command Injection Prevention
Use proper quoting and validation:

```bash
#!/bin/bash
# Safe parameter handling
if [[ -n "${FILE_PATH:-}" && -f "$FILE_PATH" ]]; then
    # Validate file is within allowed directory
    REAL_PATH=$(realpath "$FILE_PATH")
    if [[ "$REAL_PATH" != "$PWD"* ]]; then
        echo "Error: File outside working directory"
        exit 1
    fi
fi
```

### Resource Limits
Set appropriate timeouts and resource limits:

```yaml
hooks:
  - name: "long-running-hook"
    command: "./scripts/safe_script.sh"
    timeout: 60
    enabled: true
```

## Error Handling

### Graceful Degradation
Hooks should fail gracefully:

```bash
#!/bin/bash
# Check for required tools
if ! command -v flake8 >/dev/null 2>&1; then
    echo "Warning: flake8 not installed, skipping check"
    exit 0
fi

# Run with error handling
if ! flake8 "$FILE_PATH"; then
    echo "Code quality issues found" >&2
    # Don't exit with error code, just warn
    exit 0
fi
```

### Logging
Implement proper logging for debugging:

```bash
#!/bin/bash
LOG_FILE="$HOME/.claude/logs/hook_debug.log"

log_message() {
    echo "[$(date)] $HOOK_NAME: $1" >> "$LOG_FILE"
}

log_message "Hook started with FILE_PATH=${FILE_PATH:-none}"
```

## Performance Considerations

### Fast Execution
Keep hooks fast to avoid slowing down Claude:

- Use absolute paths for commands
- Avoid expensive operations in before hooks
- Cache results when possible

### Resource Management
Clean up resources properly:

```bash
#!/bin/bash
# Create temporary file
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# Use temporary file
echo "data" > "$TEMP_FILE"

# Script will automatically clean up on exit
```

## Testing Hooks

### Manual Testing
Test hooks manually:

```bash
# Set up test environment
export BASH_COMMAND="echo test"
export TOOL_NAME="bash"
export FILE_PATH="/tmp/test.py"

# Run hook
./my-hook.sh
```

### Dry Run Mode
Implement dry run functionality:

```bash
#!/bin/bash
if [[ "${DRY_RUN:-}" == "true" ]]; then
    echo "[DRY RUN] Would execute: $COMMAND"
    exit 0
fi

# Actual execution
$COMMAND
```

## Hook Management Commands

### List Hooks
```bash
/claude/hooks list
```

### Enable/Disable Hooks
```bash
/claude/hooks enable hook-name
/claude/hooks disable hook-name
```

### Test Hooks
```bash
/claude/hooks test hook-name --dry-run
/claude/hooks test hook-name --tool bash --command "echo test"
```

### Remove Hooks
```bash
/claude/hooks remove hook-name
```