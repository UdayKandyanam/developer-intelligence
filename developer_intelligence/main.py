import hashlib
import hmac
import os

from fastapi import FastAPI, Header, HTTPException, Request

from .normalize import normalize_deployment, normalize_push, normalize_repository
from .store import Store

DB_PATH = os.environ.get("DATABASE_PATH", "events.db")

app = FastAPI(title="Developer Intelligence Platform")
store = Store(DB_PATH)


def verify_signature(secret, body, signature_header):
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header[len("sha256="):])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
):
    body = await request.body()
    secret = os.environ.get("WEBHOOK_SECRET")
    if secret and not verify_signature(secret, body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event_type = x_github_event or "unknown"

    if event_type == "push":
        event = normalize_push(payload)
    elif event_type == "deployment":
        event = normalize_deployment(payload)
    elif event_type == "repository":
        if payload.get("action") != "created":
            return {
                "status": "ignored",
                "reason": f"repository action '{payload.get('action')}' is not tracked",
            }
        event = normalize_repository(payload)
    else:
        return {"status": "ignored", "reason": f"event type '{event_type}' is not tracked"}

    event_id = store.add_event(event)
    return {"status": "stored", "id": event_id, "service": event["service"], "event_type": event_type}


@app.get("/services")
def services():
    return store.list_services()


@app.get("/services/{name}")
def service_detail(name: str):
    service = store.get_service(name)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Unknown service '{name}'")
    return service


@app.get("/events")
def events(service: str | None = None, type: str | None = None):
    return store.list_events(service=service, event_type=type, limit=50)
