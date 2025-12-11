# Cross-Platform Architecture Patterns

## 1. Layered Architecture

### Overview
The most common pattern for cross-platform applications, separating concerns into distinct layers.

```
┌─────────────────────────────────────┐
│        Presentation Layer          │  <- UI (Cross-platform or Native)
├─────────────────────────────────────┤
│         Application Layer          │  <- Business Logic (Platform-agnostic)
├─────────────────────────────────────┤
│       Abstraction Layer            │  <- Platform Interfaces
├─────────────────────────────────────┤
│      Implementation Layer          │  <- Platform-specific Code
└─────────────────────────────────────┘
```

### Implementation Example

```python
# Platform Interface (Abstraction Layer)
class FileSystemInterface:
    def get_config_path(self) -> Path:
        raise NotImplementedError

    def get_temp_path(self) -> Path:
        raise NotImplementedError

    def list_drives(self) -> List[str]:
        raise NotImplementedError

# Windows Implementation
class WindowsFileSystem(FileSystemInterface):
    def get_config_path(self) -> Path:
        import os
        return Path(os.environ["APPDATA"]) / "MyApp"

    def get_temp_path(self) -> Path:
        import tempfile
        return Path(tempfile.gettempdir())

    def list_drives(self) -> List[str]:
        import win32api
        drives = win32api.GetLogicalDriveStrings()
        return [d.strip("\\") for d in drives.split("\\x00") if d]

# Linux Implementation
class LinuxFileSystem(FileSystemInterface):
    def get_config_path(self) -> Path:
        return Path.home() / ".config" / "myapp"

    def get_temp_path(self) -> Path:
        return Path("/tmp") / "myapp"

    def list_drives(self) -> List[str]:
        return ["/"]

# Factory Pattern
class FileSystemFactory:
    @staticmethod
    def create() -> FileSystemInterface:
        import platform
        system = platform.system().lower()

        if system == "windows":
            return WindowsFileSystem()
        elif system == "linux":
            return LinuxFileSystem()
        else:
            raise NotImplementedError(f"Platform {system} not supported")
```

## 2. Plugin Architecture

### Overview
Load platform-specific modules at runtime, allowing for easy extension.

```python
# core/plugin_manager.py
import importlib
from pathlib import Path
from typing import Dict, Type, Any

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.load_plugins()

    def load_plugins(self):
        plugins_path = Path(__file__).parent.parent / "plugins"

        for plugin_file in plugins_path.glob("*_plugin.py"):
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "register_plugin"):
                plugin = module.register_plugin()
                self.plugins[plugin.name] = plugin

    def get_plugin(self, name: str):
        return self.plugins.get(name)

# plugins/windows_notification_plugin.py
import win10toast
from core.interfaces import NotificationInterface

class WindowsNotificationPlugin(NotificationInterface):
    name = "windows_notification"

    def __init__(self):
        self.toaster = win10toast.ToastNotifier()

    def show_notification(self, title: str, message: str):
        self.toaster.show_toast(title, message)

def register_plugin():
    return WindowsNotificationPlugin()
```

## 3. Adapter Pattern

### Overview
Adapts platform-specific APIs to a common interface.

```python
# core/interfaces/notification.py
from abc import ABC, abstractmethod

class NotificationInterface(ABC):
    @abstractmethod
    def show_notification(self, title: str, message: str):
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

# adapters/windows_adapter.py
class WindowsNotificationAdapter(NotificationInterface):
    def __init__(self):
        try:
            import win10toast
            self.toaster = win10toast.ToastNotifier()
            self._available = True
        except ImportError:
            self._available = False

    def show_notification(self, title: str, message: str):
        if self._available:
            self.toaster.show_toast(title, message)

    def is_available(self) -> bool:
        return self._available

# adapters/linux_adapter.py
class LinuxNotificationAdapter(NotificationInterface):
    def __init__(self):
        try:
            import gi
            gi.require_version('Notify', '0.7')
            from gi.repository import Notify
            self.Notify = Notify
            self.Notify.init("MyApp")
            self._available = True
        except (ImportError, ValueError):
            self._available = False

    def show_notification(self, title: str, message: str):
        if self._available:
            notification = self.Notify.Notification.new(title, message)
            notification.show()

    def is_available(self) -> bool:
        return self._available

# core/notification_service.py
class NotificationService:
    def __init__(self):
        self.adapters = [
            WindowsNotificationAdapter(),
            LinuxNotificationAdapter(),
            # Add more adapters as needed
        ]
        self.adapter = self._select_adapter()

    def _select_adapter(self) -> NotificationInterface:
        for adapter in self.adapters:
            if adapter.is_available():
                return adapter
        raise RuntimeError("No suitable notification adapter found")

    def show(self, title: str, message: str):
        self.adapter.show_notification(title, message)
```

