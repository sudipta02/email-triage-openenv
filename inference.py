"""Submission inference script for email_triage_env.

Required environment variables:
- API_BASE_URL: LLM endpoint for OpenAI-compatible chat completions.
- MODEL_NAME: Model identifier used for inference.
- HF_TOKEN: API key/token used by the OpenAI client.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

try:
    from client import EmailTriageEnv
    from models import EmailTriageAction
except ImportError:
    current_dir = Path(__file__).resolve().parent
    for candidate in (current_dir, current_dir.parent):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
    try:
        from client import EmailTriageEnv
        from models import EmailTriageAction
    except ImportError:
        module = importlib.import_module("email_triage_env")
        EmailTriageAction = module.EmailTriageAction
        EmailTriageEnv = module.EmailTriageEnv

TASK_IDS: List[str] = [
    "easy_security_triage",
    "medium_billing_outage",
    "hard_vip_legal_security",
]


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"{name} is required.")
    return value


def build_prompt(observation: Dict[str, Any]) -> str:
    return (
        "You are an email operations triage agent. Return ONLY valid JSON with keys: "
        "action_type,email_id,category,priority,assignee,reply_template,follow_up_days,resolution_note. "
        "Use null for unused keys.\n\n"
        f"Task: {observation['objective']}\n"
        f"Difficulty: {observation['difficulty']}\n"
        f"Step: {observation['current_step']}/{observation['max_steps']}\n"
        f"Current score: {observation['score']}\n"
        f"Checklist:\n{json.dumps(observation['checklist'], indent=2)}\n"
        f"Inbox:\n{json.dumps(observation['inbox'], indent=2)}\n"
        f"Last feedback: {observation.get('last_feedback', '')}\n"
    )


def llm_action(client: OpenAI, model: str, observation: Dict[str, Any]) -> Any:
    completion = client.chat.completions.create(
        model=model,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Choose one triage action that maximizes checklist completion and "
                    "avoids invalid actions."
                ),
            },
            {"role": "user", "content": build_prompt(observation)},
        ],
    )

    text = completion.choices[0].message.content or "{}"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = {"action_type": "noop"}

    try:
        return EmailTriageAction(**payload)
    except Exception:
        return EmailTriageAction(action_type="noop")


def run_task(
    env: Any,
    client: OpenAI,
    model: str,
    task_id: str,
    seed: int,
) -> float:
    result = env.reset(task_id=task_id, seed=seed)
    while not result.done:
        action = llm_action(client, model, result.observation.model_dump())
        result = env.step(action)
    return float(result.observation.score)


def main() -> None:
    parser = argparse.ArgumentParser(description="Submission inference for email_triage_env")
    parser.add_argument("--env-url", default=os.getenv("ENV_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    api_base_url = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
    model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
    hf_token = _required_env("HF_TOKEN")

    client = OpenAI(base_url=api_base_url, api_key=hf_token)

    scores: Dict[str, float] = {}
    with EmailTriageEnv(base_url=args.env_url).sync() as env:
        for task_id in TASK_IDS:
            scores[task_id] = run_task(env, client, model_name, task_id, args.seed)

    average = sum(scores.values()) / len(scores)
    result_payload = {
        "model": model_name,
        "scores": scores,
        "average": average,
    }
    print(json.dumps(result_payload, indent=2))


if __name__ == "__main__":
    main()