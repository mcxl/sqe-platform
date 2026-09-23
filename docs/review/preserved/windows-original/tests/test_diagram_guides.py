from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = (
    "auditor-workflow",
    "evidence-relationship-map",
    "approval-review-states",
)
CONTROLLED_ONLY_DIAGRAMS = ("superpowers-build-foundation",)


def test_progress_guide_uses_presentation_diagrams_and_controlled_links() -> None:
    guide = (ROOT / "ACE_PROGRESS_GUIDE.html").read_text(encoding="utf-8")

    assert "ACE records remain the source of truth" in guide
    assert "Pretty Mermaid" not in guide
    for name in DIAGRAMS:
        presentation = f"docs/diagrams/presentation/svg/{name}.svg"
        controlled = f"docs/diagrams/controlled/mermaid/{name}.mmd"
        fidelity = f"docs/diagrams/presentation/fidelity/{name}.md"
        assert presentation in guide
        assert controlled in guide
        assert fidelity in guide
        assert (ROOT / presentation).is_file()
        assert (ROOT / controlled).is_file()
        assert (ROOT / fidelity).is_file()

    for name in CONTROLLED_ONLY_DIAGRAMS:
        controlled_svg = f"docs/diagrams/controlled/svg/{name}.svg"
        controlled_source = f"docs/diagrams/controlled/mermaid/{name}.mmd"
        assert controlled_svg in guide
        assert controlled_source in guide
        assert (ROOT / controlled_svg).is_file()
        assert (ROOT / controlled_source).is_file()


def test_diagram_manifest_has_current_hashes_and_pinned_tools() -> None:
    manifest = json.loads(
        (ROOT / "docs/diagrams/diagram-manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["authority"]["audit_records"] == "ACE"
    assert manifest["authority"]["controlled_diagram_source"] == "Mermaid .mmd"
    assert manifest["tools"]["mermaid_cli"] == "11.16.0"
    assert (
        manifest["tools"]["diagram_design_commit"]
        == "4da4dfb80b1f3d2f11678726b0db58c33c1d7e9d"
    )

    for diagram in manifest["diagrams"]:
        for item in diagram["files"].values():
            path = ROOT / item["path"]
            assert path.is_file()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_diagram_outputs_have_no_external_font_or_script_connections() -> None:
    forbidden = ("fonts.googleapis.com", "fonts.gstatic.com", "@import url", "<script")
    paths = list((ROOT / "docs/diagrams/controlled/svg").glob("*.svg"))
    paths += list((ROOT / "docs/diagrams/presentation/svg").glob("*.svg"))
    paths += list((ROOT / "docs/diagrams/presentation/html").glob("*.html"))

    assert len(paths) == 10
    for path in paths:
        content = path.read_text(encoding="utf-8").lower()
        for blocked in forbidden:
            assert blocked not in content, f"{blocked} found in {path}"
