#!/usr/bin/env python3
"""Test script for device discovery functionality."""

import sys
import os
import time
import threading
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from platforms.network import UDPClipboardNetwork
from interfaces import DeviceInfo

def test_device_discovery():
    """Test device discovery between two instances."""

    class MockReceiver:
        def __init__(self, name):
            self.name = name
            self.clipboard_data_received = []
            self.device_events = []

        def on_clipboard_data(self, data):
            """Handle received clipboard data."""
            self.clipboard_data_received.append(data)
            print(f"[{self.name}] Received clipboard data from {data.device_name}")

        def on_device_event(self, event_type, device):
            """Handle device events."""
            self.device_events.append((event_type, device))
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{self.name}][{timestamp}] Device {event_type}: {device.name} ({device.ip_address}) - {device.platform}")

    print("=== Device Discovery Test ===")

    # Create two mock receivers
    receiver1 = MockReceiver("Node1")
    receiver2 = MockReceiver("Node2")

    # Create two network instances with the same port (they need to listen on same port for broadcast)
    network1 = UDPClipboardNetwork(port=5555)
    network2 = UDPClipboardNetwork(port=5555)

    print("Starting network listeners...")

    # Start listening
    network1.start_listening(receiver1.on_clipboard_data)
    network2.start_listening(receiver2.on_clipboard_data)

    # Set device callbacks
    network1.set_device_callback(receiver1.on_device_event)
    network2.set_device_callback(receiver2.on_device_event)

    print("Network listeners started. Waiting for device discovery...")

    # Wait for devices to discover each other
    time.sleep(5)

    print("\n=== Device Discovery Results ===")
    print(f"Receiver 1 devices found: {len(network1.get_connected_devices())}")
    for device in network1.get_connected_devices():
        print(f"  - {device.name} ({device.ip_address}) [{device.platform}]")

    print(f"Receiver 2 devices found: {len(network2.get_connected_devices())}")
    for device in network2.get_connected_devices():
        print(f"  - {device.name} ({device.ip_address}) [{device.platform}]")

    print("\n=== Device Events ===")
    print("Receiver 1 events:")
    for event_type, device in receiver1.device_events:
        print(f"  - {event_type}: {device.name} ({device.ip_address})")

    print("Receiver 2 events:")
    for event_type, device in receiver2.device_events:
        print(f"  - {event_type}: {device.name} ({device.ip_address})")

    # Test device refresh
    print("\n=== Testing Device Refresh ===")
    network1.discover_devices()
    time.sleep(2)

    # Cleanup
    print("\nCleaning up...")
    network1.stop_listening()
    network2.stop_listening()

    print("Test completed!")

if __name__ == "__main__":
    test_device_discovery()