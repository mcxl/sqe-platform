"""Phase 6A/6B1 — Read-only client release view.

Endpoints:
    GET /client                           — HTML page (mobile-friendly)
    GET /client/signout                   — Ends the browser Basic auth session
    GET /client/api/v1/release/current    — JSON API
"""

from __future__ import annotations

import html

from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasicCredentials

from src.ace.domain.release import ClientReleaseResponse
from src.ace.workbench.client_auth import basic_auth, require_client
from src.ace.workbench.client_release_projection import ClientReleaseProjection
from src.ace.workbench.client_release_service import ClientReleaseService
from src.ace.workbench.storage import WorkbenchStore

router = APIRouter(prefix="/client", tags=["client"])


# ── Page authentication ────────────────────────────────────────

AUTH_REALM_HEADER = {"WWW-Authenticate": 'Basic realm="ACE Client Release"'}


def require_client_page(
    credentials: HTTPBasicCredentials | None = Security(basic_auth),
) -> str:
    """Page variant of ``require_client`` for browsers.

    ``require_client`` runs first, so an unconfigured server still fails
    closed with 503. A browser only sends Basic credentials after a 401
    challenge, so only the missing-credentials 403 becomes 401 plus
    ``WWW-Authenticate``. Wrong credentials keep the generic 403.
    The JSON API keeps ``require_client`` unchanged.
    """
    try:
        return require_client(credentials)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_403_FORBIDDEN and credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sign in required",
                headers=AUTH_REALM_HEADER,
            ) from exc
        raise


# ── Storage helpers ────────────────────────────────────────────

def _get_client_data(
    store: WorkbenchStore, engagement_id: str
) -> ClientReleaseResponse:
    """Fetch the full client response or return an empty-state response."""
    service = ClientReleaseService()
    projection = ClientReleaseProjection()
    with store.connect() as conn:
        current = service.get_current_release(conn, engagement_id)
        if current is None:
            return projection.project(None, [], None)
        engagement = service.get_engagement(conn, engagement_id)
        if engagement is None:
            return projection.project(current.package, current.entries, None)
        # G0 guard: reject any engagement that is not fictional-only.
        if (
            engagement["is_fictional"] != 1
            or engagement["data_classification"] != "FICTIONAL"
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Client release view is unavailable.",
            )
        return projection.project(current.package, current.entries, engagement)


# ── API endpoint ────────────────────────────────────────────────

@router.get("/api/v1/release/current")
def release_current(
    engagement_id: str = Depends(require_client),
    store: WorkbenchStore = Depends(lambda: WorkbenchStore()),
) -> ClientReleaseResponse:
    """Return the current published release for the configured engagement."""
    return _get_client_data(store, engagement_id)


# ── HTML page ──────────────────────────────────────────────────

CLIENT_PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Client Release View — ACE</title>
<style>
  :root {{
    --bg: #fafafa;
    --card-bg: #fff;
    --text: #1a1a1a;
    --muted: #555;
    --border: #ddd;
    --brand: #1e4d8c;
    --notice-bg: #eef2f7;
    --notice-text: #1e4d8c;
    --tap: 44px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    -webkit-text-size-adjust: 100%;
  }}
  .container {{
    max-width: 720px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }}
  h1 {{ font-size: 1.5rem; font-weight: 600; color: var(--brand); overflow-wrap: anywhere; }}
  h2 {{ font-size: 1.125rem; font-weight: 600; color: var(--brand); margin-top: 2rem; }}
  .page-actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-top: 1rem;
  }}
  .page-actions a {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: var(--tap);
    min-width: var(--tap);
    padding: 0 1rem;
    border: 1px solid var(--brand);
    border-radius: 8px;
    color: var(--brand);
    background: var(--card-bg);
    text-decoration: none;
    font-weight: 600;
  }}
  .page-actions a:focus-visible,
  .copy-button:focus-visible {{ outline: 3px solid #0a58ca; outline-offset: 2px; }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    margin-top: 1rem;
  }}
  .card p {{ margin-top: 0.5rem; overflow-wrap: anywhere; }}
  .card p:first-of-type {{ margin-top: 0; }}
  .label {{
    font-weight: 600;
    color: var(--muted);
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .notice {{
    background: var(--notice-bg);
    color: var(--notice-text);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-top: 1.5rem;
    font-size: 0.9375rem;
  }}
  .meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    margin-top: 0.75rem;
  }}
  .meta-item {{ font-size: 0.875rem; color: var(--muted); }}
  .action-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-top: 0.75rem;
    font-size: 0.875rem;
    color: var(--muted);
  }}
  .action-meta span {{ white-space: nowrap; }}
  .copy-button {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: var(--tap);
    min-width: var(--tap);
    margin-top: 1rem;
    padding: 0 1rem;
    border: 1px solid var(--brand);
    border-radius: 8px;
    background: var(--brand);
    color: #fff;
    font: inherit;
    font-weight: 600;
    cursor: pointer;
  }}
  .copy-status {{
    min-height: 1.5rem;
    margin-top: 0.5rem;
    font-size: 0.9375rem;
    color: var(--muted);
  }}
  .empty {{
    text-align: center;
    padding: 3rem 1rem;
    color: var(--muted);
  }}
  @media (max-width: 480px) {{
    .container {{ padding: 1rem 0.75rem; }}
    .meta {{ gap: 0.75rem; }}
    .action-meta {{ gap: 0.5rem; flex-direction: column; }}
    .page-actions a {{ flex: 1 1 auto; }}
    .copy-button {{ width: 100%; }}
  }}
