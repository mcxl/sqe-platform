# ACE System Atlas

**Historical snapshot — status clarified 23 September 2026.** The diagram's earlier planned-client descriptions are superseded by implemented August release services and client routes. Nodes and flows are retained for reference; no current acceptance is implied.

Use the [current development hub](LOCAL_HOME/Documents/sqe-platform/SQE_DEVELOPER_HUB.html), [code/evidence index](LOCAL_HOME/Documents/sqe-platform/docs/ace/CODE-AND-EVIDENCE-INDEX.md), and [full Vortex brief](LOCAL_HOME/sqe-private/handoffs/2026-09-23-vortex-full-review-brief.md).

This folder is a fictional ACE architecture pilot. It is a discussion surface. It does not change the ACE runtime or audit method.

Edit `data.mjs` only. Then run:

```powershell
node docs/ace/atlas/build.mjs
```

The command writes `SYSTEM.md` and `atlas.html`. Do not edit generated files directly.

Validate the data without writing files:

```powershell
node docs/ace/atlas/build.mjs --validate-only
```

Run the built-in malformed-data check without writing files:

```powershell
node docs/ace/atlas/build.mjs --self-test
```

Open `atlas.html` in a modern browser. It works without a network connection. It has no external fonts, scripts, images, telemetry, or other assets.

The atlas uses representative fictional packets. Do not add client evidence, credentials, or private source text.

See `THIRD_PARTY_NOTICES.md` for the renderer notice.
