from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from openai import OpenAI

from email_triage_env import EmailTriageAction, EmailTriageEnv


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


def llm_action(client: OpenAI, model: str, observation: Dict[str, Any]) -> EmailTriageAction:
    prompt = build_prompt(observation)
    completion = client.chat.completions.create(
        model=model,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "Choose one triage action that maximizes checklist completion while avoiding invalid actions.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    text = completion.choices[0].message.content or "{}"
    payload = json.loads(text)
    return EmailTriageAction(**payload)


def run_task(env: Any, client: OpenAI, model: str, task_id: str, seed: int) -> float:
    result = env.reset(task_id=task_id, seed=seed)
    while not result.done:
        action = llm_action(client, model, result.observation.model_dump())
        result = env.step(action)
    return float(result.observation.score)


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenAI baseline for email_triage_env")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required.")

    client = OpenAI(api_key=api_key)
    task_ids = ["easy_security_triage", "medium_billing_outage", "hard_vip_legal_security"]

    scores: Dict[str, float] = {}
    with EmailTriageEnv(base_url=args.base_url).sync() as env:
        for task_id in task_ids:
            scores[task_id] = run_task(env, client, args.model, task_id, args.seed)

    aggregate = sum(scores.values()) / len(scores)
    print(json.dumps({"model": args.model, "scores": scores, "average": aggregate}, indent=2))


if __name__ == "__main__":
    main()
