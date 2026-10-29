from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


HERE = Path(__file__).resolve().parent
CHRONOS = HERE.parents[1]
MANUSCRIPT = HERE / "stochastic-process-manuscript.md"
OUTPUT = HERE / "How-Polymarket-Probabilities-Move.docx"
FIGURE_DIR = HERE / "figures"
AUDIT = CHRONOS / "studies/polymarket-paper-acceptance-audit-2026-08-24/paper-acceptance-receipt.json"
PROCESS = CHRONOS / (
    "studies/polymarket-stochastic-process-paper-2026-08-18/"
    "development-receipts/01_fresh_process_signatures.json"
)
LATER_LAW = CHRONOS / (
    "studies/polymarket-stochastic-process-paper-2026-08-18/"
    "successor-corpus/development-receipts/13_frozen_process_successor_replay.json"
)
LATER_ARRIVAL = CHRONOS / (
    "studies/polymarket-stochastic-process-paper-2026-08-18/"
    "successor-corpus/development-receipts/17_frozen_arrival_hazard_successor_replay.json"
)
REVERSAL = CHRONOS / (
    "studies/polymarket-fresh-reversal-replication-2026-08-17/"
    "resource-retry-receipts/01_fresh_reversal_replication.json"
)

AUDIT_ID = "paper-audit-report:e8ed21a7f08e0e35c8277138515f0cad1cf0d84f0fe6fca438aa380f0fa2d910"
FONT_SERIF = "Liberation Serif"
FONT_SANS = "Liberation Sans"
INK = RGBColor(24, 31, 42)
NAVY = RGBColor(27, 55, 79)
BLUE = RGBColor(47, 99, 135)
MUTED = RGBColor(92, 101, 111)
LIGHT = "E8EEF2"
LIGHTER = "F5F7F8"
WHITE = "FFFFFF"
TABLE_WIDTH_DXA = 9360
TABLE_INDENT_DXA = 100


def _read_details(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())["details"]


