"""Simplified WebSocket-based network communication for clipboard sharing."""
import asyncio
import websockets
import json
import threading
import time
import base64
import platform
import socket
from typing import Callable, Dict, Any, List, Set
from datetime import datetime

from interfaces import (
    NetworkInterface, ClipboardData, ClipboardType,
    DeviceInfo, NetworkPacket
)

class SimpleWebSocketNetwork(NetworkInterface):
    """Simplified WebSocket network communication."""

    def __init__(self, port: int = 8765):
        self.port = port
        self.device_name = socket.gethostname()
        self.device_ip = self._get_local_ip()
        self.platform = platform.system()

        # Server state
        self.server = None
        self.clients = {}
        self.running = False

        # Event loop
        self.loop = None
        self.thread = None

        # Callbacks
        self._clipboard_callback = None
        self._device_callback = None

        # Device management
        self.connected_devices = {}
        self.processed_data = set()

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            try:
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except Exception:
                return "127.0.0.1"

    def _serialize_packet(self, packet: NetworkPacket) -> str:
        """Serialize network packet for transmission."""
        data = {
            'packet_type': packet.packet_type,
            'sender_name': packet.sender_name,
            'sender_ip': packet.sender_ip,
            'timestamp': packet.timestamp,
            'data': packet.data
        }
        return json.dumps(data, ensure_ascii=False)

    def _deserialize_packet(self, data: str) -> NetworkPacket:
        """Deserialize network packet from transmission."""
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
            packet_data['content'] = base64.b64encode(data.content).decode('utf-8')

        return packet_data

    def _deserialize_clipboard_data(self, packet_data: Dict[str, Any]) -> ClipboardData:
        """Deserialize clipboard data from network transmission."""
        try:
            content = packet_data['content']
            if packet_data['type'] == ClipboardType.IMAGE.value:
                content = base64.b64decode(content)

            return ClipboardData(
                content=content,
                type=ClipboardType(packet_data['type']),
                timestamp=float(packet_data['timestamp']),
                device_name=packet_data['device_name']
            )
        except Exception as e:
            print(f"Error deserializing clipboard data: {e}")
            return None

    async def _handle_client(self, websocket, path):
        """Handle a WebSocket client connection."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.clients[client_id] = websocket

        # Send device info to client
        device_info = DeviceInfo(
            name=self.device_name,
            ip_address=self.device_ip,
            last_seen=time.time(),
            platform=self.platform
        )

        device_packet = NetworkPacket(
            packet_type="device_info",
            sender_name=self.device_name,
            sender_ip=self.device_ip,
            timestamp=time.time(),
            data={'platform': self.platform, 'device_name': device_info.name}
        )

        try:
            await websocket.send(self._serialize_packet(device_packet))

            # Add to connected devices
            device_id = f"{self.device_name}@{self.device_ip}"
            self.connected_devices[device_id] = device_info
            if self._device_callback:
                self._device_callback('device_joined', device_info)

            # Listen for messages
            async for message in websocket:
                packet = self._deserialize_packet(message)
                if packet:
                    await self._handle_packet(packet)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            # Remove client
            if client_id in self.clients:
                del self.clients[client_id]

    async def _handle_packet(self, packet: NetworkPacket):
        """Handle incoming packets."""
        if packet.sender_name == self.device_name and packet.sender_ip == self.device_ip:
            return

        if packet.packet_type == "device_info":
            # Handle device info
            device_data = packet.data
            device_info = DeviceInfo(
                name=device_data.get('device_name', packet.sender_name),
                ip_address=packet.sender_ip,
                last_seen=packet.timestamp,
                platform=device_data.get('platform', 'Unknown')
            )

            device_id = f"{device_info.name}@{device_info.ip_address}"
            if device_id not in self.connected_devices:
                self.connected_devices[device_id] = device_info
                if self._device_callback:
                    self._device_callback('device_joined', device_info)

        elif packet.packet_type == "clipboard_data":
            # Handle clipboard data
            clipboard_data = self._deserialize_clipboard_data(packet.data)
            if clipboard_data and self._clipboard_callback:
                # Check for duplicates
                data_id = f"{packet.sender_name}@{packet.sender_ip}:{clipboard_data.timestamp}"
                if data_id not in self.processed_data:
                    self.processed_data.add(data_id)
                    self._clipboard_callback(clipboard_data)

    async def _run_server(self):
        """Run WebSocket server."""
        try:
            self.server = await websockets.serve(
                self._handle_client,
                "0.0.0.0",
                self.port,
                ping_interval=20,
                ping_timeout=10
            )
            print(f"WebSocket server started on port {self.port}")

            # Keep server running
            await asyncio.Future()  # Wait forever
        except Exception as e:
            print(f"WebSocket server error: {e}")

    def _run_event_loop(self):
        """Run event loop in thread."""
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self._run_server())
        except Exception as e:
            print(f"Event loop error: {e}")

    def start_listening(self, clipboard_callback: Callable[[ClipboardData], None]) -> None:
        """Start listening for clipboard data."""
        if self.running:
            return

        self._clipboard_callback = clipboard_callback
        self.running = True

        # Start server in separate thread
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

        # Give server time to start
        time.sleep(1)

    def stop_listening(self) -> None:
        """Stop listening."""
        self.running = False

        if self.server:
            self.server.close()

        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)

    def broadcast_clipboard(self, data: ClipboardData) -> None:
        """Broadcast clipboard data."""
        if not self.clients:
            return

        packet = NetworkPacket(
            packet_type="clipboard_data",
            sender_name=self.device_name,
            sender_ip=self.device_ip,
            timestamp=time.time(),
            data=self._serialize_clipboard_data(data)
        )

        message = self._serialize_packet(packet)
        disconnected = []

        for client_id, websocket in list(self.clients.items()):
            try:
                asyncio.run_coroutine_threadsafe(
                    websocket.send(message),
                    self.loop
                ).result(timeout=1)
            except Exception as e:
                print(f"Error sending to {client_id}: {e}")
                disconnected.append(client_id)

        # Remove disconnected clients
        for client_id in disconnected:
            if client_id in self.clients:
                del self.clients[client_id]

    def get_connected_devices(self) -> List[DeviceInfo]:
        """Get connected devices."""
        return list(self.connected_devices.values())

    def set_device_callback(self, callback: Callable[[str, DeviceInfo], None]) -> None:
        """Set device callback."""
        self._device_callback = callback

    def get_bound_port(self) -> int:
        """Get bound port."""
        return self.port

    def get_device_info(self) -> Dict[str, str]:
        """Get device info."""
        return {
            'name': self.device_name,
            'ip': self.device_ip,
            'platform': self.platform,
            'port': self.port,
            'protocol': 'WebSocket'
        }

    def discover_devices(self) -> None:
        """Not implemented in simple version."""
        pass

    def announce_device(self) -> None:
        """Not implemented in simple version."""
        pass