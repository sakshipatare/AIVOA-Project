import requests

try:
    response = requests.post("http://localhost:8001/chat", json={
        "message": "Update the outcome to 'successful' for the last interaction",
        "hcp_id": 1
    })
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