def verify_evidence() -> None:
    audit = json.loads(AUDIT.read_text())
    assert audit["report_id"] == AUDIT_ID
    assert audit["decision"] == "accept"
    assert len(audit["trials"]) == 90
    assert audit["unique_analysis_count"] == 48
    assert audit["duplicate_execution_count"] == 42
    assert all(claim["passed"] for claim in audit["claims"])
    assert not [
        check
        for claim in audit["claims"]
        for check in claim["checks"]
        if not check["passed"]
    ]

    process = _read_details(PROCESS)
    assert process["observation_count"] == 803862
    assert process["market_count"] == 562
    assert process["event_count"] == 157
    assert math.isclose(process["regular_interior_zero_rate"], 0.6239800947413752)

    law = _read_details(LATER_LAW)
    assert law["sample_count"] == 17671
    assert law["event_count"] == 29
    assert law["full_hurdle_vs_state"]["event_count"] == 27
    assert math.isclose(law["state_hurdle"]["event_macro_mean_nll"], 3.116050059340227)
    assert math.isclose(law["full_hurdle_vs_state"]["event_macro_mean_nll"], 2.8703496562712845)
    assert law["full_hurdle_vs_state"]["event_wins_vs_comparator"] == 27

    arrival = _read_details(LATER_ARRIVAL)
    assert arrival["sample_count"] == 17671
    assert arrival["state_plus_staleness_logistic"]["event_count"] == 27
    assert math.isclose(arrival["state_logistic"]["event_macro_brier"], 0.26106340393802135)
    assert math.isclose(
        arrival["state_plus_staleness_logistic"]["event_macro_brier"],
        0.1739238992828049,
    )
    assert arrival["state_plus_staleness_logistic"]["event_wins_vs_comparator"] == 27

    reversal = _read_details(REVERSAL)
    assert reversal["oof_row_count"] == 6174
    assert reversal["oof_market_count"] == 410
    assert reversal["oof_event_count"] == 128
    assert reversal["state_shock_logistic"]["event_wins_vs_comparator"] == 87
    assert math.isclose(reversal["rate_baseline"]["event_macro_brier"], 0.25221710707820455)
    assert math.isclose(reversal["state_shock_logistic"]["event_macro_brier"], 0.23901967124210044)


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    bold_candidates = (
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    )
    for candidate in bold_candidates if bold else candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def build_process_figure() -> Path:
    width, height = 1680, 530
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(34, bold=True)
    label_font = _font(27)
    small_font = _font(23)
    draw.text((55, 28), "Four features of contract movement", fill=(27, 55, 79), font=title_font)
    draw.text((55, 75), "Dots are averages across events; bars are 95% intervals", fill=(92, 101, 111), font=small_font)

    rows = (
        ("Hours with no change", 43.81, 38.71, 49.52, 20.0, "higher"),
        ("Direction reversals", 58.45, 55.53, 61.41, 50.0, "higher"),
        ("Move rate after a long quiet run", 7.36, 5.23, 9.65, 50.0, "lower"),
        ("24-hour variance / independent case", 32.40, 24.97, 40.43, 75.0, "lower"),
    )
    x0, x1 = 610, 1570
    for tick in range(0, 81, 10):
        x = x0 + (x1 - x0) * tick / 80
        draw.line((x, 120, x, 455), fill=(228, 232, 235), width=2)
        draw.text((x - 12, 466), str(tick), fill=(92, 101, 111), font=small_font)
    draw.text((1545, 494), "%", fill=(92, 101, 111), font=small_font)

    for index, (label, estimate, lower, upper, threshold, direction) in enumerate(rows):
        y = 155 + index * 82
        draw.text((55, y - 18), label, fill=(24, 31, 42), font=label_font)
        tx = x0 + (x1 - x0) * threshold / 80
        color = (164, 92, 44) if direction == "higher" else (130, 76, 118)
        draw.line((tx, y - 30, tx, y + 30), fill=color, width=5)
        lx = x0 + (x1 - x0) * lower / 80
        ux = x0 + (x1 - x0) * upper / 80
        ex = x0 + (x1 - x0) * estimate / 80
        draw.line((lx, y, ux, y), fill=(47, 99, 135), width=10)
        draw.ellipse((ex - 12, y - 12, ex + 12, y + 12), fill=(27, 55, 79))
        draw.text((ex + 18, y - 18), f"{estimate:.2f}", fill=(24, 31, 42), font=small_font)

    path = FIGURE_DIR / "process_signatures.png"
    image.save(path, dpi=(220, 220))
    return path


def build_score_figure() -> Path:
    width, height = 1680, 610
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(34, bold=True)
    label_font = _font(25)
    small_font = _font(22)
    draw.text((55, 25), "Which stochastic model fits the later probability paths?", fill=(27, 55, 79), font=title_font)
    draw.text((55, 72), "Average negative log likelihood across events; lower is better", fill=(92, 101, 111), font=small_font)

    def bars(
        left: int,
        top: int,
        chart_width: int,
        title: str,
        values: tuple[tuple[str, float], ...],
        maximum: float,
    ) -> None:
        draw.text((left, top), title, fill=(24, 31, 42), font=label_font)
        for idx, (name, value) in enumerate(values):
            y = top + 68 + idx * 79
            draw.text((left, y), name, fill=(24, 31, 42), font=small_font)
            bar_y = y + 31
            bar_width = int(chart_width * value / maximum)
            color = (47, 99, 135) if idx == len(values) - 1 else (170, 183, 193)
            draw.rounded_rectangle(
                (left, bar_y, left + bar_width, bar_y + 25), radius=7, fill=color
            )
            draw.text((left + bar_width + 10, bar_y - 4), f"{value:.3f}", fill=(24, 31, 42), font=small_font)

    bars(
        55,
        135,
        1180,
        "Distribution of the next hourly change",
        (
            ("Smooth Gaussian change", 4.582),
            ("No-change / direction / size, without context", 3.240),
            ("Current probability and time remaining", 3.116),
            ("Current probability, time, and recent history", 2.870),
        ),
        5.0,
    )
    path = FIGURE_DIR / "model_scores.png"
    image.save(path, dpi=(220, 220))
    return path


