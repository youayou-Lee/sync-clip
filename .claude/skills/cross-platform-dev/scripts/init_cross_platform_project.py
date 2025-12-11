#!/usr/bin/env python3
"""
Cross-platform project initialization script.
Creates standard project directory structure and initial files.
"""

import os
import sys
import argparse
from pathlib import Path

def create_project_structure(project_name, language="python"):
    """Create project directory structure"""
    base_dirs = [
        "src",
        "src/core",
        "src/interfaces",
        "src/platforms",
        "src/platforms/windows",
        "src/platforms/linux",
        "src/platforms/macos",
        "src/ui",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "docs",
        "scripts",
        "config",
        "build",
        "dist"
    ]

    # Create directories
    for dir_path in base_dirs:
        (Path(project_name) / dir_path).mkdir(parents=True, exist_ok=True)

    # Create __init__.py files for Python projects
    if language == "python":
        for root, dirs, files in os.walk(f"{project_name}/src"):
            for dir_name in dirs:
                init_file = Path(root) / dir_name / "__init__.py"
                if not init_file.exists():
                    init_file.touch()

    # Create initial files
    files_to_create = {
        "README.md": readme_template(project_name),
        ".gitignore": gitignore_template(language),
        "requirements.txt": "# Requirements\n",
        "requirements-dev.txt": dev_requirements_template(language),
        "setup.py": setup_template(project_name, language) if language == "python" else "",
        "pyproject.toml": pyproject_template(project_name) if language == "python" else "",
        "Makefile": makefile_template(language),
        ".editorconfig": editorconfig_template(),
        "config/config.yaml": config_template(),
        "tests/conftest.py": conftest_template() if language == "python" else "",
        ".github/workflows/ci.yml": github_actions_template(language),
    }

    for file_path, content in files_to_create.items():
        full_path = Path(project_name) / file_path
        if content and not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

    print(f"✅ Project '{project_name}' initialized successfully!")
    print("\nNext steps:")
    print(f"1. cd {project_name}")
    print("2. Edit README.md and configuration files")
    print("3. Start developing your cross-platform application")

def readme_template(name):
    return f"""# {name}

## Description

[Project description]

## Features

- [Feature 1]
- [Feature 2]
- [Feature 3]

## Supported Platforms

- Windows 10/11
- Linux (Ubuntu 18.04+)
- macOS 10.15+

## Installation

### Windows

```powershell
pip install {name}
```

### Linux/macOS

```bash
pip install {name}
```

## Usage

```python
from {name} import main

main()
```

## Development

```bash
# Clone repository
git clone https://github.com/username/{name}.git
cd {name}

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\\Scripts\\activate  # Windows

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

## License

MIT License
"""

def gitignore_template(language):
    base_ignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
config/local.yaml
build/
dist/
"""

    if language == "node":
        base_ignore += """
# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
"""
    elif language == "go":
        base_ignore += """
# Go
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
vendor/
"""
    elif language == "rust":
        base_ignore += """
