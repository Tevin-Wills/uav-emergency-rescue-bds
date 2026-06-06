"""
generate_paper_plan.py -- Generates BDS-SMC2_Paper_Plan.pdf
Two-paper IEEE publication plan for the BDS-SMC2 dissertation.
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
    Paragraph("IEEE Publication Plan — Two Papers", S_SUB),
    Paragraph("Letsoalo Maile  |  GNSS &amp; Satellite Communication Dissertation", S_DATE),
    Paragraph("June 2026", S_DATE),
    sp(8), hr(), sp(6),
]

# ── Section 1: Strategy ─────────────────────────────────────────────────────────
story.append(h1("1.  Publication Strategy", NAVY))
story += [sp(6),
    body("The five research gaps addressed in this dissertation form two distinct "
         "contribution clusters. Splitting them into two papers maximises impact, "
         "avoids desk rejection for scope, and matches the data requirements of each venue."),
    sp(6),
]

strat = simple_table([
    [Paragraph("<b>Paper</b>", S_NOTE),
     Paragraph("<b>Gaps</b>", S_NOTE),
     Paragraph("<b>Target Venue</b>", S_NOTE),
     Paragraph("<b>Core Claim</b>", S_NOTE)],
    [Paragraph("<b>Paper 1</b>", S_BODY),
     body("Gap 2 + Gap 3"),
     body("IEEE Transactions on\nAerospace &amp; Electronic Systems (TAES)"),
     body("BDS-3 SMC latency characterisation + environmental reliability for UAV rescue")],
    [Paragraph("<b>Paper 2</b>", S_BODY),
     body("Gap 1 + Gap 6"),
     body("IEEE Communications Letters"),
     body("Payload encoding efficiency and AES security overhead for BDS-3 SMC")],
], col_widths=[2*cm, 2.5*cm, 5*cm, 7.5*cm])
story += [strat, sp(10)]

# ── Section 2: Paper 1 ──────────────────────────────────────────────────────────
story.append(h1("2.  Paper 1 — IEEE TAES  (Gap 2 + Gap 3)", BLUE))
story += [sp(6)]

story.append(simple_table([
    [Paragraph("<b>Field</b>", S_NOTE), Paragraph("<b>Detail</b>", S_NOTE)],
    [body("Full title"),    body("End-to-End Latency and Environmental Reliability of "
                                 "BeiDou-3 Short Message Communication for UAV Search-and-Rescue")],
    [body("Venue"),         body("IEEE Transactions on Aerospace and Electronic Systems (TAES)")],
    [body("Impact factor"), body("5.1  |  Q1 journal  |  Target length: 14 pages IEEE double-column")],
    [body("Submission"),    body("After 2-week experiment window — target August 2026")],
    [body("Gaps covered"),  body("Gap 2 (latency across sessions) + Gap 3 (4 environments x 3 locations)")],
], col_widths=[3.5*cm, 13.5*cm]))

story += [sp(8), h2("2.1  Data Requirements (what you must collect)")]
story.append(simple_table([
    [Paragraph("<b>Gap</b>", S_NOTE),
     Paragraph("<b>Requirement</b>", S_NOTE),
     Paragraph("<b>Minimum</b>", S_NOTE),
     Paragraph("<b>Target</b>", S_NOTE),
     Paragraph("<b>Status</b>", S_NOTE)],
    [body("Gap 2"), body("TX latency across 3 time-of-day sessions"),
     body("70 TX"), body("100 TX"), body("30 collected (baseline)")],
    [body("Gap 3"), body("Success rate: 4 environments x 3 locations"),
     body("20 TX/env"), body("20 TX x 3 locations = 60/env"), body("0 — hardware needed")],
], col_widths=[1.8*cm, 6*cm, 2.2*cm, 3.8*cm, 3.2*cm]))

story += [sp(8), h2("2.2  Paper Structure (8 sections)")]
story.append(simple_table([
    [Paragraph("<b>Section</b>", S_NOTE),
     Paragraph("<b>Title</b>", S_NOTE),
     Paragraph("<b>Content</b>", S_NOTE),
     Paragraph("<b>Write when</b>", S_NOTE)],
    [body("I"),   body("Introduction"),
     body("UAV rescue problem, BDS-3 SMC opportunity, 5 contributions"), body("Now")],
    [body("II"),  body("Background &amp; Related Work"),
     body("BDS-3 RDSS architecture, prior latency studies, gap table"), body("Now")],
    [body("III"), body("System Design"),
     body("ESP32 firmware, wiring, AT command protocol, portal"), body("Now")],
    [body("IV"),  body("Methodology"),
     body("Experiment setup, session design, environment classification, statistical plan"), body("Now")],
    [body("V"),   body("Gap 2 Results — Latency"),
     body("Mean 2.58s, sigma 1.09s, ANOVA, CDF, UAV error model"), body("After hardware")],
    [body("VI"),  body("Gap 3 Results — Environments"),
     body("Success rates, 95% CI, chi-square, Fisher's exact, Bonferroni"), body("After hardware")],
    [body("VII"), body("Discussion"),
     body("UAV update rate limit, environment ranking, comparison to LTE/LoRa"), body("After hardware")],
    [body("VIII"),body("Conclusion"),
     body("Summary, limitations, future work"), body("Last")],
], col_widths=[1*cm, 4*cm, 8.5*cm, 3.5*cm]))

story += [sp(8), h2("2.3  Key Results to Report (from existing + new data)")]
story.append(simple_table([
    [Paragraph("<b>Metric</b>", S_NOTE), Paragraph("<b>Value</b>", S_NOTE),
     Paragraph("<b>Source</b>", S_NOTE)],
    [body("Mean end-to-end TX latency"),  body("2582.9 ms"),         body("gap2_latency.csv (n=30)")],
    [body("Std deviation"),               body("1093.7 ms"),         body("gap2_latency.csv")],
    [body("Latency range"),               body("1070 – 4488 ms"),    body("gap2_latency.csv")],
    [body("Decode overhead"),             body("8.4 ms"),            body("gap2_latency.csv")],
    [body("UAV max error @ 10 m/s"),      body("25.8 m (mean), 44.9 m (P95)"), body("Derived")],
    [body("ANOVA p-value"),               body("TBD after 3 sessions"),         body("gap2_analysis.py")],
    [body("Open sky success rate"),       body("TBD"),               body("gap3_field_test.csv")],
    [body("Indoor success rate"),         body("TBD (expected < 30%)"),         body("gap3_field_test.csv")],
    [body("Chi-square across envs"),      body("TBD (expected p < 0.001)"),     body("gap3_analysis.py")],
], col_widths=[6*cm, 5.5*cm, 5.5*cm]))

story += [sp(8), h2("2.4  Task List — Paper 1")]
story.append(simple_table([
    [Paragraph("<b>#</b>", S_NOTE),
     Paragraph("<b>Task</b>", S_NOTE),
     Paragraph("<b>When</b>", S_NOTE),
     Paragraph("<b>Tool</b>", S_NOTE)],
    [body("1"),  body("Collect Gap 2: 70 more TX across 3 sessions"),
     body("Hardware days 1-4"), body("serial_logger.py")],
    [body("2"),  body("Collect Gap 3: 4 envs x 3 locations x 20 TX"),
     body("Hardware days 2-5"), body("field_test_logger.py")],
    [body("3"),  body("Run gap2_analysis.py — ANOVA + CDF + UAV error"),
     body("After Day 5"),       body("gap2_analysis.py")],
    [body("4"),  body("Run gap3_analysis.py — chi-square + Fisher's + Bonferroni"),
     body("After Day 5"),       body("gap3_analysis.py")],
    [body("5"),  body("Regenerate all figures (Gap 3 auto-generates)"),
     body("After analysis"),    body("generate_figures.py")],
    [body("6"),  body("Write Sections I – IV (no new data needed)"),
     body("Now / before hw"),   body("IEEE TAES template")],
    [body("7"),  body("Download IEEE TAES LaTeX/Word template"),
     body("Now"),               body("ieeeauthorcenter.ieee.org")],
    [body("8"),  body("Compile 30 references in IEEE format"),
     body("Now"),               body("Google Scholar / Zotero")],
    [body("9"),  body("Write Sections V – VI with real numbers"),
     body("After analysis"),    body("Paper draft")],
    [body("10"), body("Write Sections VII – VIII (discussion + conclusion)"),
     body("After Sec V-VI"),    body("Paper draft")],
    [body("11"), body("Supervisor review — send full draft"),
     body("End of week 2"),     body("Email")],
    [body("12"), body("Revise and submit to TAES"),
     body("Target Aug 2026"),   body("IEEE Manuscript Central")],
], col_widths=[0.7*cm, 7.8*cm, 3.5*cm, 5*cm]))

# ── Section 3: Paper 2 ──────────────────────────────────────────────────────────
story.append(h1("3.  Paper 2 — IEEE Communications Letters  (Gap 1 + Gap 6)", GREEN))
story += [sp(6)]

story.append(simple_table([
    [Paragraph("<b>Field</b>", S_NOTE), Paragraph("<b>Detail</b>", S_NOTE)],
    [body("Full title"),    body("Payload Encoding Efficiency and AES-128 Security Overhead "
                                 "for BeiDou-3 Short Message Communication in UAV Rescue")],
    [body("Venue"),         body("IEEE Communications Letters")],
    [body("Impact factor"), body("4.1  |  Q1  |  Length: 5 pages IEEE two-column (Letters format)")],
    [body("Submission"),    body("Target October 2026 (after Paper 1 draft is complete)")],
    [body("Gaps covered"),  body("Gap 1 (ASCII vs Binary encoding), Gap 5 (AES-128 overhead), "
                                 "Gap 6 (full telemetry struct comparison)")],
], col_widths=[3.5*cm, 13.5*cm]))

story += [sp(8), h2("3.1  Data Requirements (mostly already collected)")]
story.append(simple_table([
    [Paragraph("<b>Gap</b>", S_NOTE),
     Paragraph("<b>What you have</b>", S_NOTE),
     Paragraph("<b>Additional needed</b>", S_NOTE),
     Paragraph("<b>Status</b>", S_NOTE)],
    [body("Gap 1"), body("264 bits (ASCII) vs 64 bits (Binary) — software verified"),
     body("10 hardware TX each mode for validation"),    body("Hardware Day 1")],
    [body("Gap 5"), body("3/3 AES round-trip verified, +100% overhead confirmed"),
     body("10 hardware TX for stronger sample size"),    body("Hardware Day 1")],
    [body("Gap 6"), body("ASCII=368b, Binary=128b (-65.2%), Huffman=184b (-50%)"),
     body("10 hardware TX with Huffman mode"),           body("Hardware Day 1")],
], col_widths=[1.8*cm, 6.5*cm, 5.5*cm, 3.2*cm]))

story += [sp(8), h2("3.2  Key Results to Report (all already confirmed)")]
story.append(simple_table([
    [Paragraph("<b>Gap</b>", S_NOTE),
     Paragraph("<b>Metric</b>", S_NOTE),
     Paragraph("<b>Value</b>", S_NOTE)],
    [body("Gap 1"), body("ASCII lat/lon payload"),              body("264 bits")],
    [body("Gap 1"), body("Binary lat/lon payload"),             body("64 bits  (−75.8%, 4.12x)")],
    [body("Gap 5"), body("Binary payload (plaintext)"),         body("64 bits")],
    [body("Gap 5"), body("AES-128-CBC ciphertext"),             body("128 bits (+100% overhead)")],
    [body("Gap 5"), body("Round-trip verified"),                body("3/3 messages (100%)")],
    [body("Gap 6"), body("ASCII full telemetry (7 fields)"),    body("368 bits  (baseline)")],
    [body("Gap 6"), body("Binary struct packing"),              body("128 bits (−65.2%)")],
    [body("Gap 6"), body("Dynamic Huffman coding"),             body("184 bits (−50.0%)")],
    [body("Gap 6"), body("Counterintuitive finding"),
     body("Binary BEATS Huffman for structured numerical data — contradicts compression theory")],
], col_widths=[1.8*cm, 7.5*cm, 7.7*cm]))

story += [sp(8), h2("3.3  Task List — Paper 2")]
story.append(simple_table([
    [Paragraph("<b>#</b>", S_NOTE),
     Paragraph("<b>Task</b>", S_NOTE),
     Paragraph("<b>When</b>", S_NOTE)],
    [body("1"),  body("Hardware validate Gap 1: 10 ASCII + 10 Binary TX"),
     body("Hardware Day 1")],
    [body("2"),  body("Hardware validate Gap 5: 10 AES TX"),
     body("Hardware Day 1")],
    [body("3"),  body("Hardware validate Gap 6: 10 Huffman TX"),
     body("Hardware Day 1")],
    [body("4"),  body("Write 5-page Letters draft (Intro, System, Results, Discussion, Conclusion)"),
     body("After Paper 1 draft")],
    [body("5"),  body("Download IEEE Communications Letters template"),
     body("Before writing")],
    [body("6"),  body("Highlight the Binary-beats-Huffman finding as the key novelty"),
     body("Section III of letter")],
    [body("7"),  body("Compile 15 references (shorter than Paper 1)"),
     body("Before writing")],
    [body("8"),  body("Supervisor review"),
     body("Target Sep 2026")],
    [body("9"),  body("Submit to IEEE Communications Letters"),
     body("Target Oct 2026")],
], col_widths=[0.7*cm, 11.8*cm, 5.5*cm]))

# ── Section 4: Timeline ─────────────────────────────────────────────────────────
story.append(h1("4.  Combined Timeline", NAVY))
story += [sp(6)]
story.append(simple_table([
    [Paragraph("<b>Period</b>", S_NOTE),
     Paragraph("<b>Activity</b>", S_NOTE),
     Paragraph("<b>Output</b>", S_NOTE)],
    [body("Week 1 (now)"),       body("Build scripts, scout locations, write Paper 1 Sec I-IV"),
     body("Scripts on standby, paper skeleton")],
    [body("Week 2 (hardware)"),  body("5 hardware days: collect all Gap 2 + Gap 3 data"),
     body("gap2_latency.csv + gap3_field_test.csv complete")],
    [body("Week 3"),             body("Run analysis, regenerate figures, write Sec V-VI"),
     body("All figures, stats tables, results sections")],
    [body("Week 4"),             body("Write Sec VII-VIII, full paper review, supervisor"),
     body("Paper 1 first draft")],
    [body("Month 2"),            body("Revise Paper 1, write Paper 2 (5 pages, faster)"),
     body("Paper 1 submission-ready, Paper 2 draft")],
    [body("August 2026"),        body("Submit Paper 1 to IEEE TAES"),
     body("Under review")],
    [body("October 2026"),       body("Submit Paper 2 to IEEE Communications Letters"),
     body("Under review")],
], col_widths=[3.5*cm, 8*cm, 5.5*cm]))

story += [sp(8), hr()]
story.append(Paragraph(
    "BDS-SMC2 IEEE Publication Plan  |  Letsoalo Maile  |  June 2026",
    S_FOOT
))

doc.build(story)
print(f"[SAVED] {OUT}")
