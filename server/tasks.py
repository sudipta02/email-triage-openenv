from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal


Difficulty = Literal["easy", "medium", "hard"]


@dataclass(frozen=True)
class ChecklistItem:
    key: str
    description: str
    weight: float
    expected: Dict[str, Any]


@dataclass(frozen=True)
class TriageTask:
    task_id: str
    difficulty: Difficulty
    objective: str
    max_steps: int
    emails: List[Dict[str, Any]]
    checklist: List[ChecklistItem]


TASKS: Dict[str, TriageTask] = {
    "easy_security_triage": TriageTask(
        task_id="easy_security_triage",
        difficulty="easy",
        objective=(
            "Prioritize and contain a suspicious login alert while ignoring low-risk noise."
        ),
        max_steps=8,
        emails=[
            {
                "email_id": "E-100",
                "sender": "sec-alerts@acmebank.example",
                "subject": "Unusual login from new device",
                "body": "A privileged account signed in from a new country."
                " Confirm if this is expected and rotate credentials if needed.",
                "customer_tier": "enterprise",
                "received_at": "2026-03-28T09:00:00Z",
            },
            {
                "email_id": "E-101",
                "sender": "newsletter@vendor.example",
                "subject": "Weekly product digest",
                "body": "No action required. Promotional newsletter.",
                "customer_tier": "free",
                "received_at": "2026-03-28T09:02:00Z",
            },
        ],
        checklist=[
            ChecklistItem(
                key="e100_category",
                description="Classify E-100 as a security incident.",
                weight=0.20,
                expected={"email_id": "E-100", "category": "security_incident"},
            ),
            ChecklistItem(
                key="e100_priority",
                description="Mark E-100 as urgent.",
                weight=0.15,
                expected={"email_id": "E-100", "priority": "urgent"},
            ),
            ChecklistItem(
                key="e100_assignee",
                description="Assign E-100 to security_team.",
                weight=0.15,
                expected={"email_id": "E-100", "assignee": "security_team"},
            ),
            ChecklistItem(
                key="e100_reply",
                description="Send security escalation response for E-100.",
                weight=0.20,
                expected={"email_id": "E-100", "reply_template": "security_escalation"},
            ),
            ChecklistItem(
                key="e100_followup",
                description="Set a 1-day follow-up for E-100.",
                weight=0.15,
                expected={"email_id": "E-100", "follow_up_days": 1},
            ),
            ChecklistItem(
                key="e100_close",
                description="Close E-100 with a resolution note.",
                weight=0.15,
                expected={"email_id": "E-100", "closed": True},
            ),
        ],
    ),
    "medium_billing_outage": TriageTask(
        task_id="medium_billing_outage",
        difficulty="medium",
        objective=(
            "Handle a billing dispute and a service outage report with correct prioritization"
            " and ownership."
        ),
        max_steps=12,
        emails=[
            {
                "email_id": "E-200",
                "sender": "ap@northwind.example",
                "subject": "Invoice mismatch on March bill",
                "body": "We were charged for 25 seats but only have 20 active seats.",
                "customer_tier": "pro",
                "received_at": "2026-03-28T08:30:00Z",
            },
            {
                "email_id": "E-201",
                "sender": "ops@globex.example",
                "subject": "Production API latency spike",
                "body": "P95 latency > 8s for critical write endpoints.",
                "customer_tier": "enterprise",
                "received_at": "2026-03-28T08:31:00Z",
            },
            {
                "email_id": "E-202",
                "sender": "marketing@globex.example",
                "subject": "Sponsorship inquiry",
                "body": "Exploring co-marketing opportunities.",
                "customer_tier": "free",
                "received_at": "2026-03-28T08:35:00Z",
            },
        ],
        checklist=[
            ChecklistItem(
                key="e200_category",
                description="Classify E-200 as billing_issue.",
                weight=0.10,
                expected={"email_id": "E-200", "category": "billing_issue"},
            ),
            ChecklistItem(
                key="e200_priority",
                description="Mark E-200 as medium priority.",
                weight=0.10,
                expected={"email_id": "E-200", "priority": "medium"},
            ),
            ChecklistItem(
                key="e200_assignee",
                description="Assign E-200 to billing_ops.",
                weight=0.10,
                expected={"email_id": "E-200", "assignee": "billing_ops"},
            ),
            ChecklistItem(
                key="e200_reply",
                description="Respond to E-200 with billing refund policy.",
                weight=0.10,
                expected={"email_id": "E-200", "reply_template": "billing_refund_policy"},
            ),
            ChecklistItem(
                key="e200_followup",
                description="Set a 3-day follow-up for E-200.",
                weight=0.10,
                expected={"email_id": "E-200", "follow_up_days": 3},
            ),
            ChecklistItem(
                key="e201_category",
                description="Classify E-201 as bug_report.",
                weight=0.10,
                expected={"email_id": "E-201", "category": "bug_report"},
            ),
            ChecklistItem(
                key="e201_priority",
                description="Mark E-201 as urgent.",
                weight=0.10,
                expected={"email_id": "E-201", "priority": "urgent"},
            ),
            ChecklistItem(
                key="e201_assignee",
                description="Assign E-201 to sre_oncall.",
                weight=0.10,
                expected={"email_id": "E-201", "assignee": "sre_oncall"},
            ),
            ChecklistItem(
                key="e201_reply",
                description="Respond to E-201 requesting logs and impact details.",
                weight=0.10,
                expected={"email_id": "E-201", "reply_template": "acknowledge_and_request_logs"},
            ),
            ChecklistItem(
                key="e201_followup",
                description="Set same-day follow-up for E-201.",
                weight=0.10,
                expected={"email_id": "E-201", "follow_up_days": 0},
            ),
        ],
    ),
    "hard_vip_legal_security": TriageTask(
        task_id="hard_vip_legal_security",
        difficulty="hard",
        objective=(
            "Triage a mixed inbox where VIP uptime, legal discovery, and suspected"
            " account takeover must all be handled correctly under time pressure."
        ),
        max_steps=16,
        emails=[
            {
                "email_id": "E-300",
                "sender": "cto@blueorbit.example",
                "subject": "VIP customer reports data sync failure",
                "body": "Enterprise CTO reports failed sync jobs in production.",
                "customer_tier": "enterprise",
                "received_at": "2026-03-28T07:40:00Z",
            },
            {
                "email_id": "E-301",
                "sender": "legal@blueorbit.example",
                "subject": "Litigation hold request",
                "body": "Please preserve and acknowledge retention workflow.",
                "customer_tier": "enterprise",
                "received_at": "2026-03-28T07:44:00Z",
            },
            {
                "email_id": "E-302",
                "sender": "alerts@identity.example",
                "subject": "Password reset storm detected",
                "body": "20 password reset attempts in 4 minutes for same admin account.",
                "customer_tier": "enterprise",
                "received_at": "2026-03-28T07:47:00Z",
            },
            {
                "email_id": "E-303",
                "sender": "community@forum.example",
                "subject": "Feature request: dark mode variant",
                "body": "General product feedback from community thread.",
                "customer_tier": "free",
                "received_at": "2026-03-28T07:50:00Z",
            },
        ],
        checklist=[
            ChecklistItem(
                key="e300_category",
                description="Classify E-300 as bug_report.",
                weight=0.07,
                expected={"email_id": "E-300", "category": "bug_report"},
            ),
            ChecklistItem(
                key="e300_priority",
                description="Mark E-300 as high priority.",
                weight=0.07,
                expected={"email_id": "E-300", "priority": "high"},
            ),
            ChecklistItem(
                key="e300_assignee",
                description="Assign E-300 to enterprise_support.",
                weight=0.07,
                expected={"email_id": "E-300", "assignee": "enterprise_support"},
            ),
            ChecklistItem(
                key="e300_reply",
                description="Send acknowledge_and_request_logs for E-300.",
                weight=0.07,
                expected={"email_id": "E-300", "reply_template": "acknowledge_and_request_logs"},
            ),
            ChecklistItem(
                key="e301_category",
                description="Classify E-301 as legal_request.",
                weight=0.07,
                expected={"email_id": "E-301", "category": "legal_request"},
            ),
            ChecklistItem(
                key="e301_priority",
                description="Mark E-301 as high priority.",
                weight=0.07,
                expected={"email_id": "E-301", "priority": "high"},
            ),
            ChecklistItem(
                key="e301_assignee",
                description="Assign E-301 to legal_ops.",
                weight=0.07,
                expected={"email_id": "E-301", "assignee": "legal_ops"},
            ),
            ChecklistItem(
                key="e301_reply",
                description="Send legal_intake response for E-301.",
                weight=0.07,
                expected={"email_id": "E-301", "reply_template": "legal_intake"},
            ),
            ChecklistItem(
                key="e302_category",
                description="Classify E-302 as security_incident.",
                weight=0.07,
                expected={"email_id": "E-302", "category": "security_incident"},
            ),
            ChecklistItem(
                key="e302_priority",
                description="Mark E-302 as urgent.",
                weight=0.07,
                expected={"email_id": "E-302", "priority": "urgent"},
            ),
            ChecklistItem(
                key="e302_assignee",
                description="Assign E-302 to security_team.",
                weight=0.07,
                expected={"email_id": "E-302", "assignee": "security_team"},
            ),
            ChecklistItem(
                key="e302_reply",
                description="Send security_escalation response for E-302.",
                weight=0.07,
                expected={"email_id": "E-302", "reply_template": "security_escalation"},
            ),
            ChecklistItem(
                key="e302_followup",
                description="Set same-day follow-up for E-302.",
                weight=0.04,
                expected={"email_id": "E-302", "follow_up_days": 0},
            ),
            ChecklistItem(
                key="e300_close",
                description="Close E-300 after triage actions.",
                weight=0.04,
                expected={"email_id": "E-300", "closed": True},
            ),
            ChecklistItem(
                key="e301_close",
                description="Close E-301 after legal intake actions.",
                weight=0.04,
                expected={"email_id": "E-301", "closed": True},
            ),
            ChecklistItem(
                key="e302_close",
                description="Close E-302 after incident escalation.",
                weight=0.04,
                expected={"email_id": "E-302", "closed": True},
            ),
        ],
    ),
}


def get_task(task_id: str) -> TriageTask:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task_id: {task_id}")
    return TASKS[task_id]


def get_task_ids() -> List[str]:
    return sorted(TASKS.keys())
