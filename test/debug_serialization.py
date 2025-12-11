#!/usr/bin/env python3
"""Debug clipboard data serialization and deserialization."""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from platforms.network import UDPClipboardNetwork
from interfaces import ClipboardData, ClipboardType

def test_serialization():
    """Test clipboard data serialization and deserialization."""
    print("=== Testing Clipboard Data Serialization ===")

    network = UDPClipboardNetwork()

    # Test with text data
    print("\n1. Testing text data:")
    test_text = "Hello from Windows test"
    text_data = ClipboardData(
        content=test_text,
        type=ClipboardType.TEXT,
        timestamp=time.time(),
        device_name="TestDevice"
    )

    serialized = network._serialize_clipboard_data(text_data)
    print(f"Serialized: {serialized}")

    deserialized = network._deserialize_clipboard_data(serialized)
    if deserialized:
        print(f"Deserialized successfully:")
        print(f"  Content: {deserialized.content}")
        print(f"  Type: {deserialized.type}")
        print(f"  Device: {deserialized.device_name}")
        print(f"  Timestamp: {deserialized.timestamp}")
    else:
        print("Deserialization failed!")

    # Test with Chinese characters
    print("\n2. Testing Chinese text:")
    chinese_text = "你好，世界！测试中文"
    chinese_data = ClipboardData(
        content=chinese_text,
        type=ClipboardType.TEXT,
        timestamp=time.time(),
        device_name="测试设备"
    )

    serialized_chinese = network._serialize_clipboard_data(chinese_data)
    print(f"Serialized Chinese: {serialized_chinese}")

    deserialized_chinese = network._deserialize_clipboard_data(serialized_chinese)
    if deserialized_chinese:
        print(f"Deserialized Chinese successfully:")
        print(f"  Content: {deserialized_chinese.content}")
        print(f"  Type: {deserialized_chinese.type}")
        print(f"  Device: {deserialized_chinese.device_name}")
    else:
        print("Chinese deserialization failed!")

    # Test full packet serialization
    print("\n3. Testing full packet serialization:")
    from interfaces import NetworkPacket
    packet = NetworkPacket(
        packet_type="clipboard_data",
        sender_name="TestSender",
        sender_ip="192.168.1.100",
        timestamp=time.time(),
        data=serialized
    )

    serialized_packet = network._serialize_packet(packet)
    print(f"Serialized packet length: {len(serialized_packet)} bytes")

    deserialized_packet = network._deserialize_packet(serialized_packet)
    if deserialized_packet:
        print("Packet deserialized successfully:")
        print(f"  Type: {deserialized_packet.packet_type}")
        print(f"  Sender: {deserialized_packet.sender_name}@{deserialized_packet.sender_ip}")
        print(f"  Data type: {type(deserialized_packet.data)}")

        if deserialized_packet.packet_type == "clipboard_data":
            clipboard_data = network._deserialize_clipboard_data(deserialized_packet.data)
            if clipboard_data:
                print(f"  Clipboard content: {clipboard_data.content}")
            else:
                print("  Clipboard data deserialization failed!")
    else:
        print("Packet deserialization failed!")

if __name__ == "__main__":
    test_serialization()