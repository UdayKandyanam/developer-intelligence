"""Post the synthetic sample events to a running server.

Usage: python scripts/seed.py [base_url]   (default http://127.0.0.1:8000)
If the server has WEBHOOK_SECRET set, set the same value in this
script's environment and the payloads are signed.
"""

import hashlib
import hmac
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sample_events import EVENTS


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    secret = os.environ.get("WEBHOOK_SECRET")
    for event_type, payload in EVENTS:
        body = json.dumps(payload).encode()
        request = urllib.request.Request(
            f"{base_url}/webhooks/github",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "X-GitHub-Event": event_type},
        )
        if secret:
            signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            request.add_header("X-Hub-Signature-256", f"sha256={signature}")
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read())
        print(f"{event_type:12} {payload['repository']['full_name']:35} -> {result['status']}")
    print(f"Sent {len(EVENTS)} events to {base_url}")


if __name__ == "__main__":
    main()
