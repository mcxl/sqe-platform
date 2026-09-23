# ACE Sprint 1 Design

## Purpose

Sprint 1 establishes the local decision core of the Assurance Compass Engine (ACE) for the Squadron Energy WHS governance audit. It will:

- represent WHS controls and assurance dimensions as validated records;
- rate each control using an explicit four-dimension decision rule;
- produce clear audit results whose rating, failed dimensions and reasoning are reproducible for a given control;
- expose five fictional example evaluations through a local FastAPI server; and
- remain private by default, with no telemetry, external API calls or automatic internet exposure.

`ACE_VISION_AND_ROADMAP.md` was not present in the workspace during design. The user confirmed the updated Sprint 1 brief and the decisions recorded here as the authoritative scope for this build.

## Scope

### Included

- Python 3.11 or later.
- Pydantic v2 domain models.
- A control evaluator with deterministic rating, failed dimensions and reasoning.
- FastAPI and Uvicorn for a read-only local demonstration.
- Five fictional WHS controls covering BESS thermal runaway, HV energisation, arc flash, simultaneous operations and SOCI cyber-physical safety.
- Exhaustive testing of all 16 assurance-dimension combinations.
- Confidence validation and automatic low-confidence reviewer flags.
- Immutable evaluation results.
- Local boot verification on `127.0.0.1:8000`.
- Documentation of the deliberate Cloudflare Tunnel hand-off.

### Excluded

- A database or other permanent storage.
- Creating, editing or deleting controls through the website.
- Authentication or authorisation inside ACE.
- Real audit evidence or client-confidential information.
- Automatically starting or configuring Cloudflare Tunnel.
- Cloudflare credentials, deployment automation or public hosting.
- External APIs, AI services, analytics, crash reporting or telemetry.

## Architecture

ACE will use a thin web adapter over a focused domain engine.

### Domain Vocabulary

`src/ace/domain/enums.py` defines string-backed enums:

- `ControlRating`: `ADEQUATE`, `PARTIALLY_ADEQUATE`, `INADEQUATE`.
- `HazardCategory`: `BESS_THERMAL_RUNAWAY`, `HV_ENERGIZATION`, `ARC_FLASH`, `SIMOPS`, `SOCI_CYBER_PHYSICAL`, `TPRM_CONTRACTOR_ONBOARDING`, `GOVERNANCE_OVERSIGHT`, `SAFETY_IN_DESIGN`.

String-backed enums ensure that API responses contain stable, readable values.

### Domain Records

`src/ace/domain/models.py` defines:

- `AssuranceDimensions`, containing the four required Boolean checks.
- `Control`, containing control identity, description, hazard category, dimensions, confidence and reviewer notes.
- `EvaluationResult`, containing the immutable audit result.

The four assurance fields will use strict Boolean validation so values such as arbitrary strings or numbers are not silently treated as yes or no. Required identity and descriptive text will reject empty or whitespace-only values.

`confidence_score` defaults to `1.0` and must be between `0.0` and `1.0`, inclusive.

An `@model_validator(mode="after")` on `Control` adds this reviewer flag when a validated confidence score is below `0.8`:

> Review required: confidence score is below 0.8.

The validator will preserve existing notes and will not add the same flag more than once.

`EvaluationResult` will be frozen. Its failed-dimensions collection will use an immutable internal sequence so callers cannot change the audit record after creation. Its JSON representation will remain an ordinary array.

### Evaluation Engine

`src/ace/engine/evaluator.py` defines:

```python
evaluate_control(control: Control) -> EvaluationResult
```

The evaluator has no FastAPI, filesystem, database, environment or network dependencies.

It inspects dimensions in this stable order:

1. mandate;
2. accountability;
3. trigger;
4. escalation.

It applies this strict precedence:

1. `ADEQUATE`: zero failed dimensions.
2. `INADEQUATE`: two or more failed dimensions, or mandate is false, or accountability is false.
3. `PARTIALLY_ADEQUATE`: exactly one failed dimension, which is trigger or escalation.

The inadequate rule takes precedence over partial adequacy. Therefore, a control with mandate and accountability present but both trigger and escalation absent is inadequate.

Each result contains:

- the source control identifier;
- the rating;
- failed dimensions in stable order;
- a timezone-aware UTC timestamp in ISO 8601 format; and
- deterministic, board-readable reasoning.

Reasoning names the passed dimensions, failed dimensions and rating rationale. It never relies on AI-generated text.

For a given control, the rating, failed dimensions and reasoning are
deterministic. The complete result is intentionally not fully reproducible
because its timestamp records the actual UTC assessment time.

### FastAPI Adapter

`src/ace/app.py` owns only the web application, an immutable collection of five fictional sample controls and the local Uvicorn entry point. Rating decisions remain in the evaluator.

The application exposes two read-only endpoints:

#### `GET /`

Returns exactly:

```json
{
  "system": "Assurance Compass Engine",
  "status": "ONLINE",
  "audit_engagement": "Squadron Energy WHS Governance"
}
```

#### `GET /evaluations`

