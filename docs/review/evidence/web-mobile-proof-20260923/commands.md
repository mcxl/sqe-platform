# Commands And Exit Codes

| Timestamp (UTC) | Command | Exit | Note |
|---|---|---|---|
| 2026-09-23T07:36:09Z | `git switch -c vorflux/client-mobile-proof` | 0 | From cc05ca085e2b3d1e374c13f503bd35e280ba859f |
| 2026-09-23T07:36:18Z | `uv sync --extra test` | 0 | |
| 2026-09-23T07:36:31Z | `git checkout -- uv.lock` | 0 | uv sync rewrote uv.lock (resolver metadata); reverted, no dependency change |
| 2026-09-23T07:39:40Z | `uv run pytest tests/test_client_release.py tests/test_client_release_projection.py -q -p no:cacheprovider` | 0 | baseline |
| 2026-09-23T07:40:25Z | `curl -si http://127.0.0.1:8000/client` (no credentials) | 0 | see baseline/curl-client-noauth.txt |
| 2026-09-23T07:42:14Z | agent-browser baseline: set credentials → browser stayed on 403 JSON (no WWW-Authenticate challenge); rendered page captured with forced Authorization header | 0 | baseline/*-browser-denied.*, baseline/*-forced-header.* |
| 2026-09-23T07:43:36Z | `uv run python docs/review/evidence/web-mobile-proof-20260923/scripts/publish_fictional_release_webproof.py` | 1 | attempt 1 |
| 2026-09-23T07:43:49Z | `uv run python docs/review/evidence/web-mobile-proof-20260923/scripts/publish_fictional_release_webproof.py` | 0 | attempt 2 after dict-access fix |
| 2026-09-23T07:52:31Z | `uv run pytest tests/test_client_release.py tests/test_client_release_projection.py tests/test_app.py -q -p no:cacheprovider -x` | 0 | after Group B changes |
| 2026-09-23T07:53:29Z | curl checks through public preview https://p8nkikhn9jtm.preview.us1.vorflux.com | 0 | after/curl-public-preview.txt |
| 2026-09-23T07:54:56Z | curl checks through plain exposed port 8002 preview | 0 | after/curl-public-preview.txt; session preview route on 8000 dropped Authorization |
| 2026-09-23T08:02:55Z | `uv run pytest tests/test_client_release.py tests/test_client_release_projection.py tests/test_app.py -q -p no:cacheprovider` | 0 | final run on rebuilt head (CRLF preserved) |
