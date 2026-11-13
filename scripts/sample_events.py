"""Synthetic GitHub webhook payloads. Every org, repository, and person
here is invented, and the payloads are trimmed to the fields the
normalizer actually reads."""

EVENTS = [
    (
        "repository",
        {
            "action": "created",
            "repository": {
                "name": "checkout-api",
                "full_name": "acme-platform/checkout-api",
                "created_at": "2026-11-02T09:14:00Z",
            },
            "sender": {"login": "priya-dev"},
        },
    ),
    (
        "repository",
        {
            "action": "created",
            "repository": {
                "name": "storefront-web",
                "full_name": "acme-platform/storefront-web",
                "created_at": "2026-11-02T09:20:00Z",
            },
            "sender": {"login": "marcus-ops"},
        },
    ),
    (
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
    ),
    (
        "push",
        {
            "ref": "refs/heads/main",
            "repository": {"name": "checkout-api", "full_name": "acme-platform/checkout-api"},
            "pusher": {"name": "priya-dev"},
            "sender": {"login": "priya-dev"},
            "commits": [{"id": "a1"}, {"id": "a2"}, {"id": "a3"}],
            "head_commit": {"timestamp": "2026-11-10T15:42:00Z"},
        },
    ),
    (
        "push",
        {
            "ref": "refs/heads/main",
            "repository": {"name": "storefront-web", "full_name": "acme-platform/storefront-web"},
            "pusher": {"name": "marcus-ops"},
            "sender": {"login": "marcus-ops"},
            "commits": [{"id": "b1"}],
            "head_commit": {"timestamp": "2026-11-10T16:05:00Z"},
        },
    ),
    (
        "push",
        {
            "ref": "refs/heads/fix/retry-backoff",
            "repository": {"name": "billing-worker", "full_name": "northwind-labs/billing-worker"},
            "pusher": {"name": "lena-builds"},
            "sender": {"login": "lena-builds"},
            "commits": [{"id": "c1"}, {"id": "c2"}],
            "head_commit": {"timestamp": "2026-11-11T10:31:00Z"},
        },
    ),
    (
        "deployment",
        {
            "repository": {"name": "checkout-api", "full_name": "acme-platform/checkout-api"},
            "sender": {"login": "priya-dev"},
            "deployment": {
                "environment": "staging",
                "ref": "main",
                "created_at": "2026-11-10T16:20:00Z",
            },
        },
    ),
    (
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
    ),
    (
        "push",
        {
            "ref": "refs/heads/main",
            "repository": {"name": "checkout-api", "full_name": "acme-platform/checkout-api"},
            "pusher": {"name": "tom-releases"},
            "sender": {"login": "tom-releases"},
            "commits": [{"id": "a4"}],
            "head_commit": {"timestamp": "2026-11-11T09:12:00Z"},
        },
    ),
    (
        "deployment",
        {
            "repository": {"name": "storefront-web", "full_name": "acme-platform/storefront-web"},
            "sender": {"login": "marcus-ops"},
            "deployment": {
                "environment": "production",
                "ref": "main",
                "created_at": "2026-11-11T12:44:00Z",
            },
            "deployment_status": {"state": "success"},
        },
    ),
    (
        "push",
        {
            "ref": "refs/heads/main",
            "repository": {"name": "billing-worker", "full_name": "northwind-labs/billing-worker"},
            "pusher": {"name": "lena-builds"},
            "sender": {"login": "lena-builds"},
            "commits": [{"id": "c3"}, {"id": "c4"}, {"id": "c5"}, {"id": "c6"}],
            "head_commit": {"timestamp": "2026-11-12T08:57:00Z"},
        },
    ),
    (
        "deployment",
        {
            "repository": {"name": "billing-worker", "full_name": "northwind-labs/billing-worker"},
            "sender": {"login": "lena-builds"},
            "deployment": {
                "environment": "production",
                "ref": "main",
                "created_at": "2026-11-12T09:30:00Z",
            },
            "deployment_status": {"state": "failure"},
        },
    ),
    (
        "push",
        {
            "ref": "refs/heads/main",
            "repository": {"name": "storefront-web", "full_name": "acme-platform/storefront-web"},
            "pusher": {"name": "marcus-ops"},
            "sender": {"login": "marcus-ops"},
            "commits": [{"id": "b2"}, {"id": "b3"}],
            "head_commit": {"timestamp": "2026-11-12T13:18:00Z"},
        },
    ),
]
