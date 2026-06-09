"""
generate_directive.py -- Generates BDS-SMC2_Directive.pdf
Run: python generate_directive.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

OUT = os.path.join(os.path.dirname(__file__), "BDS-SMC2_Directive.pdf")

# ── Colours ────────────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1a3a5c")
BLUE   = colors.HexColor("#2e5fa3")
GREEN  = colors.HexColor("#2d7a3a")
RED    = colors.HexColor("#c0392b")
GOLD   = colors.HexColor("#b07d1a")
LGRAY  = colors.HexColor("#f4f7fb")
DGRAY  = colors.HexColor("#555555")
WHITE  = colors.white

# ── Styles ─────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def style(name, **kw):
    return ParagraphStyle(name, **kw)

S_TITLE   = style("Title",   fontSize=22, textColor=NAVY,  alignment=TA_CENTER,
                  fontName="Helvetica-Bold", spaceAfter=4)
S_SUB     = style("Sub",     fontSize=11, textColor=BLUE,  alignment=TA_CENTER,
                  fontName="Helvetica", spaceAfter=2)
S_DATE    = style("Date",    fontSize=9,  textColor=DGRAY, alignment=TA_CENTER,
                  fontName="Helvetica", spaceAfter=16)
S_H1      = style("H1",      fontSize=13, textColor=WHITE, fontName="Helvetica-Bold",
                  spaceBefore=14, spaceAfter=4)
S_H2      = style("H2",      fontSize=11, textColor=NAVY,  fontName="Helvetica-Bold",
                  spaceBefore=10, spaceAfter=3)
S_BODY    = style("Body",    fontSize=9,  textColor=colors.black, fontName="Helvetica",
                  leading=14, spaceAfter=3)
S_CODE    = style("Code",    fontSize=8,  textColor=colors.HexColor("#222222"),
                  fontName="Courier", backColor=colors.HexColor("#f0f0f0"),
                  borderPadding=(3,6,3,6), leading=12, spaceAfter=2)
S_WARN    = style("Warn",    fontSize=9,  textColor=RED,   fontName="Helvetica-Bold",
                  spaceBefore=4, spaceAfter=4)
S_NOTE    = style("Note",    fontSize=8,  textColor=DGRAY, fontName="Helvetica-Oblique",
                  spaceAfter=2)

def h1(text, color=BLUE):
    bg = Table([[Paragraph(text, S_H1)]], colWidths=[17*cm])
    bg.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), color),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
    ]))
    return bg

def h2(text):
    return Paragraph(text, S_H2)

def body(text):
    return Paragraph(text, S_BODY)

def code(text):
    return Paragraph(text, S_CODE)

def note(text):
    return Paragraph(f"<i>{text}</i>", S_NOTE)

def warn(text):
    return Paragraph(f"&#9888;  {text}", S_WARN)

def sp(h=4):
    return Spacer(1, h)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=4)

def step_table(rows, col_widths=None):
    if col_widths is None:
        col_widths = [1.2*cm, 8.5*cm, 7.3*cm]
    data = [[Paragraph(f"<b>{c}</b>", S_NOTE) for c in ("Step", "Action", "Command / Note")]]
    for i, (action, cmd) in enumerate(rows, 1):
        data.append([
            Paragraph(f"<b>{i}</b>", style("Num", fontSize=9, fontName="Helvetica-Bold",
                                           alignment=TA_CENTER)),
            Paragraph(action, S_BODY),
            Paragraph(f'<font name="Courier" size="7.5">{cmd}</font>', S_BODY),
        ])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#dce6f1")),
        ("BACKGROUND",    (0,1), (-1,-1), LGRAY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [LGRAY, WHITE]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return t

def cmd_table(rows):
    data = [[Paragraph(f"<b>{c}</b>", S_NOTE) for c in ("Script", "When", "Command")]]
    for script, when, cmd in rows:
        data.append([
            Paragraph(f"<b>{script}</b>", S_BODY),
            Paragraph(when, S_BODY),
            Paragraph(f'<font name="Courier" size="7.5">{cmd}</font>', S_BODY),
        ])
    t = Table(data, colWidths=[3.5*cm, 3.5*cm, 10*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#dce6f1")),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [LGRAY, WHITE]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return t

# ── Build document ─────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
)

story = []

# ── Cover ──────────────────────────────────────────────────────────────────────
story += [
    sp(20),
    Paragraph("BDS-SMC2 UAV Rescue System", S_TITLE),
    Paragraph("Field Experiment Directive", S_SUB),
    Paragraph("Letsoalo Maile  |  GNSS &amp; Satellite Communication Dissertation", S_DATE),
    Paragraph("June 2026", S_DATE),
    sp(8),
    hr(),
    sp(6),
]

# ── Section 1: Overview ────────────────────────────────────────────────────────
story.append(h1("1.  Overview", NAVY))
story += [
    sp(6),
    body("This directive covers every task from today until the dissertation experiments are "
         "complete. Follow the steps in order. Do not skip sections."),
    sp(4),
]

overview = Table([
    [Paragraph("<b>Item</b>", S_NOTE), Paragraph("<b>Detail</b>", S_NOTE)],
    [body("Project"),       body("BeiDou-3 Short Message Communication for UAV Search &amp; Rescue")],
    [body("Student"),       body("Letsoalo Maile")],
    [body("Hardware"),      body("ESP32 Dev Board + BDS-3 RDSS Module (RS232-TTL)")],
    [body("Portal"),        body("http://bdrd.hwasmart.com/   Login: RCSSTEAP_3058_SM_1 / 123456")],
    [body("Hardware days"), body("5 days")],
    [body("Total timeline"),body("2 weeks")],
    [body("Research gaps"), body("Gap 1 (encoding), Gap 2 (latency), Gap 3 (environments), "
                                 "Gap 6 (telemetry)")],
], colWidths=[4*cm, 13*cm])
overview.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#dce6f1")),
    ("ROWBACKGROUNDS",(0,1), (-1,-1), [LGRAY, WHITE]),
    ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
    ("TOPPADDING",    (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ("VALIGN",        (0,0), (-1,-1), "TOP"),
]))
story += [overview, sp(8)]

# ── Section 2: Before Hardware ─────────────────────────────────────────────────
story.append(h1("2.  Before Hardware  (PC — Do This Now)", GREEN))
story += [sp(6), h2("2.1  Install Missing Library")]
story.append(step_table([
    ("Open terminal in project folder", "cd C:\\Users\\OMEN\\OneDrive\\Desktop\\BDS-SMC2"),
    ("Install scipy for statistical p-values", "pip install scipy"),
    ("Verify all scripts run", "python python/gap2_analysis.py --demo"),
]))
story += [sp(8), h2("2.2  Scout Your 12 Field Locations")]
story += [
    body("Walk to each location <b>before</b> hardware day. Take a photo and note the GPS "
         "coordinates on your phone. Confirm access."),
    sp(4),
]

loc_table = Table([
    [Paragraph("<b>Environment</b>", S_NOTE),
     Paragraph("<b>Locations needed</b>", S_NOTE),
     Paragraph("<b>What to look for</b>", S_NOTE)],
    [body("Open sky"),     body("OS-1, OS-2, OS-3"), body("Wide open, no obstruction above")],
    [body("Light canopy"), body("LC-1, LC-2, LC-3"), body("Trees overhead, sky still visible")],
    [body("Urban canyon"), body("UC-1, UC-2, UC-3"), body("Tall buildings either side, narrow sky")],
    [body("Indoor"),       body("IN-1, IN-2, IN-3"), body("Ground floor window / no window / upper floor")],
], colWidths=[3.5*cm, 4.5*cm, 9*cm])
loc_table.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#dce6f1")),
    ("ROWBACKGROUNDS",(0,1), (-1,-1), [LGRAY, WHITE]),
    ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
    ("TOPPADDING",    (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING",   (0,0), (-1,-1), 6),
]))
story += [loc_table, sp(4)]
story.append(warn("Do NOT arrive at a hardware day without pre-scouted locations. "
                  "You will lose 2 hours and miss a session."))

# ── Section 3: Hardware Day 1 ──────────────────────────────────────────────────
story += [sp(6), h1("3.  Hardware Day 1 — INDOOR Setup + Encoding Gaps", BLUE)]
story += [sp(6), note("Location: Lab / indoors.  Duration: Full day.")]
story.append(step_table([
    ("Wire ESP32 to BDS module",
     "RXD→GPIO16, TXD→GPIO17, VCC→3.3V, GND→GND, LED→GPIO27"),
    ("Open BDS portal in browser",
     "http://bdrd.hwasmart.com/  →  Login: RCSSTEAP_3058_SM_1 / 123456"),
    ("Upload firmware MODE=0 (ASCII)",
     "Arduino IDE → esp32_sender.ino → set MODE=0 → Upload"),
    ("Proof of life: wait for first TX on portal",
     "Portal must show incoming message. If not, debug wiring."),
    ("Run Gap 2 Session A — Morning",
     "python python/serial_logger.py --port COM3 --session morning --weather clear"),
    ("Wait for 34 transmissions then Ctrl+C", "~6 minutes at 10s intervals"),
    ("Switch to MODE=1 (Binary), upload, run 10 TX",
     "Arduino IDE → MODE=1 → Upload → confirm 10 TX on portal"),
    ("Switch to MODE=2 (Huffman), upload, run 10 TX",
     "Arduino IDE → MODE=2 → Upload → confirm 10 TX on portal"),
    ("Push all data to GitHub",
     "git add data/   git commit -m 'day1: indoor + gap2 session A'   git push"),
]))
story.append(warn("If proof of life fails: check RS232-TTL adapter orientation, "
                  "re-seat all jumpers, confirm portal login before blaming firmware."))

# ── Section 4: Hardware Day 2 ──────────────────────────────────────────────────
story += [sp(6), h1("4.  Hardware Day 2 — OUTDOOR  Open Sky", BLUE)]
story += [sp(6), note("Location: Pre-scouted open sky spots.  Duration: Full day.")]
story.append(step_table([
    ("Go to OS-1, start logger",
     "python python/field_test_logger.py --env open_sky --location OS-1 --gps \"LAT,LON\" --weather clear --n 20"),
    ("Wait for 20 TX, Ctrl+C", "~5 mins TX + setup. Note actual GPS from phone."),
    ("Move to OS-2, repeat", "--location OS-2  (same command, change location)"),
    ("Move to OS-3, repeat", "--location OS-3"),
    ("Run Gap 2 Session B — Midday",
     "python python/serial_logger.py --port COM3 --session midday --weather clear"),
    ("Wait for 33 TX then Ctrl+C", "~6 minutes"),
    ("Push data immediately — do not wait until end of day",
     "git add data/   git commit -m 'day2: open sky OS-1/2/3 + gap2 midday'   git push"),
]))

# ── Section 5: Hardware Day 3 ──────────────────────────────────────────────────
story += [sp(6), h1("5.  Hardware Day 3 — OUTDOOR  Light Canopy", BLUE)]
story += [sp(6), note("Location: Pre-scouted canopy spots.  Duration: Full day.")]
story.append(step_table([
    ("Go to LC-1, start logger",
     "python python/field_test_logger.py --env light_canopy --location LC-1 --gps \"LAT,LON\" --obstruction 20 --n 20"),
    ("Wait for 20 TX, Ctrl+C", "Note sky obstruction estimate (0-100%)."),
    ("Move to LC-2, repeat", "--location LC-2"),
    ("Move to LC-3, repeat", "--location LC-3"),
    ("Push data",
     "git add data/   git commit -m 'day3: light canopy LC-1/2/3'   git push"),
]))

# ── Section 6: Hardware Day 4 ──────────────────────────────────────────────────
story += [sp(6), h1("6.  Hardware Day 4 — OUTDOOR  Urban Canyon", BLUE)]
story += [sp(6), note("Location: Pre-scouted urban canyon spots.  Duration: Full day.")]
story.append(step_table([
    ("Go to UC-1, start logger",
     "python python/field_test_logger.py --env urban_canyon --location UC-1 --gps \"LAT,LON\" --obstruction 60 --n 20"),
    ("Wait for 20 TX, Ctrl+C", ""),
    ("Move to UC-2, repeat", "--location UC-2"),
    ("Move to UC-3, repeat", "--location UC-3"),
    ("Run Gap 2 Session C — Evening",
     "python python/serial_logger.py --port COM3 --session evening --weather clear"),
    ("Wait for 33 TX then Ctrl+C", "~6 minutes"),
    ("Push all data",
     "git add data/   git commit -m 'day4: urban canyon UC-1/2/3 + gap2 evening'   git push"),
]))

# ── Section 7: Hardware Day 5 ──────────────────────────────────────────────────
story += [sp(6), h1("7.  Hardware Day 5 — INDOOR  Environments", BLUE)]
story += [sp(6), note("Location: Pre-scouted indoor spots.  Duration: Half day.")]
story.append(step_table([
    ("Go to IN-1 (ground floor, near window)",
     "python python/field_test_logger.py --env indoor --location IN-1 --obstruction 90 --n 20"),
    ("Wait for 20 TX, Ctrl+C", ""),
    ("Move to IN-2 (ground floor, no window)", "--location IN-2  --obstruction 100"),
    ("Move to IN-3 (upper floor)", "--location IN-3  --obstruction 80"),
    ("Final push — all experiments complete",
     "git add data/   git commit -m 'day5: all indoor complete'   git push"),
]))
story.append(warn("After Day 5 all hardware work is done. Do not run more TX. "
                  "Move to analysis immediately."))

# ── Section 8: After Hardware ──────────────────────────────────────────────────
story += [sp(6), h1("8.  After All Hardware Days — Analysis (PC Only)", GREEN)]
story += [sp(6),
    body("Run these three commands in order. Each prints results to the console "
         "and saves figures/CSV files automatically."),
    sp(4),
]
story.append(step_table([
    ("Run Gap 2 latency analysis (ANOVA + UAV error model)",
     "python python/gap2_analysis.py"),
    ("Run Gap 3 environmental analysis (chi-square + Fisher's exact + Bonferroni)",
     "python python/gap3_analysis.py"),
    ("Regenerate all 6 figures including Gap 3 bar chart",
     "python generate_figures.py"),
    ("Check figures/ folder — all PNG files are paper-ready at 150 DPI",
     "figures/ folder in project root"),
    ("Numbers from console output go directly into your paper tables",
     "Copy mean, std, CI, p-values into Lab7_Report.md"),
], col_widths=[0.6*cm, 10.5*cm, 5.9*cm]))

# ── Section 9: Quick Reference ─────────────────────────────────────────────────
story += [sp(6), h1("9.  Quick Command Reference", NAVY)]
story += [sp(6)]
story.append(cmd_table([
    ("serial_logger",      "Gap 2 TX session",
     "python python/serial_logger.py --port COM3 --session morning --weather clear"),
    ("field_test_logger",  "Gap 3 field TX",
     "python python/field_test_logger.py --env open_sky --location OS-1 --gps \"30.4196,120.2977\" --n 20"),
    ("gap2_analysis",      "After hardware",
     "python python/gap2_analysis.py"),
    ("gap3_analysis",      "After hardware",
     "python python/gap3_analysis.py"),
    ("generate_figures",   "After analysis",
     "python generate_figures.py"),
    ("git push",           "After every location",
     "git add data/   &&   git commit -m 'message'   &&   git push"),
    ("field summary",      "Check progress",
     "python python/field_test_logger.py --summary"),
]))

# ── Section 10: Risk Mitigation ────────────────────────────────────────────────
story += [sp(6), h1("10.  Risk Mitigation", colors.HexColor("#8B0000"))]
story += [sp(6)]

risk_data = [
    [Paragraph("<b>Risk</b>", S_NOTE),
     Paragraph("<b>If it happens</b>", S_NOTE),
     Paragraph("<b>Recovery</b>", S_NOTE)],
    [body("Hardware doesn't work Day 1"),
     body("Give full Day 1 to debugging"),
     body("Reduce Gap 3 to 20 TX x 4 environments (original plan). Still publishable.")],
    [body("Rain on outdoor day"),
     body("Reschedule that environment to next available day"),
     body("Indoor environments can fill a rain day")],
    [body("Portal login fails"),
     body("Log in the night before each hardware day"),
     body("Use User 2: RCSSTEAP_3058_SM_2 / 123456")],
    [body("Laptop crashes mid-session"),
     body("Push CSV after every location — not end of day"),
     body("Data already on GitHub. Re-run only that location.")],
    [body("Location inaccessible"),
     body("Scout day before. Have a backup spot within 5 mins walk"),
     body("GPS within 200m of original is acceptable")],
]
risk_tbl = Table(risk_data, colWidths=[4*cm, 5*cm, 8*cm])
risk_tbl.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#f5c6c6")),
    ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.HexColor("#fff5f5"), WHITE]),
    ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
    ("TOPPADDING",    (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ("VALIGN",        (0,0), (-1,-1), "TOP"),
]))
story += [risk_tbl, sp(10), hr()]

story.append(Paragraph(
    "BDS-SMC2 Field Experiment Directive  |  Letsoalo Maile  |  June 2026",
    style("Footer", fontSize=8, textColor=DGRAY, alignment=TA_CENTER)
))

# ── Build PDF ──────────────────────────────────────────────────────────────────
doc.build(story)
print(f"[SAVED] {OUT}")
