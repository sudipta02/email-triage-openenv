---
title: Email Triage Environment
emoji: "📬"
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
tags:
  - openenv
---

# Email Triage Environment

A real-world task simulation where an agent triages operational email queues under strict process constraints. The environment is designed for agent training and evaluation with deterministic graders, trajectory-level rewards, and escalating difficulty.

## Motivation

Operations teams handle mixed inboxes: outages, security alerts, legal requests, and billing disputes. This environment models that workflow in a way that is useful for reinforcement learning and offline evaluation.

## OpenEnv API Compliance

This environment implements typed OpenEnv contracts:
- `reset(seed=None, task_id=..., episode_id=...) -> EmailTriageObservation`
- `step(action) -> EmailTriageObservation`
- `state -> EmailTriageState`

The standard step outputs are carried on the typed observation model:
- `reward`: dense trajectory reward for the last action
- `done`: episode termination flag
- `metadata`: structured diagnostics and workspace snapshot

The exported models are:
- `EmailTriageAction`
- `EmailTriageObservation`
- `EmailTriageState`

Manifest: `openenv.yaml`

## Action Space

`EmailTriageAction` fields:
- `action_type`: `classify | draft_reply | set_follow_up | close_case | noop`
- `email_id`: target email id
- `category`: optional category label
- `priority`: optional priority label
- `assignee`: optional queue/team owner
- `reply_template`: optional reply strategy
- `follow_up_days`: optional 0-30 integer
- `resolution_note`: optional close summary

## Observation Space

`EmailTriageObservation` returns:
- task metadata (`task_id`, `difficulty`, `objective`)
- bounded horizon (`current_step`, `max_steps`)
- inbox snapshot (`inbox`)
- deterministic grader status (`checklist`, `score`)
- trajectory diagnostics (`last_feedback`, `invalid_actions`)

## Tasks (Easy -> Medium -> Hard)

1. `easy_security_triage`
- Objective: escalate suspicious login alert correctly.
- Difficulty: easy.
- Core skills: security routing, urgency labeling, incident follow-up.

2. `medium_billing_outage`
- Objective: jointly triage billing dispute + production latency report.
- Difficulty: medium.
- Core skills: multi-ticket prioritization, parallel ownership.

3. `hard_vip_legal_security`
- Objective: handle VIP product failure, legal hold, and account takeover alert.
- Difficulty: hard.
- Core skills: context switching, compliance, security escalation.

Each task has a deterministic checklist grader with weighted criteria in `server/tasks.py` and `server/grader.py`.

## Reward Design

Trajectory-level reward is emitted every step:
- Positive credit for newly satisfied checklist items (partial progress).
- Penalty for malformed/invalid actions.
- Penalty for incorrect target values (wrong category/priority/assignee/template).
- Penalty for duplicate or no-op actions.
- Penalty for closing before prerequisites.
- Completion bonus when all checklist items are satisfied.
- Timeout penalty if max steps reached before completion.

Reward range is clipped to `[-1.0, 1.0]`.

## Run Locally

If this environment is in its own repository, run from the repository root:

```bash
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

If this environment is inside the OpenEnv monorepo:

```bash
cd envs/email_triage_env
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Docker

If this environment is in its own repository:

```bash
docker build -t email-triage-env:latest -f Dockerfile .
docker run --rm -p 8000:8000 email-triage-env:latest
```

If this environment is inside the OpenEnv monorepo:

```bash
cd envs/email_triage_env
docker build -t email-triage-env:latest -f Dockerfile .
docker run --rm -p 8000:8000 email-triage-env:latest
```

## Hugging Face Space Deployment

```bash
cd envs/email_triage_env
openenv push --repo-id sudipta02/email-triage-env
```

After deployment:
- Web UI: `https://sudipta02-email-triage-env.hf.space/web`
- Docs: `https://sudipta02-email-triage-env.hf.space/docs`
- Health: `https://sudipta02-email-triage-env.hf.space/health`

## Validation

```bash
cd envs/email_triage_env
openenv validate --verbose
```

Verified in this workspace:
- `openenv validate envs/email_triage_env --verbose` passes.
- Supported deployment modes: `docker`, `openenv_serve`, `uv_run`, `python_module`.
