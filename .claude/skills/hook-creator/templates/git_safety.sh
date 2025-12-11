#!/bin/bash
# Hook: Git Safety
# Purpose: Prevent dangerous git operations
# Trigger: Before bash execution

set -euo pipefail

# Check for dangerous git commands
if echo "$BASH_COMMAND" | grep -qE "(git push.*--force|git reset --hard|rm -rf)"; then
    echo "⚠️  Dangerous command detected:"
    echo "  $BASH_COMMAND"
    echo ""

    if echo "$BASH_COMMAND" | grep -q "git push.*--force"; then
        echo "This will rewrite remote history. Consider using:"
        echo "  git push --force-with-lease origin BRANCH_NAME"
    fi

    if echo "$BASH_COMMAND" | grep -q "git reset --hard"; then
        echo "This will discard all uncommitted changes."
    fi

    if echo "$BASH_COMMAND" | grep -q "rm -rf"; then
        echo "This will recursively delete files without confirmation."
    fi

    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Command cancelled for safety"
        exit 1
    fi
fi

exit 0