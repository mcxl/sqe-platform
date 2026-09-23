# Assurance Compass Engine

ACE Sprint 1 is a private-by-default, deterministic demonstration of WHS
governance control evaluation for the Squadron Energy engagement.

The included controls are fictional. Do not add real audit evidence to this
Sprint 1 demonstration.

## Project Map

- [ACE Vision And Roadmap](ACE_VISION_AND_ROADMAP.md)
- [ACE Progress Guide](ACE_PROGRESS_GUIDE.html)

Use the progress guide to see the current build phase, decision gates and
workspace boundaries.

## Requirements

- Python 3.11 or later

## Set Up

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Start ACE Locally

```powershell
.\.venv\Scripts\python.exe -m src.ace.app
```

Open:

- `http://127.0.0.1:8000/` for system status
- `http://127.0.0.1:8000/evaluations` for five fictional evaluations

The server listens only on this computer.

## Use The Field Capture Workbench

Set a local auditor password before you start ACE. Do not use a client
password or client evidence.

```powershell
$env:ACE_AUDITOR_PASSWORD = "set-a-local-password"
```

ACE stores workbench media and SQLite data in the sibling `sqe-local-data`
folder. Set `ACE_DATA_DIR` only to an external folder if you need a different
local data location.

For one trusted private Wi-Fi session, start ACE on the laptop network
interface. Do not use a public network.

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.ace.app:app --host 0.0.0.0 --port 8000
```

Open `http://<laptop-private-ip>:8000/workbench` in iPhone Safari. Enter the
username `auditor` and the password from `ACE_AUDITOR_PASSWORD`.

The workbench accepts image files only. It does not send data to external
services. Stop ACE when the site session ends.
