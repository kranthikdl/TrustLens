import requests
import json

# Simple test payload with a comment containing a URL
test_payload = {
    "filename": "test_evidence_integration.json",
    "data": {
        "comments": [
            {
                "id": "test1",
                "body": "Check out this article: https://www.example.com"
            },
            {
                "id": "test2",
                "body": "This is just an opinion with no sources"
            },
            {
                "id": "test3",
                "body": "Here's a news article: https://www.bbc.com/news and also https://www.wikipedia.org"
            }
        ]
    }
}

print("Sending test request to /ingest...")
response = requests.post("http://127.0.0.1:8000/ingest", json=test_payload, timeout=60)

print(f"\nStatus Code: {response.status_code}")
print(f"\nResponse:")
print(json.dumps(response.json(), indent=2))
