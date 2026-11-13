import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL,
    repository TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT,
    summary TEXT NOT NULL,
    ref TEXT,
    environment TEXT,
    status TEXT,
    created_at TEXT,
    received_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_service ON events (service);
"""


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    """SQLite storage. The SQL here sticks to standard types and queries so
    moving to Postgres later is a connection change, not a rewrite."""

    def __init__(self, path=":memory:"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def add_event(self, event):
        cur = self.conn.execute(
            """
            INSERT INTO events
                (service, repository, event_type, actor, summary, ref,
                 environment, status, created_at, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["service"],
                event["repository"],
                event["event_type"],
                event.get("actor"),
                event["summary"],
                event.get("ref"),
                event.get("environment"),
                event.get("status"),
                event.get("created_at"),
                utc_now(),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def list_events(self, service=None, event_type=None, limit=50):
        query = "SELECT * FROM events"
        clauses, params = [], []
        if service:
            clauses.append("service = ?")
            params.append(service)
        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return [dict(row) for row in self.conn.execute(query, params)]

    def list_services(self):
        rows = self.conn.execute(
            """
            SELECT service,
                   MAX(repository) AS repository,
                   COUNT(*) AS event_count,
                   SUM(event_type = 'push') AS push_count,
                   SUM(event_type = 'deployment') AS deployment_count,
                   MAX(COALESCE(created_at, received_at)) AS last_activity
            FROM events
            GROUP BY service
            ORDER BY service
            """
        ).fetchall()
        services = []
        for row in rows:
            service = dict(row)
            service.update(self._last_deployment(service["service"]))
            services.append(service)
        return services

    def get_service(self, name):
        for service in self.list_services():
            if service["service"] == name:
                service["recent_events"] = self.list_events(service=name, limit=20)
                return service
        return None

    def _last_deployment(self, service):
        row = self.conn.execute(
            """
            SELECT environment, status FROM events
            WHERE service = ? AND event_type = 'deployment'
            ORDER BY id DESC LIMIT 1
            """,
            (service,),
        ).fetchone()
        if row is None:
            return {"last_deployment_environment": None, "last_deployment_status": None}
        return {
            "last_deployment_environment": row["environment"],
            "last_deployment_status": row["status"],
        }
