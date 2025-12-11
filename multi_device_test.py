#!/usr/bin/env python3
"""Multi-device test script for device discovery with configurable ports."""

import sys
import os
import time
import argparse
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from platforms.network import UDPClipboardNetwork
from interfaces import DeviceInfo

def run_device_instance(port: int, instance_name: str, duration: int = 60):
    """Run a single device instance."""

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

    print(f"\n=== Starting {instance_name} ===")

    # Create receiver
    receiver = MockReceiver(instance_name)

    # Create network instance
    network = UDPClipboardNetwork(port=port, broadcast_ports=[5555, 5556, 5557, 5558, 5559])

    print(f"{instance_name} starting on port {port}...")
    print(f"Device name: {network.device_name}")
    print(f"Device IP: {network.device_ip}")
    print(f"Platform: {network.platform}")

    # Start listening
    network.start_listening(receiver.on_clipboard_data)
    network.set_device_callback(receiver.on_device_event)

    actual_port = network.get_bound_port()
    print(f"{instance_name} actually bound to port {actual_port}")

    print(f"{instance_name} started. Will run for {duration} seconds...")

    # Run for specified duration
    for i in range(duration):
        time.sleep(1)
        if i % 10 == 0:
            devices = network.get_connected_devices()
            print(f"[{instance_name}][{duration-i}s] Connected devices: {len(devices)}")

            # Trigger discovery periodically
            if i % 15 == 0:
                network.discover_devices()
                print(f"[{instance_name}] Triggered device discovery")

    print(f"\n=== {instance_name} Final Results ===")
    devices = network.get_connected_devices()
    print(f"Total devices found: {len(devices)}")
    for device in devices:
        last_seen = time.time() - device.last_seen
        print(f"  - {device.name} ({device.ip_address}) [{device.platform}] - Last seen: {last_seen:.1f}s ago")

    print(f"Device events: {len(receiver.device_events)}")
    for event_type, device in receiver.device_events:
        print(f"  - {event_type}: {device.name}")

    # Cleanup
    network.stop_listening()
    print(f"{instance_name} stopped.")

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description='Test device discovery')
    parser.add_argument('--port', type=int, default=5555, help='Starting port (default: 5555)')
    parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds (default: 30)')
    parser.add_argument('--instances', type=int, default=1, help='Number of instances to run (default: 1)')

    args = parser.parse_args()

    print("=== Multi-Device Discovery Test ===")
    print(f"Starting {args.instances} instance(s)")
    print(f"Starting port: {args.port}")
    print(f"Test duration: {args.duration} seconds")
    print("Run this script on multiple computers in the same network to test cross-device discovery.")

    # Run instances (for testing multiple instances on the same machine)
    if args.instances == 1:
        run_device_instance(args.port, "Instance1", args.duration)
    else:
        # Create threads for multiple instances
        import threading

        threads = []
        for i in range(args.instances):
            port = args.port + i
            instance_name = f"Instance{i+1}"
            thread = threading.Thread(
                target=run_device_instance,
                args=(port, instance_name, args.duration)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    print("\nTest completed!")
    print("If you ran this on multiple computers, you should see devices discovered across the network.")

if __name__ == "__main__":
    main()