import requests
import socket

print("Testing DNS resolution for huggingface.co...")
try:
    info = socket.getaddrinfo("huggingface.co", 443)
    print(f"DNS Resolution successful: {info}")
except Exception as e:
    print(f"DNS Resolution failed: {e}")

print("\nTesting requests.get('https://huggingface.co')...")
try:
    response = requests.get("https://huggingface.co", timeout=5)
    print(f"Response code: {response.status_code}")
except Exception as e:
    print(f"Request failed: {e}")
