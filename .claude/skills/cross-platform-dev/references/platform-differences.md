# Platform Differences Guide

## File System Operations

### Path Handling
- **Windows**: Use backslashes `\`, but most APIs accept forward slashes `/`
- **Linux/macOS**: Use forward slashes `/` exclusively
- **Solution**: Use `pathlib` (Python) or `path` module (Node.js)

```python
# Good: Cross-platform compatible
from pathlib import Path
config_path = Path.home() / ".config" / "myapp"

# Bad: Platform-specific
config_path = "~/.config/myapp"  # Works on Unix, issues on Windows
```

### Case Sensitivity
- **Windows**: Case-insensitive (preserves case)
- **Linux**: Case-sensitive
- **macOS**: Case-insensitive by default (APFS), can be case-sensitive

```python
# Always use consistent case
config_file = "config.yaml"  # Not Config.yaml or CONFIG.YAML
```

### Line Endings
- **Windows**: `\r\n` (CRLF)
- **Linux/macOS**: `\n` (LF)
- **Solution**: Use text mode with universal newlines or normalize

```python
# Python automatically handles line endings in text mode
with open('file.txt', 'r') as f:
    content = f.read()
```

### Special Directories
- **Windows**: `C:\Program Files`, `%APPDATA%`, `%LOCALAPPDATA%`
- **Linux**: `/usr/local/bin`, `~/.config`, `/var/log`
- **macOS**: `/Applications`, `~/Library/Application Support`

```python
# Cross-platform approach
from pathlib import Path
import platform

if platform.system() == "Windows":
    config_dir = Path(os.environ["APPDATA"])
else:
    config_dir = Path.home() / ".config"
```

## Process Management

### Running Commands
- **Windows**: Use `cmd.exe` or PowerShell
- **Linux/macOS**: Use shell (`/bin/sh` or `/bin/bash`)
- **Solution**: Abstract command execution

```python
import subprocess
import sys

def run_command(cmd, shell=None):
    if shell is None:
        shell = True if sys.platform == "win32" else False

    result = subprocess.run(
        cmd,
        shell=shell,
        capture_output=True,
        text=True
    )
    return result
```

### Administrative Privileges
- **Windows**: UAC elevation, run as Administrator
- **Linux**: Use `sudo` or setuid
- **macOS**: Admin privileges, authentication prompts

```python
import ctypes
import platform

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False  # Not Windows

def require_admin():
    if platform.system() == "Windows" and not is_admin():
        # Re-run with admin privileges
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()
```

## System Services

### Windows Services
- **Registration**: Use `sc create` or `New-Service`
- **Management**: Service Control Manager (SCM)
- **Python**: `pywin32` library

```python
import win32serviceutil
import win32service

class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MyService"
    _svc_display_name_ = "My Service"

    def SvcDoRun(self):
        # Service logic here
        pass
```

### Linux systemd
- **Service files**: `/etc/systemd/system/`
- **Management**: `systemctl` commands
- **Logs**: `journalctl`

```ini
# /etc/systemd/system/myservice.service
[Unit]
Description=My Service
After=network.target

[Service]
Type=simple
User=myuser
ExecStart=/usr/bin/myservice
Restart=always

[Install]
WantedBy=multi-user.target
```

### macOS Launch Agents/Daemons
- **Agents**: User-level, `~/Library/LaunchAgents/`
- **Daemons**: System-level, `/Library/LaunchDaemons/`
- **Format**: XML plist files

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.example.myservice</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/myservice</string>
    </array>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

## Environment Variables

### Accessing Variables
```python
import os

# Cross-platform access
home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
path_sep = os.pathsep  # ; on Windows, : on Unix
```

### Common Variables
| Variable | Windows | Linux/macOS |
|----------|---------|-------------|
| Home | `%USERPROFILE%` | `$HOME` |
| Path | `%PATH%` | `$PATH` |
| Temp | `%TEMP%` or `%TMP%` | `$TMPDIR` |
| App Data | `%APPDATA%` | `$XDG_CONFIG_HOME` or `~/.config` |

## Network Configuration

### Port Binding
- **Windows**: May require admin for ports < 1024
- **Linux**: Root required for ports < 1024
- **macOS**: Root required for ports < 1024

```python
import socket

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port
```

### Firewall Rules
- **Windows**: Windows Firewall API
- **Linux**: `iptables`, `ufw`, or `firewalld`
- **macOS**: `pfctl` or Application Firewall

## System Notifications

### Windows
```python
import win10toast
toaster = win10toast.ToastNotifier()
toaster.show_toast("Title", "Message")
```

### Linux
```python
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify

Notify.init("MyApp")
notification = Notify.Notification.new("Title", "Message")
notification.show()
```

### macOS
```python
import os
os.system("""
osascript -e 'display notification "Message" with title "Title"'
""")
```

## Common Pitfalls

### 1. Hardcoding Paths
```python
# Bad
config_path = "C:\\Program Files\\MyApp\\config.yaml"

# Good
config_path = Path(__file__).parent / "config.yaml"
```

### 2. Assuming OS Features
```python
# Bad - assumes Unix-only command
os.system("cp source.txt dest.txt")

# Good - use Python standard library
import shutil
shutil.copy2("source.txt", "dest.txt")
```

### 3. Ignoring Encoding
```python
# Bad - default encoding varies by platform
with open("file.txt") as f:
    content = f.read()

# Good - specify encoding
with open("file.txt", encoding="utf-8") as f:
    content = f.read()
```

### 4. Thread Sleep Precision
- **Windows**: Minimum ~15ms with time.sleep()
- **Linux/macOS**: Higher precision (~1ms)
- **Solution**: Use platform-specific timing when needed

## Testing Strategy

### 1. Unit Tests
- Mock platform-specific functions
- Test core logic independently

```python
from unittest.mock import patch

@patch('platform.system')
def test_windows_behavior(mock_system):
    mock_system.return_value = 'Windows'
    # Test Windows-specific code
```

### 2. Integration Tests
- Use Docker containers for Linux
- Use VMs or cloud services for Windows/macOS
- GitHub Actions provides matrix builds

### 3. Manual Testing
- Test on actual hardware
- Verify installation processes
- Check user experience consistency

## Debugging Tips

### 1. Logging
```python
import logging
import platform

logging.basicConfig(
    level=logging.DEBUG,
    format=f"%(asctime)s [{platform.system()}] %(message)s"
)
```

### 2. Platform Detection
```python
import platform
import sys

system = platform.system()
machine = platform.machine()
architecture = platform.architecture()

# More specific checks
is_windows = sys.platform == "win32"
is_linux = sys.platform.startswith("linux")
is_macos = sys.platform == "darwin"
```

### 3. Conditional Code
```python
if sys.platform == "win32":
    import winreg
    # Windows-specific code
elif sys.platform == "darwin":
    # macOS-specific code
else:
    # Linux/Unix-specific code
```