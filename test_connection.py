#!/usr/bin/env python3
"""
Test script to verify HeartLink network connectivity
"""
import requests
import socket
import sys

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return None

def test_backend(url):
    """Test if backend is reachable"""
    try:
        # Disable SSL verification for self-signed certificates
        # Try the sessions endpoint which should exist
        response = requests.get(f"{url}/api/sessions", verify=False, timeout=5)
        if response.status_code == 200:
            return True, "Backend is responding"
        else:
            return False, f"Status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused - is the server running?"
    except requests.exceptions.Timeout:
        return False, "Connection timeout"
    except Exception as e:
        return False, str(e)

def main():
    print("🧪 HeartLink Network Connection Test")
    print("="*70)
    
    local_ip = get_local_ip()
    if not local_ip:
        print("❌ Could not determine local IP address")
        return
    
    print(f"📍 Local IP: {local_ip}\n")
    
    # Test localhost
    print("Testing localhost connection...")
    success, result = test_backend("https://localhost:8765")
    if success:
        print(f"✅ Localhost: OK")
        print(f"   Response: {result}")
    else:
        print(f"❌ Localhost: FAILED")
        print(f"   Error: {result}")
    
    print()
    
    # Test network IP
    print(f"Testing network connection ({local_ip})...")
    success, result = test_backend(f"https://{local_ip}:8765")
    if success:
        print(f"✅ Network IP: OK")
        print(f"   Response: {result}")
    else:
        print(f"❌ Network IP: FAILED")
        print(f"   Error: {result}")
    
    print("\n" + "="*70)
    print("\n💡 Tips:")
    print("   - Make sure the backend is running: python app.py")
    print("   - Check firewall settings if network IP test fails")
    print("   - Ignore SSL certificate warnings (we use self-signed certs)")
    print()

if __name__ == "__main__":
    # Suppress SSL warnings for testing
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main()

