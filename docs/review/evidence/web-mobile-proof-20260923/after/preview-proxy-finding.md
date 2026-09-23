# Preview Proxy Finding

Date: 2026-09-23 (UTC). Environment: Vorflux Linux sandbox, `port expose` to `*.preview.us1.vorflux.com`.

## Observation

- Local `curl -u <client credentials> http://127.0.0.1:8000/client` returns 200.
- The same request through the public preview URL returns 401 with `WWW-Authenticate`.
- A throwaway header-echo server on port 8001 received the client `Authorization` header locally
  (SHA-256 prefix `917ce6d0bcf2`, length 50) but, through the proxy, a fixed proxy-owned value
  (prefix `98ce890923ed`, length 43) for any client credentials, including `a:b`.
- Other headers (`Cookie`, `X-Custom`) pass unchanged. The proxy adds `X-Forwarded-*` headers.
- Both the registered session preview route (port 8000) and a plain exposed port (8002) behave the same.

## Consequence

HTTP Basic sign-in cannot traverse the Vorflux preview proxy. The iPhone test over a
preview URL is **not possible** without either a different tunnel or a different sign-in
mechanism. The application itself is not at fault: the 401 challenge, 403 on wrong
credentials, and 200 on correct credentials all hold locally and in the headless browser.

## Status

Inconclusive for the public-URL path, as the plan anticipated. Reported to the platform as
infrastructure issue ID 3. Awaiting a human decision on how to run the iPhone step.
