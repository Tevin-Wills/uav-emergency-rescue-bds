"""
Generates BDS-SMC2_Field_Sheet.pdf — printable A4 data collection sheet for Gap 3.
One sheet covers 1 environment × 1 location × 20 transmissions.
Run: python generate_field_sheet.py
Output: BDS-SMC2_Field_Sheet.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import datetime

OUTPUT = "BDS-SMC2_Field_Sheet.pdf"
W, H = A4

styles = getSampleStyleSheet()
TITLE  = ParagraphStyle("TITLE",  parent=styles["Title"],  fontSize=15, leading=18,
                         textColor=colors.HexColor("#1a3a5c"), alignment=TA_CENTER, spaceAfter=4)
SUB    = ParagraphStyle("SUB",    parent=styles["Normal"], fontSize=9,  leading=12,
                         textColor=colors.HexColor("#4a6fa5"), alignment=TA_CENTER, spaceAfter=2)
LABEL  = ParagraphStyle("LABEL",  parent=styles["Normal"], fontSize=9,  leading=12,
                         textColor=colors.HexColor("#1a3a5c"), spaceAfter=2)
SMALL  = ParagraphStyle("SMALL",  parent=styles["Normal"], fontSize=7.5, leading=10,
                         textColor=colors.grey, spaceAfter=1)
META   = ParagraphStyle("META",   parent=styles["Normal"], fontSize=7.5, leading=10,
                         textColor=colors.grey, alignment=TA_CENTER)

def rule(thick=0.5, color="#c0ccd8"):
    return HRFlowable(width="100%", thickness=thick, color=colors.HexColor(color), spaceAfter=6)

def header_box(data, col_widths):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 8),
        ("FONTSIZE",     (0, 1), (-1,-1), 8),
        ("FONTNAME",     (0, 1), (-1,-1), "Helvetica"),
        ("BACKGROUND",   (0, 1), (-1,-1), colors.HexColor("#eef2f7")),
        ("GRID",         (0, 0), (-1,-1), 0.5, colors.HexColor("#c0ccd8")),
        ("VALIGN",       (0, 0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1,-1), 5),
        ("BOTTOMPADDING",(0, 0), (-1,-1), 18),
        ("LEFTPADDING",  (0, 0), (-1,-1), 6),
    ]))
    return t

def tx_table():
    header = ["TX #", "Time\n(HH:MM:SS)", "Result\n(✓/✗/T)", "Latency\n(sec)", "LED\n(G/–)", "Notes / Errors"]
    rows = [header]
    for i in range(1, 21):
        rows.append([str(i), "", "", "", "", ""])
    t = Table(rows, colWidths=[1.1*cm, 2.8*cm, 2.2*cm, 2.4*cm, 1.8*cm, 7.4*cm])
    style = [
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#2e5fa3")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("FONTSIZE",      (0, 1), (-1,-1),  8),
        ("FONTNAME",      (0, 1), (-1,-1),  "Helvetica"),
        ("ROWBACKGROUNDS",(0, 1), (-1,-1),  [colors.HexColor("#f7f9fc"), colors.white]),
        ("GRID",          (0, 0), (-1,-1),  0.5, colors.HexColor("#c0ccd8")),
        ("VALIGN",        (0, 0), (-1,-1),  "MIDDLE"),
        ("ALIGN",         (0, 0), (4, -1),  "CENTER"),
        ("TOPPADDING",    (0, 0), (-1,-1),  5),
        ("BOTTOMPADDING", (0, 0), (-1,-1),  10),
        ("LEFTPADDING",   (0, 0), (-1,-1),  4),
    ]
    # shade every 5 rows slightly darker for readability
    for row in [5, 10, 15, 20]:
        style.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor("#dce6f0")))
    t.setStyle(TableStyle(style))
    return t

def summary_table():
    rows = [
        ["Metric", "Value"],
        ["Total TX", "20"],
        ["Successes (✓)", ""],
        ["Failures (✗)", ""],
        ["Timeouts (T)", ""],
        ["Success rate (%)", ""],
        ["Mean latency (sec)", ""],
        ["Min / Max latency", "  /  "],
    ]
    t = Table(rows, colWidths=[5.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1,-1), 8),
        ("FONTNAME",     (0, 1), (-1,-1), "Helvetica"),
        ("BACKGROUND",   (0, 1), (-1,-1), colors.HexColor("#eef2f7")),
        ("GRID",         (0, 0), (-1,-1), 0.5, colors.HexColor("#c0ccd8")),
        ("VALIGN",       (0, 0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1,-1), 5),
        ("BOTTOMPADDING",(0, 0), (-1,-1), 12),
        ("LEFTPADDING",  (0, 0), (-1,-1), 6),
    ]))
    return t

def make_page(env_label, story):
    story += [
        Paragraph("BDS-SMC2 Field Data Collection Sheet", TITLE),
        Paragraph("Gap 3 — Environmental Signal Reception  ·  4 Environments × 3 Locations × 20 TX", SUB),
        rule(1.5, "#1a3a5c"),
        Spacer(1, 0.2*cm),
    ]

    # Session info block
    info = [
        ["Environment", "Location ID", "Date", "Experimenter"],
        [env_label, "", "", "Letsoalo Maile"],
    ]
    story.append(header_box(info, [4.5*cm, 3.0*cm, 4.5*cm, 5.7*cm]))
    story.append(Spacer(1, 0.2*cm))

    coords = [
        ["GPS Lat", "GPS Lon", "Weather", "Cloud % (0-100)", "Antenna Direction", "Sky Obstruction %"],
        ["", "", "", "", "North", ""],
    ]
    story.append(header_box(coords, [2.8*cm, 2.8*cm, 2.8*cm, 3.0*cm, 3.3*cm, 3.0*cm]))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("Firmware Mode: 0 (ASCII)   ·   BDS portal: http://bdrd.hwasmart.com/   ·   Login: RCSSTEAP_3058_SM_1 / 123456", SMALL))
    story.append(Paragraph("Result codes: ✓ = Send Success (green LED)   ✗ = Failed/Error   T = 30s Timeout", SMALL))
    story.append(Spacer(1, 0.15*cm))

    # TX log table
    story.append(tx_table())
    story.append(Spacer(1, 0.3*cm))

    # Summary + notes side-by-side
    notes_data = [
        [summary_table(),
         Table([
             [Paragraph("<b>Field Notes / Observations</b>", LABEL)],
             [""],
             [""],
             [""],
             [""],
             [""],
         ], colWidths=[8.9*cm],
         style=TableStyle([
             ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a3a5c")),
             ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
             ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
             ("FONTSIZE",   (0,0), (-1,-1), 8),
             ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
             ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#eef2f7")),
             ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#c0ccd8")),
             ("TOPPADDING", (0,0), (-1,-1), 5),
             ("BOTTOMPADDING",(0,0),(-1,-1), 18),
             ("LEFTPADDING", (0,0),(-1,-1), 6),
         ]))
        ]
    ]
    notes_tbl = Table(notes_data, colWidths=[8.9*cm, 8.9*cm])
    notes_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(notes_tbl)
    story.append(Spacer(1, 0.2*cm))
    story.append(rule())
    story.append(Paragraph(
        f"Generated: {datetime.date.today().strftime('%B %d, %Y')}  ·  BDS-SMC2 UAV Rescue System  ·  "
        "Dissertation Research — Letsoalo Maile, 2026",
        META))

environments = [
    "Open Sky (OS)",
    "Light Canopy (LC)",
    "Urban Canyon (UC)",
    "Indoor (IN)",
]

# Each environment gets 3 location pages (3 locations × 20 TX)
location_labels = ["Location 1", "Location 2", "Location 3"]

story = []
page_count = 0
for env in environments:
    for loc in location_labels:
        if page_count > 0:
            story.append(PageBreak())
        env_label = f"{env} — {loc}"
        make_page(env_label, story)
        page_count += 1

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=1.8*cm, rightMargin=1.8*cm,
    topMargin=1.5*cm,  bottomMargin=1.5*cm,
    title="BDS-SMC2 Field Data Collection Sheet",
    author="Letsoalo Maile",
)

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)
    env_idx = (doc.page - 1) // 3 + 1
    loc_idx = (doc.page - 1) % 3 + 1
    canvas.drawString(1.8*cm, 0.8*cm, f"Sheet {doc.page}/12  ·  Environment {env_idx}/4  ·  Location {loc_idx}/3")
    canvas.drawRightString(W - 1.8*cm, 0.8*cm, "BDS-SMC2 Gap 3 Field Data Sheet")
    canvas.restoreState()

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"[DONE] Field data sheet saved: {OUTPUT}  ({page_count} pages — 4 envs × 3 locations)")
