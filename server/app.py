from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi.routing import APIRoute
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.types import SchemaResponse

# Import models and environment - try package style first, fall back to repo style
try:
    from ..models import EmailTriageAction, EmailTriageObservation, EmailTriageState
    from .email_triage_environment import EmailTriageEnvironment
except ImportError:
    # When running outside package context, add root to path
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from models import EmailTriageAction, EmailTriageObservation, EmailTriageState
    from server.email_triage_environment import EmailTriageEnvironment


_SHARED_ENV: Optional[EmailTriageEnvironment] = None


def create_email_triage_environment() -> EmailTriageEnvironment:
    global _SHARED_ENV
    if _SHARED_ENV is None:
        default_task_id = os.getenv("EMAIL_TRIAGE_DEFAULT_TASK_ID")
        _SHARED_ENV = EmailTriageEnvironment(default_task_id=default_task_id)
    return _SHARED_ENV


MAX_CONCURRENT_ENVS = int(os.getenv("MAX_CONCURRENT_ENVS", "64"))

app = create_app(
    create_email_triage_environment,
    EmailTriageAction,
    EmailTriageObservation,
    env_name="email_triage_env",
    max_concurrent_envs=MAX_CONCURRENT_ENVS,
)


app.router.routes = [
    route
    for route in app.router.routes
    if not (
        isinstance(route, APIRoute)
        and route.path in {"/state", "/schema"}
        and route.methods
        and "GET" in route.methods
    )
]
app.openapi_schema = None


@app.get("/state", response_model=EmailTriageState, tags=["State Management"])
def get_state() -> EmailTriageState:
    env = create_email_triage_environment()
    return env.state


@app.get("/schema", response_model=SchemaResponse, tags=["Schema"])
def get_schema() -> SchemaResponse:
    return SchemaResponse(
        action=EmailTriageAction.model_json_schema(),
        observation=EmailTriageObservation.model_json_schema(),
        state=EmailTriageState.model_json_schema(),
    )


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