Passes all five fictional controls through `evaluate_control()` and returns a response model of `list[EvaluationResult]`.

The sample set demonstrates every rating:

| Hazard | Dimension Pattern | Expected Rating |
|---|---|---|
| BESS thermal runaway | All four pass | Adequate |
| HV energisation | Escalation fails | Partially Adequate |
| Arc flash | Accountability fails | Inadequate |
| Simultaneous operations | Trigger fails | Partially Adequate |
| SOCI cyber-physical safety | Trigger and escalation fail | Inadequate |

At least one fictional sample will use a confidence score below `0.8` so the low-confidence model behaviour is exercised during sample construction. The endpoint returns evaluation results, not the source control records.

Running:

```text
python -m src.ace.app
```

starts Uvicorn with:

```text
host=127.0.0.1
port=8000
```

The server does not listen on the office network or public internet.

## Data Flow

1. A client requests `/evaluations`.
2. The FastAPI adapter constructs the five validated fictional controls.
3. Pydantic rejects invalid or incomplete control data.
4. The adapter passes each valid control to the focused evaluator.
5. The evaluator collects failed dimensions and applies the strict rating precedence.
6. The evaluator generates the UTC timestamp and plain-English reasoning.
7. The evaluator returns a frozen `EvaluationResult`.
8. FastAPI serialises the five results to JSON.

No step writes data to disk or sends data outside the local process.

## Validation And Failure Behaviour

ACE will fail clearly rather than guess.

- Confidence scores below `0.0` or above `1.0` are rejected.
- Missing required fields are rejected.
- Unknown hazard categories are rejected.
- Invalid dimension values are rejected.
- FastAPI and Pydantic return structured validation details for invalid application data.
- Programming errors are not hidden behind misleading successful responses.

The two Sprint 1 endpoints do not accept user-supplied control data, so normal
operation is read-only. For the same source control, decision content is
deterministic while the assessment timestamp records the actual UTC time.

## Privacy And Cloudflare Readiness

ACE contains no external API client, telemetry SDK, analytics, crash reporting or automatic update check.

The server binds only to `127.0.0.1:8000`. Cloudflare sharing is a separate operator action, for example:

```text
cloudflared tunnel --url http://127.0.0.1:8000
```

A Quick Tunnel link is public to anyone who has the link. Sprint 1 therefore exposes fictional examples only. Real audit data must not be shared through a Quick Tunnel. A later production design must use a managed hostname, Cloudflare Access or equivalent authentication and an approved data-handling process.

ACE will not start a tunnel, store Cloudflare credentials or make Cloudflare API calls.

## Testing And Acceptance Criteria

`tests/test_rating_engine.py` will include:

- a parameterised truth table covering all 16 Boolean permutations;
- explicit expected ratings independent of the implementation logic;
- checks for stable failed-dimension ordering;
- reasoning checks that identify passed and failed dimensions;
- confidence boundary checks at `0.0`, `0.8` and `1.0`;
- rejection checks below `0.0` and above `1.0`;
- low-confidence flagging below, but not at, `0.8`;
- preservation of existing reviewer notes;
- prevention of duplicate confidence flags; and
- attempts to mutate the result or its failed-dimensions collection.

Application checks will confirm:

- `/` returns the exact agreed health response;
- `/evaluations` returns five results;
- the internal fictional sample collection covers all five required hazards before evaluation;
- the sample results include adequate, partially adequate and inadequate ratings; and
- no endpoint writes data or calls an external service.

Final verification will:

1. run the complete Pytest suite with no failures;
2. start `python -m src.ace.app`;
3. poll `http://127.0.0.1:8000/` until it returns the expected response;
4. request `/evaluations` and confirm five structured results; and
5. stop the local server cleanly.

Sprint 1 is complete only when every check passes.

## Planned Files

Required implementation files:

```text
src/ace/domain/enums.py
src/ace/domain/models.py
src/ace/engine/evaluator.py
src/ace/app.py
tests/test_rating_engine.py
```

Supporting package, application-test and project files:

```text
pyproject.toml
README.md
src/__init__.py
src/ace/__init__.py
src/ace/domain/__init__.py
src/ace/engine/__init__.py
tests/test_app.py
```

`pyproject.toml` will declare Python 3.11 or later and runtime dependencies on Pydantic v2, FastAPI and Uvicorn. Its test dependencies will include Pytest and HTTPX for local FastAPI endpoint tests.

`README.md` will document local installation, testing, startup, endpoint use and the fictional-data-only Cloudflare demonstration command.

## Key Decisions

- Use a focused evaluator behind a thin FastAPI adapter, with deterministic
  decision content and an actual UTC assessment timestamp.
- Treat the updated Sprint 1 brief and this approved design as authoritative because the referenced roadmap is absent.
- Give inadequate strict precedence for foundational or multiple failures.
- Keep Sprint 1 read-only and without persistence.
- Use fictional samples only.
- Bind privately to localhost and require a deliberate external tunnel action.
- Preserve audit records through deep immutability.
- Use deterministic reasoning and UTC timestamps.
- Prove the decision table exhaustively before completion.