</style>
</head>
<body>
<main class="container" id="main">
  <header class="page-header">
    <h1>{engagement_name}</h1>
    <div class="meta">
      <span class="meta-item">Status: {review_status}</span>
      <span class="meta-item">Release: v{release_version}</span>
      <span class="meta-item">Published: {published_at}</span>
    </div>
    <nav class="page-actions" aria-label="Page actions">
      <a href="/client">Refresh</a>
      <a href="/client/signout">Sign out</a>
    </nav>
  </header>

  {content}

  <div class="notice">
    Fictional pilot information only. This view is not a client audit report.
  </div>
</main>
{script}
</body>
</html>"""


# Kept out of ``str.format`` so the JavaScript braces need no escaping and
# the page never contains a literal ``<script>`` tag.
CLIENT_PAGE_SCRIPT = """\
<script type="module">
const fallbackMessage =
  "Copy is unavailable here. The action text is selected \\u2014 use Copy from the menu.";

function selectAndReport(target, statusEl) {
  const range = document.createRange();
  range.selectNodeContents(target);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  statusEl.textContent = fallbackMessage;
}

for (const button of document.querySelectorAll("button.copy-button")) {
  button.addEventListener("click", () => {
    const target = document.getElementById(button.dataset.copyTarget);
    const statusEl = document.getElementById(button.dataset.statusTarget);
    if (!target || !statusEl) {
      return;
    }
    const text = target.textContent;
    const doneMessage = button.textContent.trim().replace("Copy", "Copied") + ".";
    if (window.isSecureContext && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        () => { statusEl.textContent = doneMessage; },
        () => { selectAndReport(target, statusEl); },
      );
      return;
    }
    selectAndReport(target, statusEl);
  });
}
</script>"""


SIGNOUT_PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Signed Out — ACE</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
         background: #fafafa; color: #1a1a1a; line-height: 1.6; margin: 0; }
  main { max-width: 720px; margin: 0 auto; padding: 2rem 1rem; }
  h1 { font-size: 1.5rem; font-weight: 600; color: #1e4d8c; }
  a { display: inline-flex; align-items: center; min-height: 44px; padding: 0 1rem; margin-top: 1rem;
      border: 1px solid #1e4d8c; border-radius: 8px; color: #1e4d8c; text-decoration: none; font-weight: 600; }
</style>
</head>
<body>
<main id="main">
  <h1>Signed Out</h1>
  <p>The server asked your browser to forget the sign-in for the client release view.</p>
  <p>Some browsers keep the sign-in until every window closes. To finish signing out, close all browser windows.</p>
  <a href="/client">Sign in again</a>
</main>
</body>
</html>"""


def _render_page(data: ClientReleaseResponse) -> str:
    """Render the client page HTML from response data."""
    if data.conclusion is None and not data.actions:
        content = '<div class="empty">No current client release is available.</div>'
    else:
        parts: list[str] = []
        if data.conclusion is not None:
            parts.append(
                '<h2>Approved Conclusion</h2>'
                '<div class="card">'
                '<p class="label">Title</p>'
                f"<p>{html.escape(data.conclusion.title)}</p>"
                '<p class="label" style="margin-top:1rem">Summary</p>'
                f"<p>{html.escape(data.conclusion.summary)}</p>"
                '<p class="label" style="margin-top:1rem">Evidence Reference</p>'
                f"<p>{html.escape(data.conclusion.evidence_reference_id)}</p>"
                "</div>"
            )
        if data.actions:
            parts.append('<h2>Agreed Actions</h2>')
            for index, action in enumerate(data.actions, start=1):
                parts.append(
                    '<div class="card">'
                    '<p class="label">Description</p>'
                    f'<p id="action-desc-{index}">{html.escape(action.description)}</p>'
                    '<div class="action-meta">'
                    f"<span>Owner: {html.escape(action.owner)}</span>"
                    f"<span>Target: {html.escape(action.target_date)}</span>"
                    f"<span>Status: {html.escape(action.status)}</span>"
                    "</div>"
                    '<button type="button" class="copy-button" '
                    f'data-copy-target="action-desc-{index}" '
                    f'data-status-target="copy-status-{index}">'
                    f"Copy action {index}</button>"
                    f'<p class="copy-status" id="copy-status-{index}" '
                    'role="status" aria-live="polite"></p>'
                    "</div>"
                )
        content = "".join(parts)

    return CLIENT_PAGE_HTML.format(
        engagement_name=html.escape(data.engagement_name),
        review_status=html.escape(data.review_status),
        release_version=data.release_version,
        published_at=html.escape(data.published_at),
        content=content,
        script=CLIENT_PAGE_SCRIPT,
    )


@router.get("", response_class=HTMLResponse)
def client_page(
    request: Request,
    engagement_id: str = Depends(require_client_page),
    store: WorkbenchStore = Depends(lambda: WorkbenchStore()),
) -> HTMLResponse:
    """Render the read-only client release page."""
    data = _get_client_data(store, engagement_id)
    return HTMLResponse(_render_page(data))


@router.get("/signout", response_class=HTMLResponse)
def client_signout() -> HTMLResponse:
    """Always answer 401 so the browser drops its cached Basic credentials.

    No store access and no dependency on configuration or credentials.
    """
    return HTMLResponse(
        SIGNOUT_PAGE_HTML,
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers=AUTH_REALM_HEADER,
    )
