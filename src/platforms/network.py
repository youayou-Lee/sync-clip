"""Network communication for clipboard sharing."""
import socket
import threading
import json
import time
import base64
from typing import Callable, Dict, Any

from interfaces import NetworkInterface, ClipboardData, ClipboardType

class UDPClipboardNetwork(NetworkInterface):
    """UDP-based network communication for clipboard sharing."""

    def __init__(self, port: int = 5555):
        self.port = port
        self.device_name = socket.gethostname()
        self._listening = False
        self._listen_thread = None
        self._callback = None
        self._socket = None

    def _serialize_clipboard_data(self, data: ClipboardData) -> bytes:
        """Serialize clipboard data for network transmission."""
        packet = {
            'type': data.type.value,
            'timestamp': data.timestamp,
            'device_name': data.device_name
        }

        if data.type == ClipboardType.TEXT:
            packet['content'] = data.content
        elif data.type == ClipboardType.IMAGE:
            # Encode image as base64
            packet['content'] = base64.b64encode(data.content).decode('utf-8')

        return json.dumps(packet).encode('utf-8')

    def _deserialize_clipboard_data(self, data: bytes) -> ClipboardData:
        """Deserialize clipboard data from network transmission."""
        try:
            packet = json.loads(data.decode('utf-8'))

            content = packet['content']
            if packet['type'] == ClipboardType.IMAGE.value:
                content = base64.b64decode(content)

            return ClipboardData(
                content=content,
                type=ClipboardType(packet['type']),
                timestamp=packet['timestamp'],
                device_name=packet['device_name']
            )
        except Exception as e:
            print(f"Error deserializing clipboard data: {e}")
            return None

    def broadcast_clipboard(self, data: ClipboardData) -> None:
        """Broadcast clipboard data to network."""
        try:
            # Create UDP socket for broadcasting
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            serialized_data = self._serialize_clipboard_data(data)

            # Broadcast to local network
            sock.sendto(serialized_data, ('<broadcast>', self.port))
            sock.close()
        except Exception as e:
            print(f"Error broadcasting clipboard data: {e}")

    def _listen_loop(self):
        """Main listening loop."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind(('', self.port))

            while self._listening:
                try:
                    data, addr = self._socket.recvfrom(65536)  # Max UDP packet size

                    # Ignore data from ourselves
                    clipboard_data = self._deserialize_clipboard_data(data)
                    if clipboard_data and clipboard_data.device_name != self.device_name:
                        if self._callback:
                            self._callback(clipboard_data)

                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error receiving data: {e}")

        except Exception as e:
            print(f"Error setting up listener: {e}")
        finally:
            if self._socket:
                self._socket.close()

    def start_listening(self, callback: Callable[[ClipboardData], None]) -> None:
        """Start listening for clipboard data."""
        if self._listening:
            return

        self._callback = callback
        self._listening = True

        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

    def stop_listening(self) -> None:
        """Stop listening for clipboard data."""
        self._listening = False
        if self._socket:
            self._socket.close()
        if self._listen_thread:
            self._listen_thread.join(timeout=1)