def _set_run_font(run, *, name: str, size: float, color: RGBColor = INK, bold: bool = False, italic: bool = False) -> None:
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.bold = bold
    run.italic = italic


def _shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def _set_cell_margins(cell, *, top: int = 60, start: int = 100, bottom: int = 60, end: int = 100) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _set_table_geometry(table, widths: list[int]) -> None:
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    tbl_w.set(qn("w:w"), str(sum(widths)))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.first_child_found_in("w:tblInd")
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(TABLE_INDENT_DXA))
    tbl_ind.set(qn("w:type"), "dxa")

    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        grid_col = OxmlElement("w:gridCol")
        grid_col.set(qn("w:w"), str(width))
        grid.append(grid_col)

    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)
        for index, cell in enumerate(row.cells):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.first_child_found_in("w:tcW")
            tc_w.set(qn("w:w"), str(widths[index]))
            tc_w.set(qn("w:type"), "dxa")
            cell.width = Inches(widths[index] / 1440)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            _set_cell_margins(cell)


def _table_widths(headers: list[str]) -> list[int]:
    if headers[0] == "Evidence set":
        return [1700, 3900, 3760]
    if headers[0] == "Measure":
        return [2450, 1200, 1700, 1450, 1350, 1210]
    if headers[0] == "Feature":
        return [1700, 3900, 3760]
    if headers[0] == "Model":
        return [2250, 1400, 1200, 4510]
    equal = TABLE_WIDTH_DXA // len(headers)
    widths = [equal for _ in headers]
    widths[-1] += TABLE_WIDTH_DXA - sum(widths)
    return widths


def add_table(document: Document, rows: list[list[str]]) -> None:
    table = document.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    widths = _table_widths(rows[0])
    _set_table_geometry(table, widths)
    header_properties = table.rows[0]._tr.get_or_add_trPr()
    table_header = OxmlElement("w:tblHeader")
    table_header.set(qn("w:val"), "true")
    header_properties.append(table_header)
    for row_index, values in enumerate(rows):
        for column_index, value in enumerate(values):
            cell = table.cell(row_index, column_index)
            cell.text = ""
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.paragraph_format.keep_with_next = row_index < len(rows) - 1
            if column_index > 0 and rows[0][0] in {"Measure", "Model"} and row_index > 0:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.add_run(value)
            _set_run_font(
                run,
                name=FONT_SANS,
                size=6.85 if len(rows[0]) >= 6 else 7.2,
                color=INK,
                bold=row_index == 0,
            )
            if row_index == 0:
                _shade(cell, LIGHT)
            elif row_index % 2 == 0:
                _shade(cell, LIGHTER)
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)


def _add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Page ")
    _set_run_font(run, name=FONT_SANS, size=7.5, color=MUTED)
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend((fld_char1, instr, fld_char2))


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.82)
    section.bottom_margin = Inches(0.82)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.header_distance = Inches(0.35)
    section.footer_distance = Inches(0.35)

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = FONT_SERIF
    normal._element.rPr.rFonts.set(qn("w:ascii"), FONT_SERIF)
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), FONT_SERIF)
    normal.font.size = Pt(10.0)
    normal.font.color.rgb = INK
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(4.5)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    normal.paragraph_format.line_spacing = 1.08

    for style_name, size, before, after in (
        ("Heading 1", 14.0, 9, 4),
        ("Heading 2", 11.8, 6, 3),
        ("Heading 3", 10.2, 4, 2),
    ):
        style = styles[style_name]
        style.font.name = FONT_SANS
        style._element.rPr.rFonts.set(qn("w:ascii"), FONT_SANS)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), FONT_SANS)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = NAVY
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.keep_together = True

    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    hp.paragraph_format.space_after = Pt(0)
    run = hp.add_run("POLYMARKET PROBABILITY PROCESS   |   CHRONOS RESEARCH PROJECT")
    _set_run_font(run, name=FONT_SANS, size=7.1, color=MUTED, bold=True)

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.paragraph_format.space_before = Pt(0)
    _add_page_number(fp)

    core = document.core_properties
    core.title = "How Polymarket Probabilities Move"
    core.subject = "Stasis, bursts, reversal, and variance growth in Polymarket probability histories"
    core.author = "Chronos Research Project"
    core.keywords = "Polymarket, probability, stochastic process, volatility, reversal"


