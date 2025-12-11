"""Device discovery mechanism for WebSocket connections."""
import socket
import threading
import time
import json
from typing import Callable, Dict, List, Optional
from interfaces import DeviceInfo

class WebSocketDeviceDiscovery:
    """Device discovery for WebSocket-based clipboard sharing."""

    def __init__(self, websocket_port: int = 8765):
        self.websocket_port = websocket_port
        self.device_name = socket.gethostname()
        self.device_ip = self._get_local_ip()

        # Discovery socket
        self.discovery_socket = None
        self.broadcast_socket = None
        self.running = False
        self.thread = None

        # Callbacks
        self.device_callback: Optional[Callable[[str, DeviceInfo], None]] = None

        # Discovered devices
        self.discovered_devices: Dict[str, DeviceInfo] = {}
        self.device_lock = threading.Lock()

        # Discovery intervals
        self.announce_interval = 30  # Announce every 30 seconds
        self.cleanup_interval = 60   # Clean up every 60 seconds
        self.device_timeout = 120    # Remove devices after 2 minutes

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Try to connect to an external address to find the local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            # Fallback methods
            try:
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except Exception:
                return "127.0.0.1"

    def start_discovery(self, device_callback: Callable[[str, DeviceInfo], None]):
        """Start device discovery."""
        if self.running:
            return

        self.device_callback = device_callback
        self.running = True

        # Start discovery thread
        self.thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.thread.start()

        print(f"WebSocket device discovery started for {self.device_name} ({self.device_ip})")

    def stop_discovery(self):
        """Stop device discovery."""
        self.running = False

        if self.discovery_socket:
            try:
                self.discovery_socket.close()
            except:
                pass

        if self.broadcast_socket:
            try:
                self.broadcast_socket.close()
            except:
                pass

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        print("WebSocket device discovery stopped")

    def _discovery_loop(self):
        """Main discovery loop."""
        try:
            # Setup discovery socket (listening)
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.discovery_socket.bind(('', 8766))  # Discovery port
            self.discovery_socket.settimeout(2.0)

            # Setup broadcast socket (sending)
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            print(f"Discovery listening on port 8766")

            last_announce = 0
            last_cleanup = 0

            while self.running:
                current_time = time.time()

                # Announce ourselves periodically
                if current_time - last_announce > self.announce_interval:
                    self._announce_device()
                    last_announce = current_time

                # Clean up old devices periodically
                if current_time - last_cleanup > self.cleanup_interval:
                    self._cleanup_devices()
                    last_cleanup = current_time

                # Listen for discovery messages
                try:
                    data, addr = self.discovery_socket.recvfrom(1024)
                    self._handle_discovery_message(data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error in discovery loop: {e}")

        except Exception as e:
            print(f"Error setting up discovery: {e}")

    def _announce_device(self):
        """Announce our device to the network."""
        try:
            announcement = {
                'type': 'websocket_clipboard_device',
                'device_name': self.device_name,
                'device_ip': self.device_ip,
                'websocket_port': self.websocket_port,
                'timestamp': time.time()
            }

            message = json.dumps(announcement).encode('utf-8')

            # Broadcast to discovery port
            self.broadcast_socket.sendto(message, ('<broadcast>', 8766))

            # Also try specific broadcast addresses
            self.broadcast_socket.sendto(message, ('255.255.255.255', 8766))

            # Try network-specific broadcast
            if '.' in self.device_ip:
                parts = self.device_ip.split('.')
                if len(parts) == 4:
                    network_broadcast = f"{parts[0]}.{parts[1]}.{parts[2]}.255"
                    self.broadcast_socket.sendto(message, (network_broadcast, 8766))

        except Exception as e:
            print(f"Error announcing device: {e}")

    def _handle_discovery_message(self, data: bytes, addr: tuple):
        """Handle incoming discovery messages."""
        try:
            if addr[0] == self.device_ip:
                return  # Ignore messages from ourselves

            message = json.loads(data.decode('utf-8'))

            if message.get('type') == 'websocket_clipboard_device':
                device_info = DeviceInfo(
                    name=message.get('device_name', 'Unknown'),
                    ip_address=message.get('device_ip', addr[0]),
                    last_seen=message.get('timestamp', time.time()),
                    platform='WebSocket'
                )

                # Add WebSocket port to device info
                device_info.websocket_port = message.get('websocket_port', 8765)

                with self.device_lock:
                    device_id = f"{device_info.name}@{device_info.ip_address}"
                    is_new = device_id not in self.discovered_devices

                    self.discovered_devices[device_id] = device_info

                    if is_new and self.device_callback:
                        self.device_callback('device_discovered', device_info)

        except Exception as e:
            print(f"Error handling discovery message from {addr}: {e}")

    def _cleanup_devices(self):
        """Remove old devices from discovery list."""
        current_time = time.time()
        removed_devices = []

        with self.device_lock:
            for device_id, device in list(self.discovered_devices.items()):
                if current_time - device.last_seen > self.device_timeout:
                    del self.discovered_devices[device_id]
                    removed_devices.append(device)

        # Notify about removed devices
        for device in removed_devices:
            if self.device_callback:
                self.device_callback('device_timed_out', device)

    def get_discovered_devices(self) -> List[DeviceInfo]:
        """Get list of discovered devices."""
        with self.device_lock:
            return list(self.discovered_devices.values())

    def trigger_discovery(self):
        """Trigger immediate device discovery."""
        self._announce_device()