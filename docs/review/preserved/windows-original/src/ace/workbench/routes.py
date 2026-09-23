"""Authenticated HTTP routes for the private local workbench."""

from __future__ import annotations

import base64
import binascii
import html
import os
import secrets
import warnings
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.ace.workbench.engagement import (
    EngagementConflictError,
    EngagementDraft,
    EngagementG0Error,
    EngagementNotFoundServiceError,
    EngagementService,
    EngagementValidationError,
)
from src.ace.workbench.storage import (
    CaptureAttemptConflictError,
    NoReadyCurrentEngagementError,
    WorkbenchStore,
)


MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
IMAGE_FORMATS = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
    "image/gif": "GIF",
}
basic_auth = HTTPBasic(auto_error=False)
router = APIRouter(prefix="/workbench")


class CaptureRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    media_type: str
    data_base64: str = Field(min_length=1)
    capture_attempt_key: str | None = Field(
        default=None, min_length=8, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"
    )

    @field_validator("media_type")
    @classmethod
    def image_media_type_is_required(cls, media_type: str) -> str:
        if media_type not in ALLOWED_MEDIA_TYPES:
            raise ValueError("Only image media is permitted")
        return media_type

    @field_validator("filename")
    @classmethod
    def filename_is_present(cls, filename: str) -> str:
        filename = filename.strip()
        if not filename:
            raise ValueError("A filename is required")
        return filename


class CaptureV1Request(CaptureRequest):
    model_config = ConfigDict(extra="forbid", strict=True)

    capture_attempt_key: str = Field(
        min_length=8, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"
    )


class ReviewRequest(BaseModel):
    notes: str = Field(min_length=1, max_length=4000)


class EngagementCreateRequest(BaseModel):
    """Strict, safe input for one controlled Engagement draft."""

    model_config = ConfigDict(extra="forbid", strict=True)

    creation_attempt_key: str = Field(
        min_length=8, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"
    )
    title: str | None = Field(default=None, max_length=240)
    reference: str | None = Field(default=None, max_length=120)
    authority: str | None = Field(default=None, max_length=2000)
    purpose: str | None = Field(default=None, max_length=2000)
    scope: str | None = Field(default=None, max_length=4000)
    exclusions: str | None = Field(default=None, max_length=4000)
    review_start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    review_end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    evidence_cut_off_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    accountable_auditor: str | None = Field(default=None, max_length=240)
    data_classification: str | None = None
    is_fictional: bool | None = None

    @field_validator("data_classification")
    @classmethod
    def data_classification_is_controlled(cls, value: str | None) -> str | None:
        if value is not None and value not in {
            "FICTIONAL",
            "PUBLIC",
            "AUDITCO_OWNED",
            "REAL_CLIENT",
        }:
            raise ValueError("Use a controlled data classification")
        return value


class EngagementActivationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    confirmed: bool


