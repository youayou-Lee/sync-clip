#!/usr/bin/env python3
"""Simple test for device discovery functionality."""

import sys
import os
import time
import threading
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from platforms.network import UDPClipboardNetwork
from interfaces import DeviceInfo

def single_device_test():
    """Test single device network functionality."""

    class MockReceiver:
        def __init__(self, name):
            self.name = name
            self.clipboard_data_received = []
            self.device_events = []

        def on_clipboard_data(self, data):
            """Handle received clipboard data."""
            self.clipboard_data_received.append(data)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{self.name}][{timestamp}] Received clipboard data from {data.device_name}")

        def on_device_event(self, event_type, device):
            """Handle device events."""
            self.device_events.append((event_type, device))
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{self.name}][{timestamp}] Device {event_type}: {device.name} ({device.ip_address}) - {device.platform}")

    print("=== Single Device Network Test ===")

    # Create receiver
    receiver = MockReceiver("TestNode")

    # Create network instance
    network = UDPClipboardNetwork(port=5555)

    print("Starting network listener...")
    print(f"Device name: {network.device_name}")
    print(f"Device IP: {network.device_ip}")
    print(f"Platform: {network.platform}")

    # Start listening
    network.start_listening(receiver.on_clipboard_data)
    network.set_device_callback(receiver.on_device_event)

    print("Network listener started.")
    print("This instance will discover itself and other instances on the network.")
    print("You can run this script on multiple computers to test device discovery.")

    # Run for 30 seconds
    for i in range(30):
        time.sleep(1)
        if i % 5 == 0:
            print(f"Running... {i}s. Connected devices: {len(network.get_connected_devices())}")

            # Show current devices
            devices = network.get_connected_devices()
            for device in devices:
                last_seen = time.time() - device.last_seen
                print(f"  - {device.name} ({device.ip_address}) [{device.platform}] - Last seen: {last_seen:.1f}s ago")

            # Trigger discovery every 10 seconds
            if i % 10 == 0:
                print("Triggering device discovery...")
                network.discover_devices()

    print("\n=== Final Results ===")
    print(f"Total devices found: {len(network.get_connected_devices())}")
    for device in network.get_connected_devices():
        print(f"  - {device.name} ({device.ip_address}) [{device.platform}]")

    print("\n=== Device Events ===")
    for event_type, device in receiver.device_events:
        print(f"  - {event_type}: {device.name} ({device.ip_address})")

    # Cleanup
    print("\nCleaning up...")
    network.stop_listening()

    print("Test completed!")

if __name__ == "__main__":
    single_device_test()