import hashlib
import hmac
import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from sample_events import EVENTS  # noqa: E402

import developer_intelligence.main as main_module  # noqa: E402
from developer_intelligence.store import Store  # noqa: E402

SECRET = "test-secret"


@pytest.fixture()
def client():
    main_module.store = Store(":memory:")
    return TestClient(main_module.app)


def post_event(client, event_type, payload, secret=None, signature=None):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "X-GitHub-Event": event_type}
    if signature is not None:
        headers["X-Hub-Signature-256"] = signature
    elif secret:
        digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        headers["X-Hub-Signature-256"] = f"sha256={digest}"
    return client.post("/webhooks/github", content=body, headers=headers)


def push_payload(repo="checkout-api", full="acme-platform/checkout-api", commits=2):
    return {
        "ref": "refs/heads/main",
        "repository": {"name": repo, "full_name": full},
        "pusher": {"name": "priya-dev"},
        "sender": {"login": "priya-dev"},
        "commits": [{"id": str(i)} for i in range(commits)],
        "head_commit": {"timestamp": "2026-11-10T15:42:00Z"},
    }


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_signature_accepted(client, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", SECRET)
    response = post_event(client, "push", push_payload(), secret=SECRET)
    assert response.status_code == 200
    assert response.json()["status"] == "stored"


def test_signature_rejected(client, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", SECRET)
    response = post_event(client, "push", push_payload(), signature="sha256=" + "0" * 64)
    assert response.status_code == 401


def test_signature_missing_rejected(client, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", SECRET)
    response = post_event(client, "push", push_payload())
    assert response.status_code == 401


def test_push_creates_service_and_event(client):
    response = post_event(client, "push", push_payload())
    assert response.json()["status"] == "stored"

    services = client.get("/services").json()
    assert len(services) == 1
    assert services[0]["service"] == "checkout-api"
    assert services[0]["event_count"] == 1
    assert services[0]["push_count"] == 1

    events = client.get("/events").json()
    assert len(events) == 1
    assert events[0]["summary"] == "priya-dev pushed 2 commits to main on checkout-api"


def test_deployment_updates_service_fields(client):
    post_event(client, "push", push_payload())
    post_event(
        client,
        "deployment",
        {
            "repository": {"name": "checkout-api", "full_name": "acme-platform/checkout-api"},
            "sender": {"login": "priya-dev"},
            "deployment": {
                "environment": "production",
                "ref": "main",
                "created_at": "2026-11-10T17:02:00Z",
            },
            "deployment_status": {"state": "success"},
        },
    )
    service = client.get("/services/checkout-api").json()
    assert service["deployment_count"] == 1
    assert service["last_deployment_environment"] == "production"
    assert service["last_deployment_status"] == "success"


def test_repository_created_registers_service(client):
    response = post_event(
        client,
        "repository",
        {
            "action": "created",
            "repository": {
                "name": "billing-worker",
                "full_name": "northwind-labs/billing-worker",
                "created_at": "2026-11-03T11:02:00Z",
            },
            "sender": {"login": "lena-builds"},
        },
    )
    assert response.json()["status"] == "stored"
    names = [s["service"] for s in client.get("/services").json()]
    assert names == ["billing-worker"]


def test_repository_other_action_ignored(client):
    response = post_event(
        client,
        "repository",
        {
            "action": "deleted",
            "repository": {"name": "old-service", "full_name": "acme-platform/old-service"},
            "sender": {"login": "priya-dev"},
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert client.get("/services").json() == []


def test_unknown_event_type_ignored(client):
    response = post_event(client, "issues", {"action": "opened"})
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert "issues" in response.json()["reason"]


def test_services_reflect_seeded_data(client):
    for event_type, payload in EVENTS:
        post_event(client, event_type, payload)
    services = {s["service"]: s for s in client.get("/services").json()}
    assert set(services) == {"checkout-api", "storefront-web", "billing-worker"}
    assert services["checkout-api"]["event_count"] == 5
    assert services["checkout-api"]["push_count"] == 2
    assert services["checkout-api"]["deployment_count"] == 2
    assert services["checkout-api"]["last_deployment_environment"] == "production"
    assert services["billing-worker"]["last_deployment_status"] == "failure"


def test_service_detail_returns_recent_events(client):
    for event_type, payload in EVENTS:
        post_event(client, event_type, payload)
    detail = client.get("/services/checkout-api").json()
    assert detail["service"] == "checkout-api"
    assert len(detail["recent_events"]) == 5
    assert detail["recent_events"][0]["event_type"] == "push"


def test_service_detail_unknown_404(client):
    assert client.get("/services/nope").status_code == 404


def test_events_filters(client):
    for event_type, payload in EVENTS:
        post_event(client, event_type, payload)
    pushes = client.get("/events", params={"type": "push"}).json()
    assert pushes and all(e["event_type"] == "push" for e in pushes)
    billing = client.get("/events", params={"service": "billing-worker"}).json()
    assert billing and all(e["service"] == "billing-worker" for e in billing)
    assert len(client.get("/events").json()) == len(EVENTS)
