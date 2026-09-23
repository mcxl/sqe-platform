# Revision 5 B/C Wrapper Review Notes

Prepared 16 September 2026. This wrapper collects diagnostics; it grants no acceptance or pilot credit.

## Files And Identity

- Private wrapper: `run-d1-bc-case.py` in the D1 evidence root.
- Wrapper SHA-256: `76235dd27439a3545515a21a8b2a6acae4038403950b1935ba659a5152be7fe1`.
- Required Swift patch SHA-256: `62f87d10820c5cbffdc06f4d663d4ed5e2f23486ae9a5b9c2a833569283b3e3e`.
- Mechanical check record: `run-d1-bc-case-verification.json` in the same folder.
- Reproducible fixture source: `run-d1-bc-case-fixtures.py.txt` in the same folder; pure Python data checks only.

The existing A wrapper, live runner, builder and Swift sources were not edited by this specialist.
The primary separately tightened builder checks for the reviewed patch and original build products.

## Behaviour

Run with the approved Mac Python and arguments `B 1` through `B 5`, then `C 1` through `C 5`.
Luna remains the sole build and simulator execution owner.

The wrapper reuses the live runner's Settings, capture, batch and restoration primitives.
Settings always use the original test template without a D1 environment request.
Coverage configuration receives both `ACE_D1_ARM` and `ACE_D1_REPETITION`; the generated configuration is checked.

The wrapper verifies all retained build hashes, original application binding, reviewed patch and diagnostic source identity.
XCTest's `__TESTHOST__` bundle placeholder resolves against `TestHostPath` before path checks.
The candidate and build identities are checked again after restoration.

It requires 14 ordered B calls or two C unrestricted calls, covering both viewports.
Completion counts, returned calls, callback counts and error markers must agree exactly.
C also requires the recorded stable frame and upper-viewport geometry.
Passing outer case markers still require two audit invocations.

Every native finding remains `FAILED`, including when collection succeeds with native exit 65.
Collection success is separate from native outcome; findings set `stopRequired=true`.
Later executions refuse a prior finding, blocked record, active record or incomplete restoration.
The existing 15-case limit, 360-second case timeout and fixed D1 deadline remain in force.
The conservative latest case-start cutoff is 15:35:44 UTC; the hard deadline is 15:47:44 UTC.
Settings helper executions are counted separately. Their native runner mechanisms remain unchanged.

Thrown calls require exact error equality with that call's callback compact or detailed description.
Unknown errors, errors without callback findings, mixed native failures and incomplete calls block collection.
The native summary must preserve each callback finding as a matching native failure.
The known retained pilot strings are `Contrast failed` and `Contrast failed for SwiftUI.AccessibilityNode`.
There is no generic XCTest-error allowlist.

All manifest entries must retain non-empty exported files. Required PNG signatures and image counts are checked.
Repeated callback names retain separate manifest exports; no one-name-to-one-file assumption is made.
Callback images show callback-time rendering, not the audit's sampled rendering.
An absent native element remains the exact `type=unavailable` sentinel with no invented label or frame.
Available elements require valid recorded frames.

## Verification

Mac command: `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 -m py_compile <D1>/run-d1-bc-case.py`.
Result: exit 0 on the final wrapper hash.

Fixture command: `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 <D1>/run-d1-bc-case-fixtures.py.txt`.
Result: 28 checks passed at `2026-09-16T12:30:14.843160+00:00`.
The retained JSON includes expected rejection messages and the checked wrapper hash.

Checks cover clean B/C diagnostics, preserved native failures, issue-backed throws, unknown errors, missing calls,
wrong repetitions, false completion markers, C geometry, missing frames, native nil elements, environment injection,
unchanged Settings requests, mixed launch failures, timeouts, generated bundle paths and repeated callback names.
Missing exports and callback-image count mismatches are rejected.

## Remaining Work

Primary inspection of the final wrapper and the reviewed diagnostic build remain required before native execution.
No native build, simulator operation, test execution or new native deliberate-failure run occurred here.
The existing retained failure/pass evidence gate must be cited by the primary as approved reuse.
Luna must collect B/C results, verify restoration, inspect every required image and apply each D1 stop row.
Unfamiliar Apple error text deliberately blocks; do not infer that it was caused by a native finding.
