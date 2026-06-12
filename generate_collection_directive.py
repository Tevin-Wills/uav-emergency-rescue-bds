"""
generate_collection_directive.py
Gap 2 Data Collection Directive — step-by-step field guide
Run: python generate_collection_directive.py
Output: BDS_SMC2_Collection_Directive.pdf
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUT = os.path.join(os.path.dirname(__file__), "BDS_SMC2_Collection_Directive.pdf")

C_BLUE   = colors.HexColor("#1a5276")
C_GREEN  = colors.HexColor("#1e8449")
C_RED    = colors.HexColor("#c0392b")
C_ORANGE = colors.HexColor("#d35400")
C_DARK   = colors.HexColor("#1a2533")
C_PALE   = colors.HexColor("#eaf2ff")
C_WARN   = colors.HexColor("#fef9e7")
C_OK     = colors.HexColor("#eafaf1")

def styles():
    B = "Helvetica-Bold"
    N = "Helvetica"
    return {
        "title":   ParagraphStyle("t",  fontName=B, fontSize=20, textColor=C_BLUE,  spaceAfter=4,  alignment=TA_CENTER),
        "sub":     ParagraphStyle("s",  fontName=N, fontSize=11, textColor=C_DARK,  spaceAfter=16, alignment=TA_CENTER),
        "h1":      ParagraphStyle("h1", fontName=B, fontSize=14, textColor=C_BLUE,  spaceBefore=14, spaceAfter=6),
        "h2":      ParagraphStyle("h2", fontName=B, fontSize=11, textColor=C_DARK,  spaceBefore=8,  spaceAfter=4),
        "body":    ParagraphStyle("b",  fontName=N, fontSize=10, textColor=C_DARK,  spaceAfter=5,  leading=15),
        "step":    ParagraphStyle("st", fontName=B, fontSize=10, textColor=C_BLUE,  spaceAfter=3,  leftIndent=10),
        "check":   ParagraphStyle("c",  fontName=N, fontSize=10, textColor=C_DARK,  spaceAfter=4,  leftIndent=20),
        "warn":    ParagraphStyle("w",  fontName=B, fontSize=10, textColor=C_RED,   spaceAfter=4,  leftIndent=10),
        "ok":      ParagraphStyle("ok", fontName=B, fontSize=10, textColor=C_GREEN, spaceAfter=4,  leftIndent=10),
        "code":    ParagraphStyle("cd", fontName="Courier", fontSize=10, textColor=C_DARK, spaceAfter=4, leftIndent=20, backColor=colors.HexColor("#f4f4f4")),
        "caption": ParagraphStyle("cp", fontName=N, fontSize=8,  textColor=colors.grey, spaceAfter=4, alignment=TA_CENTER),
    }

S = styles()

def hr(): return HRFlowable(width="100%", thickness=1.5, color=C_BLUE, spaceAfter=8, spaceBefore=4)
def sp(n=6): return Spacer(1, n)
def p(t, s="body"): return Paragraph(t, S[s])

def box(rows, col_widths, bg=C_PALE):
    style = [
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1),  9),
        ("BACKGROUND",   (0,0), (-1,0),  C_BLUE),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [bg, colors.white]),
        ("GRID",         (0,0), (-1,-1),  0.5, colors.HexColor("#cccccc")),
        ("LEFTPADDING",  (0,0), (-1,-1),  6),
        ("RIGHTPADDING", (0,0), (-1,-1),  6),
        ("TOPPADDING",   (0,0), (-1,-1),  4),
        ("BOTTOMPADDING",(0,0), (-1,-1),  4),
        ("VALIGN",       (0,0), (-1,-1),  "MIDDLE"),
    ]
    return Table(rows, colWidths=col_widths, style=TableStyle(style))

def warn_box(text):
    data = [[Paragraph(f"⚠  {text}", ParagraphStyle("wb", fontName="Helvetica-Bold", fontSize=10, textColor=C_RED))]]
    t = Table(data, colWidths=[16.6*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#fdecea")),
        ("BOX",        (0,0), (-1,-1), 1.5, C_RED),
        ("LEFTPADDING",(0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    return t

def ok_box(text):
    data = [[Paragraph(f"✓  {text}", ParagraphStyle("ob", fontName="Helvetica-Bold", fontSize=10, textColor=C_GREEN))]]
    t = Table(data, colWidths=[16.6*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#eafaf1")),
        ("BOX",        (0,0), (-1,-1), 1.5, C_GREEN),
        ("LEFTPADDING",(0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    return t

def info_box(text):
    data = [[Paragraph(f"ℹ  {text}", ParagraphStyle("ib", fontName="Helvetica", fontSize=10, textColor=C_BLUE))]]
    t = Table(data, colWidths=[16.6*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#eaf2ff")),
        ("BOX",        (0,0), (-1,-1), 1.5, C_BLUE),
        ("LEFTPADDING",(0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    return t

def numbered(n, text): return Paragraph(f"<b>{n}.</b>  {text}", S["body"])

def build():
    doc = SimpleDocTemplate(OUT, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2.2*cm, bottomMargin=2.2*cm)
    story = []

    # ── TITLE ──────────────────────────────────────────────
    story += [
        p("BDS-SMC2 DATA COLLECTION DIRECTIVE", "title"),
        p("Gap 2 — Latency Sessions · Field Operator Guide", "sub"),
        hr(),
        sp(4),
    ]

    # ── OVERVIEW ───────────────────────────────────────────
    story += [
        p("WHAT YOU ARE COLLECTING", "h1"),
        box([
            ["Session",   "When",              "Command",              "Duration"],
            ["Midday",    "Before 12:00 noon",  ".\\run_gap2_midday.bat",  "~5 minutes"],
            ["Evening",   "After 18:00",        ".\\run_gap2_evening.bat", "~5 minutes"],
        ], [3*cm, 4*cm, 5.5*cm, 3.5*cm]),
        sp(6),
        info_box("Both sessions collect exactly 30 transmissions then stop automatically. "
                 "You do NOT need to press Ctrl+C."),
        sp(6),
        warn_box("CRITICAL: Do NOT leave the ESP32 running for hours before a session. "
                 "Rate limiting will cause 0% delivery. Power on only when ready to run."),
        sp(10),
    ]

    # ── HARDWARE CHECKLIST ─────────────────────────────────
    story += [
        p("HARDWARE CHECKLIST — Check Before Every Session", "h1"),
        hr(),
        box([
            ["#", "Item",                                          "Check"],
            ["1", "ESP32 USB cable plugged into PC (COM14)",       "☐"],
            ["2", "DB9 RS232 cable connected: BDS module ↔ blue TTL board", "☐"],
            ["3", "Red wire (VCC) → 3.3V pin on ESP32",           "☐"],
            ["4", "Black wire (GND) → GND pin on ESP32",          "☐"],
            ["5", "Blue wire (RXD) → GPIO16 on ESP32",            "☐"],
            ["6", "Green wire (TXD) → GPIO17 on ESP32",           "☐"],
            ["7", "Green patch antenna pointing at open sky",      "☐"],
            ["8", "BDS module powered (UPS or power supply on)",   "☐"],
            ["9", "You are OUTDOORS in open sky area",             "☐"],
        ], [1*cm, 11.6*cm, 2.5*cm]),
        sp(10),
    ]

    # ── STEP BY STEP ───────────────────────────────────────
    story += [
        p("STEP-BY-STEP PROCEDURE", "h1"),
        hr(),
        sp(4),

        p("BEFORE YOU GO OUTSIDE", "h2"),
        numbered(1, "Open PowerShell or terminal on your PC."),
        numbered(2, "Navigate to project folder:"),
        p("cd C:\\Users\\OMEN\\OneDrive\\Desktop\\BDS-SMC2", "code"),
        numbered(3, "Confirm the correct bat file exists:"),
        p("ls run_gap2_midday.bat     (for midday session)", "code"),
        p("ls run_gap2_evening.bat    (for evening session)", "code"),
        sp(8),

        p("POWERING ON THE HARDWARE", "h2"),
        numbered(4, "Plug ESP32 USB cable into PC."),
        numbered(5, "Turn on the BDS module power supply (UPS or DC power)."),
        numbered(6, "WAIT 2 FULL MINUTES. The BDS module needs time to register with the satellite."),
        sp(4),
        warn_box("Do not skip the 2-minute wait. Running before the module registers "
                 "will result in all TIMEOUT rows and no valid latency data."),
        sp(8),

        p("OUTDOOR LOCATION", "h2"),
        numbered(7, "Go outside to an open area — no roof, no dense trees directly above."),
        numbered(8, "Point the green patch antenna towards the sky / equator direction (south)."),
        numbered(9, "Keep the antenna still during the session — do not hold it at an angle."),
        sp(4),
        info_box("You do not need to be far from the building — just have clear sky view above."),
        sp(8),

        p("RUNNING THE SESSION", "h2"),
        numbered(10, "In PowerShell, type the command for your session:"),
        p(".\\run_gap2_midday.bat       ← if it is before noon", "code"),
        p(".\\run_gap2_evening.bat      ← if it is after 6pm", "code"),
        numbered(11, "Press Enter and watch the output."),
        sp(6),

        p("WHAT YOU SHOULD SEE (Good output):", "h2"),
        p("[LOGGER] Session=midday  Weather=clear  Cloud=0%", "code"),
        p("[LOGGER] Appending from TX#31 -> ...gap2_latency.csv  Target=30 TX", "code"),
        p("  ---TX---", "code"),
        p("  [T1] 12345", "code"),
        p("  [ASCII TX] $CCTXM,0,LAT:30.4196,LON:120.2977*78", "code"),
        p("  [TX#] 31", "code"),
        p("  [T2] module-ack", "code"),
        p("  [T3] Send Success", "code"),
        p("  >> TX#31 latency=2450ms  (decode=0ms)", "code"),
        sp(4),
        ok_box("You should see latency values like '2450ms' or '3100ms' — this means "
               "the satellite is responding. Green LED on ESP32 flashes on each success."),
        sp(6),

        p("WHAT YOU SHOULD SEE (Problem output):", "h2"),
        p("  [TIMEOUT] TX#31 -- no satellite ACK before next TX", "code"),
        sp(4),
        warn_box("If you see only TIMEOUT rows with no latency values — STOP. "
                 "Press Ctrl+C. The module is not responding. Power off the ESP32, "
                 "wait 5 minutes, power on again, wait 2 more minutes, then retry."),
        sp(8),

        p("WHEN SESSION COMPLETES", "h2"),
        numbered(12, "The logger will print automatically:"),
        p("[LOGGER] Target of 30 TX reached. Done.", "code"),
        numbered(13, "IMMEDIATELY unplug the ESP32 USB cable after the session ends."),
        numbered(14, "Do NOT leave the ESP32 running between sessions."),
        sp(4),
        warn_box("Leaving ESP32 running for hours triggers satellite rate limiting — "
                 "the module stops responding and the next session will record all timeouts."),
        sp(8),

        p("VERIFYING YOUR DATA", "h2"),
        numbered(15, "Run the quick data check in PowerShell:"),
        p("python -c \"import csv; rows=list(csv.DictReader(open('data/gap2_latency.csv'))); "
          "from collections import Counter; s=Counter(r['session'] for r in rows); print(dict(s))\"", "code"),
        p("You should see the new session name appear with count=30.", "code"),
        sp(4),
        info_box("If the count is less than 30, some TX were lost. That is acceptable "
                 "as long as you have at least 20 rows with valid latency (not -1)."),
        PageBreak(),
    ]

    # ── TIMING PLAN ────────────────────────────────────────
    story += [
        p("SAME-DAY TIMING PLAN", "h1"),
        hr(),
        box([
            ["Time",         "Action",                                           "Duration"],
            ["Morning",      "Power on → wait 2 min → run_gap2_midday.bat → POWER OFF", "~7 min"],
            ["Gap",          "ESP32 must be OFF between sessions",               "min. 5 hrs"],
            ["After 18:00",  "Power on → wait 2 min → run_gap2_evening.bat → POWER OFF", "~7 min"],
            ["After session","Run: python python/gap2_analysis.py",              "~1 min"],
        ], [3.5*cm, 9*cm, 3*cm]),
        sp(8),
        info_box("The 5+ hour gap between sessions is what makes the ANOVA meaningful — "
                 "it tests whether time of day affects BDS-SMC latency. Do not run both "
                 "sessions within the same hour."),
        sp(10),
    ]

    # ── AFTER COLLECTION ───────────────────────────────────
    story += [
        p("AFTER BOTH SESSIONS — RUN ANALYSIS", "h1"),
        hr(),
        numbered(1, "Open PowerShell in the project folder."),
        numbered(2, "Run Gap 2 analysis:"),
        p("python python/gap2_analysis.py", "code"),
        numbered(3, "Run figure generation:"),
        p("python generate_figures.py", "code"),
        numbered(4, "Update the progress report:"),
        p("python generate_progress_report.py", "code"),
        sp(6),
        ok_box("After these 3 commands, all Gap 2 data is analysed, all figures are "
               "updated, and the progress report PDF is regenerated with full results."),
        sp(10),
    ]

    # ── QUICK REFERENCE ────────────────────────────────────
    story += [
        p("QUICK REFERENCE CARD", "h1"),
        hr(),
        box([
            ["Item",                  "Value"],
            ["Project folder",        "C:\\Users\\OMEN\\OneDrive\\Desktop\\BDS-SMC2"],
            ["Midday command",         ".\\run_gap2_midday.bat"],
            ["Evening command",        ".\\run_gap2_evening.bat"],
            ["Serial port",           "COM14"],
            ["TX per session",        "30 (auto-stops)"],
            ["Wait after power-on",   "2 minutes minimum"],
            ["Portal (receive side)", "bdrd.hwasmart.com"],
            ["Portal login",          "RCSSTEAP_3058_SM_1  /  123456"],
            ["GPIO RXD",              "GPIO16 (blue wire)"],
            ["GPIO TXD",              "GPIO17 (green wire)"],
            ["GPIO LED",              "GPIO27 (flashes green on success)"],
            ["BDS module baud",       "9600"],
            ["USB serial baud",       "115200"],
        ], [6*cm, 10*cm]),
        sp(10),
        hr(),
        p("BDS-SMC2 Node 5 · Letsoalo Maile · 2026", "caption"),
    ]

    doc.build(story)
    print(f"[DONE] Directive saved to: {OUT}")

if __name__ == "__main__":
    build()
