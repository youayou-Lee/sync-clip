#!/usr/bin/env python3
"""
Hook Creator - Generate Claude Code hooks interactively

Usage:
    python create_hook.py [options]

Examples:
    python create_hook.py --name logging --tool bash --event before
    python create_hook.py --interactive
"""

import argparse
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

HOOK_TYPES = {
    'before': 'Before tool execution',
    'after': 'After tool execution',
    'session_start': 'When Claude starts',
    'session_end': 'When Claude ends',
    'slash_command': 'On specific slash commands'
}

TOOLS = [
    'bash', 'write', 'read', 'edit', 'glob', 'grep', 'webfetch',
    'task', 'slashcommand', 'killshell', 'git'
]

def get_user_input(prompt, default=None):
    """Get user input with optional default value"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    response = input(full_prompt).strip()
    return response if response else default

def create_hook_script(name, description, event, tool=None, command=None):
    """Create a hook script file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    script_content = f'''#!/bin/bash
# Hook: {name}
# Purpose: {description}
# Created: {timestamp}
# Trigger: {event}{' for ' + tool if tool else ''}

set -euo pipefail

# Environment variables available:
# $BASH_COMMAND - The command being executed
# $TOOL_NAME - Name of the tool being used
# $FILE_PATH - Path of file being operated on (if applicable)
# $CLAUDE_SESSION_ID - Current session identifier
# $HOOK_NAME - Name of this hook

echo "[$(date)] Hook '$HOOK_NAME' triggered"

# Your custom logic here
'''

    if command:
        script_content += f'\n# Custom command\n{command}\n'

    script_content += '\nexit 0\n'

    return script_content

def create_hook_config(name, event, tool=None, script_path=None, command=None,
                      conditions=None, interactive=False, timeout=None):
    """Create hook configuration entry"""
    config = {
        'name': name,
        'event': event,
        'enabled': True
    }

    if tool:
        config['tool'] = tool

    if script_path:
        config['command'] = script_path
    elif command:
        config['command'] = command

    if conditions:
        config['conditions'] = conditions

    if interactive:
        config['interactive'] = True

    if timeout:
        config['timeout'] = timeout

    return config

def update_hooks_yaml(config, hooks_file='.claude/hooks.yaml'):
    """Update or create hooks.yaml file"""
    hooks_path = Path(hooks_file)
    hooks_path.parent.mkdir(exist_ok=True)

    # Load existing hooks if file exists
    if hooks_path.exists():
        with open(hooks_path, 'r') as f:
            hooks_config = yaml.safe_load(f) or {'hooks': []}
    else:
        hooks_config = {'hooks': []}

    # Check for existing hook with same name
    for i, hook in enumerate(hooks_config['hooks']):
        if hook['name'] == config['name']:
            print(f"Updating existing hook: {config['name']}")
            hooks_config['hooks'][i] = config
            break
    else:
        print(f"Adding new hook: {config['name']}")
        hooks_config['hooks'].append(config)

    # Write updated config
    with open(hooks_path, 'w') as f:
        yaml.dump(hooks_config, f, default_flow_style=False, indent=2)

    print(f"✅ Hook configuration saved to {hooks_file}")

def interactive_create():
    """Interactive hook creation"""
    print("=== Claude Code Hook Creator ===\n")

    name = get_user_input("Hook name")
    if not name:
        print("❌ Hook name is required")
        return 1

    description = get_user_input("Hook description")

    print("\nAvailable events:")
    for i, (event, desc) in enumerate(HOOK_TYPES.items(), 1):
        print(f"  {i}. {event}: {desc}")

    event_choice = get_user_input("Select event (1-5)", "1")
    try:
        event_index = int(event_choice) - 1
        event = list(HOOK_TYPES.keys())[event_index]
    except (ValueError, IndexError):
        event = 'before'

    use_tool = get_user_input("Hook to specific tool? (y/n)", "n").lower() == 'y'
    tool = None
    if use_tool:
        print("\nAvailable tools:")
        for i, t in enumerate(TOOLS, 1):
            print(f"  {i}. {t}")
        tool_choice = get_user_input("Select tool (1-{})".format(len(TOOLS)), "1")
        try:
            tool_index = int(tool_choice) - 1
            tool = TOOLS[tool_index]
        except (ValueError, IndexError):
            tool = 'bash'

    command_type = get_user_input("Command type (script/custom)", "script")

    if command_type == 'script':
        script_name = f"{name.replace('-', '_')}.sh"
        script_path = f".claude/hooks/{script_name}"
        command = None
    else:
        command = get_user_input("Custom command")
        script_path = None

    # Create script if needed
    if command_type == 'script':
        os.makedirs('.claude/hooks', exist_ok=True)
        script_content = create_hook_script(name, description, event, tool)

        with open(script_path, 'w') as f:
            f.write(script_content)

        os.chmod(script_path, 0o755)
        print(f"✅ Script created: {script_path}")

    # Create configuration
    config = create_hook_config(name, event, tool, script_path, command)

    # Ask for additional options
    if get_user_input("Add conditions? (y/n)", "n").lower() == 'y':
        conditions = {}
        if get_user_input("File extension filter? (y/n)", "n").lower() == 'y':
            ext = get_user_input("File extension (without dot)")
            conditions['file_extension'] = ext
        if conditions:
            config['conditions'] = conditions

    if get_user_input("Interactive hook? (y/n)", "n").lower() == 'y':
        config['interactive'] = True

    # Update hooks.yaml
    update_hooks_yaml(config)

    print(f"\n✅ Hook '{name}' created successfully!")
    return 0

def main():
    parser = argparse.ArgumentParser(description='Create Claude Code hooks')
    parser.add_argument('--name', help='Hook name')
    parser.add_argument('--description', help='Hook description')
    parser.add_argument('--event', choices=HOOK_TYPES.keys(), help='Hook event')
    parser.add_argument('--tool', choices=TOOLS, help='Tool to hook')
    parser.add_argument('--command', help='Command to execute')
    parser.add_argument('--script', help='Path to script file')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode')
    parser.add_argument('--hooks-file', default='.claude/hooks.yaml',
                       help='Path to hooks configuration file')

    args = parser.parse_args()

    if args.interactive or not args.name:
        return interactive_create()

    # Non-interactive mode
    if not args.name:
        print("❌ Hook name is required")
        return 1

    if not args.event:
        print("❌ Hook event is required")
        return 1

    config = create_hook_config(
        args.name,
        args.event,
        args.tool,
        args.script,
        args.command
    )

    update_hooks_yaml(config, args.hooks_file)
    print(f"✅ Hook '{args.name}' created successfully!")

    return 0

if __name__ == '__main__':
    sys.exit(main())