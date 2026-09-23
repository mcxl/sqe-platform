# Web Mobile Proof For The Client Release Page

Date: 2026-09-23 (UTC). Branch: `vorflux/client-mobile-proof` from review commit
`cc05ca085e2b3d1e374c13f503bd35e280ba859f`. Main is untouched. The branch was pushed to
`origin/vorflux/client-mobile-proof` on 2026-09-23 after user approval. No pull request exists
unless a later record says so.

## Outcome

**Inconclusive** by the plan's outcome table: the public preview proxy replaces the
`Authorization` header, so the user could not test on an iPhone within the session. Local
evidence is complete and passes every local rule (focused tests green, browser sign-in, copy,
zero axe violations, API bytes unchanged, diff limited to the allowed files plus one
recorded deviation). The iPhone step is pending on the user's own network.

Fictional data only (G0). No credentials are stored in this folder.

## Purpose

Prove that a fictional client can open the existing Python release page (`GET /client`)
in a mobile browser, sign in, read the current release, copy an action, refresh, and sign
out. The Swift app is frozen for this round. The JSON API is unchanged.

## What Changed

One product file and two test files (commit `cba3db3`, review fixes in `75e6a14`):

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
| Focused pytest after review fixes | 344 passed | `after/pytest-final.txt` |
| Unauthenticated `/client` before | 403, no `WWW-Authenticate`; headless Chromium with credentials configured never signed in | `baseline/curl-client-noauth.txt`, `baseline/*-browser-denied.*` |
| Unauthenticated `/client` after | 401 with `WWW-Authenticate`; browser signed in on the retry | `after/snapshot-mobile-native-auth.txt`, `after/mobile-390x844-signed-in.png` |
| Wrong credentials | 403, no challenge | `test_page_requires_auth` (no separate curl capture was kept) |
| Unconfigured server, no credentials | 503, no challenge (fail-closed check runs first) | `test_page_unconfigured_server_fails_closed_before_challenge` |
| API without credentials | 403 unchanged | tests, curl |
| Copy action 1 (headless Chromium, secure context) | status line `Copied action 1.` | `after/copy-status-after-click.txt`, `after/mobile-390x844-after-copy.png` |
| Tap targets at 390x844 | Refresh 175x44, Sign out 179x44, Copy 139x44 | `after/tap-targets-mobile.json` |
| axe WCAG 2.0 A/AA at 390x844 and 1280x800 | 0 violations before and after | `baseline/a11y-*-forced-header.json`, `after/a11y-*.json` |
| Release v4 published through `ClientReleaseService` | v2 withdrawn, v4 published, visible in API and page | `scripts/publish-output.txt`, `baseline/api-current-after-publish.json` |
| Sign-out page body in headless Chromium | Inconclusive: Chromium reports `ERR_INVALID_AUTH_CREDENTIALS` on any 401 and does not render the body | `after/snapshot-signout.txt` |
| Public preview URL sign-in | Blocked: the Vorflux proxy replaces `Authorization` with a fixed value | `after/preview-proxy-finding.md` |
| iPhone test | Pending: see "iPhone Test On Your Own Network" | `iphone/` (empty) |

## Branch And Commits

| Commit | Content |
|---|---|
| `a35b988` | Group A baseline evidence |
| `cba3db3` | Group B product and test change |
| `59a01f2` | Group B after-change evidence |
| `0814718` | This README (first version) |
| `3b1b1db`, `404f0df`, `2a39964`, `3b1d846` | Group D instruction edits (5, 3, 21, 13 lines) |
| `43fa11d` | Final focused test run record |
| `75e6a14` | Review fixes: auth order, exact copy text, CSS, two tests |

The history was rebuilt once before the first push: the first Group B commit converted the
three CRLF code files to LF and rewrote about 19,000 lines. The commits were recreated with
CRLF preserved (313 code lines changed). The earlier hashes (`c627704`, `4c5c40c`, `e206255`)
exist only on a stale local branch and are not part of this branch.

## Review Record

Roles per AGENTS.md "Implementation And Review Roles":

| Role | Identity | Outcome |
|---|---|---|
| Implementation owner | Vorflux agent, session `fcbc5fd9-1849-448d-bad3-98848678b555` | Change plus focused tests |
| Independent standards reviewer | Vorflux review subagent (same session) | No blocker; six should-fix items on README honesty and one on auth order, all addressed in `75e6a14` and this README |
| Code reviewer with risk assessment | Vorflux review subagent (same session) | Risk 3/10, Low; "ship with mitigations"; mitigations applied in `75e6a14` |
| Exact-candidate final reviewer | Not yet run on the final head | Pending |

No Greptile configuration exists in this repository. A Greptile review, if wanted, runs on a
pull request by one manual `@greptileai` comment with user approval (delivery workflow step 4).

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

1. Sign in when Safari asks. Confirm the engagement name and `Release: v2` appear. (The sandbox
   screenshots show `v4` because the proof published a new release there; a fresh data directory
   seeds `v2`.)
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

## What This Does Not Prove

- Behaviour on a real iPhone or in Safari (pending).
- Hosting with HTTPS, or any credential handling beyond the single environment identity.
- Real client data or a real engagement (fictional data only).
- VoiceOver, other screen readers, or browsers other than headless Chromium.
- That Safari drops Basic credentials on sign-out.

## Retained Evidence Naming

File names differ from the plan's list: `curl-client-noauth.txt` replaces
`unauth-response-baseline.txt`; axe results are `a11y-*.json` only; no `group-b.diff` was
kept (the commit is the record); no iPhone emulation screenshot beyond the 390x844 viewport
captures; `iphone/` is empty and therefore untracked.

## Cleanup

Stop uvicorn and delete the temporary data directory after the proof. `uv.lock` was rewritten by
`uv sync` and reverted with `git checkout -- uv.lock`; no dependency changed.
