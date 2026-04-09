from __future__ import annotations

import random
from typing import Any, Dict, Optional, Set
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment

try:
    from ..models import (
        ChecklistItemStatus,
        EmailItem,
        EmailTriageAction,
        EmailTriageObservation,
        EmailTriageState,
    )
except ImportError:
    from models import ChecklistItemStatus, EmailItem, EmailTriageAction, EmailTriageObservation, EmailTriageState

try:
    from .grader import grade_task, is_wrong_update, minimum_bounded_score, summarize_progress
    from .tasks import TASKS, TriageTask, get_task, get_task_ids
except ImportError:
    from server.grader import grade_task, is_wrong_update, minimum_bounded_score, summarize_progress
    from server.tasks import TASKS, TriageTask, get_task, get_task_ids


class EmailTriageEnvironment(Environment[EmailTriageAction, EmailTriageObservation, EmailTriageState]):
    """Real-world email triage simulation with deterministic grader-based rewards."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self, default_task_id: Optional[str] = None) -> None:
        super().__init__()
        self._rng = random.Random(0)
        self._default_task_id = default_task_id
        self._task: TriageTask = get_task(default_task_id) if default_task_id else get_task(get_task_ids()[0])
        self._completed_keys: Set[str] = set()
        self._state = EmailTriageState()
        self._inbox_by_id: Dict[str, Dict[str, Any]] = {}
        self._last_feedback = ""

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> EmailTriageObservation:
        task_id = kwargs.get("task_id") or self._default_task_id
        if task_id is None:
            task_id = self._choose_task_id(seed)

        self._task = get_task(str(task_id))

        if seed is not None:
            self._rng.seed(seed)

        self._completed_keys = set()
        self._last_feedback = "Environment reset. Begin triage."

        self._state = EmailTriageState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=self._task.task_id,
            difficulty=self._task.difficulty,
            objective=self._task.objective,
            score=minimum_bounded_score(),
            completed_items=0,
            total_items=len(self._task.checklist),
            invalid_actions=0,
            max_steps=self._task.max_steps,
            action_history=[],
            workspace={email["email_id"]: {} for email in self._task.emails},
        )

        self._inbox_by_id = {email["email_id"]: email for email in self._task.emails}
        return self._build_observation(reward=0.0, done=False)

    def step(
        self,
        action: EmailTriageAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> EmailTriageObservation:
        del timeout_s, kwargs

        self._state.step_count += 1
        penalty = 0.0
        feedback_parts = []

        if action.action_type == "noop":
            penalty -= 0.02
            feedback_parts.append("No-op action used.")
        else:
            valid, step_penalty, detail = self._apply_action(action)
            penalty += step_penalty
            feedback_parts.append(detail)
            if not valid:
                self._state.invalid_actions += 1

        grade = grade_task(self._task, self._state.workspace, self._completed_keys)
        completion_bonus = 0.0
        done = False

        if grade.completed_keys != self._completed_keys:
            new_keys = sorted(grade.completed_keys - self._completed_keys)
            if new_keys:
                feedback_parts.append("Completed checklist items: " + ", ".join(new_keys))

        self._completed_keys = grade.completed_keys
        self._state.score = grade.score
        self._state.completed_items, self._state.total_items = summarize_progress(
            self._task, self._completed_keys
        )

        reward = grade.new_credit + penalty

        if self._state.score >= 0.999:
            done = True
            completion_bonus = 0.20
            reward += completion_bonus
            feedback_parts.append("All checklist items satisfied.")

        if self._state.step_count >= self._task.max_steps and not done:
            done = True
            reward -= 0.20
            feedback_parts.append("Step budget exhausted before task completion.")

        reward = max(-1.0, min(1.0, reward))

        summary = f"score={self._state.score:.2f} ({self._state.completed_items}/{self._state.total_items})"
        feedback_parts.append(summary)
        self._last_feedback = " ".join(part for part in feedback_parts if part)
        self._state.action_history.append(self._action_to_logline(action, reward, done))

        return self._build_observation(reward=reward, done=done)

    @property
    def state(self) -> EmailTriageState:
        return self._state

    def _choose_task_id(self, seed: Optional[int]) -> str:
        task_ids = get_task_ids()
        if seed is None:
            return task_ids[self._rng.randrange(0, len(task_ids))]
        idx = seed % len(task_ids)
        return task_ids[idx]

    def _apply_action(self, action: EmailTriageAction) -> tuple[bool, float, str]:
        if not action.email_id:
            return False, -0.08, "Action requires email_id."

        if action.email_id not in self._state.workspace:
            return False, -0.08, f"Unknown email_id: {action.email_id}."

        email_workspace = self._state.workspace[action.email_id]
        duplicated = False
        penalty = 0.0

        if action.action_type == "classify":
            if not (action.category and action.priority and action.assignee):
                return False, -0.08, "classify requires category, priority, and assignee."
            duplicated = (
                email_workspace.get("category") == action.category
                and email_workspace.get("priority") == action.priority
                and email_workspace.get("assignee") == action.assignee
            )
            email_workspace["category"] = action.category
            email_workspace["priority"] = action.priority
            email_workspace["assignee"] = action.assignee

            if is_wrong_update(self._task, action.email_id, "category", action.category):
                penalty -= 0.05
            if is_wrong_update(self._task, action.email_id, "priority", action.priority):
                penalty -= 0.05
            if is_wrong_update(self._task, action.email_id, "assignee", action.assignee):
                penalty -= 0.05

        elif action.action_type == "draft_reply":
            if not action.reply_template:
                return False, -0.08, "draft_reply requires reply_template."
            duplicated = email_workspace.get("reply_template") == action.reply_template
            email_workspace["reply_template"] = action.reply_template
            if is_wrong_update(self._task, action.email_id, "reply_template", action.reply_template):
                penalty -= 0.05

        elif action.action_type == "set_follow_up":
            if action.follow_up_days is None:
                return False, -0.08, "set_follow_up requires follow_up_days."
            duplicated = email_workspace.get("follow_up_days") == action.follow_up_days
            email_workspace["follow_up_days"] = action.follow_up_days
            if is_wrong_update(self._task, action.email_id, "follow_up_days", action.follow_up_days):
                penalty -= 0.05

        elif action.action_type == "close_case":
            has_prerequisites = {
                "category",
                "priority",
                "assignee",
                "reply_template",
            }.issubset(set(email_workspace.keys()))
            duplicated = bool(email_workspace.get("closed", False))
            email_workspace["closed"] = True
            email_workspace["resolution_note"] = action.resolution_note or "Closed by agent"

            if not has_prerequisites:
                penalty -= 0.10

            if is_wrong_update(self._task, action.email_id, "closed", True):
                # Closing non-target emails is neutral; wrong close only penalized if checklist expects False-like behavior.
                penalty -= 0.03

        else:
            return False, -0.08, f"Unsupported action_type: {action.action_type}."

        if duplicated:
            penalty -= 0.02
            return True, penalty, "Duplicate update; no new information added."

        return True, penalty, f"Applied {action.action_type} to {action.email_id}."

    def _action_to_logline(self, action: EmailTriageAction, reward: float, done: bool) -> str:
        return (
            f"step={self._state.step_count} action={action.action_type} "
            f"email_id={action.email_id} reward={reward:.3f} done={done}"
        )

    def _build_observation(self, reward: float, done: bool) -> EmailTriageObservation:
        checklist = [
            ChecklistItemStatus(
                key=item.key,
                description=item.description,
                weight=item.weight,
                completed=item.key in self._completed_keys,
            )
            for item in self._task.checklist
        ]

        obs = EmailTriageObservation(
            task_id=self._task.task_id,
            difficulty=self._task.difficulty,
            objective=self._task.objective,
            current_step=self._state.step_count,
            max_steps=self._task.max_steps,
            inbox=[EmailItem(**email) for email in self._task.emails],
            checklist=checklist,
            score=self._state.score,
            invalid_actions=self._state.invalid_actions,
            last_feedback=self._last_feedback,
            reward=reward,
            done=done,
            metadata={
                "task_ids": list(TASKS.keys()),
                "workspace": self._state.workspace,
                "progress": {
                    "completed": self._state.completed_items,
                    "total": self._state.total_items,
                },
            },
        )
        return obs
