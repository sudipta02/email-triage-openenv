from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.routing import APIRoute
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.types import SchemaResponse

try:
    from email_triage_env.models import EmailTriageAction, EmailTriageObservation, EmailTriageState
    from email_triage_env.server.email_triage_environment import EmailTriageEnvironment
except ImportError:
    try:
        from models import EmailTriageAction, EmailTriageObservation, EmailTriageState
        from .email_triage_environment import EmailTriageEnvironment
    except ImportError:
        env_root = Path(__file__).resolve().parent.parent
        if str(env_root) not in sys.path:
            sys.path.insert(0, str(env_root))
        from models import EmailTriageAction, EmailTriageObservation, EmailTriageState
        from server.email_triage_environment import EmailTriageEnvironment


def create_email_triage_environment() -> EmailTriageEnvironment:
    default_task_id = os.getenv("EMAIL_TRIAGE_DEFAULT_TASK_ID")
    return EmailTriageEnvironment(default_task_id=default_task_id)


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
    try:
        return env.state
    finally:
        env.close()


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
