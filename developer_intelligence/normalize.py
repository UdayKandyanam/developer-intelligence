from pydantic import BaseModel


class Repository(BaseModel):
    name: str
    full_name: str
    created_at: str | None = None


class Sender(BaseModel):
    login: str


class PushPayload(BaseModel):
    ref: str
    repository: Repository
    pusher: dict = {}
    sender: Sender | None = None
    commits: list[dict] = []
    head_commit: dict | None = None


class DeploymentPayload(BaseModel):
    action: str | None = None
    repository: Repository
    sender: Sender | None = None
    deployment: dict = {}
    deployment_status: dict | None = None


class RepositoryPayload(BaseModel):
    action: str
    repository: Repository
    sender: Sender | None = None


def short_ref(ref):
    if ref and ref.startswith("refs/heads/"):
        return ref[len("refs/heads/"):]
    return ref


def normalize_push(payload):
    data = PushPayload.model_validate(payload)
    branch = short_ref(data.ref)
    count = len(data.commits)
    noun = "commit" if count == 1 else "commits"
    actor = data.pusher.get("name") or (data.sender.login if data.sender else None)
    created_at = None
    if data.head_commit:
        created_at = data.head_commit.get("timestamp")
    return {
        "service": data.repository.name,
        "repository": data.repository.full_name,
        "event_type": "push",
        "actor": actor,
        "summary": f"{actor} pushed {count} {noun} to {branch} on {data.repository.name}",
        "ref": branch,
        "environment": None,
        "status": None,
        "created_at": created_at,
    }


def normalize_deployment(payload):
    data = DeploymentPayload.model_validate(payload)
    deployment = data.deployment
    environment = deployment.get("environment")
    actor = data.sender.login if data.sender else None
    status = None
    if data.deployment_status:
        status = data.deployment_status.get("state")
    summary = f"Deployment of {data.repository.name} to {environment} recorded"
    if status:
        summary = f"Deployment of {data.repository.name} to {environment} finished with status {status}"
    return {
        "service": data.repository.name,
        "repository": data.repository.full_name,
        "event_type": "deployment",
        "actor": actor,
        "summary": summary,
        "ref": deployment.get("ref"),
        "environment": environment,
        "status": status,
        "created_at": deployment.get("created_at"),
    }


def normalize_repository(payload):
    data = RepositoryPayload.model_validate(payload)
    actor = data.sender.login if data.sender else None
    return {
        "service": data.repository.name,
        "repository": data.repository.full_name,
        "event_type": "repository",
        "actor": actor,
        "summary": f"Repository {data.repository.full_name} created by {actor}",
        "ref": None,
        "environment": None,
        "status": None,
        "created_at": data.repository.created_at,
    }
