import urllib.request
import urllib.error
import json

paths = [
    "/finance/fees",
    "/finance/expenses",
    "/expenses"
]

BASE_URL = "http://localhost:8000"

for path in paths:
    url = BASE_URL + path
    print(f"--- Probing {url} ---")
    try:
        headers = {"Authorization": "Bearer dummy_token"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            print(f"Status: {response.getcode()}")
            print("OK")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")
