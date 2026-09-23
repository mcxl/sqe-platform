# Repository Map Setup

Installed 23 September 2026 at the owner's request. This record concerns tooling, not application acceptance.

## Central Access

Guide filepath: `LOCAL_HOME\Documents\sqe-platform\docs\ace\REPOSITORY-MAP-SETUP.md`.
Hub filepath: `LOCAL_HOME\Documents\sqe-platform\SQE_DEVELOPER_HUB.html`.

| Tool | Status | Main Filepath |
|---|---|---|
| CodeGraph | Verified current against indexed code; see freshness checks below | `LOCAL_HOME\Documents\sqe-platform\.codegraph\codegraph.db` |
| Understand Anything | Current repository snapshot; interactive viewer available locally | `LOCAL_HOME\Documents\sqe-platform\.ua\knowledge-graph.json` |
| Graphify | Current repository snapshot, with documented format exclusions | `LOCAL_HOME\Documents\sqe-platform\graphify-out\graph.html` |
| Code Atlas | Historical architecture illustration | `LOCAL_HOME\Documents\agentic-os-workspace\sqe\docs\ace\atlas\atlas.html` |
| Archify 2.17 | Installed, doctor checks passed; available in Codex | `LOCAL_HOME\.codex\skills\archify\SKILL.md` |

Understand Anything dashboard: [open with the access token included](LOCAL_VIEWER_NOT_PUBLISHED).
If prompted, paste `LOCAL_ACCESS_TOKEN_REMOVED`.
This token belongs to the running local Understand Anything viewer, not CodeGraph. It can change when the viewer restarts.
Keep this guide internal; it contains local access details and private filepaths.

