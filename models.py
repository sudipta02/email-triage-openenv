from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import BaseModel, Field


class EmailItem(BaseModel):
    email_id: str
    sender: str
    subject: str
    body: str
    customer_tier: Literal["free", "pro", "enterprise"]
    received_at: str


class ChecklistItemStatus(BaseModel):
    key: str
    description: str
    weight: float
    completed: bool


class EmailTriageAction(Action):
    """Agent action for triaging inbound email."""

    action_type: Literal["classify", "draft_reply", "set_follow_up", "close_case", "noop"]
    email_id: Optional[str] = None
    category: Optional[
        Literal[
            "bug_report",
            "billing_issue",
            "security_incident",
            "feature_request",
            "spam",
            "legal_request",
            "general_inquiry",
        ]
    ] = None
    priority: Optional[Literal["low", "medium", "high", "urgent"]] = None
    assignee: Optional[str] = None
    reply_template: Optional[
        Literal[
            "acknowledge_and_request_logs",
            "billing_refund_policy",
            "security_escalation",
            "legal_intake",
            "generic_followup",
        ]
    ] = None
    follow_up_days: Optional[int] = Field(default=None, ge=0, le=30)
    resolution_note: Optional[str] = None


class EmailTriageObservation(Observation):
    task_id: str
    difficulty: Literal["easy", "medium", "hard"]
    objective: str
    current_step: int
    max_steps: int
    inbox: List[EmailItem] = Field(default_factory=list)
    checklist: List[ChecklistItemStatus] = Field(default_factory=list)
    score: float = 0.0
    invalid_actions: int = 0
    last_feedback: str = ""


class EmailTriageState(State):
    task_id: str = ""
    difficulty: str = "easy"
    objective: str = ""
    score: float = 0.0
    completed_items: int = 0
    total_items: int = 0
    invalid_actions: int = 0
    max_steps: int = 0
    action_history: List[str] = Field(default_factory=list)
    workspace: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
