#!/usr/bin/env python3
"""
Script to package the cross-platform-dev skill into a distributable .skill file.
"""

import os
import sys
import zipfile
import tempfile
import shutil
from pathlib import Path

def validate_skill(skill_path):
    """Validate that the skill meets all requirements"""
    errors = []

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md is required")
    else:
        # Validate frontmatter
        content = skill_md.read_text()
        if not content.startswith('---'):
            errors.append("SKILL.md must have YAML frontmatter")
        else:
            # Extract frontmatter
            try:
                end_idx = content.find('---', 3)
                if end_idx == -1:
                    errors.append("SKILL.md frontmatter must be closed with ---")
                else:
                    frontmatter = content[3:end_idx]
                    if 'name:' not in frontmatter:
                        errors.append("SKILL.md frontmatter must include name")
                    if 'description:' not in frontmatter:
                        errors.append("SKILL.md frontmatter must include description")
            except Exception as e:
                errors.append(f"Error parsing SKILL.md frontmatter: {e}")

    # Check directory structure
    required_dirs = ['scripts', 'references', 'assets']
    for dir_name in required_dirs:
        dir_path = skill_path / dir_name
        if not dir_path.exists():
            print(f"Warning: Optional directory {dir_name} does not exist")

    # Check for required files
    required_files = [
        'scripts/init_cross_platform_project.py'
    ]

    for file_path in required_files:
        full_path = skill_path / file_path
        if not full_path.exists():
            errors.append(f"Required file {file_path} does not exist")

    # Check for unwanted files
    unwanted_patterns = [
        '.git',
        '__pycache__',
        '.DS_Store',
        'Thumbs.db',
        '*.pyc',
        '.pyo'
    ]

    for pattern in unwanted_patterns:
        for path in skill_path.rglob(pattern):
            if path.is_file() and path.name.endswith('.pyc'):
                errors.append(f"Unwanted file found: {path}")

    return errors

def package_skill(skill_path, output_dir=None):
    """Package the skill into a .skill file"""

    # Validate skill first
    errors = validate_skill(skill_path)
    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"  - {error}")
        return False

    # Get skill name from SKILL.md
    skill_md = skill_path / "SKILL.md"
    content = skill_md.read_text()
    start_idx = content.find('name:') + 5
    end_idx = content.find('\n', start_idx)
    skill_name = content[start_idx:end_idx].strip()

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_skill_dir = Path(temp_dir) / skill_name
        temp_skill_dir.mkdir()

        # Copy all files except unwanted ones
        exclude_patterns = {
            '.git', '__pycache__', '.DS_Store', 'Thumbs.db',
            '*.pyc', '*.pyo', '.gitignore'
        }

        for item in skill_path.rglob('*'):
            if item.name in exclude_patterns or item.suffix in ['.pyc', '.pyo']:
                continue

            if item.is_file():
                # Create relative path
                rel_path = item.relative_to(skill_path)
                dest_path = temp_skill_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)

        # Create zip file
        if output_dir:
            output_path = Path(output_dir) / f"{skill_name}.skill"
        else:
            output_path = skill_path.parent / f"{skill_name}.skill"

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_skill_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_skill_dir)
                    zipf.write(file_path, arcname)

    print(f"✅ Skill successfully packaged: {output_path}")
    return True

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Package cross-platform-dev skill")
    parser.add_argument("skill_path", nargs="?",
                       default="/home/you/cs/code/ai/sync_clip/.claude/skills/cross-platform-dev",
                       help="Path to skill directory")
    parser.add_argument("--output", "-o",
                       help="Output directory for the .skill file")

    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not skill_path.exists():
        print(f"❌ Skill path does not exist: {skill_path}")
        sys.exit(1)

    if not skill_path.is_dir():
        print(f"❌ Skill path is not a directory: {skill_path}")
        sys.exit(1)

    success = package_skill(skill_path, args.output)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()