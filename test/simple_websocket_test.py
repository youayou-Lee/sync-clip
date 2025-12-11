#!/usr/bin/env python3
"""Simple WebSocket test to check basic functionality."""

import sys
import os
import time
import threading

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from platforms.websocket_network import WebSocketClipboardNetwork
from interfaces import ClipboardData, ClipboardType

def simple_test():
    """Simple test to check if WebSocket network works."""
    print("=== Simple WebSocket Test ===")

    # Create a network instance
    network = WebSocketClipboardNetwork(port=8765)

    # Track received data
    received_data = []
    device_events = []

    def on_clipboard_data(data):
        print(f"Received clipboard: {data.content}")
        received_data.append(data)

    def on_device_event(event_type, device):
        print(f"Device event: {event_type} - {device.name}")
        device_events.append((event_type, device))

    try:
        print("Starting WebSocket network...")
        network.start_listening(on_clipboard_data)
        network.set_device_callback(on_device_event)

        print("Network started. Waiting 3 seconds...")
        time.sleep(3)

        print("Testing clipboard broadcast...")
        test_data = ClipboardData(
            content="Test message from simple test",
            type=ClipboardType.TEXT,
            timestamp=time.time(),
            device_name="SimpleTest"
        )

        network.broadcast_clipboard(test_data)
        print("Broadcast sent. Waiting 2 seconds...")
        time.sleep(2)

        print(f"Results:")
        print(f"  Received data: {len(received_data)}")
        print(f"  Device events: {len(device_events)}")
        print(f"  Connected devices: {len(network.get_connected_devices())}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("Stopping network...")
        network.stop_listening()

    print("Simple test completed!")

if __name__ == "__main__":
    simple_test()