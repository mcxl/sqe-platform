"""Write a reproducible manifest for ACE diagram sources and outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NAMES = (
    "auditor-workflow",
    "evidence-relationship-map",
    "approval-review-states",
)
CONTROLLED_ONLY_NAMES = ("superpowers-build-foundation",)


def digest(relative_path: str) -> str:
    """Return one file SHA-256 digest."""

    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def main() -> None:
    """Write the controlled two-layer manifest."""

    diagrams = []
    for name in NAMES:
        files = {
            "controlled_source": f"docs/diagrams/controlled/mermaid/{name}.mmd",
            "controlled_svg": f"docs/diagrams/controlled/svg/{name}.svg",
            "presentation_source": f"docs/diagrams/presentation/html/{name}.html",
            "presentation_svg": f"docs/diagrams/presentation/svg/{name}.svg",
            "fidelity_report": f"docs/diagrams/presentation/fidelity/{name}.md",
        }
        diagrams.append(
            {
                "name": name,
                "files": {
                    role: {"path": path, "sha256": digest(path)}
                    for role, path in files.items()
                },
            }
        )

    for name in CONTROLLED_ONLY_NAMES:
        files = {
            "controlled_source": f"docs/diagrams/controlled/mermaid/{name}.mmd",
            "controlled_svg": f"docs/diagrams/controlled/svg/{name}.svg",
        }
        diagrams.append(
            {
                "name": name,
                "files": {
                    role: {"path": path, "sha256": digest(path)}
                    for role, path in files.items()
                },
            }
        )

    manifest = {
        "authority": {
            "audit_records": "ACE",
            "controlled_diagram_source": "Mermaid .mmd",
            "presentation_role": "Auditor guidance only",
        },
        "tools": {
            "mermaid_cli": "11.16.0",
            "diagram_design_commit": "4da4dfb80b1f3d2f11678726b0db58c33c1d7e9d",
        },
        "diagrams": diagrams,
    }
    target = ROOT / "docs" / "diagrams" / "diagram-manifest.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