# Rust
/target/
Cargo.lock
**/*.rs.bk
"""

    return base_ignore

def dev_requirements_template(language):
    if language == "python":
        return """pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
black>=22.0.0
flake8>=5.0.0
mypy>=1.0.0
pre-commit>=2.20.0
"""
    elif language == "node":
        return """jest
eslint
prettier
@types/node
"""
    elif language == "go":
        return """golangci-lint
gotestsum
"""
    elif language == "rust":
        return """cargo-nextest
cargo-audit
cargo-deny
"""
    return "# Development requirements\n"

def setup_template(name, language):
    return f'''"""
{ name } setup script
"""

from setuptools import setup, find_packages

setup(
    name="{name}",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    install_requires=[
        # Add your dependencies here
    ],
    extras_require={{
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
        ]
    }},
    entry_points={{
        "console_scripts": [
            "{name}={name}.main:main",
        ],
    }},
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
'''

def pyproject_template(name):
    return f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = ""
authors = [
    {{name = "Your Name", email = "your.email@example.com"}},
]
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
'''

def makefile_template(language):
    if language == "python":
        return """.PHONY: install install-dev test lint format clean build run

install:
	pip install -e .

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -v --cov=src

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

lint:
	flake8 src tests
	mypy src

format:
	black src tests
	isort src tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

run:
	python -m src.main

dev-run:
	python -m src.main --debug
"""
    elif language == "node":
        return """.PHONY: install install-dev test lint build run

install:
	npm install

install-dev:
	npm install --dev

test:
	npm test

test-integration:
	npm run test:integration

test-e2e:
	npm run test:e2e

lint:
	npm run lint

format:
	npm run format

clean:
	rm -rf dist/
	rm -rf node_modules/

build:
	npm run build

run:
	npm start

dev-run:
	npm run dev
"""
    elif language == "go":
        return """.PHONY: install test lint build run clean

install:
	go mod download

test:
	go test -v ./...

test-integration:
	go test -v -tags=integration ./...

lint:
	golangci-lint run

build:
	go build -o bin/$(shell basename $$(pwd)) ./cmd/main.go

run:
	go run ./cmd/main.go

clean:
	rm -rf bin/
	go clean -cache
"""
    return "# Makefile for build automation\n"

def editorconfig_template():
    return """root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.json]
indent_style = space
indent_size = 2

[Makefile]
indent_style = tab

[*.go]
indent_style = tab

[*.rs]
indent_style = space
indent_size = 4
"""

def config_template():
    return """# Application configuration
app:
  name: "MyApp"
  version: "1.0.0"
  debug: false

# Platform-specific configuration
platform:
  windows:
    service_name: ""
    install_path: "C:\\Program Files\\MyApp"
    registry_key: "HKLM\\Software\\MyApp"
  linux:
    systemd_service: "myapp.service"
    config_path: "/etc/myapp"
    log_path: "/var/log/myapp"
  macos:
    bundle_id: "com.example.myapp"
    plist_path: "~/Library/LaunchAgents/com.example.myapp.plist"

# Logging configuration
logging:
  level: "INFO"
  file: "app.log"
  max_size: "10MB"
  backup_count: 5
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Network configuration
network:
  host: "0.0.0.0"
  port: 8080
  timeout: 30
  retries: 3
"""

def conftest_template():
    return """import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def test_config():
    \"\"\"Test configuration fixture\"\"\"
    return {
        "app": {"name": "TestApp", "debug": True},
        "logging": {"level": "DEBUG"},
        "platform": {
            "windows": {"install_path": "C:\\TestApp"},
            "linux": {"config_path": "/tmp/testapp"},
            "macos": {"bundle_id": "com.testapp"}
        }
    }

@pytest.fixture
def temp_dir(tmp_path):
    \"\"\"Temporary directory fixture\"\"\"
    return tmp_path

@pytest.fixture
def mock_platform():
    \"\"\"Mock platform detection\"\"\"
    with Mock() as mock_platform:
        mock_platform.system.return_value = "Linux"
        mock_platform.release.return_value = "5.4.0"
        mock_platform.machine.return_value = "x86_64"
        yield mock_platform

@pytest.fixture
def mock_os_functions():
    \"\"\"Mock OS-specific functions\"\"\"
    with Mock() as mock_os:
        mock_os.path.join.side_effect = lambda *args: "/".join(args)
        mock_os.path.expanduser.return_value = "/home/test"
        yield mock_os
"""

def github_actions_template(language):
    if language == "python":
        return """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.8, 3.9, '3.10', 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt

    - name: Lint with flake8
      run: |
        flake8 src tests

    - name: Type check with mypy
      run: |
        mypy src

    - name: Test with pytest
      run: |
        pytest tests/ -v --cov=src

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
"""
    elif language == "node":
        return """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [16.x, 18.x, 20.x]

    steps:
    - uses: actions/checkout@v3

    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run tests
      run: npm test

    - name: Run linting
      run: npm run lint
"""
    elif language == "go":
        return """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        go-version: [1.19, 1.20, 1.21]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: ${{ matrix.go-version }}

    - name: Download dependencies
      run: go mod download

    - name: Run tests
      run: go test -v ./...

    - name: Run linter
      uses: golangci/golangci-lint-action@v3
"""
    elif language == "rust":
        return """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        rust: [stable, beta, nightly]

    steps:
    - uses: actions/checkout@v3

    - name: Install Rust
      uses: dtolnay/rust-toolchain@master
      with:
        toolchain: ${{ matrix.rust }}
        components: rustfmt, clippy

    - name: Run tests
      run: cargo test --verbose

    - name: Run clippy
      run: cargo clippy -- -D warnings

    - name: Check formatting
      run: cargo fmt -- --check
"""
    return "# CI configuration\n"

def main():
    parser = argparse.ArgumentParser(description="Initialize cross-platform project")
    parser.add_argument("name", help="Project name")
    parser.add_argument("--language", "-l",
                       choices=["python", "node", "go", "rust"],
                       default="python",
                       help="Programming language (default: python)")

    args = parser.parse_args()

    if os.path.exists(args.name):
        print(f"❌ Directory '{args.name}' already exists")
        sys.exit(1)

    create_project_structure(args.name, args.language)

if __name__ == "__main__":
    main()