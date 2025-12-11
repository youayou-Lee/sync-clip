"""Platform interfaces for clipboard monitoring."""
from abc import ABC, abstractmethod
from typing import Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class ClipboardType(Enum):
    TEXT = "text"
    IMAGE = "image"

@dataclass
class ClipboardData:
    content: Any
    type: ClipboardType
    timestamp: float
    device_name: str

class ClipboardMonitorInterface(ABC):
    """Interface for platform-specific clipboard monitoring."""

    @abstractmethod
    def get_clipboard_data(self) -> Optional[ClipboardData]:
        """Get current clipboard data."""
        pass

    @abstractmethod
    def set_clipboard_data(self, data: ClipboardData) -> bool:
        """Set clipboard data."""
        pass

    @abstractmethod
    def start_monitoring(self, callback) -> None:
        """Start monitoring clipboard changes."""
        pass

    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop monitoring clipboard changes."""
        pass

class NetworkInterface(ABC):
    """Interface for network communication."""

    @abstractmethod
    def broadcast_clipboard(self, data: ClipboardData) -> None:
        """Broadcast clipboard data to network."""
        pass

    @abstractmethod
    def start_listening(self, callback) -> None:
        """Start listening for clipboard data."""
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """Stop listening for clipboard data."""
        pass