# Developer Intelligence Platform

A small event-driven pipeline I built to answer a simple question: what is happening across my services right now? GitHub sends webhook events, the service normalizes them into one store, and a read API serves a per-service view of recent activity: pushes, deployments, and the last deployment result.

All sample data is synthetic. The repositories (checkout-api, storefront-web, billing-worker), the orgs, and the people in the seed data are invented.

## How it fits together

```
GitHub webhook (push, deployment, repository)
        |
        v
POST /webhooks/github  ->  verify signature (when a secret is set)
        |
        v
Normalize: service name from the repository, one summary sentence per event
        |
        v
Store: one row per event in SQLite
        |
        v
Read API: GET /services, GET /services/{name}, GET /events
```

## Quick start

You need Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn developer_intelligence.main:app --port 8000
```

In a second terminal, load the synthetic sample events:

```bash
python scripts/seed.py
```

Captured from a real run of the seed script:

```text
repository   acme-platform/checkout-api          -> stored
repository   acme-platform/storefront-web        -> stored
repository   northwind-labs/billing-worker       -> stored
push         acme-platform/checkout-api          -> stored
push         acme-platform/storefront-web        -> stored
push         northwind-labs/billing-worker       -> stored
deployment   acme-platform/checkout-api          -> stored
deployment   acme-platform/checkout-api          -> stored
push         acme-platform/checkout-api          -> stored
deployment   acme-platform/storefront-web        -> stored
push         northwind-labs/billing-worker       -> stored
deployment   northwind-labs/billing-worker       -> stored
push         acme-platform/storefront-web        -> stored
Sent 13 events to http://127.0.0.1:8000
```

Then read the API:

```bash
curl http://127.0.0.1:8000/services
```

```json
[
    {
        "service": "billing-worker",
        "repository": "northwind-labs/billing-worker",
        "event_count": 4,
        "push_count": 2,
        "deployment_count": 1,
        "last_activity": "2026-11-12T09:30:00Z",
        "last_deployment_environment": "production",
        "last_deployment_status": "failure"
    },
    {
        "service": "checkout-api",
        "repository": "acme-platform/checkout-api",
        "event_count": 5,
        "push_count": 2,
        "deployment_count": 2,
        "last_activity": "2026-11-11T09:12:00Z",
        "last_deployment_environment": "production",
        "last_deployment_status": "success"
    },
    {
        "service": "storefront-web",
        "repository": "acme-platform/storefront-web",
        "event_count": 4,
        "push_count": 2,
        "deployment_count": 1,
        "last_activity": "2026-11-12T13:18:00Z",
        "last_deployment_environment": "production",
        "last_deployment_status": "success"
    }
]
```

One service in detail, with its 20 most recent events:

```bash
curl http://127.0.0.1:8000/services/checkout-api
```

Filtered events, for example the failed billing-worker deployment:

```bash
curl "http://127.0.0.1:8000/events?service=billing-worker&type=deployment"
```

```json
[
    {
        "id": 12,
        "service": "billing-worker",
        "repository": "northwind-labs/billing-worker",
        "event_type": "deployment",
        "actor": "lena-builds",
        "summary": "Deployment of billing-worker to production finished with status failure",
        "ref": "main",
        "environment": "production",
        "status": "failure",
        "created_at": "2026-11-12T09:30:00Z",
        "received_at": "2026-11-13T19:49:19+00:00"
    }
]
```

## Endpoints

| Route | What it returns |
| --- | --- |
| GET /health | {"status": "ok"} |
| POST /webhooks/github | Stores one event, or returns a clear ignored response |
| GET /services | Every known service with counts and last deployment |
| GET /services/{name} | One service plus its 20 most recent events (404 when unknown) |
| GET /events | Most recent 50 events, optional service and type filters |

The webhook endpoint reads the event type from the X-GitHub-Event header. It handles push, deployment, and repository events. For repository events only the created action is stored; other actions get an ignored response that says why. Unknown event types get the same treatment.

## Design choices

**SQLite now, Postgres later.** Storage uses the standard library sqlite3 module. The schema sticks to standard types and plain SQL, and the services view is built from aggregation queries, so moving to Postgres later is a connection change rather than a rewrite. Set DATABASE_PATH to choose the database file; it defaults to events.db.

**Signature verification.** When the WEBHOOK_SECRET environment variable is set, every webhook must carry a valid X-Hub-Signature-256 HMAC header or it is rejected with 401. When the variable is unset, signatures are not checked. That is convenient on a laptop and unsafe on a public URL, so set the secret anywhere beyond local testing. The seed script signs its payloads when the same variable is set in its environment.

**Service derived from repository.** The service name is the repository name, and the full org and repository pair is stored alongside it. That keeps ingestion dumb: no registry to maintain before the first event arrives, and a repository created event registers the service on its own.

**One summary sentence per event.** Each stored event carries a plain sentence, such as "priya-dev pushed 2 commits to main on checkout-api". The read API stays simple, and the sentence is what a dashboard or a chat notification would show anyway.

## Limits

- No authentication on the read API. It is a local and demo tool in this version.
- Duplicate deliveries are stored twice. GitHub can redeliver webhooks, and this version does not deduplicate on a delivery id.
- Deployment status is only present when the payload carries a deployment_status block; a plain deployment event records the environment and leaves status empty.
- One process, one SQLite file. Fine for a demo, not for real traffic.

## Tests

```bash
pytest
```

13 tests cover signature accept and reject, one test per event type, the ignored responses, the services view against the full seed set, service detail, the 404 case, and the event filters.

## Roadmap

1. Postgres storage behind the same store interface.
2. A simple dashboard page that renders the services view.
3. Deployment frequency and lead time metrics per service.
