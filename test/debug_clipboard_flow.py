#!/usr/bin/env python3
"""Debug tool to analyze clipboard data flow between platforms."""

import sys
import os
import time
import threading
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from platforms.network import UDPClipboardNetwork
from interfaces import DeviceInfo, ClipboardData, ClipboardType

class DebugClipboardReceiver:
    """Debug receiver to track all clipboard events."""

    def __init__(self, name):
        self.name = name
        self.clipboard_data_received = []
        self.device_events = []
        self.network_packets = []

    def on_clipboard_data(self, data):
        """Handle received clipboard data."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{self.name}][{timestamp}] Clipboard Data:")
        print(f"  Device: {data.device_name}")
        print(f"  Type: {data.type.name}")
        content_preview = str(data.content)[:100].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"  Content: {content_preview}...")
        print(f"  Timestamp: {data.timestamp}")
        print("-" * 50)

        self.clipboard_data_received.append(data)

    def on_device_event(self, event_type, device):
        """Handle device events."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{self.name}][{timestamp}] Device Event: {event_type}")
        print(f"  Device: {device.name} ({device.ip_address}) - {device.platform}")
        print("-" * 50)

        self.device_events.append((event_type, device))

    def on_network_packet(self, packet_type, sender_name, sender_ip):
        """Track all network packets."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.network_packets.append((timestamp, packet_type, sender_name, sender_ip))
        print(f"[{self.name}][{timestamp}] Packet: {packet_type} from {sender_name}@{sender_ip}")

def debug_device_discovery():
    """Debug device discovery and clipboard flow."""

    print("=== Clipboard Flow Debug Tool ===")
    print("This tool will show detailed clipboard data flow between platforms.\n")

    # Create debug receivers
    receiver1 = DebugClipboardReceiver("Node1")
    receiver2 = DebugClipboardReceiver("Node2")

    # Create network instances
    network1 = UDPClipboardNetwork(port=5555)
    network2 = UDPClipboardNetwork(port=5556)

    print("Starting network listeners...")

    # Start listening
    network1.start_listening(receiver1.on_clipboard_data)
    network2.start_listening(receiver2.on_clipboard_data)

    # Set device callbacks
    network1.set_device_callback(receiver1.on_device_event)
    network2.set_device_callback(receiver2.on_device_event)

    # Patch the _handle_packet method to log all packets
    original_handle_1 = network1._handle_packet
    original_handle_2 = network2._handle_packet

    def debug_handle_1(packet, addr):
        receiver1.on_network_packet(packet.packet_type, packet.sender_name, packet.sender_ip)
        return original_handle_1(packet, addr)

    def debug_handle_2(packet, addr):
        receiver2.on_network_packet(packet.packet_type, packet.sender_name, packet.sender_ip)
        return original_handle_2(packet, addr)

    network1._handle_packet = debug_handle_1
    network2._handle_packet = debug_handle_2

    print("Network listeners started. Waiting for device discovery...")

    # Wait for initial discovery
    time.sleep(3)

    print("\n=== Initial Device Discovery Results ===")
    print(f"Node1 devices found: {len(network1.get_connected_devices())}")
    for device in network1.get_connected_devices():
        print(f"  - {device.name} ({device.ip_address}) [{device.platform}]")

    print(f"Node2 devices found: {len(network2.get_connected_devices())}")
    for device in network2.get_connected_devices():
        print(f"  - {device.name} ({device.ip_address}) [{device.platform}]")

    print("\n=== Testing Manual Clipboard Broadcast ===")
    print("Sending test clipboard data from Node1 to Node2...")

    # Create test clipboard data
    test_data = ClipboardData(
        content="Test message from Node1 to Node2",
        type=ClipboardType.TEXT,
        timestamp=time.time(),
        device_name=network1.device_name
    )

    # Broadcast from Node1
    network1.broadcast_clipboard(test_data)

    # Wait for transmission
    time.sleep(2)

    # Test from Node2 to Node1
    print("\nSending test clipboard data from Node2 to Node1...")
    test_data2 = ClipboardData(
        content="Test message from Node2 to Node1",
        type=ClipboardType.TEXT,
        timestamp=time.time(),
        device_name=network2.device_name
    )

    network2.broadcast_clipboard(test_data2)
    time.sleep(2)

    print("\n=== Final Results ===")
    print(f"Node1 received {len(receiver1.clipboard_data_received)} clipboard messages:")
    for i, data in enumerate(receiver1.clipboard_data_received, 1):
        print(f"  {i}. From {data.device_name}: {data.content}")

    print(f"\nNode2 received {len(receiver2.clipboard_data_received)} clipboard messages:")
    for i, data in enumerate(receiver2.clipboard_data_received, 1):
        print(f"  {i}. From {data.device_name}: {data.content}")

    print(f"\nNode1 network packets: {len(receiver1.network_packets)}")
    print(f"Node2 network packets: {len(receiver2.network_packets)}")

    # Cleanup
    print("\nCleaning up...")
    network1.stop_listening()
    network2.stop_listening()

    print("Debug completed!")
    return receiver1, receiver2

if __name__ == "__main__":
    debug_device_discovery()