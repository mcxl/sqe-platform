from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


SOURCE = Path(r"LOCAL_HOME\OneDrive - AuditCo\SQE\SQE-EOI-Review-260810-V2.docx")
OUTPUT = Path(r"LOCAL_HOME\OneDrive - AuditCo\SQE\SQE-EOI-Review-260810-V3.docx")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def paragraph_text(paragraph):
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


def find_middle_range(root):
    body = root.find("w:body", namespaces=NS)
    children = list(body)
    start = None
    end = None
    for index, child in enumerate(children):
        if child.tag != f"{{{W_NS}}}p":
            continue
        text = paragraph_text(child).strip()
        if text == "Rapid Five-Day Diagnostic and Elected Scope Engagements":
            start = index
            break
    if start is None:
        raise RuntimeError("Could not locate the V2 body start")
    for index in range(start + 1, len(children)):
        child = children[index]
        if child.tag == f"{{{W_NS}}}p" and child.xpath("./w:pPr/w:sectPr", namespaces=NS):
            end = index
            break
    if end is None:
        raise RuntimeError("Could not locate the V2 body end")
    return body, children, start, end


def apply_text_replacements(middle_children):
    replacements = {
        "This Expression of Interest sets out a staged service for Squadron Energy, starting with a rapid diagnostic and moving to separate, client-elected scope engagements.":
            "This Expression of Interest sets out a staged service for Squadron Energy, starting with a rapid diagnostic before any separate client-elected scope engagement.",
        "The fee model separates the rapid diagnostic from later scope work. The diagnostic has a fixed fee. Each elected scope engagement has its own fee, confirmed before activation.":
            "The fee model separates the rapid diagnostic from later scope work: the diagnostic has a fixed fee, while each elected scope engagement has its own fee confirmed before activation.",
    }
    changed = []
    for child in middle_children:
        if child.tag != f"{{{W_NS}}}p":
            continue
        full_text = paragraph_text(child)
        for old, new in replacements.items():
            if old not in full_text:
                continue
            text_nodes = child.xpath(".//w:t", namespaces=NS)
            if len(text_nodes) != 1:
                raise RuntimeError(f"Expected one text node for replacement: {old[:60]}")
            text_nodes[0].text = text_nodes[0].text.replace(old, new)
            changed.append(old[:60])
    if len(changed) != len(replacements):
        raise RuntimeError(f"Expected {len(replacements)} text replacements, applied {len(changed)}")


def normalise_table_font_sizes(middle_children):
    changed = 0
    for child in middle_children:
        for size_node in child.xpath(".//w:sz | .//w:szCs", namespaces=NS):
            if size_node.get(f"{{{W_NS}}}val") == "19":
                size_node.set(f"{{{W_NS}}}val", "20")
                changed += 1
    if changed == 0:
        raise RuntimeError("No 9.5-point table text was found to normalise")
    return changed


def table_header_text(table):
    first_row = table.find("w:tr", namespaces=NS)
    return " | ".join(
        "".join(cell.xpath(".//w:t/text()", namespaces=NS)).strip()
        for cell in first_row.xpath("./w:tc", namespaces=NS)
    )


def set_table_widths(table, widths):
    widths_twips = [str(int(width * 1440)) for width in widths]
    grid = table.find("w:tblGrid", namespaces=NS)
    if grid is None:
        raise RuntimeError("Target table has no grid")
    grid_columns = grid.findall("w:gridCol", namespaces=NS)
    if len(grid_columns) != len(widths_twips):
        raise RuntimeError("Target table grid does not match the requested widths")
    for column, width in zip(grid_columns, widths_twips):
        column.set(f"{{{W_NS}}}w", width)
    for row in table.findall("w:tr", namespaces=NS):
        cells = row.findall("w:tc", namespaces=NS)
        if len(cells) != len(widths_twips):
            raise RuntimeError("Target table contains an unexpected cell count")
        for cell, width in zip(cells, widths_twips):
            tc_pr = cell.find("w:tcPr", namespaces=NS)
            tc_w = tc_pr.find("w:tcW", namespaces=NS)
            if tc_w is None:
                raise RuntimeError("Target table cell has no width")
            tc_w.set(f"{{{W_NS}}}w", width)
            tc_w.set(f"{{{W_NS}}}type", "dxa")


def remove_page_break_before_heading(body, middle_children, heading_text):
    for index, child in enumerate(middle_children):
        if child.tag != f"{{{W_NS}}}p" or paragraph_text(child).strip() != heading_text:
            continue
        if index == 0:
            raise RuntimeError(f"No paragraph precedes {heading_text}")
        previous = middle_children[index - 1]
        has_page_break = bool(previous.xpath(".//w:br[@w:type='page']", namespaces=NS))
        if not has_page_break:
            raise RuntimeError(f"No page break precedes {heading_text}")
        body.remove(previous)
        return
    raise RuntimeError(f"Could not locate heading {heading_text}")


def insert_page_break_before_heading(body, middle_children, heading_text):
    for child in middle_children:
        if child.tag != f"{{{W_NS}}}p" or paragraph_text(child).strip() != heading_text:
            continue
        page_break_paragraph = etree.Element(f"{{{W_NS}}}p")
        run = etree.SubElement(page_break_paragraph, f"{{{W_NS}}}r")
        page_break = etree.SubElement(run, f"{{{W_NS}}}br")
        page_break.set(f"{{{W_NS}}}type", "page")
        child.addprevious(page_break_paragraph)
        return
    raise RuntimeError(f"Could not locate heading {heading_text}")


def patch_document(document_xml):
    root = etree.fromstring(document_xml)
    body, children, start, end = find_middle_range(root)
    middle_children = children[start:end]
    apply_text_replacements(middle_children)
    changed_sizes = normalise_table_font_sizes(middle_children)
    tables = [child for child in middle_children if child.tag == f"{{{W_NS}}}tbl"]
    diagnostic_table = next(table for table in tables if table_header_text(table).startswith("Day | Focus"))
    set_table_widths(diagnostic_table, [0.55, 1.15, 1.85, 1.35, 1.30])
    insert_page_break_before_heading(body, middle_children, "Diagnostic Outputs")
    remove_page_break_before_heading(body, middle_children, "6. Separate Scope Engagement Activation")
    remove_page_break_before_heading(body, middle_children, "7. Individual Scope Delivery Plans — Part 1")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), changed_sizes


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE, "r") as source_zip:
        parts = {info.filename: source_zip.read(info.filename) for info in source_zip.infolist()}
    parts["word/document.xml"], changed_sizes = patch_document(parts["word/document.xml"])
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as output_zip:
        for name, data in parts.items():
            output_zip.writestr(name, data)
    print(OUTPUT)
    print(f"TABLE_FONT_SIZE_CHANGES {changed_sizes}")


if __name__ == "__main__":
    main()
