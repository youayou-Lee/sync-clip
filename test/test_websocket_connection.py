#!/usr/bin/env python3
"""Test WebSocket connection stability and clipboard synchronization."""

import sys
import os
import time
import asyncio
import threading
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from platforms.websocket_network import WebSocketClipboardNetwork
from interfaces import ClipboardData, ClipboardType

class WebSocketTestReceiver:
    """Test receiver for WebSocket connections."""

    def __init__(self, name):
        self.name = name
        self.clipboard_data_received = []
        self.device_events = []

    def on_clipboard_data(self, data):
        """Handle received clipboard data."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{self.name}][{timestamp}] Clipboard Data:")
        print(f"  Device: {data.device_name}")
        print(f"  Type: {data.type.name}")
        content_preview = str(data.content)[:100].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"  Content: {content_preview}...")
        print("-" * 50)

        self.clipboard_data_received.append(data)

    def on_device_event(self, event_type, device):
        """Handle device events."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{self.name}][{timestamp}] Device Event: {event_type}")
        print(f"  Device: {device.name} ({device.ip_address}) - {device.platform}")
        print("-" * 50)

        self.device_events.append((event_type, device))

async def test_websocket_stability():
    """Test WebSocket connection stability over time."""
    print("=== WebSocket Connection Stability Test ===")
    print("This test will run WebSocket connections and monitor stability.\n")

    # Create two WebSocket instances
    receiver1 = WebSocketTestReceiver("WebSocket-1")
    receiver2 = WebSocketTestReceiver("WebSocket-2")

    # Create networks on different ports
    network1 = WebSocketClipboardNetwork(port=8765)
    network2 = WebSocketClipboardNetwork(port=8766)

    print("Starting WebSocket servers...")

    # Start listening
    network1.start_listening(receiver1.on_clipboard_data)
    network2.start_listening(receiver2.on_clipboard_data)

    # Set device callbacks
    network1.set_device_callback(receiver1.on_device_event)
    network2.set_device_callback(receiver2.on_device_event)

    print("WebSocket servers started. Waiting for connections...")
    print(f"Server 1: {network1.get_device_info()}")
    print(f"Server 2: {network2.get_device_info()}")

    # Give servers time to start
    await asyncio.sleep(2)

    print("\n=== Manual Connection Test ===")
    print("Use a WebSocket client to connect to:")
    print(f"  ws://localhost:8765")
    print(f"  ws://localhost:8766")
    print("Send JSON messages with format:")
    print('{"packet_type": "clipboard_data", "sender_name": "Test", "sender_ip": "127.0.0.1", "timestamp": 1234567890, "data": {"type": "text", "content": "Hello", "device_name": "TestDevice", "timestamp": 1234567890}}')

    # Test sending clipboard data
    print("\n=== Testing Clipboard Data Transmission ===")
    for i in range(3):
        print(f"\nTest {i+1}: Sending clipboard data...")

        test_data = ClipboardData(
            content=f"Test message {i+1} from WebSocket test at {datetime.now().strftime('%H:%M:%S')}",
            type=ClipboardType.TEXT,
            timestamp=time.time(),
            device_name="WebSocketTest"
        )

        # Broadcast from network1
        network1.broadcast_clipboard(test_data)
        await asyncio.sleep(1)

        # Broadcast from network2
        network2.broadcast_clipboard(test_data)
        await asyncio.sleep(2)

    # Monitor connections for a period
    print(f"\n=== Monitoring Connections for 30 seconds ===")
    start_time = time.time()
    check_interval = 5

    while time.time() - start_time < 30:
        await asyncio.sleep(check_interval)
        elapsed = time.time() - start_time

        print(f"\n[{elapsed:.1f}s] Connection Status:")
        print(f"  Server 1 clients: {len(network1.clients)}")
        print(f"  Server 2 clients: {len(network2.clients)}")
        print(f"  Server 1 devices: {len(network1.get_connected_devices())}")
        print(f"  Server 2 devices: {len(network2.get_connected_devices())}")
        print(f"  Data received by receiver 1: {len(receiver1.clipboard_data_received)}")
        print(f"  Data received by receiver 2: {len(receiver2.clipboard_data_received)}")

    # Final statistics
    print(f"\n=== Final Statistics ===")
    print(f"Total running time: {time.time() - start_time:.1f} seconds")
    print(f"Receiver 1:")
    print(f"  Clipboard messages received: {len(receiver1.clipboard_data_received)}")
    print(f"  Device events: {len(receiver1.device_events)}")
    print(f"  Connected devices: {len(network1.get_connected_devices())}")
    print(f"Receiver 2:")
    print(f"  Clipboard messages received: {len(receiver2.clipboard_data_received)}")
    print(f"  Device events: {len(receiver2.device_events)}")
    print(f"  Connected devices: {len(network2.get_connected_devices())}")

    # Cleanup
    print("\nShutting down...")
    network1.stop_listening()
    network2.stop_listening()

    print("WebSocket stability test completed!")

def run_websocket_test():
    """Run the WebSocket test in an async context."""
    asyncio.run(test_websocket_stability())

if __name__ == "__main__":
    run_websocket_test()