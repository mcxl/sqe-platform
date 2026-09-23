> **Review snapshot, 23 September 2026.** Read [VORFLUX_START_HERE.md](VORFLUX_START_HERE.md) first. This branch is not a verified release or an approved merge.

# Assurance Compass Engine

Current project navigation: [Development Hub](SQE_DEVELOPER_HUB.html), [Development State](DEV_STATE.md), and [Code And Evidence Index](docs/ace/CODE-AND-EVIDENCE-INDEX.md).

As of 23 September 2026, mobile alternatives are under independent review. The consolidated repository contains uncommitted imports. The Sprint 1 instructions below describe the original fictional demonstration, not the complete current delivery state.

ACE Sprint 1 is a private-by-default, deterministic demonstration of WHS
governance control evaluation for the Squadron Energy engagement.

The included controls are fictional. Do not add real audit evidence to this
Sprint 1 demonstration.

## Requirements

- Python 3.11 or later
- Cloudflared only when deliberately sharing the fictional demonstration

## Set Up

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

For the focused fictional client-release migration and lifecycle checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_client_release.py -q
```

Stage 3 trigger decision:
[`docs/specs/phase6-stage3-release-trigger-decisions.md`](docs/specs/phase6-stage3-release-trigger-decisions.md).

## Start ACE Locally

```powershell
.\.venv\Scripts\python.exe -m src.ace.app
```

Open:

- `http://127.0.0.1:8000/` for system status
- `http://127.0.0.1:8000/evaluations` for five fictional evaluations

The server listens only on this computer.

## Share The Fictional Demonstration

Start ACE first. In a second terminal, deliberately create a temporary
Cloudflare Quick Tunnel:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

A Quick Tunnel address is public to anyone who has the link. Use it only for
the fictional Sprint 1 examples. Never expose real audit evidence through a
Quick Tunnel. A production release requires authenticated Cloudflare Access
and an approved data-handling design.

ACE does not start Cloudflare, store Cloudflare credentials, call external
APIs or include telemetry.
