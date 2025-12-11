#!/bin/bash
# Hook: Activity Logging
# Purpose: Log Claude Code activity for audit and debugging
# Trigger: Before tool execution

set -euo pipefail

# Configuration
LOG_DIR="$HOME/.claude/logs"
LOG_FILE="$LOG_DIR/claude_activity_$(date +%Y%m%d).log"
MAX_LOG_SIZE="10M"

# Create log directory if needed
mkdir -p "$LOG_DIR"

# Rotate log if too large
if [[ -f "$LOG_FILE" ]]; then
    if [[ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE") -gt 10485760 ]]; then
        mv "$LOG_FILE" "$LOG_FILE.$(date +%H%M%S)"
    fi
fi

# Get additional context
if [[ -n "${FILE_PATH:-}" ]]; then
    FILE_INFO=" file=$FILE_PATH"
else
    FILE_INFO=""
fi

# Log the activity
log_entry="[$(date '+%Y-%m-%d %H:%M:%S')] [$$] [${TOOL_NAME:-unknown}]$FILE_INFO $BASH_COMMAND"

echo "$log_entry" >> "$LOG_FILE"

# Also log to stdout for visibility (comment out if too verbose)
# echo "📝 $log_entry"

exit 0