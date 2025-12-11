"""Cross-platform clipboard monitoring implementation."""
import time
import platform
import socket
import threading
from typing import Optional, Callable
import pyperclip
from PIL import ImageGrab
import io
import base64
import hashlib

from interfaces import ClipboardMonitorInterface, ClipboardData, ClipboardType

class CrossPlatformClipboardMonitor(ClipboardMonitorInterface):
    """Cross-platform clipboard monitor using pyperclip and PIL."""

    def __init__(self):
        self.device_name = socket.gethostname()
        self._monitoring = False
        self._monitor_thread = None
        self._callback = None
        self._last_hash = None

    def get_clipboard_data(self) -> Optional[ClipboardData]:
        """Get current clipboard data."""
        try:
            # Try to get image first
            if platform.system() in ["Windows", "Darwin"]:
                image = ImageGrab.grabclipboard()
                if image and isinstance(image, Image.Image):
                    # Convert image to bytes
                    img_bytes = io.BytesIO()
                    image.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    return ClipboardData(
                        content=img_bytes.read(),
                        type=ClipboardType.IMAGE,
                        timestamp=time.time(),
                        device_name=self.device_name
                    )

            # Try to get text
            text = pyperclip.paste()
            if text and text.strip():
                return ClipboardData(
                    content=text,
                    type=ClipboardType.TEXT,
                    timestamp=time.time(),
                    device_name=self.device_name
                )
        except Exception as e:
            print(f"Error getting clipboard data: {e}")

        return None

    def set_clipboard_data(self, data: ClipboardData) -> bool:
        """Set clipboard data."""
        try:
            if data.type == ClipboardType.TEXT:
                pyperclip.copy(data.content)
            elif data.type == ClipboardType.IMAGE:
                if platform.system() in ["Windows", "Darwin"]:
                    # For image clipboard, we need platform-specific code
                    # This is simplified - in production would use proper clipboard APIs
                    pass
            return True
        except Exception as e:
            print(f"Error setting clipboard data: {e}")
            return False

    def _get_clipboard_hash(self) -> Optional[str]:
        """Get hash of current clipboard content for change detection."""
        data = self.get_clipboard_data()
        if not data:
            return None

        if data.type == ClipboardType.TEXT:
            return hashlib.md5(data.content.encode()).hexdigest()
        else:
            return hashlib.md5(data.content).hexdigest()

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                current_hash = self._get_clipboard_hash()
                if current_hash and current_hash != self._last_hash:
                    self._last_hash = current_hash
                    data = self.get_clipboard_data()
                    if data and self._callback:
                        self._callback(data)

                time.sleep(0.5)  # Check every 500ms
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(1)

    def start_monitoring(self, callback: Callable[[ClipboardData], None]) -> None:
        """Start monitoring clipboard changes."""
        if self._monitoring:
            return

        self._callback = callback
        self._monitoring = True
        self._last_hash = self._get_clipboard_hash()

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop monitoring clipboard changes."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)