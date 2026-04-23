import requests

try:
    response = requests.post("http://localhost:8001/chat", json={
        "message": "Hello, can you help me log a meeting with Dr. Sarah Miller?",
        "hcp_id": 1
    })
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