def add_title_block(document: Document, lines: list[str], start: int) -> int:
    title = document.add_paragraph()
    title.paragraph_format.space_before = Pt(8)
    title.paragraph_format.space_after = Pt(2)
    run = title.add_run(lines[start][2:])
    _set_run_font(run, name=FONT_SANS, size=24, color=NAVY, bold=True)

    subtitle = document.add_paragraph()
    subtitle.paragraph_format.space_before = Pt(0)
    subtitle.paragraph_format.space_after = Pt(5)
    run = subtitle.add_run(lines[start + 2][3:])
    _set_run_font(run, name=FONT_SERIF, size=12.4, color=BLUE, italic=True)

    meta = document.add_paragraph()
    meta.paragraph_format.space_before = Pt(0)
    meta.paragraph_format.space_after = Pt(7)
    run = meta.add_run(lines[start + 4])
    _set_run_font(run, name=FONT_SANS, size=8.2, color=MUTED)
    return start + 6


def _add_paragraph(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.widow_control = True
    paragraph.paragraph_format.keep_together = False
    paragraph.paragraph_format.keep_with_next = text.startswith("Table ")
    if text.startswith("Table "):
        paragraph.paragraph_format.space_before = Pt(3)
        paragraph.paragraph_format.space_after = Pt(2)
    run = paragraph.add_run(text)
    if text.startswith("Table "):
        _set_run_font(run, name=FONT_SANS, size=8.2, color=MUTED, italic=True)
    else:
        _set_run_font(run, name=FONT_SERIF, size=10.0, color=INK)


def build_document() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    build_process_figure()
    build_score_figure()

    document = Document()
    configure_document(document)
    lines = MANUSCRIPT.read_text().splitlines()
    index = add_title_block(document, lines, 0)
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            _add_paragraph(document, " ".join(line.strip() for line in paragraph_lines))
            paragraph_lines = []

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped == "<!-- PAGE BREAK -->":
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("[[FIGURE:"):
            flush_paragraph()
            filename = stripped.removeprefix("[[FIGURE:").removesuffix("]]" )
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_before = Pt(2)
            paragraph.paragraph_format.space_after = Pt(1)
            run = paragraph.add_run()
            run.add_picture(str(FIGURE_DIR / filename), width=Inches(6.35))
            alt_text = {
                "process_signatures.png": (
                    "Four event-average process tests with 95 percent intervals: "
                    "exact-zero share, sign reversal, long-quiet to active move-rate ratio, "
                    "and the 24-hour variance ratio."
                ),
                "model_scores.png": (
                    "Later-cohort benchmark scores for the full next-change distribution "
                    "and for whether the next stored probability changes. Lower scores are better."
                ),
            }[filename]
            drawing_properties = run._r.xpath(".//wp:docPr")[0]
            drawing_properties.set("title", filename.removesuffix(".png").replace("_", " ").title())
            drawing_properties.set("descr", alt_text)
            index += 1
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(set(cell) <= {"-", ":"} for cell in cells):
                    rows.append(cells)
                index += 1
            add_table(document, rows)
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            paragraph = document.add_paragraph(style="Heading 2")
            paragraph.add_run(stripped[4:])
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            paragraph = document.add_paragraph(style="Heading 1")
            paragraph.add_run(stripped[3:])
            index += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            index += 1
            continue
        paragraph_lines.append(stripped)
        index += 1

    flush_paragraph()
    document.save(OUTPUT)


def main() -> None:
    verify_evidence()
    build_document()
    print(OUTPUT)


if __name__ == "__main__":
    main()
