#!/usr/bin/env python3
"""Network diagnostic tool for troubleshooting cross-platform device discovery."""

import sys
import os
import socket
import platform
import subprocess

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from platforms.network import UDPClipboardNetwork

def run_network_diagnostics():
    """Run comprehensive network diagnostics."""
    print("=== Network Diagnostics ===")
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")

    # Test basic socket operations
    print("\n=== Basic Socket Tests ===")
    test_socket_operations()

    # Test network interfaces
    print("\n=== Network Interfaces ===")
    test_network_interfaces()

    # Test UDP broadcast
    print("\n=== UDP Broadcast Tests ===")
    test_udp_broadcast()

    # Test firewall status
    print("\n=== Firewall Status ===")
    test_firewall_status()

    print("\n=== Recommendations ===")
    provide_recommendations()

def test_socket_operations():
    """Test basic socket operations."""
    try:
        # Test socket creation
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("✓ UDP socket creation successful")

        # Test SO_REUSEADDR
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("✓ SO_REUSEADDR set successfully")

        # Test SO_BROADCAST
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print("✓ SO_BROADCAST set successfully")

        # Test SO_REUSEPORT if available
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            print("✓ SO_REUSEPORT set successfully")
        except (AttributeError, OSError) as e:
            print(f"⚠ SO_REUSEPORT not available: {e}")

        # Test port binding
        try:
            s.bind(('', 5555))
            print("✓ Port 5555 bind successful")
        except OSError as e:
            print(f"⚠ Port 5555 bind failed: {e}")

        s.close()

    except Exception as e:
        print(f"✗ Socket test failed: {e}")

def test_network_interfaces():
    """Test network interfaces and IP detection."""
    try:
        hostname = socket.gethostname()
        print(f"Hostname: {hostname}")

        # Get local IP using same method as network.py
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                print(f"Local IP (via 8.8.8.8): {local_ip}")
        except Exception:
            local_ip = "127.0.0.1"
            print(f"⚠ Could not detect external IP, using: {local_ip}")

        # Get all interfaces
        if platform.system() != 'Windows':
            try:
                result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Network interfaces (ip addr):")
                    for line in result.stdout.split('\n'):
                        if 'inet ' in line and not '127.0.0.1' in line:
                            print(f"  {line.strip()}")
            except FileNotFoundError:
                pass
        else:
            # Windows ipconfig
            try:
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Network interfaces (ipconfig):")
                    for line in result.stdout.split('\n'):
                        if 'IPv4' in line or 'IP Address' in line:
                            print(f"  {line.strip()}")
            except Exception:
                pass

    except Exception as e:
        print(f"✗ Network interface test failed: {e}")

def test_udp_broadcast():
    """Test UDP broadcast functionality."""
    try:
        # Test receiving broadcast
        print("Testing broadcast reception...")

        # Create a test socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        try:
            test_socket.bind(('', 5555))
            test_socket.settimeout(2.0)
            print("✓ Test socket bound to port 5555")

            # Try to send a test broadcast
            test_msg = b"test_broadcast"
            test_socket.sendto(test_msg, ('<broadcast>', 5555))
            print("✓ Test broadcast sent to <broadcast>:5555")

            # Try specific broadcast addresses
            test_socket.sendto(test_msg, ('255.255.255.255', 5555))
            print("✓ Test broadcast sent to 255.255.255.255:5555")

        except Exception as e:
            print(f"⚠ Broadcast test issue: {e}")
        finally:
            test_socket.close()

    except Exception as e:
        print(f"✗ UDP broadcast test failed: {e}")

def test_firewall_status():
    """Test firewall status and rules."""
    system = platform.system()

    if system == 'Windows':
        try:
            # Check if firewall rule exists
            result = subprocess.run([
                'powershell', '-Command',
                'Get-NetFirewallRule -DisplayName "SyncClip UDP" -ErrorAction SilentlyContinue | Select-Object DisplayName, Enabled, Action'
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout.strip():
                print("Windows Firewall rules:")
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")
            else:
                print("⚠ No SyncClip UDP firewall rule found")
                print("  Run: fix_firewall.ps1 as Administrator")

        except Exception as e:
            print(f"⚠ Could not check Windows firewall: {e}")

    elif system in ['Linux', 'Darwin']:  # Darwin is macOS
        try:
            if system == 'Linux':
                # Check UFW status
                result = subprocess.run(['ufw', 'status'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("UFW Status:")
                    for line in result.stdout.strip().split('\n'):
                        print(f"  {line}")

                # Check iptables rules
                result = subprocess.run(['iptables', '-L', '-n'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("iptables rules (UDP 5555-5559):")
                    for line in result.stdout.split('\n'):
                        if '555' in line and 'udp' in line.lower():
                            print(f"  {line.strip()}")

            elif system == 'Darwin':
                # Check pfctl (macOS firewall)
                result = subprocess.run(['sudo', 'pfctl', '-sr'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("macOS pfctl rules:")
                    for line in result.stdout.split('\n'):
                        if '555' in line:
                            print(f"  {line.strip()}")

        except Exception as e:
            print(f"⚠ Could not check firewall rules: {e}")

def provide_recommendations():
    """Provide troubleshooting recommendations."""
    system = platform.system()

    print("Based on the diagnostic results:")

    if system == 'Windows':
        print("\n1. Windows-specific steps:")
        print("   - Run PowerShell as Administrator")
        print("   - Execute: .\\fix_firewall.ps1")
        print("   - Check Windows Defender firewall settings")
        print("   - Ensure UDP ports 5555-5559 are allowed")

    elif system == 'Linux':
        print("\n1. Linux-specific steps:")
        print("   - Check: sudo ufw status")
        print("   - Allow UDP: sudo ufw allow 5555:5559/udp")
        print("   - Or disable temporarily: sudo ufw disable")
        print("   - Check iptables: sudo iptables -L -n | grep 555")

    elif system == 'Darwin':
        print("\n1. macOS-specific steps:")
        print("   - System Preferences > Security & Privacy > Firewall")
        print("   - Disable firewall temporarily for testing")
        print("   - Check pfctl rules if using pf firewall")

    print("\n2. General troubleshooting:")
    print("   - Ensure devices are on the same network/subnet")
    print("   - Check if any VPN is blocking local network traffic")
    print("   - Try disabling antivirus/firewall temporarily")
    print("   - Run this diagnostic on both devices")
    print("   - Test with: uv run python test_device_discovery.py")

if __name__ == "__main__":
    run_network_diagnostics()