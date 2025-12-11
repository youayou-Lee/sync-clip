#!/usr/bin/env python3
"""Test simplified WebSocket network."""

import sys
import os
import time
import threading

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from platforms.simple_websocket_network import SimpleWebSocketNetwork
from interfaces import ClipboardData, ClipboardType

class TestReceiver:
    def __init__(self, name):
        self.name = name
        self.received_data = []
        self.device_events = []

    def on_clipboard_data(self, data):
        print(f"[{self.name}] Received: {data.content}")
        self.received_data.append(data)

    def on_device_event(self, event_type, device):
        print(f"[{self.name}] Device {event_type}: {device.name}")
        self.device_events.append((event_type, device))

def test_simple_websocket():
    """Test simplified WebSocket communication."""
    print("=== Simplified WebSocket Test ===")

    # Create two instances
    receiver1 = TestReceiver("Server1")
    receiver2 = TestReceiver("Server2")

    # Create networks on different ports
    network1 = SimpleWebSocketNetwork(port=8765)
    network2 = SimpleWebSocketNetwork(port=8766)

    try:
        print("Starting servers...")
        network1.start_listening(receiver1.on_clipboard_data)
        network2.start_listening(receiver2.on_clipboard_data)

        # Set device callbacks
        network1.set_device_callback(receiver1.on_device_event)
        network2.set_device_callback(receiver2.on_device_event)

        print("Servers started. Waiting for connection...")

        # Create manual connection test
        print("\nTesting manual connection...")
        print("You can connect using a WebSocket client to:")
        print("  ws://localhost:8765")
        print("  ws://localhost:8766")
        print("Or use curl: curl -i -N -H 'Connection: Upgrade' \\")
        print("     -H 'Upgrade: websocket' \\")
        print("     -H 'Sec-WebSocket-Key: test' \\")
        print("     -H 'Sec-WebSocket-Version: 13' http://localhost:8765")

        # Test local broadcast
        print("\nTesting local broadcast...")
        test_data = ClipboardData(
            content="Test message from local test",
            type=ClipboardType.TEXT,
            timestamp=time.time(),
            device_name="TestDevice"
        )

        network1.broadcast_clipboard(test_data)
        time.sleep(1)

        # Show status
        print(f"\nStatus after 5 seconds:")
        print(f"  Server1 received: {len(receiver1.received_data)}")
        print(f"  Server1 devices: {len(network1.get_connected_devices())}")
        print(f"  Server2 received: {len(receiver2.received_data)}")
        print(f"  Server2 devices: {len(network2.get_connected_devices())}")

        # Wait for manual testing
        print("\nPress Ctrl+C to stop servers...")
        try:
            time.sleep(30)  # Wait 30 seconds for manual testing
        except KeyboardInterrupt:
            print("\nStopping test...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("Stopping servers...")
        network1.stop_listening()
        network2.stop_listening()

    print("Test completed!")

if __name__ == "__main__":
    test_simple_websocket()