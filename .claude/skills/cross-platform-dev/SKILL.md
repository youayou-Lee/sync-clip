---
name: cross-platform-dev
description: Comprehensive cross-platform development workflow guidance for creating software that runs consistently on Windows, Linux, and macOS. Use when developing applications that need to work across multiple operating systems, handling platform-specific differences, setting up cross-platform build systems, or designing platform-abstracted architectures. Covers requirements analysis, technology selection, architecture design, testing strategies, CI/CD setup, and deployment patterns for cross-platform projects.
---

# Cross-Platform Development Workflow

## Quick Start

### 1. Project Initialization
Use the included project initialization script:
```bash
python scripts/init_cross_platform_project.py <project-name> [language]
```

### 2. Architecture Pattern
Follow the layered architecture:
- **Core Layer**: Platform-independent business logic
- **Abstraction Layer**: Platform interfaces
- **Implementation Layer**: Platform-specific code
- **Presentation Layer**: UI (cross-platform or native)

### 3. Development Workflow
1. Requirements → 2. Technology Stack → 3. Architecture → 4. Development → 5. Testing → 6. Build → 7. Deploy

## Essential Guidelines

### Directory Structure
```
project/
├── src/
│   ├── core/           # Platform-independent code
│   ├── interfaces/     # Platform abstractions
│   ├── platforms/      # Platform-specific implementations
│   │   ├── windows/
│   │   ├── linux/
│   │   └── macos/
│   └── ui/             # User interface
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── build/
└── dist/
```

### Platform Differences Handling
- **File paths**: Use `pathlib` (Python) or `path` module (Node.js)
- **Process management**: Abstract command execution patterns
- **System services**: Service interfaces for Windows services/systemd
- **Permissions**: Handle UAC/sudo requirements gracefully

### Testing Strategy
Follow the testing pyramid:
- **70% Unit Tests**: Test core logic in isolation
- **20% Integration Tests**: Test platform interfaces
- **10% E2E Tests**: Test complete workflows on each platform

## Technology Stack Options

### Languages & Frameworks
| Language | GUI Framework | Network | Packaging |
|----------|---------------|---------|-----------|
| Python | Qt, Tkinter, Kivy | asyncio, sockets | PyInstaller, cx_Freeze |
| Node.js | Electron, Qt-like | Node APIs | pkg, electron-builder |
| Go | Fyne, Wails | net package | go build, goreleaser |
| Rust | Tauri, egui | tokio | cargo build |
| Java | JavaFX, Swing | Netty | jpackage, GraalVM |
| C++ | Qt, wxWidgets | Boost.Asio | CMake, Conan |

### Platform Abstraction Strategies
1. **Interface Segregation**: Separate interfaces for each platform capability
2. **Factory Pattern**: Create platform-specific implementations
3. **Dependency Injection**: Inject platform dependencies at runtime
4. **Feature Detection**: Detect capabilities at runtime

## Common Patterns

### 1. File System Operations
```python
# Use pathlib for cross-platform compatibility
from pathlib import Path
config_path = Path.home() / ".config" / "myapp"
```

### 2. Platform Detection
```python
import platform
system = platform.system().lower()  # 'windows', 'linux', 'darwin'
```

### 3. Command Execution
```python
import subprocess
def run_command(cmd, check=True):
    return subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
```

### 4. Configuration Management
- Store config in platform-appropriate directories
- Use environment variables for overrides
- Support both file and registry-based config (Windows)

## CI/CD Integration

### GitHub Actions Matrix
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: [3.8, 3.9, '3.10', 3.11]
```

### Testing Checklist
- [ ] Unit tests on all platforms
- [ ] Integration tests with mock platform APIs
- [ ] E2E tests on real OS instances
- [ ] Performance benchmarks per platform
- [ ] Accessibility testing

## Build & Packaging

### Python Projects
- **PyInstaller**: Single executable, includes dependencies
- **cx_Freeze**: MSI on Windows, .app on macOS
- **Briefcase**: Part of BeeWare project

### Node.js Projects
- **pkg**: Node.js to executable
- **electron-builder**: Complete Electron apps

### Go Projects
- **go build**: Cross-compilation support
- **goreleaser**: Automation for releases

## References

For detailed information on:
- Platform-specific differences: [platform-differences.md](references/platform-differences.md)
- CI/CD templates: [ci-templates.md](references/ci-templates.md)
- Architecture patterns: [architecture-patterns.md](references/architecture-patterns.md)
- Testing strategies: [testing-guide.md](references/testing-guide.md)
- Deployment patterns: [deployment-guide.md](references/deployment-guide.md)

## Tools

- Project initialization: `scripts/init_cross_platform_project.py`
- Build automation: `scripts/build.py`
- Test runner: `scripts/run_tests.py`
- Platform setup: `scripts/setup_dev_env.py`