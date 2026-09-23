"""Phase 6A/6B1 — Read-only client release view.

Endpoints:
    GET /client                           — HTML page
    GET /client/api/v1/release/current    — JSON API
"""

from __future__ import annotations

import html

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from src.ace.domain.release import ClientReleaseResponse
from src.ace.workbench.client_auth import require_client
from src.ace.workbench.client_release_projection import ClientReleaseProjection
from src.ace.workbench.client_release_service import ClientReleaseService
from src.ace.workbench.storage import WorkbenchStore

router = APIRouter(prefix="/client", tags=["client"])


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
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
  }}
  .container {{
    max-width: 720px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }}
  h1 {{ font-size: 1.5rem; font-weight: 600; color: var(--brand); }}
  h2 {{ font-size: 1.125rem; font-weight: 600; color: var(--brand); margin-top: 2rem; }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    margin-top: 1rem;
  }}
  .card p {{ margin-top: 0.5rem; }}
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
  .empty {{
    text-align: center;
    padding: 3rem 1rem;
    color: var(--muted);
  }}
  @media (max-width: 480px) {{
    .container {{ padding: 1rem 0.75rem; }}
    .meta {{ gap: 0.75rem; }}
    .action-meta {{ gap: 0.5rem; flex-direction: column; }}
  }}
</style>
</head>
<body>
<div class="container">
  <h1>{engagement_name}</h1>
  <div class="meta">
    <span class="meta-item">Status: {review_status}</span>
    <span class="meta-item">Release: v{release_version}</span>
    <span class="meta-item">Published: {published_at}</span>
  </div>

  {content}

  <div class="notice">
    Fictional pilot information only. This view is not a client audit report.
  </div>
</div>
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
            for action in data.actions:
                parts.append(
                    '<div class="card">'
                    '<p class="label">Description</p>'
                    f"<p>{html.escape(action.description)}</p>"
                    '<div class="action-meta">'
                    f"<span>Owner: {html.escape(action.owner)}</span>"
                    f"<span>Target: {html.escape(action.target_date)}</span>"
                    f"<span>Status: {html.escape(action.status)}</span>"
                    "</div>"
                    "</div>"
                )
        content = "".join(parts)

    return CLIENT_PAGE_HTML.format(
        engagement_name=html.escape(data.engagement_name),
        review_status=html.escape(data.review_status),
        release_version=data.release_version,
        published_at=html.escape(data.published_at),
        content=content,
    )


@router.get("", response_class=HTMLResponse)
def client_page(
    request: Request,
    engagement_id: str = Depends(require_client),
    store: WorkbenchStore = Depends(lambda: WorkbenchStore()),
) -> HTMLResponse:
    """Render the read-only client release page."""
    data = _get_client_data(store, engagement_id)
    return HTMLResponse(_render_page(data))
