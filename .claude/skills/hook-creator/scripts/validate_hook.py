#!/usr/bin/env python3
"""
Hook Validator - Validate Claude Code hook configurations

Usage:
    python validate_hook.py [--file hooks.yaml] [--hook-name name]
"""

import argparse
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

VALID_EVENTS = [
    'before', 'after', 'session_start', 'session_end',
    'slash_command', 'agent_created', 'agent_destroyed'
]

VALID_TOOLS = [
    'bash', 'write', 'read', 'edit', 'glob', 'grep', 'webfetch',
    'task', 'slashcommand', 'killshell', 'git', 'mcp'
]

class HookValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_hooks_file(self, hooks_file: str) -> bool:
        """Validate a hooks.yaml file"""
        if not os.path.exists(hooks_file):
            self.errors.append(f"Hooks file not found: {hooks_file}")
            return False

        try:
            with open(hooks_file, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in {hooks_file}: {e}")
            return False

        if not isinstance(config, dict):
            self.errors.append(f"Root of {hooks_file} must be a dictionary")
            return False

        if 'hooks' not in config:
            self.errors.append(f"Missing 'hooks' section in {hooks_file}")
            return False

        if not isinstance(config['hooks'], list):
            self.errors.append(f"'hooks' must be a list in {hooks_file}")
            return False

        hooks = config['hooks']
        if not hooks:
            self.warnings.append(f"No hooks defined in {hooks_file}")
            return True

        for i, hook in enumerate(hooks):
            self.validate_hook(hook, f"{hooks_file}[{i}]")

        return len(self.errors) == 0

    def validate_hook(self, hook: Dict[str, Any], path: str):
        """Validate a single hook configuration"""
        if not isinstance(hook, dict):
            self.errors.append(f"{path}: Hook must be a dictionary")
            return

        # Required fields
        if 'name' not in hook:
            self.errors.append(f"{path}: Missing required field 'name'")
        else:
            if not isinstance(hook['name'], str) or not hook['name'].strip():
                self.errors.append(f"{path}: 'name' must be a non-empty string")

        if 'event' not in hook:
            self.errors.append(f"{path}: Missing required field 'event'")
        elif hook['event'] not in VALID_EVENTS:
            self.errors.append(f"{path}: Invalid event '{hook['event']}'. Valid: {VALID_EVENTS}")

        # Command/script validation
        if 'command' not in hook:
            self.errors.append(f"{path}: Missing required field 'command'")
        else:
            if not isinstance(hook['command'], str):
                self.errors.append(f"{path}: 'command' must be a string")
            else:
                # Check if command is a file path
                if hook['command'].startswith('./') or hook['command'].startswith('/'):
                    if not os.path.exists(hook['command']):
                        self.errors.append(f"{path}: Command script not found: {hook['command']}")
                    elif not os.access(hook['command'], os.X_OK):
                        self.warnings.append(f"{path}: Command script not executable: {hook['command']}")

        # Optional field validation
        if 'tool' in hook:
            if hook['tool'] not in VALID_TOOLS:
                self.errors.append(f"{path}: Invalid tool '{hook['tool']}'. Valid: {VALID_TOOLS}")

        if 'enabled' in hook and not isinstance(hook['enabled'], bool):
            self.errors.append(f"{path}: 'enabled' must be a boolean")

        if 'timeout' in hook:
            try:
                timeout = int(hook['timeout'])
                if timeout <= 0:
                    self.errors.append(f"{path}: 'timeout' must be positive")
                elif timeout > 300:
                    self.warnings.append(f"{path}: 'timeout' ({timeout}s) is very long")
            except ValueError:
                self.errors.append(f"{path}: 'timeout' must be an integer")

        # Conditions validation
        if 'conditions' in hook:
            if not isinstance(hook['conditions'], dict):
                self.errors.append(f"{path}: 'conditions' must be a dictionary")
            else:
                self.validate_conditions(hook['conditions'], f"{path}.conditions")

    def validate_conditions(self, conditions: Dict[str, Any], path: str):
        """Validate hook conditions"""
        for condition, value in conditions.items():
            if condition == 'file_extension':
                if not isinstance(value, str):
                    self.errors.append(f"{path}: 'file_extension' must be a string")
                elif value.startswith('.'):
                    self.warnings.append(f"{path}: 'file_extension' should not include dot")

            elif condition == 'file_path':
                if not isinstance(value, str):
                    self.errors.append(f"{path}: 'file_path' must be a string")

            elif condition == 'file_size':
                if not isinstance(value, str):
                    self.errors.append(f"{path}: 'file_size' must be a string")
                else:
                    # Validate size format (e.g., "100KB", "1MB")
                    import re
                    if not re.match(r'^\d+[KMGT]?B$', value, re.IGNORECASE):
                        self.errors.append(f"{path}: 'file_size' format invalid. Use: 100KB, 1MB, etc")

            else:
                self.warnings.append(f"{path}: Unknown condition '{condition}'")

    def print_results(self):
        """Print validation results"""
        if self.errors:
            print("❌ Validation errors found:")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("✅ Hook configuration is valid")

def main():
    parser = argparse.ArgumentParser(description='Validate Claude Code hook configurations')
    parser.add_argument('--file', '-f', default='.claude/hooks.yaml',
                       help='Path to hooks configuration file')
    parser.add_argument('--hook-name', '-n',
                       help='Validate only specific hook name')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    validator = HookValidator()

    if not validator.validate_hooks_file(args.file):
        sys.exit(1)

    validator.print_results()

    if validator.errors:
        sys.exit(1)
    elif validator.warnings:
        sys.exit(2)  # Warning exit code
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()