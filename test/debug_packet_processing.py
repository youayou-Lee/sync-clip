#!/usr/bin/env python3
"""Debug packet processing to find why clipboard data isn't being processed."""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from platforms.network import UDPClipboardNetwork
from interfaces import ClipboardData, ClipboardType

def debug_packet_processing():
    """Debug the packet processing pipeline."""
    print("=== Debugging Packet Processing ===")

    network = UDPClipboardNetwork(port=5557)

    # Track all processing steps
    processing_stats = {
        'packets_received': 0,
        'clipboard_packets': 0,
        'deserialization_success': 0,
        'deserialization_failure': 0,
        'callback_calls': 0,
        'duplicate_filtered': 0
    }

    def track_clipboard_callback(data):
        """Track clipboard callback calls."""
        processing_stats['callback_calls'] += 1
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ CLIPBOARD CALLBACK TRIGGERED!")
        print(f"  Device: {data.device_name}")
        print(f"  Type: {data.type}")
        print(f"  Content: {str(data.content)[:50]}...")
        print("-" * 40)

    # Override methods to track processing
    original_handle = network._handle_packet
    original_deserialize = network._deserialize_clipboard_data

    def debug_handle_packet(packet, addr):
        """Debug packet handling."""
        processing_stats['packets_received'] += 1
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] 📦 Processing packet: {packet.packet_type}")
        print(f"  From: {packet.sender_name}@{packet.sender_ip}")

        if packet.packet_type == "clipboard_data":
            processing_stats['clipboard_packets'] += 1
            print(f"  🎯 Clipboard data detected!")

            # Test deserialization
            result = original_deserialize(packet.data)
            if result:
                processing_stats['deserialization_success'] += 1
                print(f"  ✅ Deserialization successful")
            else:
                processing_stats['deserialization_failure'] += 1
                print(f"  ❌ Deserialization FAILED")
                print(f"  Raw data: {packet.data}")

        return original_handle(packet, addr)

    network._handle_packet = debug_handle_packet
    network._deserialize_clipboard_data = original_deserialize

    # Start listening
    print("Starting network listener...")
    network.start_listening(track_clipboard_callback)

    print("Waiting for packets...")
    time.sleep(5)

    # Manually send a test packet
    print("\n=== Sending Test Clipboard Data ===")
    test_data = ClipboardData(
        content="Test message for debugging",
        type=ClipboardType.TEXT,
        timestamp=time.time(),
        device_name="DebugTest"
    )

    print(f"Broadcasting test data: {test_data.content}")
    network.broadcast_clipboard(test_data)

    # Wait for processing
    time.sleep(3)

    # Show statistics
    print("\n=== Processing Statistics ===")
    for key, value in processing_stats.items():
        print(f"{key}: {value}")

    print(f"\nProcessed clipboard data set: {len(network._processed_clipboard_data)}")
    if network._processed_clipboard_data:
        for data_id in list(network._processed_clipboard_data)[:3]:
            print(f"  {data_id}")

    # Cleanup
    print("\nCleaning up...")
    network.stop_listening()

if __name__ == "__main__":
    debug_packet_processing()