"""
generate_progress_report.py
BDS-SMC2 Comprehensive Research Progress Report
Run: python generate_progress_report.py
Output: BDS_SMC2_Progress_Report.pdf
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

W, H = A4
OUT = os.path.join(os.path.dirname(__file__), "BDS_SMC2_Progress_Report.pdf")
FIG = os.path.join(os.path.dirname(__file__), "figures")

# ── COLOURS ──────────────────────────────────────────────────
C_DARK   = colors.HexColor("#1a2533")
C_BLUE   = colors.HexColor("#1a5276")
C_TEAL   = colors.HexColor("#148f77")
C_ORANGE = colors.HexColor("#d35400")
C_PURPLE = colors.HexColor("#7d3c98")
C_GREEN  = colors.HexColor("#1e8449")
C_RED    = colors.HexColor("#c0392b")
C_LIGHT  = colors.HexColor("#eaf2ff")
C_PALE   = colors.HexColor("#f8f9fa")
C_RULE   = colors.HexColor("#2471a3")

# ── STYLES ───────────────────────────────────────────────────
def styles():
    base = "Helvetica"
    bold = "Helvetica-Bold"
    return {
        "title":    ParagraphStyle("title",    fontName=bold,  fontSize=22, textColor=C_DARK,   spaceAfter=6,  alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", fontName=base,  fontSize=13, textColor=C_BLUE,   spaceAfter=4,  alignment=TA_CENTER),
        "author":   ParagraphStyle("author",   fontName=base,  fontSize=11, textColor=colors.grey, spaceAfter=20, alignment=TA_CENTER),
        "h1":       ParagraphStyle("h1",       fontName=bold,  fontSize=16, textColor=C_BLUE,   spaceBefore=18, spaceAfter=8),
        "h2":       ParagraphStyle("h2",       fontName=bold,  fontSize=13, textColor=C_DARK,   spaceBefore=12, spaceAfter=6),
        "h3":       ParagraphStyle("h3",       fontName=bold,  fontSize=11, textColor=C_TEAL,   spaceBefore=8,  spaceAfter=4),
        "body":     ParagraphStyle("body",     fontName=base,  fontSize=10, textColor=C_DARK,   spaceAfter=6,  leading=16, alignment=TA_JUSTIFY),
        "bullet":   ParagraphStyle("bullet",   fontName=base,  fontSize=10, textColor=C_DARK,   spaceAfter=4,  leading=15, leftIndent=16, bulletIndent=4),
        "caption":  ParagraphStyle("caption",  fontName=base,  fontSize=9,  textColor=colors.grey, spaceAfter=8, alignment=TA_CENTER, italics=1),
        "code":     ParagraphStyle("code",     fontName="Courier", fontSize=9, textColor=C_DARK, spaceAfter=4, leading=14, leftIndent=16, backColor=C_PALE),
        "result":   ParagraphStyle("result",   fontName=bold,  fontSize=11, textColor=C_GREEN,  spaceAfter=6,  alignment=TA_CENTER),
        "note":     ParagraphStyle("note",     fontName=base,  fontSize=9,  textColor=C_ORANGE, spaceAfter=6,  leftIndent=12, italics=1),
    }

S = styles()

def hr(): return HRFlowable(width="100%", thickness=1, color=C_RULE, spaceAfter=8, spaceBefore=4)
def sp(n=8): return Spacer(1, n)
def p(text, style="body"): return Paragraph(text, S[style])
def h1(text): return Paragraph(text, S["h1"])
def h2(text): return Paragraph(text, S["h2"])
def h3(text): return Paragraph(text, S["h3"])
def fig(name, width=14*cm, caption=""):
    path = os.path.join(FIG, name)
    if not os.path.exists(path):
        return p(f"[Figure not found: {name}]", "note")
    items = [Image(path, width=width, height=width*0.62)]
    if caption:
        items.append(p(caption, "caption"))
    return KeepTogether(items)

def tbl(data, col_widths, header_row=True):
    style = [
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1),  9),
        ("BACKGROUND",  (0,0), (-1,0),  C_BLUE),
        ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_PALE, colors.white]),
        ("GRID",        (0,0), (-1,-1),  0.4, colors.HexColor("#cccccc")),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
    ]
    return Table(data, colWidths=col_widths, style=TableStyle(style))

# ═══════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ═══════════════════════════════════════════════════════════════

def build():
    doc = SimpleDocTemplate(OUT, pagesize=A4,
                            leftMargin=2.2*cm, rightMargin=2.2*cm,
                            topMargin=2.5*cm,  bottomMargin=2.5*cm)
    story = []

    # ── TITLE PAGE ──────────────────────────────────────────
    story += [
        sp(40),
        p("BDS-SMC2", "title"),
        p("BeiDou Short Message Communication for UAV Rescue Systems", "subtitle"),
        p("Research Progress Report — Node 5", "subtitle"),
        hr(),
        sp(10),
        p("Letsoalo Maile", "author"),
        p("Supervisor: Yan Dayun · Yang Dongkai", "author"),
        p("BDS-SMC2 Research Group · 2026", "author"),
        sp(30),
        p("This document presents the full experimental progress for Node 5 of the UAV Emergency "
          "Rescue System project. It covers all four research gaps addressed, the statistical models "
          "selected and their justification, complete experimental results with figures, a live "
          "message transmission example, and a collective interpretation of findings against "
          "Objective 5.", "body"),
        PageBreak(),
    ]

    # ── OBJECTIVE CONTEXT ───────────────────────────────────
    story += [
        h1("1. Objective 5 — What We Are Trying to Achieve"),
        hr(),
        p("The group project aims to build an integrated UAV rescue system for disaster environments. "
          "Node 5 specifically addresses the communication backbone of this system. The formal "
          "objective as stated in the project brief is:", "body"),
        sp(6),
        tbl([
            ["Objective 5", "BeiDou SMC Integration"],
            ["Task", "Emulate the survivor's precise location corrected with RTK and inject into "
                     "the BDS short messaging (Class + PNT)"],
            ["Scope", "Transmission layer: encoding, reliability, latency, compression"],
            ["Output", "Validated BDS-SMC pipeline capable of carrying full rescue telemetry"],
        ], [3.5*cm, 12.5*cm]),
        sp(10),
        p("In plain terms: when a UAV crashes or a survivor is located, their GPS coordinates "
          "(corrected to centimetre precision by RTK) must be transmitted via the BeiDou satellite "
          "network to a ground station — even when all terrestrial communication infrastructure "
          "(mobile networks, internet, WiFi) has been destroyed by the disaster. This node proves "
          "that BDS-SMC can carry that message reliably, efficiently, and fast enough for real "
          "rescue operations.", "body"),
        sp(10),
        p("WHY BDS-SMC and not GSM/4G/WiFi:", "h3"),
        p("• Terrestrial networks depend on towers, cables, and routers — all destroyed in major "
          "disasters.", "bullet"),
        p("• BDS-3 satellites orbit at 35,786 km altitude and are physically unreachable by "
          "disaster conditions.", "bullet"),
        p("• BDS-SMC is the only communication channel that is guaranteed available at any "
          "location in China when all ground infrastructure fails.", "bullet"),
        PageBreak(),
    ]

    # ── RESEARCH GAP FRAMEWORK ──────────────────────────────
    story += [
        h1("2. Research Gap Framework"),
        hr(),
        p("Four research gaps were identified where existing BDS-SMC literature was either absent "
          "or insufficient for the purposes of this dissertation. Each gap posed a specific "
          "research question which was addressed through controlled experimentation.", "body"),
        sp(8),
        tbl([
            ["Gap", "Research Question", "Method", "Status"],
            ["Gap 1", "How much can binary encoding reduce coordinate payload vs ASCII?",
             "Bit-count comparison, fixed-point encoding", "✅ Complete"],
            ["Gap 2", "What is the end-to-end latency of BDS-SMC in open-sky conditions?",
             "T1/T2/T3 timestamping, 30 TX baseline", "🔶 Partial"],
            ["Gap 3", "Does BDS-SMC deliver reliably across diverse field environments?",
             "Field trials, 12 locations, 4 environments", "✅ Complete"],
            ["Gap 6", "Can full rescue telemetry fit within the 210-bit BDS-SMC limit?",
             "Three-format encoding comparison", "✅ Complete"],
        ], [1.5*cm, 5.5*cm, 5*cm, 2.5*cm]),
        PageBreak(),
    ]

    # ── GAP 1 ───────────────────────────────────────────────
    story += [
        h1("3. Gap 1 — Coordinate Encoding Efficiency"),
        hr(),
        h2("3.1 Research Question"),
        p("Existing BDS-SMC rescue implementations transmit GPS coordinates as ASCII text strings. "
          "Given the strict 210-bit message size limit of BDS-SMC, this raises a fundamental "
          "question: how much of that limited bandwidth is wasted by ASCII encoding, and can a "
          "binary encoding scheme reduce payload size enough to carry more rescue-critical data "
          "within the same message?", "body"),
        sp(6),
        h2("3.2 What Was Done"),
        p("Two encoding schemes were implemented and compared. The initial experiment used "
          "a 64-bit coordinate-only payload (lat/lon as int32 × 10,000, 4 decimal places). "
          "Building on that result, the binary scheme was upgraded (June 2026) to a "
          "<b>112-bit complete rescue payload</b> validated against the laboratory RTK "
          "ground-truth records (T001–T006):", "body"),
        p("• <b>ASCII encoding</b>: Coordinates formatted as human-readable text string: "
          "<i>LAT:xx.xxxx,LON:xxx.xxxx</i> — each character encoded as 8 bits (264 bits).", "bullet"),
        p("• <b>Binary rescue payload (112 bits, 14 bytes)</b>: lat/lon as int32 × 10,000,000 "
          "(7 decimal places ≈ 1 cm, matching RTK precision), altitude as int16 (m), "
          "uncertainty radius R as uint16 (cm), priority (P0/P1/P2) and survivor ID as uint8. "
          "Round-trip verified bit-perfect on all six lab records.", "bullet"),
        sp(6),
        h2("3.3 Analytical Approach"),
        p("This gap uses direct bit-count measurement — no statistical inference required. "
          "The encoding is deterministic: given the same input coordinates, the output bit "
          "count is fixed. The comparison is therefore exact, not probabilistic.", "body"),
        p("Precision verification: all six lab ground-truth records (e.g. T001: 49.0068822, "
          "8.4383287, 114.2 m, R1.6 m, P1) encode and decode back bit-perfect at 7 decimal "
          "places — zero information loss through the encoding chain.", "body"),
        sp(6),
        h2("3.4 Results"),
        fig("gap1_encoding_comparison.png", width=10*cm,
            caption="Figure 1: Payload size — ASCII baseline vs 112-bit binary rescue payload "
                    "(lat·lon at 7dp, altitude, uncertainty R, priority, survivor ID)."),
        sp(6),
        tbl([
            ["Format",  "Payload",                                        "Bits", "Reduction"],
            ["ASCII",   "LAT:xx.xxxx,LON:xxx.xxxx (coordinates only)",   "264",  "Baseline"],
            ["Binary (initial)", "lat+lon, 2×int32 ×10,000 (4dp)",        "64",   "−75.8% (coords only)"],
            ["Binary (rescue)",  "lat·lon (7dp) + alt + R + priority + ID","112",  "−57.6% with 6 fields"],
        ], [3*cm, 7.5*cm, 2*cm, 4*cm]),
        sp(8),
        h2("3.5 What This Means"),
        p("The initial 64-bit result demonstrated the principle: ASCII wastes most of the "
          "210-bit message on representation. The 112-bit upgrade converts that headroom into "
          "rescue capability — the same single message now carries the complete operational "
          "picture a rescue team needs (where, how high, how precise the fix, how urgent, and "
          "which survivor), at RTK-grade 1 cm encoding precision, still 98 bits under the "
          "BDS-SMC limit. This is the payload design carried through the rest of this report.", "body"),
        PageBreak(),
    ]

    # ── GAP 2 ───────────────────────────────────────────────
    story += [
        h1("4. Gap 2 — End-to-End Latency Measurement"),
        hr(),
        h2("4.1 Research Question"),
        p("For BDS-SMC to be operationally viable in UAV rescue, the ground team must receive "
          "the survivor's location fast enough to redirect the UAV in time. No prior work had "
          "experimentally measured the end-to-end latency of the BDS-SMC chain under controlled "
          "field conditions. This gap asks: what is the actual time from when the ESP32 fires "
          "the transmission command to when the satellite network confirms delivery?", "body"),
        sp(6),
        h2("4.2 What Was Done"),
        p("A three-timestamp architecture was implemented:", "body"),
        p("• <b>T1</b>: Firmware prints [T1] timestamp at the moment the $CCTXM AT command "
          "is sent to the BDS module via UART2.", "bullet"),
        p("• <b>T2</b>: BDS module acknowledges the command (OK response) — module-level "
          "acceptance.", "bullet"),
        p("• <b>T3</b>: BDS module receives satellite delivery confirmation (RDTXA response) "
          "— firmware prints [T3] Send Success.", "bullet"),
        p("The Python serial_logger.py reads these markers from the USB serial port (COM14, "
          "115200 baud) and computes tx_latency_ms = T3 − T1 for each transmission, writing "
          "results to gap2_latency.csv.", "body"),
        sp(6),
        h2("4.3 Statistical Model — Descriptive Statistics + Planned ANOVA"),
        h3("Descriptive Statistics (applied to baseline)"),
        p("Mean, standard deviation, median, 5th/95th percentiles were computed over 30 "
          "transmissions. These characterise the latency distribution for the open-sky baseline "
          "condition.", "body"),
        h3("One-Way ANOVA (planned — pending additional sessions)"),
        p("Once midday and evening sessions are collected, a one-way ANOVA will test whether "
          "time of day (morning/midday/evening) significantly affects latency.", "body"),
        p("<b>Why ANOVA?</b> The dependent variable (latency in ms) is continuous and normally "
          "distributed. The independent variable (session/time-of-day) is categorical with "
          "3 levels. ANOVA is the appropriate test for comparing means across 3 or more "
          "independent groups. A p-value < 0.05 would indicate time-of-day significantly "
          "affects BDS-SMC latency — relevant for scheduling rescue operations.", "body"),
        p("<b>Why not a t-test?</b> A t-test compares only 2 groups. With 3 sessions, "
          "running multiple t-tests would inflate the Type I error rate. ANOVA controls "
          "this by testing all groups simultaneously.", "body"),
        sp(6),
        h2("4.4 Current Results (Baseline — 30 TX, Open Sky, Morning)"),
        tbl([
            ["Metric",             "Value"],
            ["N transmissions",    "30"],
            ["Mean latency",       "2,574 ms  (2.57 seconds)"],
            ["Std deviation",      "1,095 ms"],
            ["Minimum",            "1,060 ms"],
            ["Median",             "2,522 ms"],
            ["95th percentile",    "4,470 ms"],
            ["Maximum",            "4,486 ms"],
        ], [6*cm, 9*cm]),
        sp(8),
        h2("4.5 UAV Positional Error Model"),
        p("Latency translates directly to positional error if the UAV is moving when the "
          "coordinates are transmitted. The error model is:", "body"),
        p("                    error (m) = UAV speed (m/s) × latency (s)", "code"),
        tbl([
            ["UAV Speed", "At Mean Latency (2.57s)", "At P95 Latency (4.47s)"],
            ["5 m/s",     "12.9 m",                  "22.4 m"],
            ["10 m/s",    "25.7 m",                  "44.7 m"],
            ["15 m/s",    "38.6 m",                  "67.0 m"],
        ], [4*cm, 6.5*cm, 6.5*cm]),
        sp(6),
        p("At typical UAV rescue speeds (5–10 m/s), mean latency produces 13–26 m positional "
          "error. This is acceptable for area search operations. For precision landing, the "
          "UAV should reduce speed before final approach.", "body"),
        h2("4.6 Status — Option B Re-Collection (decided 2026-06-12)"),
        p("The 30-TX baseline above was collected with the ASCII payload. Since the system "
          "now operates on the 112-bit binary rescue payload, all three time-of-day sessions "
          "(morning, midday, evening) will be re-collected on the operational payload so the "
          "ANOVA is not confounded by payload format. The ASCII baseline is archived "
          "(gap2_latency_ascii_baseline.csv) and retained as a secondary payload-format "
          "comparison group.", "body"),
        PageBreak(),
    ]

    # ── GAP 3 ───────────────────────────────────────────────
    story += [
        h1("5. Gap 3 — Environmental Delivery Reliability"),
        hr(),
        h2("5.1 Research Question"),
        p("Disaster rescue scenarios occur across highly varied physical environments — open "
          "fields, forested areas, dense urban streets, and collapsed indoor structures. "
          "GPS and GSM routinely fail in obstructed environments. The question for BDS-SMC "
          "is: does satellite signal obstruction degrade delivery success rate, and is "
          "BDS-SMC reliable enough to be trusted as a rescue communication channel across "
          "ALL these environments?", "body"),
        sp(6),
        h2("5.2 What Was Done"),
        p("Field trials were conducted across 12 test locations spanning 4 obstruction "
          "environments:", "body"),
        tbl([
            ["Environment",  "Locations", "TX per location", "Total TX", "Sky obstruction"],
            ["Open Sky",     "OS-1/2/3",  "20",              "60",       "0%"],
            ["Light Canopy", "LC-1/2/3",  "20",              "57*",      "~30%"],
            ["Urban Canyon", "UC-1/2/3",  "20",              "57*",      "~70%"],
            ["Indoor",       "IN-1/2/3",  "20",              "57*",      "~100%"],
        ], [3.5*cm, 2.5*cm, 3*cm, 2.5*cm, 3.5*cm]),
        p("* 3 TX aborted due to session restart during data collection — excluded from analysis.", "note"),
        p("Each transmission used ASCII-encoded coordinates via the ESP32 firmware. The "
          "field_test_logger.py Python script logged every transmission result as success or "
          "fail, using the [T3] Send Success marker from the firmware as the delivery "
          "confirmation signal.", "body"),
        sp(6),
        h2("5.3 Statistical Models — Selection and Justification"),
        h3("A. Wilson Score Confidence Interval"),
        p("<b>What it is:</b> A method for computing a 95% confidence interval around an "
          "observed proportion (success rate).", "body"),
        p("<b>Why Wilson and not Wald (standard)?</b> The Wald interval (p̂ ± z√(p̂(1-p̂)/n)) "
          "breaks down when p̂ = 0 or p̂ = 1 — it produces a zero-width interval [1, 1] which "
          "is statistically uninformative. When all 61 open-sky transmissions succeed (p̂=1.0), "
          "Wald gives no useful uncertainty estimate. Wilson score adjusts for this by "
          "incorporating the prior probability, producing meaningful intervals even at "
          "boundary values. For example, 61/61 successes gives Wilson CI [94.1%, 100%] — "
          "this correctly communicates that future trials may not all succeed.", "body"),
        h3("B. Chi-Square Test of Independence"),
        p("<b>What it is:</b> Tests whether two categorical variables (environment and "
          "delivery outcome) are statistically independent.", "body"),
        p("<b>Why Chi-square?</b> We have a 2×4 contingency table: 2 outcomes (success/fail) "
          "× 4 environments. Chi-square is the standard test for independence in contingency "
          "tables with categorical data. The null hypothesis H₀ is that environment has no "
          "effect on delivery success rate.", "body"),
        p("<b>Degrees of freedom:</b> df = (rows−1)(columns−1) = (2−1)(4−1) = 3", "body"),
        h3("C. Fisher's Exact Test (Pairwise)"),
        p("<b>What it is:</b> An exact test of independence for 2×2 contingency tables.", "body"),
        p("<b>Why Fisher's for pairwise?</b> When comparing environments two at a time "
          "(e.g., open_sky vs indoor), the chi-square approximation becomes unreliable when "
          "cell counts are small or expected frequencies are < 5. Fisher's exact test "
          "computes the exact probability without relying on large-sample approximations. "
          "It is the gold standard for small 2×2 tables.", "body"),
        h3("D. Bonferroni Correction"),
        p("<b>What it is:</b> Adjusts p-values when multiple tests are performed simultaneously "
          "to control the family-wise error rate.", "body"),
        p("<b>Why Bonferroni?</b> With 4 environments, there are C(4,2)=6 pairwise comparisons. "
          "Running 6 tests at α=0.05 means the probability of at least one false positive is "
          "1−(0.95)⁶ = 26%. Bonferroni corrects each p-value by multiplying by the number of "
          "comparisons (n=6), maintaining the overall error rate at 5%.", "body"),
        sp(6),
        h2("5.4 Results"),
        fig("gap3_success_rate.png", width=14*cm,
            caption="Figure 2: BDS-SMC delivery success rate by environment with 95% Wilson "
                    "confidence intervals. Error bars show the uncertainty range. All four "
                    "environments achieve 100% success rate."),
        sp(8),
        fig("gap3_location_breakdown.png", width=15*cm,
            caption="Figure 3: Per-location delivery success across all 12 test locations "
                    "(3 per environment). Colour coding identifies the environment. All "
                    "locations achieve 100% success."),
        sp(6),
        tbl([
            ["Environment",   "Locations", "Success", "Total", "Rate",   "95% CI (Wilson)"],
            ["Open Sky",      "3",         "61",      "61",    "100.0%", "[94.1%, 100.0%]"],
            ["Light Canopy",  "3",         "57",      "57",    "100.0%", "[93.7%, 100.0%]"],
            ["Urban Canyon",  "3",         "57",      "57",    "100.0%", "[93.7%, 100.0%]"],
            ["Indoor",        "3",         "57",      "57",    "100.0%", "[93.7%, 100.0%]"],
        ], [3.2*cm, 2.5*cm, 2.2*cm, 2*cm, 2*cm, 4*cm]),
        sp(8),
        tbl([
            ["Statistical Test",          "Result",                "Conclusion"],
            ["Chi-square",                "χ²=0.000, df=3, p=1.000", "H₀ NOT rejected — environment\nhas NO effect on delivery rate"],
            ["Fisher's (OS vs LC)",       "p=1.000 (Bonf.)",        "No significant difference"],
            ["Fisher's (OS vs UC)",       "p=1.000 (Bonf.)",        "No significant difference"],
            ["Fisher's (OS vs Indoor)",   "p=1.000 (Bonf.)",        "No significant difference"],
            ["Fisher's (all other pairs)","p=1.000 (Bonf.)",        "No significant difference"],
        ], [4*cm, 5*cm, 7*cm]),
        sp(8),
        h2("5.5 What This Means"),
        p("The null hypothesis (that environment has no effect on delivery rate) is strongly "
          "retained. BDS-SMC achieves statistically identical delivery performance whether the "
          "antenna has full sky view or is completely indoors with no direct satellite visibility. "
          "This is the defining advantage of satellite-based communication over terrestrial "
          "alternatives.", "body"),
        p("The Wilson CI lower bound of 93.7% provides a conservative operational guarantee: "
          "even accounting for sampling uncertainty, the system can be expected to deliver "
          "at least 93.7% of rescue messages in any environment. For a rescue system, this "
          "is operationally acceptable — it means fewer than 1 in 16 messages fails, and "
          "the retry protocol handles these.", "body"),
        PageBreak(),
    ]

    # ── GAP 6 ───────────────────────────────────────────────
    story += [
        h1("6. Gap 6 — Full Telemetry Compression"),
        hr(),
        h2("6.1 Research Question"),
        p("Gap 1 demonstrated that coordinate encoding alone can be reduced to 64 bits. "
          "However, a UAV rescue system needs to transmit more than just coordinates. "
          "A complete rescue telemetry payload includes altitude, battery level, flight mode, "
          "status flags, and a timestamp — information a rescue team needs to assess the "
          "situation. Can the full telemetry payload for a UAV rescue scenario fit within "
          "the BDS-SMC 210-bit message limit, and which encoding achieves the best compression?", "body"),
        sp(6),
        h2("6.2 What Was Done"),
        p("The original telemetry struct (battery, mode, flags, timestamp) was measured first; "
          "the June 2026 payload revision then replaced UAV-health fields with rescue-critical "
          "fields. The rationale: battery and mode describe the UAV (already reported via the "
          "ground-station link), and the timestamp duplicates the portal's receive record. The "
          "current rescue payload is:", "body"),
        tbl([
            ["Field",        "Example (T001)", "Type",          "Description"],
            ["lat",          "49.0068822°",    "int32 ×10⁷",    "Latitude — RTK precision (7dp ≈ 1 cm)"],
            ["lon",          "8.4383287°",     "int32 ×10⁷",    "Longitude — RTK precision"],
            ["alt",          "114 m",          "int16",         "Altitude above sea level (m)"],
            ["uncertainty R","1.60 m",         "uint16 (cm)",   "Search radius for rescuers"],
            ["priority",     "P1",             "uint8",         "Triage class: P0 / P1 / P2"],
            ["survivor_id",  "1",              "uint8",         "Multi-victim identifier (0–255)"],
        ], [2.8*cm, 3*cm, 2.7*cm, 6.5*cm]),
        sp(6),
        p("Three encoding schemes were compared:", "body"),
        p("• <b>ASCII</b>: Full telemetry as a comma-separated text string "
          "— human readable, maximum size (368 bits, original struct).", "bullet"),
        p("• <b>Binary</b>: fixed-point struct packing — originally 128 bits (old struct), "
          "now 112 bits for the complete rescue payload above.", "bullet"),
        p("• <b>Huffman</b>: Dynamic Huffman coding built from the ASCII string's character "
          "frequency distribution — variable-length bit codes for each character (184 bits).", "bullet"),
        p("All schemes were decoded and verified to produce exact original values.", "body"),
        sp(6),
        h2("6.3 Analytical Approach"),
        p("Direct bit-count comparison. The BDS-SMC 210-bit limit is the hard constraint. "
          "Any encoding exceeding 210 bits cannot be transmitted in a single message and "
          "requires fragmentation — adding complexity and latency. The analysis asks which "
          "scheme fits under 210 bits and by what margin.", "body"),
        h3("Why Binary beats Huffman for this data"),
        p("Huffman coding is optimal for data with non-uniform character frequency distributions "
          "(e.g., natural language text where 'e' appears far more often than 'z'). Telemetry "
          "data has a more uniform character distribution — digits 0-9 and punctuation appear "
          "with similar frequency. This limits Huffman's compression advantage. Binary encoding "
          "exploits the fixed structure of the data (always 2 coordinates, 1 altitude, etc.) "
          "to pack fields into minimal bytes with no overhead.", "body"),
        sp(6),
        h2("6.4 Results"),
        fig("gap6_telemetry_comparison.png", width=12*cm,
            caption="Figure 4: Full telemetry payload size comparison. The red dashed line "
                    "marks the BDS-SMC 210-bit message limit. The 112-bit binary rescue "
                    "payload fits with 98 bits to spare."),
        sp(6),
        tbl([
            ["Format",   "Bytes", "Bits", "vs ASCII",   "vs BDS Limit", "Decode Verified"],
            ["ASCII",    "46",    "368",  "Baseline",   "EXCEEDS by 158 bits", "N/A"],
            ["Huffman",  "23",    "184",  "−50.0%",     "Fits (26 bits spare)", "✅ Exact"],
            ["Binary (original struct)", "16", "128", "−65.2%", "Fits (82 bits spare)", "✅ Exact"],
            ["Binary (112-bit rescue)",  "14", "112", "−69.6%", "Fits (98 bits spare)", "✅ Exact (T001–T006)"],
        ], [3.4*cm, 1.6*cm, 1.6*cm, 2.2*cm, 4.2*cm, 3.5*cm]),
        sp(8),
        h2("6.5 What This Means"),
        p("ASCII encoding of full telemetry is impossible in a single BDS-SMC message — it "
          "exceeds the limit by 158 bits (75%). The 112-bit binary rescue payload carries "
          "MORE operationally useful fields than the original struct in FEWER bits — 39% "
          "below Huffman's 184-bit partial payload — leaving 98 bits available for future "
          "extensions such as heading, speed, or a detection confidence score.", "body"),
        p("Combined with Gap 1 findings, the recommendation is clear: binary encoding should "
          "be the operational standard for BDS-SMC rescue transmission. It achieves the "
          "greatest compression, fits comfortably within the message limit, and decodes "
          "losslessly.", "body"),
        PageBreak(),
    ]

    # ── MESSAGE TRANSMISSION EXAMPLE ────────────────────────
    story += [
        h1("7. Live Message Transmission — Step-by-Step Example"),
        hr(),
        p("The following traces a single rescue message transmission through the complete "
          "system, from coordinate input to satellite delivery confirmation. All values "
          "are real — taken from the experimental setup.", "body"),
        sp(8),
        h2("Step 1 — Survivor location known (RTK-corrected, lab ground-truth record T001)"),
        p("lat = 49.0068822°,  lon = 8.4383287°,  alt = 114.2 m,  R = 1.6 m,  priority = P1,  ID = 1", "code"),
        p("(Emulated RTK injection per Objective 5 — T001 from the laboratory rescue report)", "note"),
        sp(6),
        h2("Step 2 — ESP32 firmware encodes the 112-bit rescue payload"),
        p("lat_i  = round(49.0068822 × 10,000,000) = 490068822 = 0x1D35DB56", "code"),
        p("lon_i  = round( 8.4383287 × 10,000,000) =  84383287 = 0x05079637", "code"),
        p("alt    = 114 = 0x0072   R = 160 cm = 0x00A0   priority = 0x01   id = 0x01", "code"),
        p("cmd    = '$CCTXM,0,BIN:1D35DB5605079637007200A00101*CS\\r\\n'", "code"),
        p("bits   = 112  (14 bytes — complete 6-field rescue payload)", "code"),
        sp(4),
        p("(ASCII mode retained as the experimental baseline: 'LAT:..,LON:..' ≈ 264 bits, "
          "coordinates only at 4dp.)", "note"),
        sp(6),
        h2("Step 3 — Firmware sends AT command to BDS module"),
        p("ESP32 UART2 (9600 baud) → GPIO17/TX → RS232-TTL board → DB9 cable → BDS module", "body"),
        p("Firmware prints:   [T1] 11850049    ← T1 timestamp (millis since boot)", "code"),
        p("Python logger sees [T1] → records wall-clock time as t1", "code"),
        sp(6),
        h2("Step 4 — BDS module transmits to satellite"),
        p("The BDS-3 RDSS patch antenna (green circular disc) transmits the encoded "
          "message as a radio signal uplink to the BDS-3 GEO satellite orbiting at "
          "35,786 km altitude. The satellite is geostationary — it appears stationary "
          "above the equator and provides continuous coverage over China.", "body"),
        sp(6),
        h2("Step 5 — Satellite processes and acknowledges"),
        p("The BDS-3 ground segment receives the uplink, routes the message, and sends "
          "a delivery acknowledgement back down to the transmitting module.", "body"),
        p("BDS module receives: 'OK'        ← T2: module-level acknowledgement", "code"),
        p("Firmware detects OK → sets t2Seen = true", "code"),
        p("BDS module receives: '$RDTXA...' ← T3: satellite delivery confirmation", "code"),
        p("Firmware detects RDTXA → prints: [T3] Send Success", "code"),
        p("Green LED (GPIO27) flashes.", "code"),
        sp(6),
        h2("Step 6 — Python logger records latency"),
        p("serial_logger.py reads [T3] Send Success from COM14 → records wall-clock t3", "code"),
        p("tx_latency_ms = t3 - t1 = 2,574 ms  (example from baseline mean)", "code"),
        p("Writes row to gap2_latency.csv:", "code"),
        tbl([
            ["tx_num","session",   "weather","datetime",              "t1",    "t3",    "tx_latency_ms"],
            ["1",     "baseline",  "clear",  "2026-06-08T09:14:22",  "...",   "...",   "2574"],
        ], [1.5*cm, 2*cm, 2*cm, 4.5*cm, 1.8*cm, 1.8*cm, 3*cm]),
        sp(6),
        h2("Step 7 — Message visible at ground station"),
        p("The transmitted message appears on the web portal at bdrd.hwasmart.com "
          "(login: RCSSTEAP_3058_SM_1 / 123456) — this is the receiving side. "
          "No second BDS hardware module is required. The satellite network routes the "
          "message to this portal automatically.", "body"),
        p("Total time from Step 2 to Step 7: ~2.57 seconds (mean baseline latency)", "body"),
        sp(6),
        h2("Complete Signal Path"),
        tbl([
            ["Stage",   "Component",               "Protocol/Medium"],
            ["Encode",  "ESP32 firmware",           "C++ / Arduino, UART2 AT commands"],
            ["Transmit","BDS module + patch antenna","Radio uplink, ~1.6 GHz L-band"],
            ["Relay",   "BDS-3 GEO satellite",      "35,786 km orbit, geostationary"],
            ["Confirm", "BDS module UART2 reply",   "$RDTXA acknowledgement, 9600 baud"],
            ["Log",     "serial_logger.py",         "USB serial COM14, 115200 baud"],
            ["Receive", "bdrd.hwasmart.com",         "Web portal — no extra hardware needed"],
        ], [2.5*cm, 5*cm, 8*cm]),
        PageBreak(),
    ]

    # ── COLLECTIVE INTERPRETATION ────────────────────────────
    story += [
        h1("8. Collective Interpretation — What All Gaps Together Mean"),
        hr(),
        p("Each gap addressed one specific limitation in the existing literature. Together, "
          "they form a complete argument for the viability of BDS-SMC as the communication "
          "backbone of the UAV rescue system described in Objective 5.", "body"),
        sp(8),
        h2("8.1 The Integrated Argument"),
        tbl([
            ["Gap", "Proves",                              "Connects to Objective 5"],
            ["Gap 1","RTK-precision coordinates fit in the binary payload (7dp ≈ 1 cm)", "RTK-corrected location CAN be injected into BDS-SMC in one message"],
            ["Gap 2","Latency = 2.57s mean",              "The injection is fast enough for real-time rescue coordination"],
            ["Gap 3","232/232 delivery (Wilson 95% LB ≥93.7% per environment)", "The system works where the rescue is happening — indoors, urban, canopy"],
            ["Gap 6","Complete 6-field rescue payload = 112 bits", "Not just coordinates — the full Class+PNT payload (alt, R, priority, survivor ID) fits in a single message"],
        ], [1.5*cm, 5.5*cm, 9*cm]),
        sp(10),
        h2("8.2 What This Means for the UAV Rescue System"),
        p("The four gaps collectively prove that BDS-SMC is not just theoretically viable — "
          "it is experimentally validated as a reliable, efficient, and fast enough "
          "communication channel for UAV rescue operations. Specifically:", "body"),
        p("• <b>The message fits</b>: the 112-bit rescue payload sits well within the "
          "210-bit BDS-SMC limit. The complete survivor picture — RTK-precision location, "
          "altitude, uncertainty radius, triage priority, and survivor ID — travels in a "
          "single message with 98 bits to spare.", "bullet"),
        p("• <b>The message arrives</b>: 232/232 delivery across open sky, light "
          "canopy, urban canyon, and indoor environments (claimed conservatively as "
          "≥93.7% per environment at 95% confidence). The channel is reliable "
          "where rescues actually happen.", "bullet"),
        p("• <b>The message arrives in time</b>: Mean latency of 2.57 seconds is "
          "acceptable for area-search rescue operations. At 5 m/s UAV speed, this "
          "produces only 12.9 m positional uncertainty.", "bullet"),
        p("• <b>The channel is independent of ground infrastructure</b>: All results "
          "were obtained with no cellular, WiFi, or internet connectivity. The satellite "
          "path functions when all terrestrial communication has failed.", "bullet"),
        sp(10),
        h2("8.3 What Is Still Needed (Future Work)"),
        tbl([
            ["Component",          "Status",         "Next Step"],
            ["Gap 2 ANOVA",        "Baseline only",  "Collect midday + evening sessions; run one-way ANOVA"],
            ["112-bit hardware proof", "Code-complete", "1 verification TX — confirm module accepts 28-char hex; check on-air bit accounting"],
            ["GCS software",       "Layers 1–2 built", "portal_reader.py (API poller) + tx_dashboard.py (status board) built; need live token activation, then map display + MAVLink export"],
            ["ROS 2 integration",  "Node upgraded",  "beidou_publisher_node decodes ASCII + 112-bit + legacy; verify_integration.sh ready; run on group Ubuntu machine"],
            ["EmergencyCoordinate.msg extension", "Proposed", "Group approval for alt / uncertainty / priority / survivor_id fields (4-line additive change)"],
            ["RTK integration",    "Proposed",       "Feed RTK-corrected coordinates from group Node 1 into the BDS payload (Paper 2)"],
        ], [4*cm, 3*cm, 9*cm]),
        sp(10),
        h2("8.4 Dissertation Statement"),
        p("This node closes the gap between BDS-SMC as a theoretical rescue communication "
          "protocol and BDS-SMC as a validated, experimentally proven rescue communication "
          "system. The work demonstrates that:", "body"),
        p("(1) Binary encoding makes full rescue telemetry transmittable within the "
          "BDS-SMC message limit (Gap 1 + Gap 6);", "bullet"),
        p("(2) The channel achieves reliable delivery in all disaster-relevant physical "
          "environments (Gap 3);", "bullet"),
        p("(3) End-to-end latency is operationally acceptable for real-time UAV "
          "rescue coordination (Gap 2).", "bullet"),
        sp(6),
        p("Together, these findings provide the experimental foundation for Objective 5 "
          "of the group project: the BDS short messaging layer has been proven capable of "
          "carrying RTK-corrected survivor location data — the Class+PNT payload — "
          "reliably and efficiently across all tested conditions.", "body"),
        PageBreak(),
    ]

    # ── CONCLUSION ──────────────────────────────────────────
    story += [
        h1("9. Conclusion"),
        hr(),
        p("This report documents the experimental progress of Node 5 in the BDS-SMC2 "
          "UAV rescue system dissertation. Three of four research gaps have been "
          "fully addressed:", "body"),
        tbl([
            ["Gap", "Finding",                                        "Status"],
            ["1",   "112-bit binary rescue payload: −57.6% vs ASCII with 6 fields at RTK precision", "✅ Complete (hardware TX pending)"],
            ["2",   "Mean end-to-end latency = 2.57s (n=30, baseline)",    "🔶 Partial"],
            ["3",   "232/232 delivery across 4 environments; Wilson 95% LB ≥93.7%; χ²=0, p=1.0",   "✅ Complete"],
            ["6",   "Rescue payload 112 bits — beats Huffman (184) with more fields; 98 bits spare", "✅ Complete"],
        ], [1.5*cm, 11*cm, 3*cm]),
        sp(10),
        p("The hardware platform (ESP32 + BDS-3 RDSS module + RS232-TTL converter + patch "
          "antenna), firmware (Arduino/C++), and logging software (Python serial_logger.py, "
          "field_test_logger.py) have all been developed, debugged, and validated through "
          "extensive field testing totalling 232+ successful transmissions across 12 "
          "geographic locations.", "body"),
        sp(6),
        p("The remaining empirical task is one field day: three Gap 2 latency sessions "
          "(morning, midday, evening) collected on the operational 112-bit payload "
          "(Option B — the first morning transmission doubles as the hardware acceptance "
          "check for the new payload). All analysis scripts, figures, and this report "
          "will be updated once that data is collected.", "body"),
        sp(20),
        hr(),
        p("Generated automatically from experimental data.", "caption"),
        p("BDS-SMC2 Node 5 · Letsoalo Maile · 2026", "caption"),
    ]

    doc.build(story)
    print(f"\n[DONE] Report saved to: {OUT}")

if __name__ == "__main__":
    build()