def require_auditor(
    credentials: HTTPBasicCredentials | None = Security(basic_auth),
) -> str:
    password = os.environ.get("ACE_AUDITOR_PASSWORD")
    if not password:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    if (
        credentials is None
        or not secrets.compare_digest(credentials.username, "auditor")
        or not secrets.compare_digest(credentials.password, password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def store() -> WorkbenchStore:
    try:
        return WorkbenchStore()
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from error


def engagement_service() -> EngagementService:
    return EngagementService(store())


def engagement_response(record: object) -> dict[str, object]:
    return {"api_version": "v1", "engagement": record.as_dict()}  # type: ignore[union-attr]


def engagement_http_error(error: Exception) -> HTTPException:
    if isinstance(error, EngagementNotFoundServiceError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found")
    if isinstance(error, EngagementG0Error):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="G0 blocks this Engagement")
    if isinstance(error, EngagementValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error))
    if isinstance(error, EngagementConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def decode_image(payload: CaptureRequest) -> bytes:
    try:
        content = base64.b64decode(payload.data_base64, validate=True)
    except (binascii.Error, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid image data") from error
    if not content or len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Image size is invalid")
    try:
        _verify_image(content, IMAGE_FORMATS[payload.media_type])
    except (
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
        ValueError,
    ) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Image data does not match media type")
    return content


def _verify_image(content: bytes, expected_format: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(BytesIO(content)) as image:
            if image.format != expected_format:
                raise ValueError("Image data does not match media type")
            image.verify()
        with Image.open(BytesIO(content)) as image:
            if image.format != expected_format:
                raise ValueError("Image data does not match media type")
            for frame_number in range(getattr(image, "n_frames", 1)):
                image.seek(frame_number)
                image.load()


@router.get("", response_class=HTMLResponse)
def workbench_page(_: str = Depends(require_auditor)) -> HTMLResponse:
    try:
        current = engagement_service().current()
    except EngagementG0Error as error:
        raise engagement_http_error(error) from error
    current_text = (
        f"{current.title} — {current.reference} — {current.state}"
        if current is not None
        else "No READY_FOR_CAPTURE Engagement selected"
    )
    return HTMLResponse(WORKBENCH_PAGE.replace("__CURRENT_ENGAGEMENT__", html.escape(current_text)))


@router.get("/engagements/new", response_class=HTMLResponse)
def engagement_setup_page(_: str = Depends(require_auditor)) -> HTMLResponse:
    return HTMLResponse(ENGAGEMENT_SETUP_PAGE)


@router.post("/api/v1/engagements", status_code=status.HTTP_201_CREATED)
def create_engagement(
    payload: EngagementCreateRequest, auditor: str = Depends(require_auditor)
) -> dict[str, object]:
    try:
        record = engagement_service().create_draft(EngagementDraft(**payload.model_dump()), auditor)
    except (EngagementConflictError, EngagementG0Error) as error:
        raise engagement_http_error(error) from error
    return engagement_response(record)


@router.get("/api/v1/engagements/current")
def current_engagement(_: str = Depends(require_auditor)) -> dict[str, object]:
    try:
        record = engagement_service().current()
    except EngagementG0Error as error:
        raise engagement_http_error(error) from error
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current Engagement")
    return engagement_response(record)


@router.get("/api/v1/engagements/{engagement_id}")
def get_engagement(
    engagement_id: str, _: str = Depends(require_auditor)
) -> dict[str, object]:
    try:
        return engagement_response(engagement_service().get(engagement_id))
    except (EngagementG0Error, EngagementNotFoundServiceError) as error:
        raise engagement_http_error(error) from error


@router.post("/api/v1/engagements/{engagement_id}/activate")
def activate_engagement(
    engagement_id: str,
    payload: EngagementActivationRequest,
    auditor: str = Depends(require_auditor),
) -> dict[str, object]:
    try:
        return engagement_response(
            engagement_service().activate(engagement_id, payload.confirmed, auditor)
        )
    except (
        EngagementConflictError,
        EngagementG0Error,
        EngagementNotFoundServiceError,
        EngagementValidationError,
    ) as error:
        raise engagement_http_error(error) from error


@router.put("/api/v1/engagements/{engagement_id}/current")
def select_current_engagement(
    engagement_id: str, _: str = Depends(require_auditor)
) -> dict[str, object]:
    try:
        return engagement_response(engagement_service().select_current(engagement_id))
    except (EngagementConflictError, EngagementG0Error, EngagementNotFoundServiceError) as error:
        raise engagement_http_error(error) from error


@router.get("/summary")
def workbench_summary(_: str = Depends(require_auditor)) -> dict[str, object]:
    workbench_store = store()
    try:
        current = EngagementService(workbench_store).current()
    except EngagementG0Error as error:
        raise engagement_http_error(error) from error
    summary = workbench_store.summary()
    summary["current_engagement"] = current.as_dict() if current is not None else None
    summary["engagement"] = current.title if current is not None else "No current Engagement"
    return summary


@router.post("/evidence", status_code=status.HTTP_201_CREATED)
def capture_evidence(
    payload: CaptureRequest, auditor: str = Depends(require_auditor)
) -> dict[str, str]:
    workbench_store = store()
    try:
        return EngagementService(workbench_store).capture(
            payload.filename,
            payload.media_type,
            decode_image(payload),
            auditor,
            payload.capture_attempt_key,
        )
    except EngagementG0Error as error:
        raise engagement_http_error(error) from error
    except (CaptureAttemptConflictError, EngagementConflictError, NoReadyCurrentEngagementError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Capture attempt key conflicts"
                if isinstance(error, CaptureAttemptConflictError)
                else "Select a READY_FOR_CAPTURE Engagement before capture"
            ),
        ) from error


@router.post("/api/v1/evidence", status_code=status.HTTP_201_CREATED)
def capture_evidence_v1(
    payload: CaptureV1Request, auditor: str = Depends(require_auditor)
) -> dict[str, object]:
    workbench_store = store()
    try:
        evidence = EngagementService(workbench_store).capture(
            payload.filename,
            payload.media_type,
            decode_image(payload),
            auditor,
            payload.capture_attempt_key,
        )
    except EngagementG0Error as error:
        raise engagement_http_error(error) from error
    except (CaptureAttemptConflictError, EngagementConflictError, NoReadyCurrentEngagementError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Capture attempt key conflicts"
                if isinstance(error, CaptureAttemptConflictError)
                else "Select a READY_FOR_CAPTURE Engagement before capture"
            ),
        ) from error
    return {"api_version": "v1", "evidence": evidence}


@router.get("/evidence/{evidence_id}/media")
def evidence_media(evidence_id: str, _: str = Depends(require_auditor)) -> FileResponse:
    try:
        media = store().media(evidence_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    file_path, media_type = media
    return FileResponse(file_path, media_type=media_type, filename=file_path.name)


@router.post("/evidence/{evidence_id}/review")
def review_evidence(
    evidence_id: str, payload: ReviewRequest, auditor: str = Depends(require_auditor)
) -> dict[str, str]:
    try:
        reviewed = store().review(evidence_id, auditor, payload.notes)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    if reviewed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return reviewed


WORKBENCH_PAGE = """<!doctype html>
<html lang="en-AU">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#005a9c">
  <title>ACE Field Capture Workbench</title>
  <style>
    :root { color-scheme: light; font-family: Arial, sans-serif; background: #f4f7f8; color: #17212b; }
    * { -webkit-tap-highlight-color: transparent; }
    body { margin: 0; overscroll-behavior-y: none; }
    main { max-width: 980px; min-height: 100vh; min-height: 100dvh; margin: auto; padding: max(1rem, env(safe-area-inset-top)) max(1rem, env(safe-area-inset-right)) max(calc(1rem + 56px + .75rem), calc(env(safe-area-inset-bottom) + 56px + .75rem)) max(1rem, env(safe-area-inset-left)); }
    h1 { margin-bottom: .25rem; } .grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); }
    .card { min-width: 0; background: #fff; border-radius: .5rem; padding: 1rem; box-shadow: 0 1px 3px #0002; }
    .capture-area { position: fixed; left: max(1rem, env(safe-area-inset-left)); right: max(1rem, env(safe-area-inset-right)); bottom: max(.75rem, env(safe-area-inset-bottom)); z-index: 1; max-width: 980px; margin: 0 auto; }
    .capture { display: flex; align-items: center; justify-content: center; box-sizing: border-box; min-height: 56px; background: #005a9c; color: white; font-size: 1.25rem; font-weight: bold; text-align: center; padding: 1rem; border-radius: .5rem; cursor: pointer; touch-action: manipulation; user-select: none; -webkit-user-select: none; }
    .capture.is-processing { background: #52606d; cursor: wait; }
    input[type=file] { display: none; } button, input, select, textarea { font-size: 16px; } button { min-height: 44px; background: #005a9c; color: white; border: 0; border-radius: .3rem; padding: .6rem; font: inherit; cursor: pointer; touch-action: manipulation; }
    li { margin: .5rem 0; } .muted { color: #52606d; } .notice { min-height: 1.5rem; } a { display: inline-flex; align-items: center; min-height: 44px; padding: 0 .25rem; color: #005a9c; touch-action: manipulation; }
    @media (max-width: 480px) { .grid { grid-template-columns: 1fr; } .card { padding: .75rem; } }
  </style>
</head>
<body>
  <main>
    <h1>Field Capture Workbench</h1>
    <p class="muted" id="engagement">__CURRENT_ENGAGEMENT__</p>
    <p><a href="/workbench/engagements/new">New Engagement</a></p>
    <div class="capture-area"><label class="capture" id="capture-control" aria-disabled="false">Capture Evidence<input id="capture" type="file" accept="image/*" capture="environment"></label><button id="retry-capture" type="button" hidden>Retry Capture</button><span class="muted" id="capture-engagement">__CURRENT_ENGAGEMENT__</span></div>
    <p class="notice" id="notice" aria-live="polite"></p>
    <section class="card"><h2>Mini Guide</h2><div class="grid" id="counts"></div></section>
    <section class="card"><h2>Fictional Chain</h2><p id="chain"></p></section>
    <section class="card"><h2>Recent Captures</h2><ul id="recent"></ul></section>
    <section class="card"><h2>Pending Review</h2><ul id="pending"></ul></section>
  </main>
  <script>
    const notice = document.querySelector('#notice');
    const captureInput = document.querySelector('#capture');
    const captureControl = document.querySelector('#capture-control');
    const retryCapture = document.querySelector('#retry-capture');
    let captureInProgress = false;
    let pendingCapture = null;
    const escapeText = (value) => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
    async function loadWorkbench({ preserveNotice = false } = {}) {
      const response = await fetch('/workbench/summary');
      if (!response.ok) { if (!preserveNotice) notice.textContent = 'The workbench data is not available.'; return; }
      const data = await response.json();
      const current = data.current_engagement;
      const currentText = current ? `${current.title} — ${current.reference} — ${current.state}` : 'No READY_FOR_CAPTURE Engagement selected';
      document.querySelector('#engagement').textContent = currentText;
      document.querySelector('#capture-engagement').textContent = currentText;
      document.querySelector('#chain').textContent = data.chain.join(' → ');
      document.querySelector('#counts').innerHTML = Object.entries(data.counts).map(([name, value]) => `<div><strong>${value}</strong><br>${escapeText(name.replace('_', ' '))}</div>`).join('');
      document.querySelector('#recent').innerHTML = data.recent_captures.map(evidenceItem).join('');
      document.querySelector('#pending').innerHTML = data.pending_review.map(evidenceItem).join('');
    }
    function evidenceItem(item) {
      const media = item.media_url ? ` <a href="${item.media_url}">Preview</a>` : '';
      const action = item.status === 'PENDING_REVIEW' ? ` <button data-review="${item.evidence_id}">Mark Reviewed</button>` : '';
      return `<li><strong>${escapeText(item.evidence_id)}</strong> — ${escapeText(item.filename)} (${escapeText(item.status)})${media}${action}</li>`;
    }
    function readBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',', 2)[1]);
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
      });
    }
    function setCaptureProcessing(isProcessing) {
      captureInput.disabled = isProcessing;
      retryCapture.disabled = isProcessing;
      captureControl.classList.toggle('is-processing', isProcessing);
      captureControl.setAttribute('aria-disabled', String(isProcessing));
      captureControl.setAttribute('aria-busy', String(isProcessing));
    }
    function captureAttemptKey() {
      return crypto.randomUUID ? crypto.randomUUID() : `capture-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }
    async function uploadCapture(payload) {
      notice.textContent = 'Uploading';
      const response = await fetch('/workbench/api/v1/evidence', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
      if (!response.ok) { pendingCapture = null; retryCapture.hidden = true; notice.textContent = 'Capture failed. The server did not accept the image.'; return; }
      const captured = (await response.json()).evidence;
      pendingCapture = null;
      retryCapture.hidden = true;
      notice.textContent = `Captured ${captured.evidence_id}.`;
    }
    captureInput.addEventListener('change', async event => {
      const file = event.target.files[0];
      if (!file || captureInProgress) { event.target.value = ''; return; }
      captureInProgress = true;
      setCaptureProcessing(true);
      let phase = 'read';
      try {
        notice.textContent = 'Preparing capture';
        const base64 = await readBase64(file);
        phase = 'upload';
        pendingCapture = {filename: file.name, media_type: file.type, data_base64: base64, capture_attempt_key: captureAttemptKey()};
        await uploadCapture(pendingCapture);
      } catch (error) {
        if (phase === 'read') { notice.textContent = 'Capture failed. The image file could not be read.'; }
        else { retryCapture.hidden = false; notice.textContent = 'Capture failed. The upload request could not be completed. Retry the upload.'; }
      } finally {
        captureInProgress = false;
        setCaptureProcessing(false);
        event.target.value = '';
        loadWorkbench({ preserveNotice: true });
      }
    });
    retryCapture.addEventListener('click', async () => {
      if (!pendingCapture || captureInProgress) return;
      captureInProgress = true;
      setCaptureProcessing(true);
      try { await uploadCapture(pendingCapture); }
      catch (error) { retryCapture.hidden = false; notice.textContent = 'Capture failed. The upload request could not be completed. Retry the upload.'; }
      finally { captureInProgress = false; setCaptureProcessing(false); loadWorkbench({ preserveNotice: true }); }
    });
    document.addEventListener('click', async event => {
      const evidenceId = event.target.dataset.review; if (!evidenceId) return;
      const response = await fetch(`/workbench/evidence/${evidenceId}/review`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({notes: 'Reviewed in local workbench.'})});
      notice.textContent = response.ok ? `Reviewed ${evidenceId}.` : 'Review failed.'; loadWorkbench();
    });
    loadWorkbench();
  </script>
</body>
</html>"""


ENGAGEMENT_SETUP_PAGE = """<!doctype html>
<html lang="en-AU">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#005a9c">
  <title>New Engagement | ACE Workbench</title>
  <style>
    :root { font-family: Arial, sans-serif; color: #17212b; background: #f4f7f8; }
    body { margin: 0; }
    main { max-width: 780px; margin: auto; padding: max(1rem, env(safe-area-inset-top)) max(1rem, env(safe-area-inset-right)) max(1rem, env(safe-area-inset-bottom)) max(1rem, env(safe-area-inset-left)); }
    form, section { background: #fff; border-radius: .5rem; box-shadow: 0 1px 3px #0002; padding: 1rem; margin: 1rem 0; }
    .grid { display: grid; gap: 1rem; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    label { display: grid; gap: .35rem; font-weight: bold; }
    input, textarea, select, button { box-sizing: border-box; font: inherit; font-size: 16px; min-height: 44px; }
    input, textarea, select { width: 100%; border: 1px solid #9aa5b1; border-radius: .25rem; padding: .5rem; }
    textarea { min-height: 100px; resize: vertical; }
    button { border: 0; border-radius: .3rem; background: #005a9c; color: white; padding: .6rem 1rem; cursor: pointer; touch-action: manipulation; }
    button[disabled] { background: #52606d; cursor: not-allowed; }
    .notice { min-height: 1.5rem; } .muted { color: #52606d; } .status { white-space: pre-wrap; }
    @media (max-width: 560px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main>
    <p><a href="/workbench">Back To Field Capture Workbench</a></p>
    <h1>New Engagement</h1>
    <p class="muted">G0 permits fictional Engagements only. Do not enter real-client information.</p>
    <form id="engagement-form">
      <div class="grid">
        <label>Title<input name="title" maxlength="240"></label>
        <label>Engagement Reference<input name="reference" maxlength="120"></label>
        <label>Authority<input name="authority" maxlength="2000"></label>
        <label>Purpose<input name="purpose" maxlength="2000"></label>
        <label>Review Start Date<input name="review_start_date" type="date"></label>
        <label>Review End Date<input name="review_end_date" type="date"></label>
        <label>Evidence Cut-Off Date<input name="evidence_cut_off_date" type="date"></label>
        <label>Accountable Auditor<input name="accountable_auditor" maxlength="240"></label>
        <label>Data Classification<select name="data_classification"><option value="">Select classification</option><option value="FICTIONAL">FICTIONAL</option><option value="PUBLIC">PUBLIC</option><option value="AUDITCO_OWNED">AUDITCO_OWNED</option><option value="REAL_CLIENT">REAL_CLIENT</option></select></label>
        <label>Engagement Status<select name="is_fictional"><option value="">Select status</option><option value="true">Fictional</option><option value="false">Real-client</option></select></label>
      </div>
      <label>Scope<textarea name="scope"></textarea></label>
      <label>Exclusions<textarea name="exclusions"></textarea></label>
      <p><button type="submit">Save Draft</button></p>
    </form>
    <section aria-live="polite">
      <h2>Setup Summary</h2>
      <p class="notice" id="notice">Save a DRAFT for review.</p>
      <pre class="status" id="summary"></pre>
      <label><input id="confirm" type="checkbox"> I confirm the authority, scope, exclusions and fictional data boundary.</label>
      <p><button id="activate" type="button" disabled>Activate For Capture</button></p>
    </section>
  </main>
  <script>
    const form = document.querySelector('#engagement-form');
    const notice = document.querySelector('#notice');
    const summary = document.querySelector('#summary');
    const activate = document.querySelector('#activate');
    const confirm = document.querySelector('#confirm');
    let engagementId = null;
    function creationAttemptKey() {
      return crypto.randomUUID ? crypto.randomUUID() : `attempt-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }
    function draftPayload() {
      const values = Object.fromEntries(new FormData(form).entries());
      return {
        ...values,
        creation_attempt_key: form.dataset.attemptKey || (form.dataset.attemptKey = creationAttemptKey()),
        data_classification: values.data_classification || null,
        is_fictional: values.is_fictional === '' ? null : values.is_fictional === 'true'
      };
    }
    function showRecord(record) {
      engagementId = record.engagement_id;
      summary.textContent = JSON.stringify(record, null, 2);
      activate.disabled = false;
    }
    form.addEventListener('submit', async event => {
      event.preventDefault();
      activate.disabled = true;
      const response = await fetch('/workbench/api/v1/engagements', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(draftPayload()) });
      if (!response.ok) { notice.textContent = 'The Engagement DRAFT was not saved.'; return; }
      const data = await response.json();
      if (data.engagement.state === 'DRAFT') { confirm.checked = false; }
      showRecord(data.engagement);
      notice.textContent = 'The Engagement is saved as DRAFT. Review the setup before activation.';
    });
    activate.addEventListener('click', async () => {
      if (!engagementId) return;
      const response = await fetch(`/workbench/api/v1/engagements/${engagementId}/activate`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({confirmed: confirm.checked}) });
      if (!response.ok) { notice.textContent = 'The Engagement was not activated. Complete the controlled setup and confirmation.'; return; }
      const data = await response.json();
      showRecord(data.engagement);
      notice.textContent = 'The Engagement is READY_FOR_CAPTURE and is the current capture context.';
    });
  </script>
</body>
</html>"""
