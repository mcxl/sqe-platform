# ACE Diagram Controls

ACE remains the source of truth for audit records and decisions.

The diagrams use fictional labels only. They cannot approve or change audit records.

## Layer 1 — Controlled Diagrams

Files in `controlled/mermaid` contain the controlled diagram source. The pinned Mermaid CLI renders local SVG files into `controlled/svg`.

The progress guide can use a controlled SVG directly when a presentation copy is not required.

Do not change an ACE, MATE or CONTRA term in a presentation copy.

## Layer 2 — Presentation Diagrams

Files in `presentation/html` contain the editable presentation source. Files in `presentation/svg` support the ACE Progress Guide.

Presentation diagrams follow the pinned Diagram Design reference. They use manual AuditCo colours and system fonts.

Each presentation diagram has a fidelity report. The report lists all wording, content and layout changes.

## Render Controlled Diagrams

```powershell
tools\diagram-rendering\render-controlled.ps1
```

## Verify Both Layers

```powershell
.\.venv\Scripts\python.exe tools\diagram-rendering\verify_diagrams.py
```
