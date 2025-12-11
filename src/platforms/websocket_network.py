"""WebSocket-based network communication for clipboard sharing with persistent connections."""
import asyncio
import websockets
import json
import threading
import time
import base64
import platform
from typing import Callable, Dict, Any, List, Set
from datetime import datetime
import socket

from interfaces import (
    NetworkInterface, ClipboardData, ClipboardType,
    DeviceInfo, NetworkPacket
)
from .device_discovery import WebSocketDeviceDiscovery

class WebSocketClipboardNetwork(NetworkInterface):
    """WebSocket-based network communication with persistent connections."""

    def __init__(self, port: int = 8765):
        self.port = port
        self.device_name = socket.gethostname()
        self.device_ip = self._get_local_ip()
        self.platform = platform.system()

        # WebSocket server and clients
        self.server = None
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.server_task = None

        # Connection management
        self._running = False
        self._loop = None
        self._thread = None

        # Callbacks
        self._clipboard_callback = None
        self._device_callback = None

        # Device management
        self._connected_devices: Dict[str, DeviceInfo] = {}
        self._device_lock = threading.Lock()

        # Device discovery
        self.discovery = WebSocketDeviceDiscovery(websocket_port=port)

        # Data deduplication
        self._processed_data: Set[str] = set()

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

    def _serialize_packet(self, packet: NetworkPacket) -> str:
        """Serialize network packet for WebSocket transmission."""
        data = {
            'packet_type': packet.packet_type,
            'sender_name': packet.sender_name,
            'sender_ip': packet.sender_ip,
            'timestamp': packet.timestamp,
            'data': packet.data
        }
        return json.dumps(data, ensure_ascii=False)

    def _deserialize_packet(self, data: str) -> NetworkPacket:
        """Deserialize network packet from WebSocket transmission."""
        try:
            packet_data = json.loads(data)
            return NetworkPacket(
                packet_type=packet_data['packet_type'],
                sender_name=packet_data['sender_name'],
                sender_ip=packet_data['sender_ip'],
                timestamp=packet_data['timestamp'],
                data=packet_data.get('data')
            )
        except Exception as e:
            print(f"Error deserializing packet: {e}")
            return None

    def _serialize_clipboard_data(self, data: ClipboardData) -> Dict[str, Any]:
        """Serialize clipboard data for network transmission."""
        packet_data = {
            'type': data.type.value,
            'timestamp': data.timestamp,
            'device_name': data.device_name
        }

        if data.type == ClipboardType.TEXT:
            packet_data['content'] = data.content
        elif data.type == ClipboardType.IMAGE:
            # Encode image as base64
            packet_data['content'] = base64.b64encode(data.content).decode('utf-8')

        return packet_data

    def _deserialize_clipboard_data(self, packet_data: Dict[str, Any]) -> ClipboardData:
        """Deserialize clipboard data from network transmission."""
        try:
            # Validate required fields
            required_fields = ['content', 'type', 'timestamp', 'device_name']
            for field in required_fields:
                if field not in packet_data:
                    print(f"Error: Missing required field '{field}' in clipboard data")
                    return None

            content = packet_data['content']

            # Handle different data types
            try:
                clipboard_type = ClipboardType(packet_data['type'])
            except ValueError:
                print(f"Error: Invalid clipboard type '{packet_data['type']}'")
                return None

            if clipboard_type == ClipboardType.IMAGE:
                try:
                    content = base64.b64decode(content)
                except Exception as e:
                    print(f"Error decoding base64 image data: {e}")
                    return None

            # Ensure device_name is a string and content is properly encoded
            device_name = str(packet_data['device_name'])
            if isinstance(content, str):
                # Ensure string content is properly encoded for cross-platform compatibility
                try:
                    content = content.encode('utf-8').decode('utf-8')
                except UnicodeError:
                    content = str(content)  # Fallback to string conversion

            return ClipboardData(
                content=content,
                type=clipboard_type,
                timestamp=float(packet_data['timestamp']),
                device_name=device_name
            )
        except Exception as e:
            print(f"Error deserializing clipboard data: {e}")
            return None

    async def _handle_client(self, websocket, path):
        """Handle a WebSocket client connection."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"

        # Register client
        self.clients[client_id] = websocket

        try:
            # Send device info to new client
            device_info = DeviceInfo(
                name=self.device_name,
                ip_address=self.device_ip,
                last_seen=time.time(),
                platform=self.platform
            )

            await websocket.send(self._serialize_packet(NetworkPacket(
                packet_type="device_info",
                sender_name=self.device_name,
                sender_ip=self.device_ip,
                timestamp=time.time(),
                data={
                    'platform': self.platform,
                    'device_info': {
                        'name': device_info.name,
                        'ip_address': device_info.ip_address,
                        'platform': device_info.platform
                    }
                }
            )))

            # Listen for messages from this client
            async for message in websocket:
                try:
                    packet = self._deserialize_packet(message)
                    if packet:
                        await self._handle_packet(packet, websocket)
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    print(f"Error handling message from {client_id}: {e}")

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Remove client
            if client_id in self.clients:
                del self.clients[client_id]

            # Notify about device disconnection
            with self._device_lock:
                device_id = f"{client_id}"
                if device_id in self._connected_devices:
                    device = self._connected_devices[device_id]
                    del self._connected_devices[device_id]
                    if self._device_callback:
                        self._device_callback('device_left', device)

    async def _handle_packet(self, packet: NetworkPacket, websocket):
        """Handle incoming WebSocket packets."""
        # Ignore packets from ourselves
        if packet.sender_name == self.device_name and packet.sender_ip == self.device_ip:
            return

        sender_device_id = f"{packet.sender_name}@{packet.sender_ip}"

        if packet.packet_type == "device_info":
            # Device info packet
            device_data = packet.data.get('device_info', {})
            device_info = DeviceInfo(
                name=device_data.get('name', packet.sender_name),
                ip_address=device_data.get('ip_address', packet.sender_ip),
                last_seen=packet.timestamp,
                platform=device_data.get('platform', 'Unknown')
            )

            with self._device_lock:
                is_new = sender_device_id not in self._connected_devices
                self._connected_devices[sender_device_id] = device_info

                if is_new and self._device_callback:
                    self._device_callback('device_joined', device_info)

        elif packet.packet_type == "clipboard_data":
            # Clipboard data packet
            clipboard_data = self._deserialize_clipboard_data(packet.data)
            if clipboard_data and self._clipboard_callback:
                # Check for duplicate data
                data_id = f"{packet.sender_name}@{packet.sender_ip}:{clipboard_data.timestamp}:{hash(str(clipboard_data.content)[:100])}"

                if data_id not in self._processed_data:
                    self._processed_data.add(data_id)

                    # Clean up old entries
                    if len(self._processed_data) > 100:
                        old_entries = list(self._processed_data)[:50]
                        for entry in old_entries:
                            self._processed_data.discard(entry)

                    # Process clipboard data
                    self._clipboard_callback(clipboard_data)

    async def _broadcast_packet(self, packet: NetworkPacket):
        """Broadcast a packet to all connected clients."""
        if not self.clients:
            return

        message = self._serialize_packet(packet)
        disconnected_clients = []

        for client_id, websocket in self.clients.items():
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client_id)
            except Exception as e:
                print(f"Error sending to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Remove disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.clients:
                del self.clients[client_id]

    async def _run_server(self):
        """Run the WebSocket server."""
        try:
            self.server = await websockets.serve(
                self._handle_client,
                "0.0.0.0",  # Listen on all interfaces
                self.port,
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=10,    # Wait 10 seconds for pong response
                close_timeout=10    # Wait 10 seconds for close handshake
            )
            print(f"WebSocket server started on port {self.port}")

            # Keep server running
            await self.server.wait_closed()
        except Exception as e:
            print(f"Error running WebSocket server: {e}")
        finally:
            if self.server:
                self.server.close()
                await self.server.wait_closed()

    def _run_event_loop(self):
        """Run the asyncio event loop in a separate thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._run_server())
        except Exception as e:
            print(f"Error in event loop: {e}")
        finally:
            self._loop.close()

    def start_listening(self, clipboard_callback: Callable[[ClipboardData], None]) -> None:
        """Start listening for clipboard data via WebSocket."""
        if self._running:
            return

        self._clipboard_callback = clipboard_callback
        self._running = True

        # Start device discovery
        self.discovery.start_discovery(self._on_discovery_event)

        # Start event loop in separate thread
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

        # Give server time to start
        time.sleep(1)

    def stop_listening(self) -> None:
        """Stop listening for clipboard data."""
        self._running = False

        # Stop device discovery
        self.discovery.stop_discovery()

        if self._loop and not self._loop.is_closed():
            # Schedule server shutdown
            if self.server:
                self._loop.call_soon_threadsafe(self.server.close)

            # Stop the event loop
            self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def broadcast_clipboard(self, data: ClipboardData) -> None:
        """Broadcast clipboard data to all connected clients."""
        if not self._running or not self._loop or self._loop.is_closed():
            return

        packet = NetworkPacket(
            packet_type="clipboard_data",
            sender_name=self.device_name,
            sender_ip=self.device_ip,
            timestamp=time.time(),
            data=self._serialize_clipboard_data(data)
        )

        # Schedule broadcast in event loop
        self._loop.call_soon_threadsafe(
            lambda: asyncio.create_task(self._broadcast_packet(packet))
        )

    def _on_discovery_event(self, event_type: str, device: DeviceInfo):
        """Handle device discovery events."""
        if self._device_callback:
            self._device_callback(event_type, device)

    def get_connected_devices(self) -> List[DeviceInfo]:
        """Get list of connected devices (includes both connected and discovered)."""
        all_devices = {}

        # Add WebSocket-connected devices
        with self._device_lock:
            all_devices.update(self._connected_devices)

        # Add discovered devices
        discovered = self.discovery.get_discovered_devices()
        for device in discovered:
            device_id = f"{device.name}@{device.ip_address}"
            all_devices[device_id] = device

        return list(all_devices.values())

    def set_device_callback(self, callback: Callable[[str, DeviceInfo], None]) -> None:
        """Set callback for device events (join/leave)."""
        self._device_callback = callback

    def get_bound_port(self) -> int:
        """Get the actual port that the server is bound to."""
        return self.port

    def get_device_info(self) -> Dict[str, str]:
        """Get information about this device."""
        return {
            'name': self.device_name,
            'ip': self.device_ip,
            'platform': self.platform,
            'port': self.port,
            'protocol': 'WebSocket'
        }

    def connect_to_server(self, server_ip: str, server_port: int = None):
        """Connect to a remote WebSocket server."""
        if server_port is None:
            server_port = self.port

        # This would be implemented for client mode
        # For now, we use a peer-to-peer approach where each device runs a server
        # and devices discover each other through discovery protocol
        pass

    def announce_device(self) -> None:
        """Trigger device discovery announcement."""
        self.discovery.trigger_discovery()

    def discover_devices(self) -> None:
        """Trigger device discovery."""
        self.discovery.trigger_discovery()