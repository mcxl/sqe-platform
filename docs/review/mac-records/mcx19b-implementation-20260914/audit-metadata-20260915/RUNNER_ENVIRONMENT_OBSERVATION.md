# Runtime Timestamp Observation

The existing environment_identity function includes runtime.lastUsage. A read-only settings invocation rejected build reuse after a test changed only runtime.lastUsage.x86_64. See settings-environment-rejection.json.

The private invocation now compares every other environment field unchanged, and retains both full records. Existing build, source, template and product checks remain. The repository runner has not changed.

Potential pilot/full reuse defect: review environment_identity and its callers before relying on resumed pilot/full execution. No final coverage credit is claimed.
