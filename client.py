from __future__ import annotations

from typing import Any, Dict

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

from .models import EmailTriageAction, EmailTriageObservation, EmailTriageState


class EmailTriageEnv(EnvClient[EmailTriageAction, EmailTriageObservation, EmailTriageState]):
    """WebSocket client for the Email Triage environment."""

    def _step_payload(self, action: EmailTriageAction) -> Dict[str, Any]:
        return action.model_dump()

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[EmailTriageObservation]:
        observation_payload = payload.get("observation", {})
        observation = EmailTriageObservation(**observation_payload)
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> EmailTriageState:
        return EmailTriageState(**payload)
