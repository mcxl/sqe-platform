"""Build a print-friendly PDF from the car listening playbook."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "podcast" / "ACE_MATE_Car_Listening_Playbook_Print.md"
OUTPUT = ROOT / "output" / "pdf" / "ACE_MATE_Car_Listening_Playbook.pdf"


def clean_markdown(text: str) -> str:
    text = text.replace("`", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    return escape(text)


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "PlaybookTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=27,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    heading = ParagraphStyle(
        "PlaybookHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceBefore=5,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "PlaybookBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        spaceAfter=7,
    )
    bullet = ParagraphStyle(
        "PlaybookBullet",
        parent=body,
        leftIndent=12,
        firstLineIndent=-8,
    )

    story = []
    sections = SOURCE.read_text(encoding="utf-8").split("\n---\n")
    for section_index, section in enumerate(sections):
        for raw_line in section.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("# "):
                story.append(Paragraph(clean_markdown(line[2:]), title))
            elif line.startswith("## "):
                story.append(Paragraph(clean_markdown(line[3:]), heading))
            elif line.startswith("### "):
                story.append(Paragraph(clean_markdown(line[4:]), heading))
            elif line.startswith("- "):
                story.append(Paragraph(f"- {clean_markdown(line[2:])}", bullet))
            else:
                story.append(Paragraph(clean_markdown(line), body))
        if section_index < len(sections) - 1:
            story.append(PageBreak())

    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="ACE And MATE Car Listening Playbook",
        author="AuditCo",
    )
    document.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
