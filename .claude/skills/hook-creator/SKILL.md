---
name: hook-creator
description: Guide for creating Claude Code hooks - automation scripts that run at specific points during Claude's execution. Use this when users want to create hooks to automatically run commands, validate inputs, modify behavior, or integrate external tools.
license: Complete terms in LICENSE.txt
---

# Hook Creator

## Overview

This skill enables the creation of Claude Code hooks - powerful automation scripts that execute at specific points during Claude's execution lifecycle. Hooks allow you to automatically run commands, validate inputs, modify behavior, and integrate external tools seamlessly.

## Quick Start

### Choose Your Hook Type

**Tool-based Hooks**: Run scripts when specific tools are used
```bash
/claude/hooks add --tool bash --command 'echo "Running command: $BASH_COMMAND"' --before
```

**Event-based Hooks**: Trigger on specific events
```bash
/claude/hooks add --event session_start --command 'echo "Session started"'
```

**Slash Command Hooks**: Run custom scripts on slash commands
```bash
/claude/hooks add --slash mycommand --command './scripts/my_script.sh'
```

## Hook Types and Use Cases

### 1. Tool Execution Hooks
Monitor and modify tool execution

**Before Tool Hooks**:
- Validate command parameters
- Set up environment
- Log command intent
- Modify command arguments

**After Tool Hooks**:
- Process command output
- Clean up resources
- Notify external systems
- Aggregate results

### 2. Lifecycle Event Hooks
Respond to session and agent lifecycle events

**Session Hooks**:
- `session_start`: Initialize workspace
- `session_end`: Clean up and save state
- `agent_created`: Configure new agents
- `agent_destroyed`: Clean up agent resources

### 3. Slash Command Hooks
Create custom slash command behaviors

**Command Hooks**:
- Pre-process command arguments
- Execute custom validation
- Override default behavior
- Add custom commands

## Hook Configuration Structure

### Basic Hook Configuration
```yaml
# .claude/hooks.yaml
hooks:
  - name: "log-bash-commands"
    tool: "bash"
    event: "before"
    command: "echo '[$(date)] Running: $BASH_COMMAND' >> ~/.claude/bash_history.log"

  - name: "validate-git-repo"
    tool: "bash"
    event: "before"
    command: |
      if [[ "$BASH_COMMAND" == git* && "$PWD" != */.git* ]]; then
        if ! git rev-parse --git-dir > /dev/null 2>&1; then
          echo "Warning: Not in a git repository"
        fi
      fi

  - name: "session-initialization"
    event: "session_start"
    command: "source ~/.claude/session_init.sh"
```

### Advanced Hook Configuration
```yaml
hooks:
  - name: "code-quality-check"
    tool: "write"
    event: "after"
    command: |
      if [[ "$FILE_PATH" == *.py ]]; then
        python -m flake8 --max-line-length=100 "$FILE_PATH" || true
        python -m black --check "$FILE_PATH" || echo "Consider running 'black $FILE_PATH'"
      fi
    conditions:
      - file_extension: "py"
      - file_size: "< 100KB"
    timeout: 30

  - name: "security-scan"
    tool: "bash"
    event: "after"
    command: |
      if echo "$BASH_COMMAND" | grep -q "rm\|mv\|chmod"; then
        echo "⚠️  Potentially dangerous command detected"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
          exit 1
        fi
      fi
    interactive: true
```

## Hook Creation Workflow

### Step 1: Define Hook Purpose
Identify what you want to automate:
- **Validation**: Check inputs before execution
- **Transformation**: Modify data or commands
- **Notification**: Alert external systems
- **Logging**: Record activities for audit
- **Integration**: Connect with external tools

### Step 2: Choose Trigger Point
Select appropriate trigger:
- `before_tool`: Before any tool execution
- `after_tool`: After tool completion
- `session_start`: When Claude starts
- `session_end`: When Claude ends
- `slash_command`: On specific commands

### Step 3: Write Hook Script
Create efficient, focused scripts:

