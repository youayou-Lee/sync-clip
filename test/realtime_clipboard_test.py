#!/usr/bin/env python3
"""Real-time clipboard synchronization test between two instances."""

import sys
import os
import time
import threading
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from platforms.network import UDPClipboardNetwork

class RealtimeTest:
    """Real-time clipboard test."""

    def __init__(self, name):
        self.name = name
        self.clipboard_data = []
        self.network = UDPClipboardNetwork()
        self.running = True

    def on_clipboard_data(self, data):
        """Handle received clipboard data."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{self.name}][{timestamp}] Received clipboard data:")
        print(f"  From: {data.device_name}")
        print(f"  Type: {data.type.name}")
        print(f"  Content: {data.content}")
        print("-" * 40)
        self.clipboard_data.append(data)

    def start(self):
        """Start the test."""
        self.network.start_listening(self.on_clipboard_data)
        print(f"[{self.name}] Started listening on port {self.network.get_bound_port()}")

    def stop(self):
        """Stop the test."""
        self.running = False
        self.network.stop_listening()
        print(f"[{self.name}] Stopped")

def interactive_test():
    """Interactive clipboard synchronization test."""
    print("=== Interactive Clipboard Test ===")
    print("This will test real-time clipboard synchronization.")
    print("Copy text on one device and it should appear on the other.\n")

    # Create two instances
    instance1 = RealtimeTest("Instance1")
    instance2 = RealtimeTest("Instance2")

    # Start both instances
    instance1.start()
    instance2.start()

    print("Both instances started. Waiting for device discovery...")
    time.sleep(3)

    print(f"\nInstance1 connected devices: {len(instance1.network.get_connected_devices())}")
    for device in instance1.network.get_connected_devices():
        print(f"  - {device.name} ({device.ip_address}) [{device.platform}]")

    print(f"\nInstance2 connected devices: {len(instance2.network.get_connected_devices())}")
    for device in instance2.network.get_connected_devices():
        print(f"  - {device.name} ({device.ip_address}) [{device.platform}]")

    print("\nTest instructions:")
    print("1. Copy some text anywhere on your system")
    print("2. Watch for it to appear in the output above")
    print("3. Press Ctrl+C to stop the test")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping test...")
        instance1.stop()
        instance2.stop()

        print(f"\nTest Results:")
        print(f"Instance1 received {len(instance1.clipboard_data)} messages")
        print(f"Instance2 received {len(instance2.clipboard_data)} messages")

if __name__ == "__main__":
    interactive_test()