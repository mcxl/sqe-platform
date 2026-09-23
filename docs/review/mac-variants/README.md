# SQE Platform

SQE Platform is a controlled, fictional-data platform for auditor review work.

The accountable auditor makes all final professional decisions.
Do not add client data, credentials, evidence files, scan results, or generated output.

## Documentation

- [System Context](CONTEXT.md)
- [Development State](DEV_STATE.md)
- [Workflow Notes](WORKFLOW-NOTES.md)
- [Vision And Roadmap](ACE_VISION_AND_ROADMAP.md)
- [Architecture Decisions](docs/adr/)
- [Approved Specifications](docs/specs/)
- [Approved Workflows](workflows/)
- [Agent Controls](docs/agents/)

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

The service listens only on this computer.
