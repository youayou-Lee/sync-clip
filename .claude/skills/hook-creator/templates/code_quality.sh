#!/bin/bash
# Hook: Code Quality Check
# Purpose: Run code quality checks after file writes
# Trigger: After file write operations

set -euo pipefail

# Only check certain file types
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

extension="${FILE_PATH##*.}"

case "$extension" in
    py)
        echo "🔍 Running Python quality checks..."

        # Run flake8 if available
        if command -v flake8 >/dev/null 2>&1; then
            flake8 --max-line-length=100 "$FILE_PATH" || echo "⚠️  Flake8 issues found"
        fi

        # Check with black
        if command -v black >/dev/null 2>&1; then
            if ! black --check "$FILE_PATH" >/dev/null 2>&1; then
                echo "💡 Suggestion: Run 'black $FILE_PATH' to format"
            fi
        fi

        # Check with pylint if available
        if command -v pylint >/dev/null 2>&1; then
            pylint --score=no "$FILE_PATH" 2>/dev/null | head -20 || true
        fi
        ;;

    js|ts|jsx|tsx)
        echo "🔍 Running JavaScript/TypeScript quality checks..."

        # ESLint check
        if [[ -f "package.json" ]] && command -v eslint >/dev/null 2>&1; then
            if npm run lint --silent >/dev/null 2>&1; then
                eslint "$FILE_PATH" 2>/dev/null || echo "⚠️  ESLint issues found"
            fi
        fi
        ;;

    go)
        echo "🔍 Running Go quality checks..."

        # gofmt check
        if ! gofmt -l "$FILE_PATH" | grep -q .; then
            echo "💡 Suggestion: Run 'gofmt -w $FILE_PATH' to format"
        fi

        # go vet
        if command -v go >/dev/null 2>&1; then
            go vet "./$(dirname "$FILE_PATH")" 2>/dev/null || echo "⚠️  Go vet issues found"
        fi
        ;;
esac

exit 0