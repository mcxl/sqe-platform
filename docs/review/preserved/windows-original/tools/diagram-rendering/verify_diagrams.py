"""Verify ACE diagram privacy, accessibility and controlled fidelity."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
CONTROLLED_ROOT = ROOT / "docs" / "diagrams" / "controlled"
PRESENTATION_ROOT = ROOT / "docs" / "diagrams" / "presentation"
NAMES = (
    "auditor-workflow",
    "evidence-relationship-map",
    "approval-review-states",
)
FORBIDDEN = (
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "@import url",
    "<script",
    "neo4j",
    "semantica",
    "langgraph",
)


def controlled_content(source: str) -> tuple[Counter[str], Counter[str], int]:
    """Extract controlled labels, edge labels and relationship count."""

    labels: Counter[str] = Counter()
    for match in re.finditer(
        r"(?:subgraph\s+\w+|\b\w+)\s*(?:\[\"([^\"]+)\"\]|\{\"([^\"]+)\"\})",
        source,
    ):
        labels[match.group(1) or match.group(2)] += 1

    edge_labels = Counter(re.findall(r'\|\"([^\"]+)\"\|', source))
    relationship_count = sum(
        1
        for line in source.splitlines()
        if re.search(r"(?:-->|-\.->)", line) and not line.lstrip().startswith("%%")
    )
    return labels, edge_labels, relationship_count


def verify_svg(name: str) -> None:
    """Compare one presentation SVG with its controlled Mermaid source."""

    source_path = CONTROLLED_ROOT / "mermaid" / f"{name}.mmd"
    svg_path = PRESENTATION_ROOT / "svg" / f"{name}.svg"
    html_path = PRESENTATION_ROOT / "html" / f"{name}.html"
    controlled_svg_path = CONTROLLED_ROOT / "svg" / f"{name}.svg"

    for path in (source_path, svg_path, html_path, controlled_svg_path):
        if not path.is_file():
            raise AssertionError(f"Missing required diagram file: {path}")

    source = source_path.read_text(encoding="utf-8")
    controlled_labels, controlled_edge_labels, controlled_edge_count = controlled_content(source)

    tree = ET.parse(svg_path)
    root = tree.getroot()
    namespace = "{http://www.w3.org/2000/svg}"
    children = list(root)
    if not children or children[0].tag != f"{namespace}title":
        raise AssertionError(f"{name}: SVG title is not the first child.")
    if root.attrib.get("role") != "img" or not root.attrib.get("aria-labelledby"):
        raise AssertionError(f"{name}: SVG accessibility attributes are missing.")
    if root.find(f"{namespace}desc") is None:
        raise AssertionError(f"{name}: SVG description is missing.")

    presentation_labels = Counter(
        element.attrib["data-controlled-label"]
        for element in root.iter()
        if "data-controlled-label" in element.attrib
    )
    presentation_edge_labels = Counter(
        element.attrib["data-controlled-edge-label"]
        for element in root.iter()
        if "data-controlled-edge-label" in element.attrib
    )
    presentation_edge_count = sum(
        1 for element in root.iter() if element.attrib.get("data-controlled-edge") == "true"
    )

    if presentation_labels != controlled_labels:
        raise AssertionError(
            f"{name}: controlled labels differ. Source={controlled_labels}; presentation={presentation_labels}"
        )
    if presentation_edge_labels != controlled_edge_labels:
        raise AssertionError(
            f"{name}: controlled edge labels differ. Source={controlled_edge_labels}; presentation={presentation_edge_labels}"
        )
    if presentation_edge_count != controlled_edge_count:
        raise AssertionError(
            f"{name}: relationship count differs. Source={controlled_edge_count}; presentation={presentation_edge_count}"
        )

    for path in (source_path, svg_path, html_path, controlled_svg_path):
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN:
            if forbidden in text:
                raise AssertionError(f"{path}: forbidden content found: {forbidden}")

    html = html_path.read_text(encoding="utf-8")
    if "Arial, Helvetica, sans-serif" not in html:
        raise AssertionError(f"{name}: local system font stack is missing.")
    if "<foreignobject" in svg_path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{name}: presentation SVG contains foreignObject markup.")

    print(f"{name}: privacy, accessibility and fidelity PASS")


def main() -> None:
    """Verify every approved diagram."""

    for name in NAMES:
        verify_svg(name)


if __name__ == "__main__":
    main()
