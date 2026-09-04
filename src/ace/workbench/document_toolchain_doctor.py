"""document-toolchain-doctor — Probe the document toolchain before rendering.

Usage:
    python -m src.ace.workbench.document_toolchain_doctor -Probe

Exits 0 if all tools are available, non-zero otherwise.
Prints a probe report to stdout.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProbeResult:
    tool: str
    available: bool
    version: str = ""
    notes: str = ""


@dataclass
class DoctorReport:
    results: list[ProbeResult] = field(default_factory=list)

    @property
    def all_available(self) -> bool:
        return all(r.available for r in self.results)

    def print(self) -> None:
        print("document-toolchain-doctor -Probe")
        print("=" * 60)
        for r in self.results:
            status = "OK" if r.available else "MISSING"
            version_info = f" ({r.version})" if r.version else ""
            notes = f" — {r.notes}" if r.notes else ""
            print(f"  [{status}] {r.tool}{version_info}{notes}")
        print("=" * 60)
        if self.all_available:
            print("All tools available — ready for DOCX → PDF rendering.")
        else:
            print("Some tools are missing — PDF rendering may be unavailable.")


def _probe_libreoffice() -> ProbeResult:
    candidates = ("libreoffice", "soffice.com") if sys.platform == "win32" else ("libreoffice",)
    path = next((shutil.which(candidate) for candidate in candidates if shutil.which(candidate)), None)
    if path is None:
        return ProbeResult(tool="LibreOffice", available=False, notes="not found on PATH")
    try:
        result = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=10
        )
        version = result.stdout.strip() if result.returncode == 0 else ""
        return ProbeResult(
            tool="LibreOffice",
            available=result.returncode == 0,
            version=version,
        )
    except Exception as exc:
        return ProbeResult(tool="LibreOffice", available=False, notes=str(exc))


def _probe_python_docx() -> ProbeResult:
    try:
        import docx  # noqa: F401

        import importlib.metadata

        version = importlib.metadata.version("python-docx")
        return ProbeResult(tool="python-docx", available=True, version=version)
    except ImportError:
        return ProbeResult(tool="python-docx", available=False, notes="not installed")


def _probe_reportlab() -> ProbeResult:
    try:
        import reportlab  # noqa: F401

        import importlib.metadata

        version = importlib.metadata.version("reportlab")
        return ProbeResult(tool="reportlab", available=True, version=version)
    except ImportError:
        return ProbeResult(tool="reportlab", available=False, notes="not installed")


def probe() -> DoctorReport:
    """Run all toolchain probes and return a report."""
    return DoctorReport(
        results=[
            _probe_libreoffice(),
            _probe_python_docx(),
            _probe_reportlab(),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv
    if "-Probe" not in argv:
        print("Usage: document-toolchain-doctor -Probe", file=sys.stderr)
        return 2
    report = probe()
    report.print()
    return 0 if report.all_available else 1


if __name__ == "__main__":
    sys.exit(main())
