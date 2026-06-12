"""
Generates BDS-SMC2_Field_Sheet.pdf — printable A4 sheets for the FINAL hardware day.
UPDATED 2026-06-12: Gap 3 is complete (232/232) — sheets now cover what remains:
  Sheet 1: Morning setup — portal tokens + 112-bit firmware flash checklist
  Sheet 2: Gap 2 MIDDAY session (30 TX)
  Sheet 3: 112-bit payload verification + power measurement
  Sheet 4: Gap 2 EVENING session (30 TX)
Run: python generate_field_sheet.py
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
BODY   = ParagraphStyle("BODY",   parent=styles["Normal"], fontSize=8.5, leading=12, spaceAfter=2)
SMALL  = ParagraphStyle("SMALL",  parent=styles["Normal"], fontSize=7.5, leading=10,
                         textColor=colors.grey, spaceAfter=1)
MONO   = ParagraphStyle("MONO",   parent=styles["Normal"], fontSize=7.5, leading=10,
                         fontName="Courier", spaceAfter=1)
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

def grid_table(rows, col_widths, header_bg="#2e5fa3", row_pad=10):
    style = [
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(header_bg)),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("FONTSIZE",      (0, 1), (-1,-1),  8),
        ("FONTNAME",      (0, 1), (-1,-1),  "Helvetica"),
        ("ROWBACKGROUNDS",(0, 1), (-1,-1),  [colors.HexColor("#f7f9fc"), colors.white]),
        ("GRID",          (0, 0), (-1,-1),  0.5, colors.HexColor("#c0ccd8")),
        ("VALIGN",        (0, 0), (-1,-1),  "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1,-1),  5),
        ("BOTTOMPADDING", (0, 0), (-1,-1),  row_pad),
        ("LEFTPADDING",   (0, 0), (-1,-1),  4),
    ]
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle(style))
    return t

def page_header(story, title_line):
    story += [
        Paragraph("BDS-SMC2 Final Hardware Day — Field Sheet", TITLE),
        Paragraph(title_line, SUB),
        rule(1.5, "#1a3a5c"),
        Spacer(1, 0.2*cm),
    ]

def footer(story):
    story.append(Spacer(1, 0.2*cm))
    story.append(rule())
    story.append(Paragraph(
        f"Generated: {datetime.date.today().strftime('%B %d, %Y')}  ·  BDS-SMC2 UAV Rescue System  ·  "
        "Dissertation Research — Letsoalo Maile, 2026",
        META))

story = []

# ── SHEET 1: Morning setup checklist ────────────────────────────────────────────
page_header(story, "Sheet 1 — Morning Setup: Portal Activation + 112-bit Firmware")

story.append(header_box([["Date", "Start time", "Location (same as Gap 2 baseline)", "Experimenter"],
                         ["", "", "", "Letsoalo Maile"]],
                        [3.5*cm, 3.0*cm, 6.5*cm, 4.7*cm]))
story.append(Spacer(1, 0.25*cm))

story.append(grid_table([
    ["[ ]", Paragraph("<b>A. Portal reader activation (at home, before leaving)</b>", BODY), "Done time"],
    ["[ ]", Paragraph("Log in at http://bdrd.hwasmart.com (RCSSTEAP_3058_SM_1 / 123456)", BODY), ""],
    ["[ ]", Paragraph("F12 &rarr; Application &rarr; Local Storage &rarr; copy <b>data</b>, <b>access_token</b>, <b>refresh_token</b>", BODY), ""],
    ["[ ]", Paragraph("Paste into python/portal_config.json", BODY), ""],
    ["[ ]", Paragraph("Run: python python/portal_reader.py --dump  (record real message field names below)", BODY), ""],
    ["[ ]", Paragraph("Start dashboard: python python/tx_dashboard.py &rarr; http://localhost:8765", BODY), ""],
], [0.9*cm, 13.3*cm, 2.5*cm], header_bg="#1a3a5c"))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph("Portal message field names seen in --dump output:", LABEL))
story.append(grid_table([["Field name", "Example value", "Maps to"]] + [["", "", ""]]*4,
                        [5*cm, 7*cm, 4.7*cm]))
story.append(Spacer(1, 0.25*cm))

story.append(grid_table([
    ["[ ]", Paragraph("<b>B. Firmware flash (112-bit payload)</b> — disconnect GPIO16/17 first, DIO mode, 40 MHz, hold BOOT + press RESET at 'Connecting...'", BODY), "Done"],
    ["[ ]", Paragraph("Flash esp32_sender.ino (MODE=1 binary; test coord = lab T001)", BODY), ""],
    ["[ ]", Paragraph("Reconnect GPIO16/17; power on; wait 2 minutes before first TX", BODY), ""],
    ["[ ]", Paragraph("Verify serial shows: [BINARY TX] $CCTXM,0,BIN:1D35DB5605079637007200A00101*..", BODY), ""],
], [0.9*cm, 13.3*cm, 2.5*cm], header_bg="#1a3a5c"))
footer(story)
story.append(PageBreak())

# ── SHEET 2: Gap 2 midday session ───────────────────────────────────────────────
def gap2_sheet(session_name, when_line, extras=None):
    page_header(story, f"Sheet — Gap 2 {session_name} Session · 30 TX · MODE 1 (112-bit binary) · {when_line}")
    story.append(header_box([["Session", "Start (HH:MM)", "Weather", "Cloud %", "Temp (opt.)"],
                             [session_name.lower(), "", "", "", ""]],
                            [3.2*cm, 3.2*cm, 4.2*cm, 3.0*cm, 4.1*cm]))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        f"Command:  .\\run_gap2_{session_name.lower()}.bat   (auto-stops at 30 TX). "
        "Power on ESP32 &rarr; wait 2 min &rarr; run bat &rarr; power off immediately after.", SMALL))
    story.append(Paragraph(
        "Option B: ALL sessions transmit the 112-bit binary payload (one flash, no mode "
        "switching). Logger fills gap2_latency.csv automatically — use this sheet only for anomalies.", SMALL))
    story.append(Spacer(1, 0.15*cm))
    rows = [["TX block", "All OK? (Y/N)", "Anomalies (TX#, what happened)"]]
    for blk in ["1–5", "6–10", "11–15", "16–20", "21–25", "26–30"]:
        rows.append([blk, "", ""])
    story.append(grid_table(rows, [2.5*cm, 2.8*cm, 11.4*cm], row_pad=16))
    story.append(Spacer(1, 0.25*cm))
    story.append(grid_table([
        ["Metric", "Value"],
        ["Successes / 30", ""],
        ["Timeouts", ""],
        ["Mean latency from logger (ms)", ""],
        ["Dashboard 'ground confirmed' count", ""],
    ], [8*cm, 8.7*cm], header_bg="#1a3a5c", row_pad=12))
    if extras:
        story.append(Spacer(1, 0.25*cm))
        for e in extras:
            story.append(e)
    footer(story)

# ── SHEET 2: Morning session — doubles as 112-bit hardware acceptance ──────────
morning_extras = [
    Paragraph("<b>112-bit acceptance check (first TX of this session IS the hardware verification):</b>", LABEL),
    grid_table([
        ["Check", "Result"],
        ["TX #1: module accepted 28-char hex (no $CCTXM error)?   [ ] yes  [ ] no", ""],
        ["TX #1: [T3] Send Success + green LED?                    [ ] yes  [ ] no", ""],
        ["TX #1 visible on portal (screenshot taken)?              [ ] yes  [ ] no", ""],
        ["CRITICAL — portal shows: [ ] packed binary (112 bits on-air)  [ ] ASCII hex text (224 bits)", ""],
        ["IF MODULE REJECTS: stop session — fallback firmware (R as uint8, 104 bits) needed first", ""],
    ], [13.2*cm, 3.5*cm], header_bg="#c0392b", row_pad=10),
]
gap2_sheet("Morning", "run 08:00–10:00", extras=morning_extras)
story.append(PageBreak())

# ── SHEET 3: Midday session + power measurement ────────────────────────────────
midday_extras = [
    Paragraph("Optional — power measurement (USB meter in supply line, during this session):", LABEL),
    grid_table([
        ["State", "Voltage (V)", "Current (mA)", "Duration (s)", "Notes"],
        ["Idle (module on, no TX)", "", "", "", ""],
        ["During TX burst", "", "", "", ""],
        ["Peak observed", "", "", "", ""],
    ], [5*cm, 2.6*cm, 2.8*cm, 2.6*cm, 3.7*cm], row_pad=12),
]
gap2_sheet("Midday", "run 12:00–14:00 — SAME DAY", extras=midday_extras)
story.append(PageBreak())

# ── SHEET 4: Evening session ────────────────────────────────────────────────────
gap2_sheet("Evening", "run AFTER 18:00 — SAME DAY")

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=1.8*cm, rightMargin=1.8*cm,
    topMargin=1.5*cm,  bottomMargin=1.5*cm,
    title="BDS-SMC2 Final Hardware Day Field Sheet",
    author="Letsoalo Maile",
)

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)
    canvas.drawString(1.8*cm, 0.8*cm, f"Sheet {doc.page}/4  ·  Final hardware day")
    canvas.drawRightString(W - 1.8*cm, 0.8*cm, "BDS-SMC2 Field Sheet (Rev. 2 — post Gap 3)")
    canvas.restoreState()

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"[DONE] Field sheet saved: {OUTPUT}  (4 sheets — setup, midday, 112-bit verify, evening)")
