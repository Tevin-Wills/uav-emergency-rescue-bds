"""
generate_paper_plan.py -- Generates BDS-SMC2_Paper_Plan.pdf
Two-paper publication plan for the BDS-SMC2 dissertation.
UPDATED 2026-06-12: post-audit numbers (232 TX), 112-bit rescue payload,
ROS 2 integration, narrowed claim, realistic venues.
Run: python generate_paper_plan.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

OUT = os.path.join(os.path.dirname(__file__), "BDS-SMC2_Paper_Plan.pdf")

NAVY  = colors.HexColor("#1a3a5c")
BLUE  = colors.HexColor("#2e5fa3")
GREEN = colors.HexColor("#2d7a3a")
RED   = colors.HexColor("#c0392b")
GOLD  = colors.HexColor("#b07d1a")
LGRAY = colors.HexColor("#f4f7fb")
DGRAY = colors.HexColor("#555555")
WHITE = colors.white

def style(name, **kw):
    return ParagraphStyle(name, **kw)

S_TITLE = style("T",  fontSize=22, textColor=NAVY,  alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=4)
S_SUB   = style("S",  fontSize=11, textColor=BLUE,  alignment=TA_CENTER, fontName="Helvetica",      spaceAfter=2)
S_DATE  = style("D",  fontSize=9,  textColor=DGRAY, alignment=TA_CENTER, fontName="Helvetica",      spaceAfter=16)
S_H1    = style("H1", fontSize=13, textColor=WHITE, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=4)
S_H2    = style("H2", fontSize=11, textColor=NAVY,  fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3)
S_H3    = style("H3", fontSize=10, textColor=BLUE,  fontName="Helvetica-Bold", spaceBefore=6,  spaceAfter=3)
S_BODY  = style("B",  fontSize=9,  textColor=colors.black, fontName="Helvetica", leading=14, spaceAfter=3)
S_CODE  = style("C",  fontSize=8,  textColor=colors.HexColor("#222"), fontName="Courier",
                backColor=colors.HexColor("#f0f0f0"), borderPadding=(3,6,3,6), leading=12, spaceAfter=2)
S_NOTE  = style("N",  fontSize=8,  textColor=DGRAY, fontName="Helvetica-Oblique", spaceAfter=2)
S_WARN  = style("W",  fontSize=9,  textColor=RED,   fontName="Helvetica-Bold",    spaceAfter=4)
S_FOOT  = style("F",  fontSize=8,  textColor=DGRAY, alignment=TA_CENTER)

def h1(text, color=BLUE):
    bg = Table([[Paragraph(text, S_H1)]], colWidths=[17*cm])
    bg.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), color),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
    ]))
    return bg

def h2(t): return Paragraph(t, S_H2)
def h3(t): return Paragraph(t, S_H3)
def body(t): return Paragraph(t, S_BODY)
def note(t): return Paragraph(f"<i>{t}</i>", S_NOTE)
def warn(t): return Paragraph(f"&#9888;  {t}", S_WARN)
def sp(h=4): return Spacer(1, h)
def hr(): return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=4)

def simple_table(data, col_widths, header_color=colors.HexColor("#dce6f1")):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  header_color),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [LGRAY, WHITE]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return t

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm,  bottomMargin=2*cm,
)
story = []

# ── Cover ───────────────────────────────────────────────────────────────────────
story += [
    sp(20),
    Paragraph("BDS-SMC2 UAV Rescue System", S_TITLE),
    Paragraph("Publication Plan — Two Papers (Rev. 2)", S_SUB),
    Paragraph("Letsoalo Maile  |  GNSS &amp; Satellite Communication Dissertation", S_DATE),
    Paragraph("Updated 12 June 2026 — post-audit numbers, 112-bit rescue payload, ROS 2 integration", S_DATE),
    sp(8), hr(), sp(6),
]

# ── Section 1: Strategy ─────────────────────────────────────────────────────────
story.append(h1("1.  Publication Strategy", NAVY))
story += [sp(6),
    body("Revision 2 consolidates the encoding results (Gaps 1 + 6) into Paper 1: the "
         "112-bit rescue payload is now the carrying contribution and belongs with the "
         "reliability and latency evidence that proves it deliverable. Paper 2 becomes the "
         "end-to-end system paper (RTK injection, GCS decode, ROS 2, UAV mission pipeline), "
         "matching the group integration now in place."),
    sp(4),
    warn("Positioning note: the BDS-3 GSMC system paper (Geodesy &amp; Geodynamics, 2021; "
         "2149 TX, 97.72%) already field-measured the link. Our claim is therefore the "
         "NARROWED one below — never claim 'first field measurement of BDS-3 SMC'."),
    sp(6),
]

strat = simple_table([
    [Paragraph("<b>Paper</b>", S_NOTE),
     Paragraph("<b>Scope</b>", S_NOTE),
     Paragraph("<b>Target Venue</b>", S_NOTE),
     Paragraph("<b>Core Claim</b>", S_NOTE)],
    [Paragraph("<b>Paper 1</b>", S_BODY),
     body("Gaps 1, 2, 3, 6 + 112-bit rescue payload"),
     body("MDPI Drones (primary) /\nSensors / IEEE Access"),
     body("First environment-stratified characterisation of BDS-3 SMC carrying a complete "
          "6-field rescue payload: 112 bits, delivery reliability &ge;93.7% (Wilson 95% LB), "
          "2.57 s mean latency, integrated into a UAV mission pipeline")],
    [Paragraph("<b>Paper 2</b>", S_BODY),
     body("End-to-end system: RTK injection, portal GCS, ROS 2, MAVLink"),
     body("IEEE Access /\nMDPI Drones"),
     body("Full survivor-to-UAV pipeline: RTK coordinate &rarr; 112-bit BDS-SMC &rarr; portal "
          "&rarr; decode &rarr; ROS 2 mission trigger, with stage-by-stage latency budget")],
], col_widths=[2*cm, 4*cm, 3.6*cm, 7.4*cm])
story += [strat, sp(10)]

# ── Section 2: Paper 1 ──────────────────────────────────────────────────────────
story.append(h1("2.  Paper 1 — Transmission Layer  (Gaps 1, 2, 3, 6 + 112-bit payload)", BLUE))
story += [sp(6)]

story.append(simple_table([
    [Paragraph("<b>Field</b>", S_NOTE), Paragraph("<b>Detail</b>", S_NOTE)],
    [body("Working title"), body("A 112-bit Binary Rescue Payload over BeiDou-3 Short Message "
                                 "Communication: Environment-Stratified Reliability and Latency "
                                 "for UAV Search-and-Rescue")],
    [body("Venue"),         body("MDPI Drones (primary — publishes this genre, fast review); "
                                 "fallbacks: MDPI Sensors, IEEE Access")],
    [body("Submission"),    body("After 1 remaining field day (Gap 2 midday + evening, 112-bit "
                                 "verification TX) — target August 2026")],
    [body("Status"),        body("Empirical work ~75% complete. Defence sections drafted "
                                 "(BDS_SMC2_Paper1_Sections.md): comparison table, emulated-RTK "
                                 "framing, Wilson claim, exclusion appendix, repeat-TX policy.")],
], col_widths=[3.5*cm, 13.5*cm]))

story += [sp(8), h2("2.1  Data Status (audited 2026-06-12)")]
story.append(simple_table([
    [Paragraph("<b>Dataset</b>", S_NOTE),
     Paragraph("<b>Requirement</b>", S_NOTE),
     Paragraph("<b>Collected</b>", S_NOTE),
     Paragraph("<b>Status</b>", S_NOTE)],
    [body("Gap 3 reliability"), body("4 environments x 3 locations x ~20 TX"),
     body("232 valid TX (61/57/57/57)"), Paragraph("<b>COMPLETE</b>", S_BODY)],
    [body("Gap 2 latency"), body("3 time-of-day sessions x 30 TX, ALL on the 112-bit payload (Option B)"),
     body("0 of 90 (30-TX ASCII baseline archived as secondary comparison)"),
     Paragraph("<font color='#c0392b'><b>NEED morning + midday + evening</b></font>", S_BODY)],
    [body("Gap 1 / Gap 6 encoding"), body("Bit counts + round-trip verification"),
     body("Software-verified incl. 112-bit on lab T001-T006"), Paragraph("<b>COMPLETE</b>", S_BODY)],
    [body("112-bit hardware proof"), body("1 TX accepted by BDS module + portal receipt"),
     body("0"), Paragraph("<font color='#c0392b'><b>NEED 1 test TX</b></font>", S_BODY)],
], col_widths=[3.6*cm, 5.6*cm, 5*cm, 2.8*cm]))

story += [sp(8), h2("2.2  Key Results to Report (verified against raw data, 2026-06-12)")]
story.append(simple_table([
    [Paragraph("<b>Metric</b>", S_NOTE), Paragraph("<b>Value</b>", S_NOTE),
     Paragraph("<b>Source</b>", S_NOTE)],
    [body("Delivery success (valid TX)"),  body("232/232; report as Wilson 95% LB &ge;93.7% per env, &ge;98.4% pooled"), body("gap3_field_test.csv")],
    [body("Environment effect"),           body("None detectable: chi-sq=0.000, df=3, p=1.000; Fisher pairwise all 1.0"), body("gap3_analysis.py")],
    [body("Mean TX latency (T1&rarr;T3)"), body("ASCII baseline: 2574.5 ms (n=30, sd 1094.7) — archived; operational-payload sessions TBD"), body("gap2_latency_ascii_baseline.csv")],
    [body("ANOVA time-of-day"),            body("TBD after 3 sessions on 112-bit payload (Option B); ASCII-vs-binary secondary comparison via --ascii-baseline"), body("gap2_analysis.py")],
    [body("Gap 1 encoding"),               body("ASCII 264 bits vs 112-bit rescue payload (-57.6%)"), body("decode_binary.py round-trip")],
    [body("Gap 6 telemetry"),              body("ASCII 368 / Huffman 184 / Binary 112 bits (-69.6% vs ASCII; 39% under Huffman with MORE fields)"), body("gap6_telemetry.csv")],
    [body("Payload completeness"),         body("All 6 lab rescue-report fields (T001-T006) round-trip bit-perfect at 7dp"), body("decode_binary.py test")],
    [body("BDS-3 headroom"),               body("98 bits under the 210-bit regional limit"), body("design")],
    [body("Excluded records"),             body("33 rows, single cause (T3 instrumentation bug, OS-1, re-collected) — full appendix drafted"), body("Paper1_Sections C.2")],
], col_widths=[4.2*cm, 8.3*cm, 4.5*cm]))

story += [sp(8), h2("2.3  Remaining Task List — Paper 1")]
story.append(simple_table([
    [Paragraph("<b>#</b>", S_NOTE),
     Paragraph("<b>Task</b>", S_NOTE),
     Paragraph("<b>When</b>", S_NOTE),
     Paragraph("<b>Tool / Ref</b>", S_NOTE)],
    [body("1"),  body("Flash MODE 1 firmware once; Gap 2 morning session (30 TX) — TX #1 doubles as the 112-bit acceptance check + on-air bit-accounting check on the portal"),
     body("Field day, 08:00-10:00"), body("run_gap2_morning.bat")],
    [body("2"),  body("Gap 2 midday session (30 TX) + optional power measurement"),
     body("Field day, 12:00-14:00"), body("run_gap2_midday.bat")],
    [body("3"),  body("Gap 2 evening session (30 TX)"),
     body("Field day, after 18:00"), body("run_gap2_evening.bat")],
    [body("4"),  body("Activate portal reader (browser tokens) + run dashboard for portal-corroborated delivery evidence"),
     body("Field day"), body("portal_reader.py / tx_dashboard.py")],
    [body("5"),  body("Optional: power draw per TX (USB meter)"),
     body("Field day"), body("J/message metric")],
    [body("6"),  body("Run ANOVA across 3 sessions; regenerate figures"),
     body("After field day"), body("gap2_analysis.py / generate_figures.py")],
    [body("7"),  body("Fill [CITE] placeholders in drafted sections (LoRaWAN, COSPAS-SARSAT, Iridium, BDS-3 GSMC paper)"),
     body("This week"), body("BDS_SMC2_Paper1_Sections.md")],
    [body("8"),  body("Assemble full draft: drafted sections + results + figures"),
     body("After analysis"), body("venue template")],
    [body("9"),  body("Supervisor review of submission-ready draft (not an outline)"),
     body("Before submission"), body("email")],
    [body("10"), body("Submit"),
     body("Target Aug 2026"), body("venue portal")],
], col_widths=[0.7*cm, 8.8*cm, 3.5*cm, 4*cm]))

# ── Section 3: Paper 2 ──────────────────────────────────────────────────────────
story.append(h1("3.  Paper 2 — End-to-End Rescue Pipeline  (system paper)", GREEN))
story += [sp(6)]

story.append(simple_table([
    [Paragraph("<b>Field</b>", S_NOTE), Paragraph("<b>Detail</b>", S_NOTE)],
    [body("Working title"), body("End-to-End BDS-3 Short Message Rescue System: RTK Coordinate "
                                 "Injection, GCS Decoding, and UAV Mission Integration via ROS 2")],
    [body("Venue"),         body("IEEE Access or MDPI Drones")],
    [body("Prerequisite"),  body("Paper 1 submitted. Group integration validated (ROS 2 node + "
                                 "verify_integration.sh already in the team repo).")],
    [body("What it proves"),body("Paper 1 proves the transmission layer; Paper 2 proves the full "
                                 "pipeline: RTK fix &rarr; encode &rarr; satellite &rarr; portal &rarr; "
                                 "decode &rarr; ROS 2 topic &rarr; UAV mission, with a latency budget per stage.")],
    [body("Note"),          body("Group stack is ROS 2 (not ROS 1 as in Rev. 1 of this plan) and "
                                 "uXRCE-DDS/px4_msgs (not MAVROS). EmergencyCoordinate.msg extension "
                                 "(alt / uncertainty / priority / survivor_id) pending group approval.")],
], col_widths=[3.5*cm, 13.5*cm]))

story += [sp(8), h2("3.1  Data To Collect (after Paper 1)")]
story.append(simple_table([
    [Paragraph("<b>Dataset</b>", S_NOTE),
     Paragraph("<b>Minimum sample</b>", S_NOTE),
     Paragraph("<b>Purpose</b>", S_NOTE)],
    [body("RTK &rarr; BDS TX accuracy chain"), body("30 TX per coordinate set"),
     body("Coordinate accuracy loss through transmission chain")],
    [body("GCS decode latency"),               body("30+ samples"),
     body("Portal-poll + decode stage of the latency budget")],
    [body("Multi-survivor scenario"),          body("3 runs x 6 TX (T001-T006 messages ready)"),
     body("Survivor-ID field + multi-victim triage validation")],
    [body("ROS 2 publish rate"),               body("50+ samples"),
     body("Real-time capability of the integration layer")],
    [body("Mission-trigger latency"),          body("20+ samples"),
     body("Topic publish &rarr; mission reaction (uXRCE-DDS path)")],
    [body("UAV positional error model"),       body("Derived from Gap 2 data"),
     body("No new hardware — modelled from latency distribution")],
], col_widths=[5*cm, 5.5*cm, 6.5*cm]))

# ── Section 4: Timeline ─────────────────────────────────────────────────────────
story.append(h1("4.  Combined Timeline (Rev. 2)", NAVY))
story += [sp(6)]
story.append(simple_table([
    [Paragraph("<b>Period</b>", S_NOTE),
     Paragraph("<b>Activity</b>", S_NOTE),
     Paragraph("<b>Output</b>", S_NOTE)],
    [body("Now (June W2)"),     body("Fill citations; group meeting on .msg extension; push node to team repo"),
     body("Drafted sections citation-complete")],
    [body("Field day"),         body("Gap 2 midday + evening; 112-bit TX; portal tokens; dashboard evidence"),
     body("Paper 1 empirical record COMPLETE")],
    [body("June W3-W4"),        body("ANOVA, figures, assemble Paper 1 full draft"),
     body("Submission-ready draft to supervisor")],
    [body("July"),              body("Revise per supervisor; Ubuntu integration demo with group"),
     body("Paper 1 final; integration video/screenshots for Paper 2")],
    [body("August 2026"),       body("Submit Paper 1 (MDPI Drones)"),
     body("Under review")],
    [body("Sep-Oct 2026"),      body("Collect Paper 2 datasets; write system paper"),
     body("Paper 2 draft")],
    [body("Nov 2026"),          body("Submit Paper 2 (IEEE Access / Drones)"),
     body("Under review")],
], col_widths=[3.2*cm, 8.3*cm, 5.5*cm]))

story += [sp(8), hr()]
story.append(Paragraph(
    "BDS-SMC2 Publication Plan Rev. 2  |  Letsoalo Maile  |  12 June 2026  |  "
    "numbers audited against raw datasets",
    S_FOOT
))

doc.build(story)
print(f"[SAVED] {OUT}")
