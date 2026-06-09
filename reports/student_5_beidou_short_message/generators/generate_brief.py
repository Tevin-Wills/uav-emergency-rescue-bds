"""
Generates Research Brief PDF for BDS-SMC2.
Run: python generate_brief.py
Output: BDS_SMC2_Research_Brief.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import datetime

OUTPUT = "BDS-SMC2_Brief.pdf"
W, H = A4

DARK   = colors.HexColor("#1a3a5c")
MID    = colors.HexColor("#2e5fa3")
ACCENT = colors.HexColor("#e8523a")
GREEN  = colors.HexColor("#2d7a3a")
GOLD   = colors.HexColor("#b07d1a")
LGRAY  = colors.HexColor("#f4f7fb")
BORDER = colors.HexColor("#c8d8ea")

def S(name, **kw):
    base = dict(fontName="Helvetica", fontSize=10, leading=14,
                textColor=colors.HexColor("#2d2d2d"), alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(name, **base)

TITLE  = S("T",  fontName="Helvetica-Bold", fontSize=22, leading=28,
            textColor=DARK, alignment=TA_CENTER, spaceAfter=4)
SUBTITLE=S("ST", fontName="Helvetica",      fontSize=11, leading=15,
            textColor=MID,  alignment=TA_CENTER, spaceAfter=2)
META   = S("M",  fontName="Helvetica",      fontSize=8.5,leading=11,
            textColor=colors.grey, alignment=TA_CENTER)
H1     = S("H1", fontName="Helvetica-Bold", fontSize=13, leading=17,
            textColor=DARK, spaceBefore=14, spaceAfter=5, alignment=TA_LEFT)
H2     = S("H2", fontName="Helvetica-Bold", fontSize=10.5,leading=14,
            textColor=MID,  spaceBefore=8, spaceAfter=4, alignment=TA_LEFT)
BODY   = S("B",  spaceAfter=6)
BULLET = S("BU", leftIndent=14, firstLineIndent=-10, spaceAfter=4)
CAPTION= S("C",  fontSize=8, leading=11, textColor=colors.grey,
            alignment=TA_CENTER, spaceAfter=4)
PULL   = S("P",  fontName="Helvetica-BoldOblique", fontSize=11, leading=16,
            textColor=DARK, alignment=TA_CENTER)

def rule(color=BORDER, thick=0.5):
    return HRFlowable(width="100%", thickness=thick, color=color, spaceAfter=8)

def section_bar(color=DARK):
    return HRFlowable(width="100%", thickness=2.5, color=color, spaceAfter=10)

def box(content_paragraphs, bg=LGRAY, border=BORDER):
    data = [[p] for p in content_paragraphs]
    flat = [[item for sublist in data for item in sublist]]
    inner = []
    for cp in content_paragraphs:
        inner.append(cp)
    t = Table([[Paragraph(
        " ".join([p.text if hasattr(p,"text") else "" for p in content_paragraphs]),
        BODY)]], colWidths=[15.6*cm])
    # simpler: just wrap in a single-cell table
    rows = [[cp] for cp in content_paragraphs]
    cells = []
    for cp in content_paragraphs:
        cells.append(cp)
    tbl = Table([[c] for c in cells], colWidths=[15.6*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX",        (0,0), (-1,-1), 1, border),
        ("LEFTPADDING",(0,0), (-1,-1), 12),
        ("RIGHTPADDING",(0,0),(-1,-1),12),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    return tbl

def highlight_box(text, bg, border, text_style):
    tbl = Table([[Paragraph(text, text_style)]], colWidths=[15.6*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX",        (0,0), (-1,-1), 1.5, border),
        ("LEFTPADDING",(0,0),(-1,-1), 14),
        ("RIGHTPADDING",(0,0),(-1,-1),14),
        ("TOPPADDING", (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1),10),
    ]))
    return tbl

def numbered_box(num, label, color, body_text):
    num_style = S("NS", fontName="Helvetica-Bold", fontSize=16, leading=18,
                  textColor=colors.white, alignment=TA_CENTER)
    lbl_style = S("LS", fontName="Helvetica-Bold", fontSize=9.5, leading=12,
                  textColor=colors.white, alignment=TA_LEFT)
    bod_style = S("BS", fontSize=9.5, leading=13, alignment=TA_JUSTIFY,
                  textColor=colors.HexColor("#1a1a1a"))
    tbl = Table([
        [Paragraph(str(num), num_style),
         Paragraph(label, lbl_style),
         Paragraph(body_text, bod_style)]
    ], colWidths=[1.0*cm, 3.8*cm, 10.8*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (1,0), color),
        ("BACKGROUND",    (2,0), (2,0), colors.HexColor("#f9fafb")),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("BOX",           (0,0), (-1,-1), 0.8, colors.HexColor("#c0c8d0")),
        ("LINEAFTER",     (1,0), (1,0), 1.0, colors.HexColor("#c0c8d0")),
        ("LEFTPADDING",   (0,0), (1,0), 8),
        ("RIGHTPADDING",  (0,0), (1,0), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (2,0), (2,0), 10),
        ("RIGHTPADDING",  (2,0), (2,0), 10),
    ]))
    return tbl

story = []

# ── TITLE BLOCK ───────────────────────────────────────────────────────────────
story += [
    Spacer(1, 0.5*cm),
    Paragraph("Research Brief", SUBTITLE),
    Paragraph("BeiDou Short Message Communication", TITLE),
    Paragraph("Why These Gaps Must Be Fixed — Limitations, Innovations, and Impact", SUBTITLE),
    Spacer(1, 0.3*cm),
    rule(DARK, 2),
    Paragraph(
        "BDS-SMC2 UAV Rescue System  ·  Lab 7  ·  "
        f"Yuhang District, Hangzhou  ·  {datetime.date.today().strftime('%B %d, %Y')}",
        META),
    Spacer(1, 0.5*cm),
]

# ── SECTION 1 — WHY THERE IS A NEED ─────────────────────────────────────────
story += [
    section_bar(),
    Paragraph("1.  Why These Gaps Need to Be Fixed", H1),
    Paragraph(
        "BeiDou-3 Short Message Communication (BDS-3 SMC) is the only global "
        "navigation satellite system capable of two-way messaging without any "
        "terrestrial infrastructure. In disaster zones, remote wilderness, or "
        "conflict areas where cellular networks are destroyed or absent, BDS-3 "
        "SMC is the sole communication channel available to a distressed survivor. "
        "A drone dispatched to rescue that survivor depends entirely on the "
        "coordinates the survivor transmits via this channel.",
        BODY),
    Paragraph(
        "Despite this critical role, the engineering layer that connects the "
        "survivor's terminal to the drone — the payload encoding, the transmission "
        "reliability measurement, and the security of the coordinate data — has "
        "never been systematically studied or standardised. The gaps identified "
        "in this project are not academic curiosities; they are active barriers "
        "that prevent BDS-3 SMC from being reliably deployed in real UAV rescue "
        "operations today.",
        BODY),
]

pull1 = highlight_box(
    '"The probability that a distressed user below a cliff successfully completes '
    'a BDS-3 SMC transmission cycle is empirically unknown."'
    "  — Springer RDSS Performance Study, 2023",
    colors.HexColor("#eef4fb"), MID,
    S("PQ", fontName="Helvetica-Oblique", fontSize=10, leading=14,
      textColor=DARK, alignment=TA_CENTER)
)
story += [Spacer(1,0.2*cm), pull1, Spacer(1,0.3*cm)]

story += [
    Paragraph(
        "Four specific gaps make BDS-3 SMC unreliable or impractical for "
        "operational UAV rescue deployment:",
        BODY),
    Paragraph("▸  <b>Payload waste:</b> Default ASCII encoding transmits coordinates "
              "at 69% overhead — consuming channel capacity that could carry life-critical "
              "telemetry data (altitude, battery, mode).", BULLET),
    Paragraph("▸  <b>Unknown latency:</b> No one has measured how long the full "
              "chain from ESP32 to UAV takes — making it impossible to determine "
              "whether the drone arrives before a survivor's situation deteriorates.", BULLET),
    Paragraph("▸  <b>Unknown reliability:</b> There is no data on how often BDS-3 "
              "SMC transmissions succeed in forests, urban canyons, or indoors — "
              "the exact environments where accidents happen.", BULLET),
    Paragraph("▸  <b>No encoding standard:</b> Every manufacturer uses a different "
              "ASCII format. There is no interoperable, efficient telemetry encoding "
              "specification for BDS-3 SMC — making system integration unnecessarily "
              "complex and fragile.", BULLET),
    Spacer(1, 0.3*cm),
]

# ── SECTION 2 — LIMITATIONS ──────────────────────────────────────────────────
story += [
    section_bar(),
    Paragraph("2.  Limitations Imposed by These Gaps", H1),
    Paragraph(
        "Each gap translates directly into an operational limitation that prevents "
        "BDS-3 SMC from functioning as a reliable UAV rescue communication layer:",
        BODY),
    Spacer(1, 0.2*cm),
]

limitations = [
    (ACCENT, "Gap 1", "Payload Inefficiency",
     "ASCII encoding cannot fit a full telemetry struct (lat, lon, alt, battery, "
     "mode, flags, timestamp) within GSMC's 560-bit global limit. This forces "
     "message fragmentation — and since BDS-3 has no native fragment reassembly "
     "protocol, any lost fragment renders the entire coordinate useless. The drone "
     "cannot navigate to a location it cannot fully decode."),
    (MID, "Gap 2", "Unvalidated Latency Budget",
     "System designers cannot determine the minimum safe update rate for UAV "
     "waypoint corrections. If the BDS-3 SMC chain takes 3 seconds end-to-end "
     "and the survivor is in a debris flow moving at 1 m/s, the drone arrives "
     "at a position that is already 3 metres stale. Without measured latency, "
     "this error cannot be quantified or compensated."),
    (GREEN, "Gap 3", "Unquantified Reliability in Rescue Terrain",
     "Rescue operations cannot be planned around a communication channel whose "
     "success rate in the relevant terrain is unknown. A system that works 95% "
     "of the time in open sky but only 20% of the time in a forest provides "
     "false confidence — and a drone dispatched on a failed transmission will "
     "navigate to the wrong location or not at all."),
    (colors.HexColor("#6a3a8c"), "Gap 6", "No Encoding Standard for Integration",
     "Without a standardised multi-field telemetry encoding, every BDS-3 SMC "
     "integration must implement its own ad hoc format. Drone ground control "
     "stations, rescue coordination centres, and terminal manufacturers cannot "
     "interoperate. Each new deployment requires custom parsers, increasing "
     "the cost and failure risk of life-critical systems."),
]

for color, gap, label, text in limitations:
    story.append(numbered_box(gap, label, color, text))
    story.append(Spacer(1, 0.25*cm))

# ── SECTION 3 — INNOVATIONS ──────────────────────────────────────────────────
story += [
    section_bar(),
    Paragraph("3.  Innovations the Proposed Solutions Aim to Bring", H1),
    Paragraph(
        "This project does not propose theoretical solutions. It implements, "
        "transmits, and measures each solution on real BDS-3 satellite hardware "
        "using an ESP32 microcontroller and an active BDS SIM card. The "
        "innovations are concrete, reproducible, and directly address what "
        "the literature says is missing:",
        BODY),
    Spacer(1, 0.2*cm),
]

innovations = [
    ("Innovation 1 — First Standardised Coordinate Encoding for BDS-3 SMC",
     colors.HexColor("#eef4fb"), MID,
     "The multi-mode encoding framework (ASCII / Binary / Huffman) is the first "
     "proposed interoperable coordinate encoding standard for BDS-3 SMC payloads. "
     "Binary fixed-point encoding packs lat/lon into exactly 8 bytes (64 bits) "
     "with 4-decimal precision — sufficient for ±11 m UAV navigation accuracy. "
     "Huffman encoding further reduces variable-length telemetry by up to 77%. "
     "Both are implemented in open firmware and validated with matching Python "
     "decoders — making them immediately reusable by other researchers and "
     "system integrators."),
    ("Innovation 2 — First Empirical End-to-End Latency Measurement",
     colors.HexColor("#eefaf0"), GREEN,
     "For the first time, the complete BDS-3 SMC latency chain (ESP32 → RS232 → "
     "BDS module → GEO satellite → GCC → web platform) is instrumented and "
     "measured across 30 repeated transmissions. The resulting latency budget "
     "— mean, standard deviation, min, max — provides the foundational data "
     "that UAV rescue system designers need to specify waypoint update rates "
     "and assess survivor tracking accuracy under realistic conditions."),
    ("Innovation 3 — First Environmental Reliability Dataset for BDS-3 SMC",
     colors.HexColor("#fefaf0"), GOLD,
     "The field test across four terrain conditions (open sky, light canopy, "
     "urban canyon, indoor) produces the first published empirical dataset of "
     "BDS-3 RSMC transmission success rates in rescue-relevant environments. "
     "This data directly answers the question that the Springer RDSS Performance "
     "Study (2023) identified as an open problem: what is the probability of "
     "a successful BDS-3 SMC cycle from a terrain-obstructed survivor terminal?"),
]

for title, bg, border, text in innovations:
    inno_title = S("IT", fontName="Helvetica-Bold", fontSize=10, leading=13,
                   textColor=border, spaceAfter=3, alignment=TA_LEFT)
    inno_body  = S("IB", fontSize=9.5, leading=13, alignment=TA_JUSTIFY,
                   textColor=colors.HexColor("#1a1a1a"))
    tbl = Table([
        [Paragraph(title, inno_title)],
        [Paragraph(text,  inno_body)],
    ], colWidths=[15.6*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("BOX",           (0,0), (-1,-1), 1.5, border),
        ("LINEBELOW",     (0,0), (0,0), 1, border),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("RIGHTPADDING",  (0,0), (-1,-1), 12),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(KeepTogether([tbl, Spacer(1, 0.25*cm)]))

# ── SECTION 4 — IMPACT ────────────────────────────────────────────────────────
story += [
    section_bar(),
    Paragraph("4.  Expected Impact", H1),
    Paragraph(
        "The combined impact of these four experiments, conducted on real BDS-3 "
        "satellite hardware, operates at three levels:",
        BODY),
    Spacer(1, 0.2*cm),
]

impact_data = [
    ["Level", "Impact", "Specific Outcome"],
    ["Technical\nImpact",
     "Closes 4 open\nresearch gaps",
     "Delivers the first standardised BDS-3 SMC coordinate encoding, the first "
     "empirical latency budget, the first terrain reliability dataset, and the first "
     "multi-format telemetry comparison "
     "— each confirmed with literature citations as previously absent."],
    ["Operational\nImpact",
     "Enables real\nUAV rescue use",
     "Binary encoding makes full 7-field rescue telemetry fit inside a single "
     "GSMC message globally. Latency data allows correct UAV update rate "
     "specification. Reliability data allows mission planners to assess "
     "communication risk per terrain type before deploying a drone."],
    ["Scientific\nImpact",
     "Produces a\nreusable dataset",
     "All results (30-transmission latency log, 80-transmission field test, "
     "compression ratio table) are saved to CSV and "
     "are immediately reusable by other researchers — providing the first "
     "open empirical BDS-3 SMC operational dataset in the literature."],
]

impact_tbl = Table(impact_data, colWidths=[2.4*cm, 3.2*cm, 10.0*cm], repeatRows=1)
impact_tbl.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0), DARK),
    ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
    ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE",      (0,0), (-1,0), 9),
    ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
    ("FONTSIZE",      (0,1), (-1,-1), 9),
    ("FONTNAME",      (0,1), (1,-1), "Helvetica-Bold"),
    ("ROWBACKGROUNDS",(0,1), (-1,-1), [LGRAY, colors.white]),
    ("GRID",          (0,0), (-1,-1), 0.5, BORDER),
    ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ("TOPPADDING",    (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ("TEXTCOLOR",     (1,1), (1,-1), DARK),
    ("ALIGN",         (0,1), (1,-1), "CENTER"),
]))
story += [impact_tbl, Spacer(1, 0.4*cm)]

# Final pull quote
story += [
    rule(DARK, 2),
    Spacer(1, 0.2*cm),
    highlight_box(
        "If BDS-3 SMC is to become a reliable backbone for drone-assisted rescue, "
        "its payload efficiency, transmission reliability, and latency "
        "must be measured and standardised — not assumed. This project does that, "
        "for the first time, on real satellite hardware.",
        colors.HexColor("#eef2f9"), DARK,
        S("FQ", fontName="Helvetica-BoldOblique", fontSize=10.5, leading=15,
          textColor=DARK, alignment=TA_CENTER)
    ),
    Spacer(1, 0.3*cm),
    rule(BORDER),
    Paragraph(
        "BDS-SMC2 UAV Rescue System  ·  Lab 7 BeiDou Short Message Communication  ·  "
        f"Yuhang District, Hangzhou, China  ·  {datetime.date.today().strftime('%B %d, %Y')}",
        META),
]

# ── Build PDF ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=2.0*cm, rightMargin=2.0*cm,
    topMargin=2.0*cm,  bottomMargin=2.0*cm,
    title="BDS-SMC2 Research Brief", author="BDS Lab 7",
)

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2.0*cm, 1.1*cm, "BDS-SMC2 Research Brief")
    canvas.drawRightString(W - 2.0*cm, 1.1*cm, f"Page {doc.page}")
    canvas.restoreState()

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"[DONE] Saved to {OUTPUT}")
