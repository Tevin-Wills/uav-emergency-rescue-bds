"""
Generates a Gap Analysis Table PDF for BDS-SMC2 — 6 columns.
Run: python generate_gap_table.py
Output: BDS_SMC2_Gap_Table.pdf
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import datetime

OUTPUT = "BDS_SMC2_Gap_Table.pdf"
W, H = landscape(A4)

TITLE = ParagraphStyle("TITLE", fontName="Helvetica-Bold", fontSize=15,
                        leading=19, spaceAfter=3, textColor=colors.HexColor("#1a3a5c"),
                        alignment=TA_CENTER)
SUB   = ParagraphStyle("SUB",   fontName="Helvetica", fontSize=8.5,
                        leading=11, spaceAfter=2, textColor=colors.HexColor("#4a6fa5"),
                        alignment=TA_CENTER)
META  = ParagraphStyle("META",  fontName="Helvetica", fontSize=7.5,
                        leading=10, textColor=colors.grey, alignment=TA_CENTER)
HEAD  = ParagraphStyle("HEAD",  fontName="Helvetica-Bold", fontSize=8.5,
                        leading=11, textColor=colors.white, alignment=TA_CENTER)
NUM   = ParagraphStyle("NUM",   fontName="Helvetica-Bold", fontSize=11,
                        leading=13, textColor=colors.white, alignment=TA_CENTER)
GAP   = ParagraphStyle("GAP",   fontName="Helvetica-Bold", fontSize=8,
                        leading=11, textColor=colors.HexColor("#1a3a5c"), alignment=TA_LEFT)
PROB  = ParagraphStyle("PROB",  fontName="Helvetica", fontSize=7.8,
                        leading=11, textColor=colors.HexColor("#3d3d3d"), alignment=TA_JUSTIFY)
SOL   = ParagraphStyle("SOL",   fontName="Helvetica", fontSize=7.8,
                        leading=11, textColor=colors.HexColor("#1a3d1a"), alignment=TA_JUSTIFY)
METH  = ParagraphStyle("METH",  fontName="Helvetica", fontSize=7.8,
                        leading=11, textColor=colors.HexColor("#3d1a00"), alignment=TA_JUSTIFY)
HYPO  = ParagraphStyle("HYPO",  fontName="Helvetica", fontSize=7.8,
                        leading=11, textColor=colors.HexColor("#1a1a5c"), alignment=TA_JUSTIFY)

DARK_BLUE  = colors.HexColor("#1a3a5c")
LIGHT_BLUE = colors.HexColor("#dce8f5")
LIGHT_RED  = colors.HexColor("#fff3f3")
LIGHT_GRN  = colors.HexColor("#f0fff0")
LIGHT_ORG  = colors.HexColor("#fff8f0")
LIGHT_PRP  = colors.HexColor("#f5f0ff")
ALT_RED    = colors.HexColor("#fff7f7")
ALT_GRN    = colors.HexColor("#f5fff5")
ALT_ORG    = colors.HexColor("#fffcf5")
ALT_PRP    = colors.HexColor("#faf5ff")

def p(text, style):
    return Paragraph(text, style)

COL_W = [0.7*cm, 3.0*cm, 4.8*cm, 4.3*cm, 5.5*cm, 7.4*cm]

# ── Gap content ───────────────────────────────────────────────────────────────
g1_meth = (
    "<b>Method:</b> Comparative encoding experiment. "
    "Transmit the same coordinate in MODE 0 (ASCII), MODE 1 (Binary), and "
    "MODE 2 (Huffman). Record bit count per mode from Serial Monitor.<br/><br/>"
    "<b>Why chosen:</b> Direct hardware measurement is more rigorous than "
    "theoretical estimation. Allows real compression ratio on live BDS-3 hardware."
)
g1_hypo = (
    "<b>Proves:</b> Binary fixed-point encoding reduces BDS-3 coordinate payload "
    "by &ge;60% vs ASCII — making full telemetry feasible inside GSMC's 560-bit "
    "global limit in a single message.<br/><br/>"
    "<b>Refutes:</b> The assumption that ASCII is sufficient for BDS-3 SMC when "
    "global GSMC coverage is required."
)

g2_meth = (
    "<b>Method:</b> Repeated timestamped logging (n=30, 10 s intervals). "
    "[T1] marked by ESP32 firmware; [T2] recorded by serial_logger.py. "
    "Statistics: mean, std dev, min, max for TX latency and total latency.<br/><br/>"
    "<b>Why chosen:</b> 30 samples satisfies CLT for mean estimation. "
    "Timestamps at both ends eliminate clock ambiguity."
)
g2_hypo = (
    "<b>Proves:</b> First empirical end-to-end latency characterisation of the "
    "BDS-3 SMC chain. Determines whether the ~1–2 s round-trip supports "
    "UAV waypoint updates to a moving survivor.<br/><br/>"
    "<b>Refutes:</b> The assumption that BDS-3 total latency is known from "
    "individual link studies alone."
)

g3_meth = (
    "<b>Method:</b> Controlled repeated-measures field experiment. "
    "field_test_logger.py auto-detects [TX#] markers and logs success/fail/"
    "latency per attempt. Success rate computed with 95% confidence interval.<br/><br/>"
    "<b>Why chosen:</b> 20 samples per environment gives meaningful CIs. "
    "4 environments span real rescue scenarios. Repetition isolates environment "
    "as the independent variable."
)
g3_hypo = (
    "<b>Proves:</b> Whether environment significantly affects BDS-3 RSMC "
    "success rate and by how much. Provides the first empirical BDS-3 SMC "
    "acquisition dataset in terrain-obstructed rescue scenarios.<br/><br/>"
    "<b>Refutes:</b> The gap from Springer (2023): that RDSS uplink success "
    "rate in obstructed terrain is unknown and unstudied."
)

g6_meth = (
    "<b>Method:</b> Multi-format empirical comparison. Same 7-field telemetry "
    "struct (lat, lon, alt, battery, mode, flags, timestamp) encoded in ASCII, "
    "Binary, and Huffman. Bit counts measured and GSMC fit assessed "
    "against the 560-bit hard limit in Python.<br/><br/>"
    "<b>Why chosen:</b> Running all formats on identical data eliminates "
    "confounds. Python implementation mirrors ESP32 firmware — results are "
    "directly comparable to hardware measurements."
)
g6_hypo = (
    "<b>Proves:</b> Which encoding scheme best balances data density, GSMC "
    "compatibility, and complexity for full UAV rescue telemetry. Provides "
    "evidence-based encoding selection guidance — the exact contribution "
    "the 2022–2024 BDS compression literature recommended.<br/><br/>"
    "<b>Refutes:</b> The implicit assumption that ASCII is adequate for "
    "multi-field BDS-3 SMC telemetry under global GSMC constraints."
)

rows = [
    [p("#", HEAD), p("Research Gap", HEAD), p("Why It Is a Problem", HEAD),
     p("Proposed Solution", HEAD), p("Method Used &amp; Why Chosen", HEAD),
     p("What It Proves / Refutes", HEAD)],

    [p("1", NUM),
     p("No standardised coordinate encoding scheme for BDS-3 SMC payloads", GAP),
     p("ASCII encoding uses ~152–208 bits for data needing only 64 bits — a 69% "
       "waste. For GSMC (global, 560-bit limit), a full telemetry struct in ASCII "
       "exceeds the single-message limit, forcing fragmentation with no native "
       "reassembly guarantee in the BDS protocol.", PROB),
     p("Implement three modes on ESP32: MODE 0 (ASCII baseline), MODE 1 (Binary "
       "64-bit fixed-point), MODE 2 (Dynamic Huffman ~48 bits). Python decoders "
       "verify each format independently.", SOL),
     p(g1_meth, METH),
     p(g1_hypo, HYPO)],

    [p("2", NUM),
     p("End-to-end latency of the BDS-SMC &rarr; software &rarr; UAV chain is uncharacterised", GAP),
     p("No study has measured the full chain: ESP32 &rarr; BDS module &rarr; GEO "
       "satellite &rarr; GCC &rarr; web platform &rarr; UAV GCS. Without this "
       "budget it is impossible to assess if BDS-3 SMC is fast enough to guide "
       "a UAV to a moving survivor (drift &gt;0.5 m/s).", PROB),
     p("Instrument the full chain: [T1] ESP32 firmware marker at send; [T2] PC "
       "arrival via serial_logger.py; [T3] web platform receipt. Run 30 "
       "transmissions and compute mean, std dev, min, max latency.", SOL),
     p(g2_meth, METH),
     p(g2_hypo, HYPO)],

    [p("3", NUM),
     p("No empirical RDSS transmission success-rate study across rescue environments", GAP),
     p("RSMC requires clear line-of-sight to GEO satellites (elevation ~38–52° "
       "from Hangzhou). In forests, urban canyons, or indoors — common accident "
       "environments — signal acquisition is intermittent. The probability of "
       "a successful BDS-3 SMC cycle in obstructed terrain is empirically unknown.", PROB),
     p("Structured field test: 4 environments (open sky, light canopy, urban "
       "canyon, indoor) x 20 transmissions each = 80 total. Log success, fail, "
       "and latency per attempt. Compute success rate with 95% CI.", SOL),
     p(g3_meth, METH),
     p(g3_hypo, HYPO)],

    [p("4", NUM),
     p("No comparative framework for telemetry encoding schemes across BDS-3 SMC payloads", GAP),
     p("UAV rescue telemetry requires multiple fields (lat, lon, alt, battery, "
       "mode, flags, timestamp) in one message. No published work compares ASCII, "
       "binary struct, and Huffman variants for this payload — leaving "
       "protocol designers with no empirical encoding selection guidance.", PROB),
     p("Implement all 3 formats for a 7-field struct in telemetry_compare.py. "
       "Measure bytes, bits, compression ratio vs ASCII, and GSMC single-message "
       "compatibility for each. Output gap6_telemetry.csv.", SOL),
     p(g6_meth, METH),
     p(g6_hypo, HYPO)],
]

style_cmds = [
    ("BACKGROUND",    (0,0), (-1,0), DARK_BLUE),
    ("LINEBELOW",     (0,0), (-1,0), 2.0, DARK_BLUE),
    ("VALIGN",        (0,0), (-1,0), "MIDDLE"),
    ("TOPPADDING",    (0,0), (-1,0), 8),
    ("BOTTOMPADDING", (0,0), (-1,0), 8),
    ("BACKGROUND",    (0,1), (0,-1), DARK_BLUE),
    ("VALIGN",        (0,1), (0,-1), "MIDDLE"),
    ("BACKGROUND",    (1,1), (1,-1), LIGHT_BLUE),
    ("VALIGN",        (1,1), (-1,-1), "TOP"),
    ("TOPPADDING",    (1,1), (-1,-1), 6),
    ("BOTTOMPADDING", (1,1), (-1,-1), 6),
    ("LEFTPADDING",   (0,1), (-1,-1), 6),
    ("RIGHTPADDING",  (0,1), (-1,-1), 6),
    ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#b0c4d8")),
]

for i in range(1, 5):
    style_cmds += [
        ("BACKGROUND", (2,i), (2,i), LIGHT_RED if i%2==1 else ALT_RED),
        ("BACKGROUND", (3,i), (3,i), LIGHT_GRN if i%2==1 else ALT_GRN),
        ("BACKGROUND", (4,i), (4,i), LIGHT_ORG if i%2==1 else ALT_ORG),
        ("BACKGROUND", (5,i), (5,i), LIGHT_PRP if i%2==1 else ALT_PRP),
    ]

table = Table(rows, colWidths=COL_W, repeatRows=1)
table.setStyle(TableStyle(style_cmds))

story = [
    Paragraph("BeiDou Short Message Communication — Gap Analysis", TITLE),
    Paragraph("Research Gaps  |  Problem Statement  |  Proposed Solution  |  Method Used &amp; Why  |  What It Proves / Refutes", SUB),
    HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE, spaceAfter=8),
    table,
    Spacer(1, 0.25*cm),
    HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c0ccd8")),
    Spacer(1, 0.1*cm),
    Paragraph(
        f"BDS-SMC2 UAV Rescue System  |  Lab 7 BeiDou Short Message Communication  |  "
        f"Yuhang District, Hangzhou, China  |  {datetime.date.today().strftime('%B %d, %Y')}",
        META),
]

doc = SimpleDocTemplate(
    OUTPUT, pagesize=landscape(A4),
    leftMargin=1.2*cm, rightMargin=1.2*cm,
    topMargin=1.2*cm,  bottomMargin=1.2*cm,
    title="BDS-SMC2 Gap Analysis Table", author="BDS Lab 7",
)

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(W - 1.2*cm, 0.6*cm, f"Page {doc.page}")
    canvas.restoreState()

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"[DONE] Saved to {OUTPUT}")
