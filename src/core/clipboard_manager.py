"""Core clipboard management logic."""
import os
import time
from typing import List, Optional, Callable
from collections import deque
from pathlib import Path
import threading

from interfaces import ClipboardData, ClipboardType, DeviceInfo
from platforms.clipboard_monitor import CrossPlatformClipboardMonitor
from platforms.websocket_network import WebSocketClipboardNetwork

class ClipboardManager:
    """Manages clipboard history and synchronization."""

    def __init__(self, max_history: int = 5, data_dir: str = "data", websocket_port: int = 8765):
        self.max_history = max_history
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Initialize components
        self.clipboard_monitor = CrossPlatformClipboardMonitor()
        self.network = WebSocketClipboardNetwork(port=websocket_port)

        # History storage
        self.history = deque(maxlen=max_history)
        self._lock = threading.Lock()

        # Device event callbacks
        self._device_callbacks: List[Callable[[str, DeviceInfo], None]] = []

        # Setup callbacks
        self.clipboard_monitor.start_monitoring(self._on_local_clipboard_change)
        self.network.start_listening(self._on_network_clipboard_receive)
        self.network.set_device_callback(self._on_device_event)

    def _on_local_clipboard_change(self, data: ClipboardData):
        """Handle local clipboard changes."""
        with self._lock:
            # Add to history
            self.history.append(data)

            # Save image data if needed
            if data.type == ClipboardType.IMAGE:
                self._save_image_data(data)

            # Broadcast to network
            self.network.broadcast_clipboard(data)

    def _on_network_clipboard_receive(self, data: ClipboardData):
        """Handle clipboard data from network."""
        with self._lock:
            # Add to history but don't broadcast back
            self.history.append(data)

            # Save image data if needed
            if data.type == ClipboardType.IMAGE:
                self._save_image_data(data)

    def _save_image_data(self, data: ClipboardData):
        """Save image data to file."""
        if data.type == ClipboardType.IMAGE:
            filename = f"{data.device_name}_{int(data.timestamp)}.png"
            filepath = self.data_dir / filename

            with open(filepath, 'wb') as f:
                f.write(data.content)

            # Store filepath in content for easier access
            data.content = str(filepath)

    def get_history(self) -> List[ClipboardData]:
        """Get clipboard history."""
        with self._lock:
            return list(self.history)

    def copy_to_clipboard(self, data: ClipboardData) -> bool:
        """Copy data to local clipboard."""
        return self.clipboard_monitor.set_clipboard_data(data)

    def clear_history(self) -> None:
        """Clear all clipboard history and remove saved image files."""
        with self._lock:
            # Clear in-memory history
            self.history.clear()

            # Remove saved image files
            try:
                if self.data_dir.exists():
                    for file_path in self.data_dir.glob("*.png"):
                        try:
                            file_path.unlink()
                        except Exception as e:
                            print(f"Error removing file {file_path}: {e}")
            except Exception as e:
                print(f"Error clearing history directory: {e}")

            print("Clipboard history cleared")

    def get_history_count(self) -> int:
        """Get the number of items in history."""
        with self._lock:
            return len(self.history)

    def _on_device_event(self, event_type: str, device: DeviceInfo):
        """Handle device events (join/leave)."""
        for callback in self._device_callbacks:
            try:
                callback(event_type, device)
            except Exception as e:
                print(f"Error in device callback: {e}")

    def add_device_callback(self, callback: Callable[[str, DeviceInfo], None]):
        """Add a callback for device events."""
        self._device_callbacks.append(callback)

    def get_connected_devices(self) -> List[DeviceInfo]:
        """Get list of connected devices."""
        return self.network.get_connected_devices()

    def discover_devices(self):
        """Trigger device discovery."""
        self.network.discover_devices()

    def shutdown(self):
        """Shutdown the clipboard manager."""
        self.clipboard_monitor.stop_monitoring()
        self.network.stop_listening()