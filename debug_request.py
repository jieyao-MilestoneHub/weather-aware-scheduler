import requests
import json

url = "http://localhost:8000/api/schedule"
payload = {"input": "Tomorrow 2pm Taipei meet Alice 60min"}
headers = {"Content-Type": "application/json"}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print("Headers:")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")
    
    print("\nBody:")
    print(response.text)
    
    try:
        json_data = response.json()
        print("\nJSON parsed successfully.")
        print(json.dumps(json_data, indent=2))
    except json.JSONDecodeError as e:
        print(f"\nJSON Decode Error: {e}")

except Exception as e:
    print(f"Request failed: {e}")
