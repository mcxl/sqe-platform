# Web Mobile Proof For The Client Release Page

Date: 2026-09-23 (UTC). Branch: `vorflux/client-mobile-proof` from review commit
`cc05ca085e2b3d1e374c13f503bd35e280ba859f`. Main is untouched. Nothing is pushed.

Fictional data only (G0). No credentials are stored in this folder.

## Purpose

Prove that a fictional client can open the existing Python release page (`GET /client`)
in a mobile browser, sign in, read the current release, copy an action, refresh, and sign
out. The Swift app is frozen for this round. The JSON API is unchanged.

## What Changed

One product file and two test files (commit `c627704`):

| File | Change |
|---|---|
| `src/ace/workbench/client_routes.py` | `require_client_page` returns 401 with `WWW-Authenticate: Basic realm="ACE Client Release"` when no credentials arrive, so browsers can sign in. Wrong credentials keep 403. New `GET /client/signout` always answers 401 with a Signed Out page. Page gains `main`, `header`, `nav` landmarks, Refresh and Sign out links, one Copy button per action with a polite status line, 44px tap targets, and a `<script type="module">` that uses `navigator.clipboard` in secure contexts and selects the text as a fallback. |
| `tests/test_client_release.py` | 401 challenge test, no-edit-controls test allows only `type="button"` copy buttons, HTML byte pin re-recorded (5990 bytes, `fd7fb658…cb4b`; API pin 599 bytes, `5e19bc98…6856af`, unchanged), new `TestMobileClientPage` (8 tests). |
| `tests/test_app.py` | Route inventory gains `/client/signout`. Deviation from the plan, which listed two files: the inventory test enumerates every route. |

## Results

| Check | Result | Evidence |
|---|---|---|
| Focused pytest before change | 325 passed (plan estimated 266; the real count is recorded) | `baseline/pytest-baseline.txt` |
| Focused pytest after change (plus `tests/test_app.py`) | 342 passed | `after/pytest-after.txt` |
| Unauthenticated `/client` before | 403, no `WWW-Authenticate`; headless Chromium with credentials configured never signed in | `baseline/curl-client-noauth.txt`, `baseline/*-browser-denied.*` |
| Unauthenticated `/client` after | 401 with `WWW-Authenticate`; browser signed in on the retry | `after/snapshot-mobile-native-auth.txt`, `after/mobile-390x844-signed-in.png` |
| Wrong credentials | 403, no challenge (local) | `after/curl-public-preview.txt` (local block), tests |
| API without credentials | 403 unchanged | tests, curl |
| Copy action 1 (headless Chromium, secure context) | status line `Copied action 1.` | `after/copy-status-after-click.txt`, `after/mobile-390x844-after-copy.png` |
| Tap targets at 390x844 | Refresh 175x44, Sign out 179x44, Copy 139x44 | `after/tap-targets-mobile.json` |
| axe WCAG 2.0 A/AA at 390x844 and 1280x800 | 0 violations before and after | `baseline/a11y-*-forced-header.json`, `after/a11y-*.json` |
| Release v4 published through `ClientReleaseService` | v2 withdrawn, v4 published, visible in API and page | `scripts/publish-output.txt`, `baseline/api-current-after-publish.json` |
| Sign-out page body in headless Chromium | Inconclusive: Chromium reports `ERR_INVALID_AUTH_CREDENTIALS` on any 401 and does not render the body | `after/snapshot-signout.txt` |
| Public preview URL sign-in | Blocked: the Vorflux proxy replaces `Authorization` with a fixed value | `after/preview-proxy-finding.md` |
| iPhone test | Pending: see "iPhone Test On Your Own Network" | `iphone/` (empty) |

## Human Decisions Recorded

- Scope: web-first proof only; Swift frozen. (Plan approval)
- D1 (401 challenge for the page only) and D2 (`/client/signout`): proceeded on the plan's recommendation.
- D3 (publish a new fictional release): done with a disposable script in `scripts/`.
- iPhone path after the proxy finding: user left it to agent judgment. No new tools were added
  because AGENTS.md requires explicit approval. The test moves to the user's own network.

## iPhone Test On Your Own Network

Run on a Mac on the same Wi-Fi as the iPhone. Choose your own fictional credentials.

```bash
git fetch origin && git switch vorflux/client-mobile-proof   # after the branch is pushed
uv sync --extra test
export ACE_DATA_DIR="$HOME/ace-proof-data"
export ACE_AUDITOR_PASSWORD="<choose>"
export ACE_CLIENT_USERNAME="fictional-client"
export ACE_CLIENT_PASSWORD="<choose>"
export ACE_CLIENT_ENGAGEMENT_ID="ENG-FIC-0001"
uv run uvicorn src.ace.app:app --host 0.0.0.0 --port 8000
ipconfig getifaddr en0     # Mac IP for the iPhone
```

On the iPhone open `http://<mac-ip>:8000/client` in Safari.

Tester script (one screenshot per step, save as `iphone/step-1.png` to `step-5.png`):

1. Sign in when Safari asks. Confirm the engagement name and `Release: v2` appear.
2. Scroll the whole page. Confirm the conclusion and the agreed action read fully with no clipped text.
3. Tap `Copy action 1`. Over plain `http` the clipboard is unavailable, so the expected status is
   `Copy is unavailable here. The action text is selected — use Copy from the menu.` Use Copy from the
   iOS menu and paste into Notes. Over `https` the expected status is `Copied action 1.`
4. Tap `Refresh`. Confirm the page reloads without a new sign-in prompt.
5. Tap `Sign out`. Cancel the prompt and confirm the Signed Out page. Reopen `/client` and confirm
   Safari asks for credentials again. Note: Safari may keep Basic credentials until the tab closes;
   record what happens.

Write observations to `iphone/tester-notes.md`. Do not write credentials.

## Known Limits

- HTTP Basic sign-out is browser dependent. The 401 on `/client/signout` is the strongest
  server-side signal available without changing the auth model.
- Clipboard write needs a secure context (`https` or `localhost`). Over LAN `http` the fallback path runs.
- The proof used one agreed action. `test_copy_buttons_are_indexed_per_action` covers three.

## Cleanup

Stop uvicorn and delete the temporary data directory after the proof. `uv.lock` was rewritten by
`uv sync` and reverted with `git checkout -- uv.lock`; no dependency changed.
