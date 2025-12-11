#!/bin/bash
# Hook: Session Initialization
# Purpose: Initialize Claude Code session
# Trigger: When Claude starts

set -euo pipefail

echo "🚀 Initializing Claude Code session..."

# Create necessary directories
mkdir -p ~/.claude/{backups,logs,temp}

# Set up session log
SESSION_LOG="$HOME/.claude/logs/session_$(date +%Y%m%d_%H%M%S).log"
export CLAUDE_SESSION_LOG="$SESSION_LOG"

# Log session start
echo "Session started at $(date)" > "$SESSION_LOG"
echo "Working directory: $PWD" >> "$SESSION_LOG"

# Load project-specific environment
if [[ -f ".env" ]]; then
    echo "Loading .env file..."
    set -a
    source .env
    set +a
    echo ".env loaded" >> "$SESSION_LOG"
fi

# Activate virtual environment if exists
if [[ -f "venv/bin/activate" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "Virtual environment activated" >> "$SESSION_LOG"
elif [[ -f ".venv/bin/activate" ]]; then
    echo "Activating .venv..."
    source .venv/bin/activate
    echo ".venv activated" >> "$SESSION_LOG"
fi

# Check for git repository
if git rev-parse --git-dir >/dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
    REMOTE=$(git remote get-url origin 2>/dev/null || echo "no remote")
    echo "Git repository: $REMOTE ($BRANCH)" >> "$SESSION_LOG"
fi

# Display welcome message
if command -v figlet >/dev/null 2>&1; then
    figlet "Claude Code" 2>/dev/null || echo "Claude Code Ready"
else
    echo "Claude Code Ready"
fi

echo "Session initialized. Log: $SESSION_LOG"

exit 0