#!/bin/bash
# Hook: Pre-commit Project Code Quality Check
# Purpose: Check only project code (not .claude directory) before git commits
# Trigger: Before bash git commit commands

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_FILES_PATTERN="\.py$"
BLACK_LINE_LENGTH=100
MAX_FILE_SIZE_MB=5
PROJECT_DIRS="src/ main.py"  # Only check these directories/files

echo -e "${BLUE}🔍 Running pre-commit project code quality checks...${NC}"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if command exists (with uv fallback)
command_exists() {
    command -v "$1" >/dev/null 2>&1 || uv run which "$1" >/dev/null 2>&1
}

# Function to run a tool (with uv fallback)
run_tool() {
    local tool=$1
    shift

    if command -v "$tool" >/dev/null 2>&1; then
        "$tool" "$@"
    else
        uv run "$tool" "$@"
    fi
}

# Function to get staged Python files in project directories
get_staged_project_python_files() {
    git diff --cached --name-only --diff-filter=ACM | grep -E "$PYTHON_FILES_PATTERN" | grep -v "^\.claude/" || true
}

# Function to check file size
check_file_size() {
    local file=$1
    local size_bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
    local size_mb=$((size_bytes / 1024 / 1024))

    if [[ $size_mb -gt $MAX_FILE_SIZE_MB ]]; then
        print_status "$RED" "❌ File $file is too large (${size_mb}MB > ${MAX_FILE_SIZE_MB}MB)"
        return 1
    fi
    return 0
}

# Get staged Python files in project directories
staged_files=$(get_staged_project_python_files)

if [[ -z "$staged_files" ]]; then
    print_status "$GREEN" "✅ No project Python files staged for commit"
    exit 0
fi

print_status "$BLUE" "📝 Checking project Python files:"
for file in $staged_files; do
    echo "  - $file"
done

# Check file sizes
print_status "$BLUE" "📏 Checking file sizes..."
large_files_found=false
for file in $staged_files; do
    if ! check_file_size "$file"; then
        large_files_found=true
    fi
done

if [[ "$large_files_found" == true ]]; then
    print_status "$RED" "❌ Some files are too large"
    exit 1
fi

# Check for required tools
tools_missing=false

if ! command_exists black; then
    print_status "$YELLOW" "⚠️  black not found. Install with: uv add black"
    tools_missing=true
fi

if ! command_exists flake8; then
    print_status "$YELLOW" "⚠️  flake8 not found. Install with: uv add flake8"
    tools_missing=true
fi

if ! command_exists isort; then
    print_status "$YELLOW" "⚠️  isort not found. Install with: uv add isort"
    tools_missing=true
fi

if [[ "$tools_missing" == true ]]; then
    print_status "$RED" "❌ Required code quality tools are missing"
    exit 1
fi

# Store original state for rollback
print_status "$BLUE" "💾 Creating backup of staged files..."
backup_dir=$(mktemp -d)
trap "rm -rf $backup_dir" EXIT

for file in $staged_files; do
    if [[ -f "$file" ]]; then
        cp "$file" "$backup_dir/"
    fi
done

# Run black formatter
print_status "$BLUE" "🎨 Running black formatter..."
black_failed=false

for file in $staged_files; do
    if [[ -f "$file" ]]; then
        if ! run_tool black --check --line-length=$BLACK_LINE_LENGTH "$file" 2>/dev/null; then
            print_status "$YELLOW" "⚠️  $file needs formatting"
            black_failed=true
        fi
    fi
done

if [[ "$black_failed" == true ]]; then
    print_status "$YELLOW" "🔧 Running black to format files..."

    # Format files and stage changes
    for file in $staged_files; do
        if [[ -f "$file" ]]; then
            run_tool black --line-length=$BLACK_LINE_LENGTH "$file"
            git add "$file"
        fi
    done

    print_status "$GREEN" "✅ Files formatted with black and re-staged"
else
    print_status "$GREEN" "✅ All files are properly formatted with black"
fi

# Run isort
print_status "$BLUE" "📚 Running isort..."
isort_failed=false

for file in $staged_files; do
    if [[ -f "$file" ]]; then
        if ! run_tool isort --check-only "$file" 2>/dev/null; then
            print_status "$YELLOW" "⚠️  $file needs import sorting"
            isort_failed=true
        fi
    fi
done

if [[ "$isort_failed" == true ]]; then
    print_status "$YELLOW" "🔧 Running isort to sort imports..."

    # Sort imports and stage changes
    for file in $staged_files; do
        if [[ -f "$file" ]]; then
            run_tool isort "$file"
            git add "$file"
        fi
    done

    print_status "$GREEN" "✅ Imports sorted with isort and re-staged"
else
    print_status "$GREEN" "✅ All imports are properly sorted"
fi

# Run flake8
print_status "$BLUE" "🔍 Running flake8 linting..."
flake8_failed=false

# Create a temporary file for flake8 output
flake8_output=$(mktemp)
trap "rm -f $flake8_output" EXIT

# Run flake8 on all staged files
for file in $staged_files; do
    if [[ -f "$file" ]]; then
        if ! run_tool flake8 --max-line-length=$BLACK_LINE_LENGTH --ignore=E203,W503 "$file" 2>"$flake8_output"; then
            print_status "$RED" "❌ Flake8 found issues in $file:"
            cat "$flake8_output" | sed 's/^/    /'
            flake8_failed=true
            rm "$flake8_output"
            flake8_output=$(mktemp)
        fi
    fi
done

if [[ "$flake8_failed" == true ]]; then
    print_status "$RED" ""
    print_status "$RED" "❌ Flake8 checks failed. Please fix the issues above before committing."
    exit 1
else
    print_status "$GREEN" "✅ All files passed flake8 checks"
fi

# Additional syntax check
print_status "$BLUE" "🐍 Running Python syntax check..."
syntax_failed=false

for file in $staged_files; do
    if [[ -f "$file" ]]; then
        if ! uv run python -m py_compile "$file" 2>/dev/null; then
            print_status "$RED" "❌ Syntax error in $file"
            syntax_failed=true
        fi
    fi
done

if [[ "$syntax_failed" == true ]]; then
    print_status "$RED" "❌ Python syntax check failed"
    exit 1
else
    print_status "$GREEN" "✅ All files have valid Python syntax"
fi

# Final summary
print_status "$GREEN" ""
print_status "$GREEN" "🎉 All project code quality checks passed!"
print_status "$GREEN" "✅ Your project code is ready to commit"

exit 0