## 4. Bridge Pattern

### Overview
Separates abstraction from implementation, allowing independent variation.

```python
# core/abstractions/system_service.py
from abc import ABC, abstractmethod

class SystemServiceAbstraction(ABC):
    def __init__(self, implementer):
        self.implementer = implementer

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_status(self):
        pass

class ApplicationService(SystemServiceAbstraction):
    def start(self):
        self.implementer.install_service()
        self.implementer.start_service()
        print(f"Application service started: {self.get_status()}")

    def stop(self):
        self.implementer.stop_service()
        print(f"Application service stopped: {self.get_status()}")

    def get_status(self):
        return self.implementer.check_status()

# Implementations
class WindowsServiceImplementer:
    def install_service(self):
        # Windows service installation
        pass

    def start_service(self):
        import win32serviceutil
        win32serviceutil.StartService("MyApp")

    def stop_service(self):
        import win32serviceutil
        win32serviceutil.StopService("MyApp")

    def check_status(self):
        import win32service
        import win32con
        status = win32service.QueryServiceStatus("MyApp")[1]
        if status == win32service.SERVICE_RUNNING:
            return "Running"
        return "Stopped"

class LinuxServiceImplementer:
    def install_service(self):
        # systemd service file creation
        pass

    def start_service(self):
        import subprocess
        subprocess.run(["sudo", "systemctl", "start", "myapp"])

    def stop_service(self):
        import subprocess
        subprocess.run(["sudo", "systemctl", "stop", "myapp"])

    def check_status(self):
        import subprocess
        result = subprocess.run(
            ["systemctl", "is-active", "myapp"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
```

## 5. Microkernel Pattern

### Overview
Minimal core with pluggable functionality modules.

```python
# core/kernel.py
from typing import Dict, List, Any
import importlib
from pathlib import Path

class Microkernel:
    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.services: Dict[str, Any] = {}
        self.event_bus = EventBus()

    def load_plugin(self, plugin_name: str):
        plugin_path = Path(__file__).parent.parent / "plugins" / f"{plugin_name}.py"
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        plugin = module.Plugin(self)
        self.plugins[plugin_name] = plugin
        plugin.initialize()

    def register_service(self, name: str, service):
        self.services[name] = service

    def get_service(self, name: str):
        return self.services.get(name)

    def emit_event(self, event_name: str, data: Any = None):
        self.event_bus.emit(event_name, data)

    def start(self):
        self.emit_event("kernel_started")
        for plugin in self.plugins.values():
            plugin.start()

    def stop(self):
        for plugin in reversed(list(self.plugins.values())):
            plugin.stop()
        self.emit_event("kernel_stopped")

# plugins/file_watcher_plugin.py
class FileWatcherPlugin:
    def __init__(self, kernel):
        self.kernel = kernel
        self.watcher = None

    def initialize(self):
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class Handler(FileSystemEventHandler):
            def __init__(self, plugin):
                self.plugin = plugin

            def on_modified(self, event):
                if not event.is_directory:
                    self.plugin.kernel.emit_event("file_changed", event.src_path)

        self.watcher = Observer()
        self.watcher.schedule(Handler(self), path=".", recursive=True)

    def start(self):
        if self.watcher:
            self.watcher.start()

    def stop(self):
        if self.watcher:
            self.watcher.stop()
            self.watcher.join()
```

## 6. Repository Pattern

### Overview
Abstracts data access, handling platform-specific storage differences.

```python
# core/interfaces/repository.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')

class Repository(ABC, Generic[T]):
    @abstractmethod
    def save(self, entity: T) -> T:
        pass

    @abstractmethod
    def find(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        pass

# repositories/windows_registry_repository.py
import winreg
from typing import TypeVar, Generic

T = TypeVar('T')

class WindowsRegistryRepository(Repository[T]):
    def __init__(self, key_path: str, entity_class):
        self.key_path = key_path
        self.entity_class = entity_class

    def save(self, entity: T) -> T:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.key_path) as key:
            for attr, value in entity.__dict__.items():
                winreg.SetValueEx(key, attr, 0, winreg.REG_SZ, str(value))
        return entity

    def find(self, id: str) -> Optional[T]:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path) as key:
                data = {}
                i = 0
                while True:
                    try:
                        name, value, type = winreg.EnumValue(key, i)
                        data[name] = value
                        i += 1
                    except WindowsError:
                        break

                entity = self.entity_class()
                for attr, value in data.items():
                    setattr(entity, attr, value)
                return entity
        except WindowsError:
            return None

# repositories/json_file_repository.py
import json
from pathlib import Path

class JsonFileRepository(Repository[T]):
    def __init__(self, file_path: Path, entity_class):
        self.file_path = file_path
        self.entity_class = entity_class
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text("[]")

    def save(self, entity: T) -> T:
        entities = self.find_all()
        entity_data = entity.__dict__

        # Update if exists, otherwise add
        for i, e in enumerate(entities):
            if hasattr(e, 'id') and hasattr(entity, 'id') and e.id == entity.id:
                entities[i] = entity
                break
        else:
            entities.append(entity)

        self.file_path.write_text(json.dumps([e.__dict__ for e in entities], indent=2))
        return entity

    def find(self, id: str) -> Optional[T]:
        entities = self.find_all()
        for entity in entities:
            if hasattr(entity, 'id') and entity.id == id:
                return entity
        return None

    def find_all(self) -> List[T]:
        data = json.loads(self.file_path.read_text())
        entities = []
        for item in data:
            entity = self.entity_class()
            for attr, value in item.items():
                setattr(entity, attr, value)
            entities.append(entity)
        return entities
```