Use the [Development Hub — Repository Maps](../../SQE_DEVELOPER_HUB.html#repository-maps) as the single entry point.
It links the visual maps, CodeGraph instructions, saved artifacts and generation evidence.
The file links stay the same when artifacts are regenerated in place.
The Understand Anything viewer address is session-dependent; update its Hub link after restarting the viewer.

All three maps were generated on 23 September 2026. Use their linked validation records to check freshness.
Application source did not change during this navigation update.

## CodeGraph

CodeGraph 1.1.1 indexed 91 supported code files, including Swift UI tests, with 2,728 nodes and 8,627 edges.
The generation check reported zero pending changes. That check is dated, not a perpetual freshness guarantee.
Index: `LOCAL_HOME\Documents\sqe-platform\.codegraph\codegraph.db`.
It is a query tool for Codex and the terminal; no CodeGraph web dashboard is installed here.

```powershell
codegraph status --json 'LOCAL_HOME\Documents\sqe-platform'
codegraph sync 'LOCAL_HOME\Documents\sqe-platform'
codegraph explore 'ClientReleaseService' --path 'LOCAL_HOME\Documents\sqe-platform'
```

[Index verification](LOCAL_HOME/sqe-private/codegraph-20260923/README.md) records scope and local Git exclusions.

## Keeping The Hub Current

Archify is available separately as a diagram-authoring skill at `LOCAL_HOME\.codex\skills\archify`.
Upstream: [tt-a1i/archify](https://github.com/tt-a1i/archify), pinned commit `8809b273c278a813a47fa37698864779c0d4cf08`.
It complements the three indexes. It does not automatically turn them into diagrams or certify their accuracy.
The Hub links its skill guide and the separate historical Code Atlas. No new SQE Archify diagram has been generated.

After an authorised map refresh, verify the generated files before updating the Hub's generation date and links.
After a viewer restart, verify its tokenised URL and replace the dashboard link in the Hub.
Keep the saved graph and evidence links available when the viewer is stopped.
Record stale or excluded inputs openly. Do not label a map current solely because its file exists.
Refresh changed navigation documents in Graphify and Understand Anything. Check CodeGraph freshness without rebuilding unchanged code.

## Target

`LOCAL_HOME\Documents\sqe-platform`

All three tools target the main SQE repository. The older `agentic-os-workspace\sqe` folder is not the analysis target.

## Installed Tools

| Tool | Identity | Installation |
|---|---|---|
| Graphify | 0.9.13; existing Python installation | `LOCAL_HOME\AppData\Local\Programs\Python\Python314\Scripts\graphify.cmd` |
| Graphify Codex skill | Project registration | `LOCAL_HOME\Documents\sqe-platform\.codex\skills\graphify\SKILL.md` |
| Understand Anything | 2.9.7; upstream commit `6df3065f1d8ddc2ce3615314d1d493f36d6b1c80` | `LOCAL_HOME\.understand-anything\repo` |
| Understand Anything Codex skills | Nine official user-level junctions | `LOCAL_HOME\.agents\skills\understand*` |
| Understand Anything plugin root | Official Windows junction | `LOCAL_HOME\.understand-anything-plugin` |

Understand Anything dependencies are isolated in its own checkout. They were installed from its frozen lock with pnpm 10.6.2.
SQE application dependencies and locks were not changed. The existing Graphify version was retained.

## Coverage

The configured scope includes Python, Next.js, Swift, tests, tools, workflows and Markdown development records.
Tests are not excluded. This avoids the earlier iOS map's missing UI-test coverage.

`.graphifyignore` and `.understandignore` exclude generated output, dependency folders, snapshots, database files and credential-file patterns.
Each tool also applies its built-in exclusions. The generation record documents supported formats and extraction limitations.
Files outside this repository, Git history and Mac evidence are not automatically included.

Generation followed installation on September 23. Understand Anything represents 145 files; Graphify represents 135 of 139 detected files.
The four Graphify omissions and excluded raw links are recorded in its coverage and validation outputs.
The retained September 16 Understand Anything map remains historical.

## Use In Codex

The refreshed Codex skill catalogue exposes both mapping skills. Open the main SQE project.

Request a bounded analysis using one of these prompts:

```text
Use Graphify to analyse LOCAL_HOME\Documents\sqe-platform, including tests and development records.
```

```text
Use Understand Anything to analyse LOCAL_HOME\Documents\sqe-platform, including tests and development records.
```

Understand Anything also exposes `$understand`, `$understand-domain`, `$understand-chat` and `$understand-dashboard` after discovery.
Graphify provides `query`, `path` and `explain` commands once `graphify-out\graph.json` exists.

Generated graph locations:

- `LOCAL_HOME\Documents\sqe-platform\graphify-out\graph.json`
- `LOCAL_HOME\Documents\sqe-platform\.ua\knowledge-graph.json`

## Operation

Automatic hooks and rebuilds remain disabled. The September 23 generation task started a local Understand Anything viewer.
Its current link is maintained in the Hub. The viewer serves saved results; it does not regenerate them.
The installer-generated Graphify hook was disabled, and its inaccurate claim that a graph already existed was corrected.
Generation requires a bounded task; installation is not proof of coverage or correctness.
Use source identities and retained test evidence to establish behaviour. Neither map certifies acceptance or resolves the Copy finding.

## Verification

Passed installation checks:

- Graphify version command and Python parser smoke check.
- Understand Anything core build and production dashboard build.
- Understand Anything synthetic Python, TypeScript and Swift function extraction.
- Both ignore filters retain representative application, UI-test, unit-test and development-record paths.
- Both ignore filters reject representative dependency, snapshot, credential and generated-map paths.
- Nine Understand Anything skill junctions exist. Automatic analysis is disabled.

The dashboard build emitted upstream configuration, Node deprecation and bundle-size warnings, but completed successfully.
The later generation task completed SQE extraction, schema and source-identity checks.
The local viewer's page, graph and referenced assets passed HTTP checks. Visual browser inspection remains unperformed.
See [generation evidence](LOCAL_HOME/sqe-private/map-generation-20260923/README.md).

Installation commands, smoke checks and final identities are recorded under:

`LOCAL_HOME\sqe-private\tool-setup-20260923`

No commit, push, deployment or application test programme forms part of this setup.
