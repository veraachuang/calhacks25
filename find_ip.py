#!/usr/bin/env python3
"""
Quick script to find your local IP address for the video chat server
"""
import socket

def get_local_ip():
    """Get the local IP address"""
    try:
        # Create a socket and connect to an external address
        # This doesn't actually send data, just determines the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    ip = get_local_ip()
    port = 8765  # Match the port in app.py
    
    print("\n" + "="*60)
    print("🌐 VIDEO CHAT SERVER CONNECTION INFO")
    print("="*60)
    print(f"\n📍 Your Local IP Address: {ip}")
    print(f"\n🔗 Share this URL with the other person:")
    print(f"   https://{ip}:{port}")
    print(f"\n💻 On this machine, use:")
    print(f"   https://localhost:{port}")
    print(f"\n⚠️  Important: Remote user must accept the browser")
    print(f"   security warning (self-signed certificate)")
    print("\n" + "="*60 + "\n")


