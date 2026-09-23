"""Build faithful, local presentation copies of controlled ACE diagrams."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
HTML_ROOT = ROOT / "docs" / "diagrams" / "presentation" / "html"
SVG_ROOT = ROOT / "docs" / "diagrams" / "presentation" / "svg"

PAPER = "#f7f9fb"
PANEL = "#ffffff"
INK = "#1f2933"
MUTED = "#52606d"
LINE = "#d9e2ec"
ACCENT = "#0b5cab"
ACCENT_SOFT = "#e8f1fb"
SUCCESS = "#18794e"
WARNING = "#9a6700"
DANGER = "#b42318"
FONT = "Arial, Helvetica, sans-serif"


def rounded_path(points: list[tuple[int, int]], radius: int = 8) -> str:
    """Return an orthogonal path with rounded corners."""

    if len(points) < 2:
        raise ValueError("A connector needs at least two points.")

    commands = [f"M {points[0][0]} {points[0][1]}"]
    for index in range(1, len(points) - 1):
        previous = points[index - 1]
        corner = points[index]
        following = points[index + 1]

        before = move_towards(corner, previous, radius)
        after = move_towards(corner, following, radius)
        commands.append(f"L {before[0]} {before[1]}")
        commands.append(
            f"Q {corner[0]} {corner[1]} {after[0]} {after[1]}"
        )
    commands.append(f"L {points[-1][0]} {points[-1][1]}")
    return " ".join(commands)


def move_towards(
    start: tuple[int, int], target: tuple[int, int], distance: int
) -> tuple[int, int]:
    """Move an orthogonal point towards another point."""

    if start[0] == target[0]:
        direction = 1 if target[1] > start[1] else -1
        return start[0], start[1] + direction * min(distance, abs(target[1] - start[1]))
    if start[1] == target[1]:
        direction = 1 if target[0] > start[0] else -1
        return start[0] + direction * min(distance, abs(target[0] - start[0])), start[1]
    raise ValueError(f"Connector points are not orthogonal: {start} to {target}")


def connector(
    points: list[tuple[int, int]], *, dashed: bool = False, accent: bool = False
) -> str:
    """Draw a labelled-state-safe connector behind nodes."""

    colour = ACCENT if accent else MUTED
    dash = ' stroke-dasharray="6 6"' if dashed else ""
    marker = "presentation-arrow-accent" if accent else "presentation-arrow"
    return (
        f'<path data-controlled-edge="true" d="{rounded_path(points)}" fill="none" stroke="{colour}" '
        f'stroke-width="2"{dash} marker-end="url(#{marker})"/>'
    )


def connector_label(x: int, y: int, text: str, width: int) -> str:
    """Draw a local-font label with an opaque mask."""

    return (
        f'<rect x="{x - width // 2}" y="{y - 20}" width="{width}" height="20" '
        f'rx="4" fill="{PAPER}"/>'
        f'<text data-controlled-edge-label="{escape(text, quote=True)}" x="{x}" y="{y - 5}" text-anchor="middle" fill="{MUTED}" '
        f'font-family="{FONT}" font-size="12">{escape(text)}</text>'
    )


def box(
    x: int,
    y: int,
    width: int,
    height: int,
    lines: list[str],
    *,
    focal: bool = False,
    note: bool = False,
    stage: int | None = None,
) -> str:
    """Draw one labelled diagram node."""

    fill = ACCENT_SOFT if focal else PANEL
    stroke = ACCENT if focal else (LINE if note else MUTED)
    dash = ' stroke-dasharray="6 6"' if note else ""
    result = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"{dash}/>'
    ]

    text_x = x + width // 2
    anchor = "middle"
    if stage is not None:
        result.extend(
            [
                f'<circle cx="{x + 32}" cy="{y + height // 2}" r="16" fill="{INK}"/>',
                f'<text x="{x + 32}" y="{y + height // 2 + 6}" text-anchor="middle" '
                f'fill="#ffffff" font-family="{FONT}" font-size="16" font-weight="700">{stage}</text>',
            ]
        )
        text_x = x + 64
        anchor = "start"

    font_size = 14 if note else 18
    line_height = 20 if note else 22
    first_y = y + height // 2 - ((len(lines) - 1) * line_height) // 2 + 6
    tspans = "".join(
        f'<tspan x="{text_x}" y="{first_y + index * line_height}">{escape(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    controlled_label = " ".join(lines)
    result.append(
        f'<text data-controlled-label="{escape(controlled_label, quote=True)}" text-anchor="{anchor}" fill="{INK}" font-family="{FONT}" '
        f'font-size="{font_size}" font-weight="600">{tspans}</text>'
    )
    return "".join(result)


def diamond(cx: int, cy: int, lines: list[str]) -> str:
    """Draw an Auditor Decision node."""

    points = f"{cx},{cy - 64} {cx + 120},{cy} {cx},{cy + 64} {cx - 120},{cy}"
    tspans = "".join(
        f'<tspan x="{cx}" y="{cy - 5 + index * 22}">{escape(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    controlled_label = " ".join(lines)
    return (
        f'<polygon points="{points}" fill="{ACCENT_SOFT}" stroke="{ACCENT}" stroke-width="2"/>'
        f'<text data-controlled-label="{escape(controlled_label, quote=True)}" text-anchor="middle" fill="{INK}" font-family="{FONT}" '
        f'font-size="18" font-weight="700">{tspans}</text>'
    )


def zone(x: int, y: int, width: int, height: int, title: str) -> str:
    """Draw a quiet zone for faithful diagrams above nine nodes."""

    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" '
        f'fill="{PAPER}" stroke="{LINE}" stroke-width="2"/>'
        f'<text data-controlled-label="{escape(title, quote=True)}" x="{x + 16}" y="{y + 28}" fill="{INK}" font-family="{FONT}" '
        f'font-size="16" font-weight="700">{escape(title)}</text>'
    )


def shell(slug: str, title: str, description: str, width: int, height: int, body: str) -> str:
    """Create an accessible inline SVG."""

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{slug}-title {slug}-desc">
  <title id="{slug}-title">{escape(title)}</title>
  <desc id="{slug}-desc">{escape(description)}</desc>
  <defs>
    <marker id="presentation-arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
      <polygon points="0 0, 10 4, 0 8" fill="{MUTED}"/>
    </marker>
    <marker id="presentation-arrow-accent" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
      <polygon points="0 0, 10 4, 0 8" fill="{ACCENT}"/>
    </marker>
  </defs>
  <rect width="{width}" height="{height}" fill="{PAPER}"/>
  {body}
</svg>'''


def html_page(title: str, svg: str) -> str:
    """Create the editable Diagram Design presentation source."""

    return f'''<!doctype html>
<html lang="en-AU">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{ --paper: {PAPER}; --ink: {INK}; --line: {LINE}; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: var(--ink); background: var(--paper); font-family: {FONT}; }}
    main {{ width: min(100%, 432px); margin: 0 auto; padding: 16px; }}
    svg {{ display: block; width: 100%; height: auto; }}
    @media (max-width: 430px) {{ main {{ padding: 8px; }} }}
  </style>
</head>
<body>
  <main>{svg}</main>
</body>
</html>
'''


def workflow_diagram() -> tuple[str, str, str]:
    """Build the approved six-stage auditor workflow."""

    nodes = [
        ("Engagement Setup", 40),
        ("Field Evidence Capture", 152),
        ("Evidence Review", 264),
        ("Relationship Review", 376),
        ("MATE Assessment", 488),
        ("Conclusion Review", 600),
    ]
    edges = [
        connector([(200, y + 72), (200, nodes[index + 1][1])], accent=index == 2)
        for index, (_, y) in enumerate(nodes[:-1])
    ]
    boxes = [
        box(40, y, 320, 72, [label], focal=index == 3, stage=index + 1)
        for index, (label, y) in enumerate(nodes)
    ]
    note = (
        f'<text x="200" y="724" text-anchor="middle" fill="{MUTED}" '
        f'font-family="{FONT}" font-size="14">The auditor controls every decision.</text>'
    )
    svg = shell(
        "auditor-workflow-presentation",
        "ACE Auditor Workflow",
        "The six controlled stages from Engagement Setup to Conclusion Review, with Relationship Review highlighted.",
        400,
        752,
        "".join(edges + boxes) + note,
    )
    return "auditor-workflow", "ACE Auditor Workflow", svg


def evidence_relationship_diagram() -> tuple[str, str, str]:
    """Build the faithful, zoned evidence relationship map."""

    backgrounds = [
        zone(8, 8, 384, 700, "Governance Chain"),
        zone(8, 724, 384, 360, "Evidence Provenance"),
        zone(8, 1100, 384, 420, "Evidence Review And Links"),
    ]
    edges = [
        connector([(200, 120), (200, 140)]),
        connector([(200, 204), (200, 224)]),
        connector([(200, 288), (200, 308)]),
        connector([(200, 380), (200, 408)]),
        connector([(104, 504), (104, 488), (176, 488), (176, 472)]),
        connector([(104, 608), (104, 576)]),
        connector([(224, 472), (224, 488), (296, 488), (296, 504)]),
        connector([(200, 836), (200, 864)]),
        connector([(200, 928), (200, 956)]),
        connector([(180, 1020), (180, 1072), (104, 1072), (104, 1156)]),
        connector([(220, 1020), (220, 1072), (296, 1072), (296, 1156)]),
        connector([(188, 1192), (392, 1192), (392, 540), (380, 540)]),
        connector([(316, 576), (368, 576), (368, 1136), (316, 1136), (316, 1156)]),
        connector([(276, 1228), (276, 1252), (104, 1252), (104, 1280)]),
        connector([(316, 1228), (316, 1280)]),
        connector([(336, 1228), (368, 1228), (368, 1380), (200, 1380), (200, 1404)]),
    ]
    labels = [
        connector_label(104, 488, "accountable for", 112),
        connector_label(104, 604, "identifies holder of", 136),
        connector_label(296, 488, "examined by", 92),
        connector_label(200, 860, "supplies", 72),
    ]
    nodes = [
        box(116, 56, 168, 64, ["Engagement"]),
        box(116, 140, 168, 64, ["Binding", "Obligation"]),
        box(116, 224, 168, 64, ["Risk"]),
        box(116, 308, 168, 72, ["Risk-Control", "Relationship"], focal=True),
        box(116, 408, 168, 64, ["Control"]),
        box(20, 504, 168, 72, ["Accountable", "Role"]),
        box(212, 504, 168, 72, ["Audit Question"]),
        box(20, 608, 168, 64, ["Role Assignment"]),
        box(116, 772, 168, 64, ["Evidence Provider"]),
        box(116, 864, 168, 64, ["Source"]),
        box(116, 956, 168, 64, ["Evidence Item"]),
        box(20, 1036, 360, 32, ["Evidence Provider is not Accountable Role"], note=True),
        box(20, 1156, 168, 72, ["Evidence", "Relationship"]),
        box(212, 1156, 168, 72, ["Evidence Review"], focal=True),
        box(20, 1280, 168, 64, ["Evidence", "Relevance"]),
        box(212, 1280, 168, 64, ["Evidence Gap"]),
        box(116, 1404, 168, 72, ["Proposed", "Relationship"]),
    ]
    svg = shell(
        "evidence-relationship-presentation",
        "ACE Evidence Relationship Map",
        "A faithful map of governance, evidence provenance, evidence review and proposed relationship records.",
        400,
        1536,
        "".join(backgrounds + edges + labels + nodes),
    )
    return "evidence-relationship-map", "ACE Evidence Relationship Map", svg


def approval_state_diagram() -> tuple[str, str, str]:
    """Build separate evidence, relationship and conclusion state paths."""

    backgrounds = [
        zone(8, 8, 384, 280, "Evidence Item Review"),
        zone(8, 296, 384, 720, "Relationship Approval"),
        zone(8, 1032, 384, 872, "Conclusion Approval"),
    ]
    edges = [
        connector([(200, 116), (200, 148)]),
        connector([(200, 212), (200, 224)], dashed=True),
        connector([(200, 408), (200, 432)]),
        connector([(200, 496), (200, 516)]),
        connector([(80, 580), (40, 580), (40, 680), (116, 680), (116, 700)]),
        connector([(320, 580), (360, 580), (360, 680), (284, 680), (284, 700)]),
        connector([(200, 644), (200, 804)]),
        connector([(200, 868), (200, 900)]),
        connector([(300, 932), (388, 932), (388, 492), (200, 492), (200, 516)], dashed=True),
        connector([(116, 764), (24, 764), (24, 980), (40, 980)], dashed=True),
        connector([(328, 180), (388, 180), (388, 376), (300, 376)], dashed=True),
        connector([(200, 1144), (200, 1180)]),
        connector([(80, 1244), (40, 1244), (40, 1344), (116, 1344), (116, 1364)]),
        connector([(320, 1244), (360, 1244), (360, 1344), (284, 1344), (284, 1364)]),
        connector([(200, 1308), (376, 1308), (376, 1448), (284, 1448), (284, 1468)]),
        connector([(284, 1532), (284, 1564)]),
        connector([(360, 1596), (388, 1596), (388, 1156), (200, 1156), (200, 1180)], dashed=True),
        connector([(116, 1428), (116, 1468)]),
        connector([(56, 1428), (24, 1428), (24, 1596), (40, 1596)]),
        connector([(72, 1428), (8, 1428), (8, 1692), (40, 1692)]),
    ]
    labels = [
        connector_label(276, 140, "auditor confirms review", 156),
        connector_label(76, 668, "approve", 64),
        connector_label(324, 668, "reject", 56),
        connector_label(200, 796, "request changes", 116),
        connector_label(300, 288, "proposal can enter queue", 164),
        connector_label(76, 1332, "approve", 64),
        connector_label(324, 1332, "reject", 56),
        connector_label(320, 1448, "request changes", 116),
    ]
    nodes = [
        box(72, 52, 256, 64, ["PENDING_REVIEW"]),
        box(72, 148, 256, 64, ["REVIEWED"]),
        box(20, 224, 360, 48, ["Does not approve a relationship,", "MATE Assessment or conclusion"], note=True),
        box(100, 344, 200, 64, ["Proposed", "Relationship"]),
        box(100, 432, 200, 64, ["Relationship Version"]),
        diamond(200, 580, ["Auditor Decision"]),
        box(40, 700, 152, 64, ["Approved", "Relationship"]),
        box(208, 700, 152, 64, ["Rejected"]),
        box(100, 804, 200, 64, ["Changes Required"]),
        box(100, 900, 200, 64, ["New Relationship", "Version"]),
        box(40, 980, 320, 24, ["Approved records are never overwritten"], note=True),
        box(100, 1080, 200, 64, ["Conclusion Version"]),
        diamond(200, 1244, ["Auditor Decision"]),
        box(40, 1364, 152, 64, ["Approved", "Conclusion"]),
        box(208, 1364, 152, 64, ["Rejected"]),
        box(208, 1468, 152, 64, ["Changes Required"]),
        box(208, 1564, 152, 64, ["New Conclusion", "Version"]),
        box(40, 1468, 152, 64, ["Implementation", "Conclusion"]),
        box(40, 1564, 152, 64, ["Effectiveness", "Conclusion"]),
        box(40, 1660, 152, 64, ["Not Determined", "Conclusion"]),
    ]
    footer = (
        f'<text x="200" y="1872" text-anchor="middle" fill="{MUTED}" '
        f'font-family="{FONT}" font-size="14">ACE records each auditor decision.</text>'
    )
    svg = shell(
        "approval-review-states-presentation",
        "ACE Approval And Review States",
        "Separate state paths for Evidence Item review, Relationship approval and Conclusion approval.",
        400,
        1920,
        "".join(backgrounds + edges + labels + nodes) + footer,
    )
    return "approval-review-states", "ACE Approval And Review States", svg


def write_diagram(slug: str, title: str, svg: str) -> None:
    """Write editable HTML first, then extract the local SVG."""

    HTML_ROOT.mkdir(parents=True, exist_ok=True)
    SVG_ROOT.mkdir(parents=True, exist_ok=True)
    html = html_page(title, svg)
    html_path = HTML_ROOT / f"{slug}.html"
    html_path.write_text(html, encoding="utf-8")

    match = re.search(r"<svg\b[\s\S]*?</svg>", html)
    if not match:
        raise RuntimeError(f"No SVG found in {html_path}.")
    svg_path = SVG_ROOT / f"{slug}.svg"
    svg_path.write_text(match.group(0) + "\n", encoding="utf-8")


def main() -> None:
    """Build all approved presentation diagrams."""

    for slug, title, svg in (
        workflow_diagram(),
        evidence_relationship_diagram(),
        approval_state_diagram(),
    ):
        write_diagram(slug, title, svg)
        print(f"Built {slug}.html and {slug}.svg")


if __name__ == "__main__":
    main()