**Best Practices**:
- Use absolute paths when possible
- Handle errors gracefully
- Avoid interactive input (unless required)
- Keep execution time minimal
- Log meaningful information

**Script Template**:
```bash
#!/bin/bash
# Hook: [hook name]
# Purpose: [brief description]
# Trigger: [when this runs]

set -euo pipefail

# Environment variables available:
# $BASH_COMMAND - The command being executed
# $TOOL_NAME - Name of the tool being used
# $FILE_PATH - Path of file being operated on (if applicable)
# $CLAUDE_SESSION_ID - Current session identifier

# Your hook logic here
echo "[$(date)] Hook executed: $0"

exit 0
```

### Step 4: Configure Hook
Add to `.claude/hooks.yaml`:

```yaml
hooks:
  - name: "my-custom-hook"
    tool: "bash"  # or specific tool name
    event: "before"  # or "after"
    command: "/path/to/your/script.sh"
    enabled: true
```

## Template Hooks

### Logging Hook Template
```bash
#!/bin/bash
# .claude/hooks/logging.sh
LOG_FILE="$HOME/.claude/claude_activity.log"

mkdir -p "$(dirname "$LOG_FILE")"
echo "[$(date)] [$$] [$TOOL_NAME] $BASH_COMMAND" >> "$LOG_FILE"
```

### Git Safety Hook Template
```bash
#!/bin/bash
# .claude/hooks/git_safety.sh
if echo "$BASH_COMMAND" | grep -q "git push.*--force"; then
  echo "⚠️  Dangerous: Force push detected"
  echo "This will rewrite remote history. Consider using --force-with-lease"
  read -p "Proceed anyway? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Command cancelled for safety"
    exit 1
  fi
fi
```

### File Backup Hook Template
```bash
#!/bin/bash
# .claude/hooks/file_backup.sh
if [[ -n "$FILE_PATH" && -f "$FILE_PATH" ]]; then
  BACKUP_DIR="$HOME/.claude/backups/$(date +%Y-%m-%d)"
  mkdir -p "$BACKUP_DIR"
  cp "$FILE_PATH" "$BACKUP_DIR/$(basename "$FILE_PATH").$(date +%H%M%S).bak"
fi
```

### Environment Setup Hook Template
```bash
#!/bin/bash
# .claude/hooks/env_setup.sh
# Load project-specific environment
if [[ -f ".env" ]]; then
  set -a
  source .env
  set +a
fi

# Activate virtual environment if exists
if [[ -f "venv/bin/activate" ]]; then
  source venv/bin/activate
fi
```

## Managing Hooks

### List Active Hooks
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

## Advanced Features

### Conditional Hooks
Configure hooks to run only under specific conditions:

```yaml
hooks:
  - name: "python-format-check"
    tool: "write"
    event: "after"
    command: "black --check $FILE_PATH"
    conditions:
      file_extension: "py"
      file_path: "src/"
```

### Interactive Hooks
Hooks that require user input:

```yaml
hooks:
  - name: "confirm-deletion"
    tool: "bash"
    event: "before"
    command: "./scripts/confirm_rm.sh"
    interactive: true
    tools: ["bash"]
    match: "rm -rf"
```

### Chain Hooks
Create sequences of hooks:

```yaml
hooks:
  - name: "pre-build"
    event: "session_start"
    command: "./scripts/setup_build.sh"

  - name: "build"
    depends_on: "pre-build"
    command: "./scripts/build.sh"

  - name: "post-build"
    depends_on: "build"
    command: "./scripts/deploy.sh"
```

## Resources

### scripts/
Executable hook scripts and templates:
- `create_hook.py` - Python script to generate hook templates
- `validate_hook.py` - Validate hook configuration
- `test_hook.py` - Test hook functionality

### references/
Comprehensive hook documentation:
- `hook_api.md` - Complete API reference
- `examples.md` - Hook examples by use case
- `best_practices.md` - Hook development guidelines

### assets/
Hook templates and boilerplate:
- `templates/` - Ready-to-use hook templates
- `examples/` - Complete hook examples