## 7. Service Locator Pattern

### Overview
Provides a registry for platform-specific services.

```python
# core/service_locator.py
from typing import Dict, Any, TypeVar, Type

T = TypeVar('T')

class ServiceLocator:
    _instance = None
    _services: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str, service: Any):
        cls._services[name] = service

    @classmethod
    def get(cls, name: str, service_type: Type[T] = None) -> T:
        service = cls._services.get(name)
        if service is None:
            raise ValueError(f"Service '{name}' not found")
        if service_type and not isinstance(service, service_type):
            raise ValueError(f"Service '{name}' is not of type {service_type}")
        return service

    @classmethod
    def is_registered(cls, name: str) -> bool:
        return name in cls._services

# platform/service_initializer.py
import platform

def initialize_services():
    locator = ServiceLocator()

    if platform.system() == "Windows":
        from platforms.windows.file_service import WindowsFileService
        from platforms.windows.notification_service import WindowsNotificationService
        from platforms.windows.registry_service import WindowsRegistryService

        locator.register("file_service", WindowsFileService())
        locator.register("notification_service", WindowsNotificationService())
        locator.register("storage_service", WindowsRegistryService())

    elif platform.system() == "Linux":
        from platforms.linux.file_service import LinuxFileService
        from platforms.linux.notification_service import LinuxNotificationService
        from platforms.linux.file_storage_service import LinuxFileStorageService

        locator.register("file_service", LinuxFileService())
        locator.register("notification_service", LinuxNotificationService())
        locator.register("storage_service", LinuxFileStorageService())

    else:
        raise RuntimeError(f"Unsupported platform: {platform.system()}")

# Usage
from core.service_locator import ServiceLocator

def main():
    file_service = ServiceLocator.get("file_service")
    notification_service = ServiceLocator.get("notification_service")

    # Use services
    config_path = file_service.get_config_path()
    notification_service.show("Hello", "World")
```

## 8. Domain Events Pattern

### Overview
Decouples components using event-driven communication.

```python
# core/events/domain_events.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Callable
import uuid

@dataclass
class DomainEvent:
    event_id: str
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]

    def __init__(self, event_type: str, data: Dict[str, Any] = None):
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.event_type = event_type
        self.data = data or {}

class EventHandler(ABC):
    @abstractmethod
    def handle(self, event: DomainEvent):
        pass

class EventBus:
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def publish(self, event: DomainEvent):
        handlers = self.handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler.handle(event)
            except Exception as e:
                print(f"Error handling event {event.event_id}: {e}")

# handlers/platform_specific_handlers.py
class WindowsFileChangedHandler(EventHandler):
    def handle(self, event: DomainEvent):
        if event.event_type == "file_changed":
            file_path = event.data.get("path")
            # Windows-specific handling
            import win32file
            # Process file change with Windows API

class LinuxFileChangedHandler(EventHandler):
    def handle(self, event: DomainEvent):
        if event.event_type == "file_changed":
            file_path = event.data.get("path")
            # Linux-specific handling
            import os
            # Process file change with Unix API
```

## Best Practices

### 1. Separation of Concerns
- Keep platform-specific code isolated
- Use interfaces for all platform interactions
- Maintain a clear separation between business logic and platform code

### 2. Dependency Management
- Use dependency injection for platform services
- Avoid direct platform calls in business logic
- Make dependencies explicit and testable

### 3. Error Handling
- Handle platform-specific errors gracefully
- Provide meaningful error messages
- Use fallback strategies when possible

### 4. Performance Considerations
- Minimize platform crossings
- Cache platform-specific information
- Lazy load platform modules

### 5. Testing Strategy
- Mock platform interfaces for unit tests
- Test platform-specific code in integration tests
- Use CI/CD for automated cross-platform testing

### 6. Configuration Management
- Externalize platform-specific configuration
- Use configuration files or environment variables
- Support runtime configuration changes