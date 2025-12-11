"""Enhanced network communication for clipboard sharing with device discovery."""
import socket
import threading
import json
import time
import base64
import platform
import subprocess
from typing import Callable, Dict, Any, List, Set
from datetime import datetime

from interfaces import (
    NetworkInterface, ClipboardData, ClipboardType,
    DeviceInfo, NetworkPacket
)

class UDPClipboardNetwork(NetworkInterface):
    """Enhanced UDP-based network communication with device discovery."""

    def __init__(self, port: int = 5555, broadcast_ports: list[int] = None):
        self.initial_port = port
        self.port = port  # Will be updated to actual bound port
        self.broadcast_ports = broadcast_ports or [5555, 5556, 5557, 5558, 5559]  # Common ports to broadcast to
        self.device_name = socket.gethostname()
        self.device_ip = self._get_local_ip()
        self.platform = platform.system()

        # Network state
        self._listening = False
        self._listen_thread = None
        self._heartbeat_thread = None
        self._cleanup_thread = None

        # Sockets
        self._socket = None
        self._broadcast_socket = None

        # Callbacks
        self._clipboard_callback = None
        self._device_callback = None

        # Device management
        self._connected_devices: Dict[str, DeviceInfo] = {}
        self._device_lock = threading.Lock()

        # Device timeout (seconds)
        self._device_timeout = 15  # Remove devices after 15 seconds of no heartbeat

        # Data deduplication
        self._processed_clipboard_data: set[str] = set()
        self._dedup_lock = threading.Lock()

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

    def _serialize_packet(self, packet: NetworkPacket) -> bytes:
        """Serialize network packet for transmission."""
        data = {
            'packet_type': packet.packet_type,
            'sender_name': packet.sender_name,
            'sender_ip': packet.sender_ip,
            'timestamp': packet.timestamp,
            'data': packet.data
        }
        return json.dumps(data).encode('utf-8')

    def _deserialize_packet(self, data: bytes) -> NetworkPacket:
        """Deserialize network packet from transmission."""
        try:
            packet_data = json.loads(data.decode('utf-8'))
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

    def _broadcast_packet(self, packet: NetworkPacket) -> None:
        """Broadcast a packet to the network on multiple ports."""
        try:
            if not self._broadcast_socket:
                self._broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                # Platform-specific socket options
                if self.platform != 'Windows':
                    # On Linux/macOS, set broadcast timeout
                    self._broadcast_socket.settimeout(2.0)

            serialized_data = self._serialize_packet(packet)

            # Broadcast to our listening port and common ports
            ports_to_broadcast = [self.port] + self.broadcast_ports
            ports_to_broadcast = list(set(ports_to_broadcast))  # Remove duplicates

            for port in ports_to_broadcast:
                try:
                    # Try different broadcast addresses for better compatibility
                    broadcast_addresses = ['<broadcast>', '255.255.255.255']

                    # Add network-specific broadcast if possible
                    if self.device_ip and '.' in self.device_ip:
                        parts = self.device_ip.split('.')
                        if len(parts) == 4:
                            network_broadcast = f"{parts[0]}.{parts[1]}.{parts[2]}.255"
                            broadcast_addresses.append(network_broadcast)

                    for broadcast_addr in broadcast_addresses:
                        try:
                            self._broadcast_socket.sendto(serialized_data, (broadcast_addr, port))
                        except Exception as e:
                            # Silently continue for individual broadcast address failures
                            continue

                except Exception as e:
                    print(f"Error broadcasting to port {port}: {e}")

        except Exception as e:
            print(f"Error broadcasting packet: {e}")

    def broadcast_clipboard(self, data: ClipboardData) -> None:
        """Broadcast clipboard data to network."""
        packet = NetworkPacket(
            packet_type="clipboard_data",
            sender_name=self.device_name,
            sender_ip=self.device_ip,
            timestamp=time.time(),
            data=self._serialize_clipboard_data(data)
        )
        self._broadcast_packet(packet)

    def announce_device(self) -> None:
        """Announce device presence to network."""
        packet = NetworkPacket(
            packet_type="device_announce",
            sender_name=self.device_name,
            sender_ip=self.device_ip,
            timestamp=time.time(),
            data={'platform': self.platform}
        )
        self._broadcast_packet(packet)

    def discover_devices(self) -> None:
        """Send device discovery request."""
        packet = NetworkPacket(
            packet_type="device_discovery",
            sender_name=self.device_name,
            sender_ip=self.device_ip,
            timestamp=time.time()
        )
        self._broadcast_packet(packet)

    def _send_heartbeat(self):
        """Send periodic heartbeat to maintain presence."""
        while self._listening:
            try:
                packet = NetworkPacket(
                    packet_type="device_heartbeat",
                    sender_name=self.device_name,
                    sender_ip=self.device_ip,
                    timestamp=time.time()
                )
                self._broadcast_packet(packet)
                time.sleep(10)  # Send heartbeat every 10 seconds
            except Exception as e:
                print(f"Error sending heartbeat: {e}")
                break

    def _cleanup_devices(self):
        """Remove inactive devices."""
        while self._listening:
            try:
                current_time = time.time()
                with self._device_lock:
                    inactive_devices = [
                        device_id for device_id, device in self._connected_devices.items()
                        if current_time - device.last_seen > self._device_timeout
                    ]

                    for device_id in inactive_devices:
                        device = self._connected_devices[device_id]
                        del self._connected_devices[device_id]
                        if self._device_callback:
                            self._device_callback('device_left', device)

                time.sleep(2)  # Check every 2 seconds for faster detection
            except Exception as e:
                print(f"Error in device cleanup: {e}")
                break

    def _update_device(self, device_info: DeviceInfo):
        """Update or add device information."""
        with self._device_lock:
            device_id = f"{device_info.name}@{device_info.ip_address}"
            is_new = device_id not in self._connected_devices

            self._connected_devices[device_id] = device_info

            if is_new and self._device_callback:
                self._device_callback('device_joined', device_info)

    def _handle_packet(self, packet: NetworkPacket, addr: tuple):
        """Handle incoming network packets."""
        # Ignore packets from ourselves
        if packet.sender_name == self.device_name and packet.sender_ip == self.device_ip:
            return

        sender_device_id = f"{packet.sender_name}@{packet.sender_ip}"

        # Debug: Print packet type for debugging (can be removed in production)
        # print(f"Debug: Received packet type '{packet.packet_type}' from {packet.sender_name}")

        if packet.packet_type in ["device_announce", "device_discovery", "device_heartbeat"]:
            # Device management packets
            device_info = DeviceInfo(
                name=packet.sender_name,
                ip_address=packet.sender_ip,
                last_seen=packet.timestamp,
                platform=packet.data.get('platform', 'Unknown') if packet.data else 'Unknown'
            )
            self._update_device(device_info)

            # Respond to discovery requests
            if packet.packet_type == "device_discovery":
                self.announce_device()

        elif packet.packet_type == "clipboard_data":
            # Clipboard data packet
            clipboard_data = self._deserialize_clipboard_data(packet.data)
            if clipboard_data and self._clipboard_callback:
                # Check for duplicate data using a unique identifier
                data_id = f"{packet.sender_name}@{packet.sender_ip}:{clipboard_data.timestamp}:{hash(str(clipboard_data.content)[:100])}"

                with self._dedup_lock:
                    if data_id in self._processed_clipboard_data:
                        # Duplicate data, skip processing
                        return

                    # Add to processed set and clean old entries (keep only recent ones)
                    self._processed_clipboard_data.add(data_id)

                    # Clean up old entries to prevent memory leak (keep only last 100)
                    if len(self._processed_clipboard_data) > 100:
                        # Remove oldest 50 entries
                        old_entries = list(self._processed_clipboard_data)[:50]
                        for entry in old_entries:
                            self._processed_clipboard_data.discard(entry)

                # Process the unique clipboard data
                self._clipboard_callback(clipboard_data)
        else:
            # Unknown packet type - log for debugging
            print(f"Warning: Unknown packet type '{packet.packet_type}' from {sender_device_id}")

    def _listen_loop(self):
        """Main listening loop."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Windows specific: Allow multiple processes to bind to the same port
            if self.platform == 'Windows':
                try:
                    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except AttributeError:
                    pass  # SO_REUSEPORT not available on all Windows versions
            else:
                # Linux/macOS: Set SO_REUSEPORT for better multi-instance support
                try:
                    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except AttributeError:
                    pass

            # Try to bind to the specified port, fallback to random port if unavailable
            bind_success = False
            for attempt in range(10):  # Try 10 times
                try:
                    self._socket.bind(('', self.port))
                    bind_success = True
                    break
                except OSError as e:
                    # Handle both Windows and Linux "Address already in use" errors
                    windows_port_error = hasattr(e, 'winerr') and e.winerr == 10048
                    linux_port_error = hasattr(e, 'errno') and e.errno == 98
                    generic_error = "Address already in use" in str(e)

                    if windows_port_error or linux_port_error or generic_error:
                        # Port is in use, try the next one
                        self.port += 1
                        print(f"Port {self.port-1} is in use, trying port {self.port}")
                    else:
                        print(f"Bind error (not port in use): {e}")
                        raise

            if not bind_success:
                raise Exception("Could not bind to any port in range")

            self._socket.settimeout(1.0)  # Set timeout for periodic checks
            print(f"Successfully bound to port {self.port} on {self.platform}")

            while self._listening:
                try:
                    data, addr = self._socket.recvfrom(65536)
                    packet = self._deserialize_packet(data)
                    if packet:
                        self._handle_packet(packet, addr)
                    else:
                        # Debug: Failed to deserialize packet
                        # print(f"Debug: Failed to deserialize packet from {addr}, data length: {len(data)}")
                        # Print first few bytes for debugging
                        # if len(data) > 0:
                        #     try:
                        #         preview = data[:50].decode('utf-8', errors='ignore')
                        #         print(f"Data preview: {preview}")
                        #     except:
                        #         print(f"Data bytes: {data[:20]}")
                        pass
                except socket.timeout:
                    continue
                except OSError as e:
                    # Handle socket closure gracefully
                    if e.errno == 9 or "Bad file descriptor" in str(e):
                        # Socket was closed, exit the loop
                        break
                    else:
                        print(f"Error receiving data: {e}")
                except Exception as e:
                    print(f"Error receiving data: {e}")

        except Exception as e:
            print(f"Error setting up listener: {e}")
        finally:
            if self._socket:
                self._socket.close()
            if self._broadcast_socket:
                self._broadcast_socket.close()

    def start_listening(self, clipboard_callback: Callable[[ClipboardData], None]) -> None:
        """Start listening for clipboard data."""
        if self._listening:
            return

        self._clipboard_callback = clipboard_callback
        self._listening = True

        # Start main listening thread
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

        # Start heartbeat thread
        self._heartbeat_thread = threading.Thread(target=self._send_heartbeat, daemon=True)
        self._heartbeat_thread.start()

        # Start device cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_devices, daemon=True)
        self._cleanup_thread.start()

        # Announce device and discover others
        time.sleep(1)  # Give listener time to start
        self.announce_device()
        self.discover_devices()

    def stop_listening(self) -> None:
        """Stop listening for clipboard data."""
        self._listening = False

        # Close sockets to interrupt listening loops
        if self._socket:
            try:
                self._socket.close()
            except Exception as e:
                print(f"Error closing socket: {e}")
            self._socket = None

        if self._broadcast_socket:
            try:
                self._broadcast_socket.close()
            except Exception as e:
                print(f"Error closing broadcast socket: {e}")
            self._broadcast_socket = None

        # Wait for threads to finish with longer timeout
        for thread in [self._listen_thread, self._heartbeat_thread, self._cleanup_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=5)
                if thread.is_alive():
                    print(f"Warning: Thread {thread.name} did not shutdown gracefully")

    def get_connected_devices(self) -> List[DeviceInfo]:
        """Get list of connected devices."""
        with self._device_lock:
            return list(self._connected_devices.values())

    def set_device_callback(self, callback: Callable[[str, DeviceInfo], None]) -> None:
        """Set callback for device events (join/leave)."""
        self._device_callback = callback

    def get_bound_port(self) -> int:
        """Get the actual port that the socket is bound to."""
        return self.port

    def get_device_info(self) -> Dict[str, str]:
        """Get information about this device."""
        return {
            'name': self.device_name,
            'ip': self.device_ip,
            'platform': self.platform,
            'port': self.port
        }