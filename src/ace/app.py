import uvicorn
from fastapi import FastAPI

from src.ace.domain.enums import HazardCategory
from src.ace.domain.models import AssuranceDimensions, Control, EvaluationResult
from src.ace.engine.evaluator import evaluate_control
from src.ace.workbench.client_routes import router as client_router
from src.ace.workbench.routes import router as workbench_router

app = FastAPI(
    title="Assurance Compass Engine",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(workbench_router)
app.include_router(client_router)

SAMPLE_CONTROLS = (
    Control(
        control_id="ACE-BESS-001",
        title="BESS emergency response control",
        description="Fictional control for BESS thermal runaway readiness.",
        hazard_category=HazardCategory.BESS_THERMAL_RUNAWAY,
        dimensions=AssuranceDimensions(
            mandate=True,
            accountability=True,
            trigger=True,
            escalation=True,
        ),
    ),
    Control(
        control_id="ACE-HV-001",
        title="HV energisation authorisation control",
        description="Fictional control for high-voltage energisation governance.",
        hazard_category=HazardCategory.HV_ENERGIZATION,
        dimensions=AssuranceDimensions(
            mandate=True,
            accountability=True,
            trigger=True,
            escalation=False,
        ),
    ),
    Control(
        control_id="ACE-ARC-001",
        title="Arc flash boundary control",
        description="Fictional control for arc flash boundary accountability.",
        hazard_category=HazardCategory.ARC_FLASH,
        dimensions=AssuranceDimensions(
            mandate=True,
            accountability=False,
            trigger=True,
            escalation=True,
        ),
    ),
    Control(
        control_id="ACE-SIMOPS-001",
        title="Simultaneous operations gateway",
        description="Fictional control for simultaneous operations activation.",
        hazard_category=HazardCategory.SIMOPS,
        dimensions=AssuranceDimensions(
            mandate=True,
            accountability=True,
            trigger=False,
            escalation=True,
        ),
    ),
    Control(
        control_id="ACE-SOCI-001",
        title="SOCI cyber-physical escalation control",
        description="Fictional control for cyber-physical safety escalation.",
        hazard_category=HazardCategory.SOCI_CYBER_PHYSICAL,
        dimensions=AssuranceDimensions(
            mandate=True,
            accountability=True,
            trigger=False,
            escalation=False,
        ),
        confidence_score=0.75,
    ),
)


@app.get("/")
def health_check() -> dict[str, str]:
    return {
        "system": "Assurance Compass Engine",
        "status": "ONLINE",
        "audit_engagement": "Squadron Energy WHS Governance",
    }


@app.get("/evaluations", response_model=list[EvaluationResult])
def list_evaluations() -> list[EvaluationResult]:
    return [evaluate_control(control) for control in SAMPLE_CONTROLS]


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
