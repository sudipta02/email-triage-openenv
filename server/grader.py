from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set, Tuple

from .tasks import TriageTask


@dataclass
class GradeResult:
    completed_keys: Set[str]
    score: float
    new_credit: float


def _check_item(workspace: Dict[str, Dict[str, object]], expected: Dict[str, object]) -> bool:
    email_id = str(expected["email_id"])
    email_state = workspace.get(email_id, {})

    for field, expected_value in expected.items():
        if field == "email_id":
            continue
        if email_state.get(field) != expected_value:
            return False
    return True


def grade_task(
    task: TriageTask,
    workspace: Dict[str, Dict[str, object]],
    previous_completed: Set[str],
) -> GradeResult:
    completed = {
        item.key for item in task.checklist if _check_item(workspace, item.expected)
    }

    total_score = sum(item.weight for item in task.checklist if item.key in completed)
    prev_score = sum(item.weight for item in task.checklist if item.key in previous_completed)
    delta = max(0.0, total_score - prev_score)

    return GradeResult(completed_keys=completed, score=total_score, new_credit=delta)


def expected_values_for_email(task: TriageTask, email_id: str) -> Dict[str, object]:
    expected: Dict[str, object] = {}
    for item in task.checklist:
        if item.expected.get("email_id") != email_id:
            continue
        for key, value in item.expected.items():
            if key != "email_id":
                expected[key] = value
    return expected


def is_wrong_update(
    task: TriageTask,
    email_id: str,
    field: str,
    value: object,
) -> bool:
    expected = expected_values_for_email(task, email_id)
    if field not in expected:
        return False
    return expected[field] != value


def summarize_progress(task: TriageTask, completed: Set[str]) -> Tuple[int, int]:
    return len(completed), len(task.checklist)
