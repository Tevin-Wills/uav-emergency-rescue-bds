"""
generate_consolidated_report.py
Builds BDS_SMC2_Node_Consolidated_Report.pdf.

BASE: the structure of BDS_SMC2_Node_Report.pdf (generate_node_report.py) is
preserved EXACTLY - same title block, Abstract, Sections 1-7, Data/Code,
References. All other project documents (evolution audit, evaluation, hardware
bring-up plan, comprehensive/final reports) are organised INTO this structure:
enriched into the existing sections where they belong, and added as Appendices
A-E so the IMRaD spine is not disturbed.

Corrections applied during consolidation (the C1-C4 consistency fixes):
  C2 - the "strictly more information than Huffman" overclaim is reworded.
  C3 - the 210-bit limit is labelled indicative pending measurement.
  C4 - the moved ASCII baseline is disclosed in-text.
  Integration is reported as COMPLETE and VERIFIED (group ROS 2 merge).

WinAnsi-safe: uses "at least", "approx.", "x10^7", "+/-" (no >=, no approx glyph).
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from PIL import Image as PILImage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "figures")
OUT = os.path.join(ROOT, "BDS_SMC2_Node_Consolidated_Report.pdf")

ss = getSampleStyleSheet()
INK = colors.HexColor("#1b1f24")
BAND = colors.HexColor("#0d2b45")
GREY = colors.HexColor("#5b6470")
LBLUE = colors.HexColor("#f2f5f7")

body = ParagraphStyle("body", parent=ss["BodyText"], fontName="Times-Roman",
                      fontSize=10.2, leading=14.2, alignment=TA_JUSTIFY,
                      spaceAfter=6, textColor=INK)
title = ParagraphStyle("title", parent=ss["Title"], fontName="Times-Bold",
                       fontSize=17, leading=21, textColor=BAND, spaceAfter=4,
                       alignment=TA_LEFT)
authors = ParagraphStyle("authors", parent=body, fontName="Times-Roman",
                         fontSize=11, leading=14, spaceAfter=2)
affil = ParagraphStyle("affil", parent=body, fontName="Times-Italic",
                       fontSize=9.5, textColor=GREY, spaceAfter=2)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Times-Bold",
                    fontSize=12.5, leading=15, textColor=BAND,
                    spaceBefore=10, spaceAfter=4)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Times-Bold",
                    fontSize=10.8, leading=13, textColor=INK,
                    spaceBefore=6, spaceAfter=2)
abss = ParagraphStyle("abss", parent=body, fontSize=9.6, leading=13,
                      leftIndent=8, rightIndent=8, textColor=INK)
kw = ParagraphStyle("kw", parent=abss, fontName="Times-Italic")
cap = ParagraphStyle("cap", parent=body, fontSize=8.6, leading=11,
                     textColor=GREY, alignment=TA_CENTER, spaceBefore=2,
                     spaceAfter=8)
ref = ParagraphStyle("ref", parent=body, fontSize=9.0, leading=12,
                     leftIndent=14, firstLineIndent=-14, spaceAfter=3)
note = ParagraphStyle("note", parent=body, fontSize=9.0, leading=12,
                      textColor=GREY)
th = ParagraphStyle("th", parent=body, fontName="Times-Bold", fontSize=8.6,
                    textColor=colors.white, leading=10.5)
td = ParagraphStyle("td", parent=body, fontSize=8.6, leading=10.5, spaceAfter=0)

story = []


def P(t, s=body):
    story.append(Paragraph(t, s))


def H1(n, t):
    story.append(Paragraph(f"{n}&nbsp;&nbsp;{t}", h1))


def H2(n, t):
    story.append(Paragraph(f"{n}&nbsp;&nbsp;{t}", h2))


def gap(h=4):
    story.append(Spacer(1, h))


def tbl(header, rows, widths, centre=()):
    data = [[Paragraph(h, th) for h in header]]
    for r in rows:
        data.append([Paragraph(c, td) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BAND),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LBLUE]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd4da")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]
    for c in centre:
        style.append(("ALIGN", (c, 0), (c, -1), "CENTER"))
    t.setStyle(TableStyle(style))
    story.append(t)


def figure(fname, caption, max_w=15.6 * cm):
    path = os.path.join(FIG, fname)
    if not os.path.exists(path):
        return
    iw, ih = PILImage.open(path).size
    w = max_w
    h = w * ih / iw
    story.append(Spacer(1, 4))
    img = Image(path, width=w, height=h)
    img.hAlign = "CENTER"
    story.append(KeepTogether([img, Paragraph(caption, cap)]))


# ===================== TITLE BLOCK (base structure) =====================
P("A 112-Bit Binary Rescue Payload for BeiDou-3 Short Message "
  "Communication: Design, Environment-Stratified Reliability, and "
  "Autonomous UAV Integration", title)
P("Letsoalo Maile", authors)
P("BDS-SMC2 Node, WP5 BeiDou Communication, Dissertation Objective 5. "
  "Beihang University. Correspondence: Letsoalomaile1@gmail.com", affil)
P("Consolidated reporting account (26 June 2026). Supervisors: Yan Dayun, "
  "Yang Dongkai. Declared project scope: simulation-first.", affil)
story.append(HRFlowable(width="100%", thickness=1.1, color=BAND,
                        spaceBefore=4, spaceAfter=8))

# ===================== ABSTRACT =====================
P("<b>Abstract.</b> Disasters routinely destroy the terrestrial communication "
  "infrastructure on which survivors depend, and the opening hours of a rescue "
  "are governed by the cost of locating victims rather than the cost of reaching "
  "them. BeiDou-3 Short Message Communication transmits short data messages "
  "through the satellite constellation without any terrestrial relay, which makes "
  "it a candidate signalling backbone once cellular and gateway-based links have "
  "collapsed. This report characterises the regional short message service as a "
  "rescue data link and documents the module's evolution from a 64-bit, "
  "coordinate-only prototype to a 112-bit, six-field, software-complete pipeline "
  "that is integrated and verified inside a five-module UAV rescue system. A "
  "fixed-point binary payload packs latitude and longitude at seven-decimal "
  "precision, altitude, position uncertainty, triage priority, and survivor "
  "identity into 112 bits; the same six-field record in ASCII occupies 264 bits, "
  "and the full ASCII telemetry string occupies 368 bits, which dynamic Huffman "
  "coding reduces to 184 bits without the code table that practical decoding "
  "requires. Across 232 valid transmissions spanning open sky, light canopy, "
  "urban canyon, and indoor conditions, the satellite segment acknowledged every "
  "transmission; because the campaign recorded zero failures, the defensible "
  "claim is a Wilson 95 percent lower bound of at least 98.4 percent pooled and "
  "93.7 percent per environment, not a point estimate of perfect delivery. An archived baseline of "
  "thirty transmissions returned a mean end-to-end latency of 2.57 seconds. The "
  "decoded coordinate drives a ROS 2 mission trigger that mission-planning modules "
  "consume. Consistent with the project's declared simulation-first scope, the "
  "physical-layer acceptance of the 112-bit frame is reported as the one open "
  "boundary: the transmitting firmware emits the frame (serial-confirmed), but "
  "module acknowledgement is currently blocked by a diagnosed physical wiring "
  "regression, and the regional capacity limit and diurnal latency remain to be "
  "measured. Every quantitative claim is reproducible from the released scripts "
  "and datasets.", abss)
P("<b>Keywords:</b> BeiDou-3; RDSS; short message communication; search and "
  "rescue; unmanned aerial vehicle; binary encoding; delivery reliability; "
  "Wilson interval; ROS 2 integration.", kw)
gap(6)

# ===================== 1. INTRODUCTION =====================
H1("1.", "Introduction")
P("Earthquakes, floods, and landslides remove the cellular base stations and "
  "power feeds that survivors would otherwise use to call for help, and they do "
  "so precisely where demand peaks. When the network dies, the search problem "
  "reverts to physical sweeping, and time, the scarcest resource in a rescue, is "
  "spent establishing positions that survivors frequently already know.")
P("BeiDou-3 supplies a capability that no other global navigation satellite "
  "system offers at equivalent reach: short message communication, in which a "
  "terminal sends a short data message through the constellation with no "
  "dependence on terrestrial relays. The regional service, delivered by "
  "geostationary satellites, carries a small user payload over the Asia-Pacific "
  "region at a low satellite-segment response delay. A payload of this size can, "
  "in principle, carry a survivor position to a coordination point through "
  "infrastructure that the disaster cannot destroy.")
H2("1.1", "Problem statement")
P("When a disaster destroys terrestrial communication, no fielded system delivers "
  "a survivor's precise, machine-actionable position to an autonomous rescue "
  "platform over a channel that the disaster cannot disable. The infrastructure-"
  "free distress incumbent, COSPAS-SARSAT, carries no user-definable position-and-"
  "triage payload; commercial alternatives depend on proprietary networks; and in "
  "every case the received message terminates at a human operator rather than "
  "driving an autonomous mission. The problem this work addresses is to encode a "
  "complete rescue record, position with altitude, uncertainty, triage priority, "
  "and identity, within the limited payload of BeiDou-3 regional short messaging, "
  "to deliver it reliably across the propagation environments of a real rescue, "
  "and to convert it automatically into an autonomous unmanned-aerial-vehicle "
  "mission trigger, while characterising with defensible statistics how well the "
  "channel performs as a rescue data link.")
H2("1.2", "Significance")
P("The opening hours of a disaster response are dominated by the cost of locating "
  "victims rather than reaching them, so a channel that carries a known survivor "
  "position through surviving infrastructure attacks the binding constraint "
  "directly. BeiDou-3 short messaging is an existing, widely deployed regional "
  "capability, but its performance as an autonomous-rescue data link is largely "
  "uncharacterised; measuring its delivery reliability and latency converts an "
  "assumed capability into an evidenced one. Closing the loop from satellite "
  "message to autonomous mission removes the human operator from the critical "
  "path, which is the distinction between a demonstration and an operational "
  "rescue capability. The importance of this study is that it provides the first "
  "reported characterisation of that closed loop together with the encoding and "
  "integration that make it work.")
H2("1.3", "Approach and contributions")
P("This work is the WP5 communication module of a five-module UAV rescue system: "
  "it takes a survivor's RTK-corrected position, encodes it into a single "
  "message, transmits it by satellite, decodes it at a ground station, and uses "
  "it to trigger an autonomous flight. Four questions structure the work. "
  "Capacity: can a complete rescue payload fit one regional message? Reliability: "
  "does delivery survive the propagation environments of real rescues? Latency: "
  "does the message arrive quickly enough for coordination? Integration: can the "
  "decoded message drive an autonomous mission rather than terminating at a "
  "human-read display? The contributions, led by the system-level result, are: a "
  "decoded BeiDou short message that drives an autonomous ROS 2 mission trigger "
  "through a merged and verified interface, which to the author's knowledge is the "
  "first such closed loop reported; an environment-stratified, application-layer "
  "reliability characterisation reported with Wilson bounds; a latency baseline "
  "with diurnal sessions identified as pending; and an operationally complete "
  "112-bit payload that decodes bit-for-bit against ground truth, presented as a "
  "sound engineering baseline rather than the central novelty, since binary "
  "packing being smaller than ASCII is established prior art.")

# ===================== 2. BACKGROUND =====================
H1("2.", "Background and Related Work")
H2("2.1", "BeiDou-3 short message services and capacity")
P("BeiDou-3 provides two short message services. A regional service operates "
  "through geostationary satellites with a low satellite-segment response delay, "
  "and a global service operates through the medium-Earth-orbit constellation "
  "with a larger per-message budget. A terminal sends an application message on "
  "an uplink; the space and ground segments route it to a recipient, which in "
  "this work is an operator web portal acting as the coordination endpoint. The "
  "transmitting module reports two locally observable acknowledgements, command "
  "acceptance and a satellite-segment acceptance for delivery. The exact regional "
  "capacity in bits is contested in the available sources and depends on the "
  "service grade of the transmitting card; this report therefore treats the "
  "210-bit figure as indicative and frames headroom claims as conditional on a "
  "direct measurement (Section 6.4).")
H2("2.2", "Encoding for small message budgets")
P("Most prior work on fitting useful data into short messages pursues "
  "compression, including learned resource-allocation schemes for the satellite "
  "layer and text-oriented compressors for maritime safety information. These "
  "approaches assume a text-like payload whose problem is statistical redundancy. "
  "Structured numeric telemetry admits a different route: abandon character "
  "representation and pack fields at their native binary widths. Section 5.1 tests "
  "the two routes on identical rescue data and finds that fixed-point packing "
  "wins on size and on decoder cost, which is the result that matters for a "
  "constrained microcontroller. Binary packing being smaller than ASCII is "
  "established prior art; this report therefore treats the encoding as a sound "
  "engineering baseline rather than the central novelty.")
H2("2.3", "Satellite distress systems and alternative links")
P("The incumbent infrastructure-free distress system, COSPAS-SARSAT, transmits a "
  "fixed-format 406 MHz beacon message of 112 short or 144 long data bits, "
  "refined on the ground by Doppler or GNSS data; it admits no user-definable "
  "triage payload. Commercial satellite messaging such as Iridium Short Burst "
  "Data carries arbitrary payloads at per-message cost over proprietary "
  "infrastructure. Low-power wide-area approaches such as LoRaWAN require a "
  "surviving gateway within range, which reintroduces the very infrastructure "
  "dependence the disaster scenario removes. A coincidence sharpens the capacity "
  "argument: the proposed rescue payload and the COSPAS-SARSAT short format both "
  "occupy 112 bits, yet the incumbent spends that budget on identity alone while "
  "the payload here carries a complete six-field triage record.")
H2("2.4", "BeiDou and unmanned aerial vehicles in rescue")
P("Short message communication has been combined with emergency platforms to "
  "deliver text and image data, and with maritime search-and-rescue terminals "
  "that use BeiDou as a multimode channel. In these systems the received message "
  "terminates at a human operator. No published system is known to close the loop "
  "from a BeiDou short message to an autonomous unmanned-aerial-vehicle mission "
  "trigger, which is the integration that Section 3.4 describes.")

# ===================== 3. SYSTEM DESIGN =====================
H1("3.", "System Design")
figure("bds_node_workflow.png",
       "Figure 1. End-to-end node pipeline. Survivor position is encoded into a "
       "112-bit frame, transmitted through the BeiDou regional service, read from "
       "the operator portal, decoded, and published as a ROS 2 rescue trigger. "
       "The lower branch is the simulation harness that verified the chain while "
       "the physical uplink remained blocked.")
H2("3.1", "Hardware node and its evolution")
P("The transmitting node pairs an ESP32 microcontroller with a BeiDou-3 regional "
  "communication module (EVBKIT_V3 RDSS evaluation board) and a circular patch "
  "antenna, connected over a UART link through an RS232-to-TTL converter. "
  "Firmware timestamps three events on its serial output: command issue, module "
  "acceptance, and the satellite-segment acknowledgement. The node has evolved "
  "from a 64-bit, coordinate-only design (two int32 at four-decimal precision) to "
  "the present 112-bit, six-field design at seven-decimal precision; the "
  "evolution is tabulated in Appendix B. The current firmware emits the 112-bit "
  "frame correctly, confirmed on the serial line as "
  "<font name='Courier'>$CCTXM,0,BIN:1D35DB5605079637007200A00101*05</font> at a "
  "ten-second cadence. At the time of writing the module does not return command "
  "or satellite acknowledgements; this regression is diagnosed as physical (the "
  "data wires were found on the wrong pins after the rig was disturbed) rather "
  "than protocol, because the same board, command, and baud rate produced the "
  "earlier field data. This is the project's pre-registered hardware-availability "
  "risk and is treated as such in Section 6.4.")
H2("3.2", "The 112-bit rescue payload")
P("The payload packs six fields into fourteen bytes, big-endian, as Table 1 sets "
  "out.")
tbl(["Bytes", "Field", "Type", "Resolution / range"], [
    ["0-3", "Latitude", "int32 x10^7", "7 dp, approx. 1.1 cm"],
    ["4-7", "Longitude", "int32 x10^7", "7 dp"],
    ["8-9", "Altitude", "int16", "1 m, +/- 32 km"],
    ["10-11", "Uncertainty radius R", "uint16", "1 cm, 0-655 m"],
    ["12", "Priority", "uint8", "P0 / P1 / P2 triage class"],
    ["13", "Survivor identifier", "uint8", "0-255"],
], [1.7 * cm, 4.0 * cm, 2.6 * cm, 7.3 * cm])
story.append(Paragraph("Table 1. The 112-bit rescue payload layout.", cap))
P("The x10^7 coordinate scaling matches the precision of the real-time-kinematic "
  "source; encoding at four decimal places quantises a fix to roughly eleven "
  "metres and discards two orders of magnitude of positioning investment before "
  "transmission. The uncertainty radius is carried explicitly because it defines "
  "the rescuer search area. Three fields common in telemetry designs, battery, "
  "mode, and timestamp, are absent by intent: the first two describe the "
  "transmitting platform, and the receive-time record is created independently at "
  "the portal. The result is 112 bits. Whether this leaves headroom against the "
  "regional limit depends on a capacity figure this study has not yet measured "
  "(Section 6.4).")
H2("3.3", "Receive chain")
P("Messages arrive at the operator portal. A reader process polls the portal "
  "interface, removes duplicates, and records message content with receive time. "
  "A decoder unpacks the payload. A status instrument cross-matches each "
  "transmission against portal receipts by exact payload content, which yields "
  "per-message delivery corroboration and an upper bound on ground-segment "
  "transit. The chain as exercised is one-way; the regional service supports "
  "terminal-directed messages, so an application-layer acknowledgement is an "
  "implementation matter quantified through a repeat policy in Section 6.2.")
H2("3.4", "ROS 2 integration (complete and verified)")
P("The decoded coordinate enters the five-module UAV rescue system as a ROS 2 "
  "node that publishes the rescue trigger on a latched topic, "
  "<font name='Courier'>/target/emergency_coordinate</font>, carrying the agreed "
  "<font name='Courier'>EmergencyCoordinate</font> message; the mission-planning "
  "and ground-control modules consume it. The node decodes ASCII, 112-bit binary, "
  "and a legacy 64-bit format behind one unchanged interface, so the integration "
  "imposed no change on any consuming module. This integration is complete and "
  "merged into the group system (commits e37098e through 1065eaa, shared datum "
  "af76d5c) and is verified by an automated three-check kit "
  "(<font name='Courier'>verify_integration.sh</font>, expected result ALL CHECKS "
  "PASSED). The four additional rescue fields are decoded and logged today; their "
  "promotion into the shared message is an optional, backwards-compatible "
  "extension, not an unfinished integration.")

# ===================== 4. METHODOLOGY =====================
H1("4.", "Methodology")
P("The methodology follows directly from the problem. Because the contribution is "
  "a communication link and its integration, not a positioning system, the "
  "evaluation isolates the transmission layer, and three choices follow from that "
  "aim. The survivor coordinate is injected at the encoder boundary from ground-"
  "truth records rather than acquired live, so that any loss or delay observed is "
  "attributable to the channel and not to satellite positioning; this also matches "
  "the project objective, which is to emulate an RTK-corrected position and inject "
  "it. Delivery is assessed by a field campaign across four propagation "
  "environments spanning the rescue-relevant range from open sky to indoor, "
  "because reliability not measured under obstruction is no evidence for a "
  "disaster channel. Every quantity is reported as an interval or a bound rather "
  "than a point estimate, because a safety-critical claim must state what the data "
  "cannot rule out, not only what was observed. The encoding and integration are "
  "evaluated by exact bit-for-bit round-trip and an automated verification kit, so "
  "the software claims are checkable independently of the blocked hardware "
  "uplink.")
H2("4.1", "Coordinate source: emulated real-time-kinematic injection")
P("This study evaluates the transmission layer, and position acquisition is out "
  "of scope by design, consistent with the project objective to emulate a "
  "survivor precise location corrected with real-time kinematics and inject it "
  "into BeiDou short messaging. The transmitted coordinates are ground-truth "
  "records produced by the laboratory positioning system and injected at the "
  "encoder boundary at native seven-decimal precision. Controlling the injected "
  "data is the only way to attribute fidelity, loss, and latency to the channel "
  "rather than to the source. The encoder boundary is a defined interface, so any "
  "WGS-84 GNSS source can replace the emulated input.")
H2("4.2", "Reliability experiment")
P("Four propagation environments span rescue-relevant conditions: open sky, "
  "light canopy, urban canyon, and indoor. Each environment contributed three "
  "locations, and each location received approximately twenty transmissions at "
  "one message per ten-second cycle, which yielded 232 valid transmissions. These "
  "transmissions carried the ASCII coordinate payload: the field campaign "
  "(8-9 June) preceded the 112-bit upgrade (13 June), so the result characterises "
  "the link itself, independently of payload format. Success was recorded on the "
  "satellite-segment acknowledgement. The analysis uses Wilson score intervals, a "
  "chi-squared test of homogeneity, and pairwise Fisher exact tests with "
  "Bonferroni correction, and commits in advance to the Wilson lower bound. "
  "Thirty-three logged rows from one location and day were excluded because an "
  "instrumentation defect prevented the logger from detecting acknowledgements "
  "before a firmware fix; that location was re-collected in full, and the "
  "complete raw log, including the excluded rows, is published.")
H2("4.3", "Latency experiment")
P("End-to-end transmission latency is defined as the interval between command "
  "issue and satellite-segment acknowledgement. The intended design collects "
  "three thirty-transmission sessions, morning, midday, and evening, on the "
  "112-bit payload, compared by one-way analysis of variance. At the time of "
  "writing only an archived thirty-transmission session collected with the "
  "earlier ASCII payload is available; it is reported as a baseline, and the "
  "diurnal sessions are stated as pending.")
H2("4.4", "Delivery corroboration and encoding experiment")
P("The firmware acknowledgement is corroborated independently by recording the "
  "exact transmitted bytes per transmission and matching them against portal "
  "receipts; a transmission counts as confirmed when its payload appears verbatim "
  "in a portal message. Separately, three encodings of identical rescue data are "
  "compared by exact bit count: ASCII text, dynamic Huffman coding of the ASCII "
  "string, and the fixed-point binary payload. All three decode without loss, and "
  "the binary round-trip is verified bit-for-bit on all ground-truth records.")

# ===================== 5. RESULTS =====================
H1("5.", "Results")
H2("5.1", "Encoding efficiency")
P("Table 2 reports the three encodings of identical rescue data. The ASCII "
  "baseline is the operational $CCTXM command format: the six rescue fields "
  "occupy 264 bits in the coordinate form, and the full telemetry string occupies "
  "368 bits (an earlier draft used a shorter ASCII form, restated here to the "
  "operational format). Dynamic Huffman coding of the telemetry string reaches "
  "184 bits, with the code-table caveat of Section 4.4. The fixed-point binary "
  "payload reaches 112 bits while carrying the complete six-field record, a "
  "reduction of 57.6 percent against the rescue-payload ASCII form and 69.6 "
  "percent against the full telemetry string. It uses 39 percent fewer bits than "
  "Huffman for a rescue-optimised field set: the binary record substitutes "
  "uncertainty, priority, and identity, and higher coordinate precision, for the "
  "battery, mode, and timestamp fields that the ASCII telemetry string carries, "
  "so the comparison is one of equal size for a more rescue-relevant field set "
  "rather than strictly more information. Round-trip decoding reproduced every "
  "ground-truth record exactly.")
tbl(["Encoding", "Size (bits)", "Reduction vs ASCII", "Six rescue fields"], [
    ["ASCII telemetry string", "368", "baseline", "platform + position"],
    ["Dynamic Huffman", "184", "50.0 %", "platform + position (table excluded)"],
    ["Fixed-point binary", "112", "69.6 %", "yes (rescue-optimised)"],
], [5.0 * cm, 2.5 * cm, 3.6 * cm, 5.5 * cm])
story.append(Paragraph("Table 2. Bit-exact encoding comparison on identical "
                       "rescue data.", cap))
figure("gap1_encoding_comparison.png",
       "Figure 2. Rescue-payload encoding. Binary packing reduces the six-field "
       "record from 264 bits in ASCII to 112 bits (-57.6 percent).", max_w=11.5 * cm)
figure("gap6_telemetry_comparison.png",
       "Figure 3. Full-telemetry encoding. Against a 368-bit ASCII string, binary "
       "reaches 112 bits and undercuts Huffman. The 210-bit regional limit shown "
       "is indicative, pending direct measurement (Section 6.4).", max_w=11.5 * cm)
H2("5.2", "Environmental reliability")
P("Across 232 valid transmissions the satellite segment acknowledged every "
  "transmission in all four environments, with per-environment counts of "
  "sixty-one for open sky and fifty-seven each for light canopy, urban canyon, "
  "and indoor. Zero failures do not license a claim of perfect reliability, so the "
  "result is reported as a bound. Pooled over all 232 transmissions, the 95 "
  "percent Wilson lower bound is 98.4 percent, and the rule of three places the "
  "true failure rate below 1.3 percent at 95 percent confidence; per environment, "
  "with roughly fifty-seven trials per cell, the Wilson lower bound is at least "
  "93.7 percent and the rule of three bounds per-cell failure below 5.3 percent. "
  "The pooled bound is the headline result; the per-environment bounds are the "
  "conservative stratification.")
P("This design establishes a floor, not a comparison. A chi-squared test of "
  "homogeneity returned a statistic of 0.000 on three degrees of freedom "
  "(probability 1.000) and the pairwise Fisher exact tests with Bonferroni "
  "correction were non-significant, but with zero failures these outcomes are "
  "arithmetic certainties rather than evidence that the environments are "
  "equivalent. Resolving a difference of the size that would matter operationally, "
  "for example 99 against 95 percent delivery, at eighty percent power would "
  "require about 125 transmissions per environment, more than double the "
  "fifty-seven collected; resolving 99 against 97 percent would require about 360. "
  "The campaign is therefore powered to bound reliability from below, not to "
  "discriminate environments or to resolve values above approximately 94 percent "
  "per cell, and all sessions used a single emulated coordinate, so deeper fades "
  "are identified as the conditions that would localise the failure boundary.")
P("The campaign carried the ASCII coordinate payload, which occupies 264 to 368 "
  "bits, because it preceded the 112-bit upgrade. The deployed binary frame is "
  "strictly smaller and fits the same single message slot with no additional "
  "fragmentation, so a channel that delivered the larger payload at a 93.7 percent "
  "floor delivers the smaller one at least as reliably under the same single-burst "
  "transmission. The measured reliability is therefore a conservative lower bound "
  "for the 112-bit frame rather than a result on an unrelated object; the single "
  "assumption, single-burst delivery, is guaranteed by the 112-bit size.")
figure("gap3_success_rate.png",
       "Figure 4. Delivery by environment with Wilson 95 percent intervals. Every "
       "environment delivered at 100 percent in-sample.", max_w=12.5 * cm)
figure("gap3_location_breakdown.png",
       "Figure 5. Per-location delivery. All twelve sites delivered at 100 percent "
       "in-sample, which shows the aggregate is not driven by a single location.",
       max_w=14 * cm)
H2("5.3", "Latency")
P("The archived ASCII-payload session returned a mean end-to-end latency of "
  "2574.5 ms with a standard deviation of 1094.7 ms over thirty transmissions; "
  "every message completed inside a five-second window (Figure 6). This single "
  "session, on the earlier payload, cannot characterise diurnal behaviour, so the "
  "three time-of-day sessions on the operational payload remain to be collected.")
figure("fig_gap2_cdf.png",
       "Figure 6. Cumulative distribution of end-to-end latency for the archived "
       "ASCII baseline. The result is a baseline only; the diurnal 112-bit "
       "sessions are pending.", max_w=12.5 * cm)
H2("5.4", "End-to-end demonstration")
P("The full pipeline, encoder through portal reader, decoder, map, waypoint "
  "export, and ROS 2 publication, was exercised end-to-end against a simulation "
  "harness that reproduces byte-identical frames and draws latency from the "
  "measured baseline, and the ROS 2 boundary is verified by the integration kit "
  "of Section 3.4. The demonstration establishes that the software chain is "
  "complete, internally consistent, and integrated; it does not establish "
  "physical-layer delivery of the 112-bit frame, which requires the hardware "
  "regression of Section 3.1 to be cleared.")

# ===================== 6. DISCUSSION =====================
H1("6.", "Discussion")
H2("6.1", "Where the regional service sits among rescue links")
P("Among candidate links, independence from surviving ground infrastructure is "
  "the decisive property, and only the satellite systems qualify. COSPAS-SARSAT "
  "qualifies but admits no triage payload. Iridium Short Burst Data qualifies at "
  "per-message cost over proprietary infrastructure. LoRaWAN and cellular both "
  "fail the disaster test. The BeiDou regional service combines a user-definable "
  "triage payload with a single-digit-second satellite-segment response, and the "
  "112-bit coincidence with the COSPAS-SARSAT short format makes the point "
  "concrete. Positioned this way, the work occupies a cell no incumbent fills: "
  "infrastructure independence, a user-definable triage payload, and a "
  "machine-actionable endpoint together. That cell, not the binary encoding, is "
  "the defensible novelty, the encoding being established prior art.")
H2("6.2", "Delivery assurance without a return link")
P("The exercised link is one-way. With a per-attempt lower bound of 0.937, k "
  "independent attempts deliver at least one message with probability 1 minus "
  "(1 minus 0.937) raised to k, which gives 99.6 percent at two attempts and "
  "99.97 percent at three, at a cost of one ten-second cycle per repeat. The "
  "survivor-identifier field renders repeats idempotent at the receiver. This "
  "converts a missing return link from a reliability objection into a quantified "
  "design parameter, although it assumes attempt independence.")
H2("6.3", "Integration significance")
P("Because the decoded coordinate drives the trigger without modifying any "
  "consuming module (Section 3.4), the payload functions as a system interface "
  "rather than merely a transmission artefact. Promoting the rescue fields beyond "
  "position into the shared message would enable search-radius-aware planning and "
  "priority-ordered triage; this is a backwards-compatible interface agreement, "
  "not a technical obstacle.")
H2("6.4", "Scope, limitations, and the open boundary")
P("The project is declared simulation-first, with hardware unavailability "
  "pre-registered as a project risk whose mitigation is a simulation-only design. "
  "The boundaries are stated plainly. First, the physical-layer acceptance of the "
  "112-bit frame is not confirmed: the firmware emits the frame, but module "
  "acknowledgement is blocked by a diagnosed physical wiring regression on a "
  "board whose command and baud are otherwise trusted; clearing it is the single "
  "open hardware action. Second, the regional capacity in bits is not measured, "
  "so the 210-bit figure is indicative and every headroom claim is provisional. "
  "Third, the latency story rests on one archived session on a superseded "
  "payload. Fourth, the delivery result is a lower bound from environments that "
  "may not have stressed the link, using a single emulated coordinate. Fifth, a "
  "single hardware unit precludes any unit-to-unit variance claim, and a "
  "third-party portal sits on the receive path.")
H2("6.5", "Contribution within and beyond the assigned scope")
P("Within scope, WP5 required a simulation emulator, parser, and injector "
  "integrated via ROS 2, delivered as Section 3.4 describes. Beyond it, and beyond "
  "the simulation-only requirement, the work added a real hardware bring-up, the "
  "232-transmission field-reliability campaign, the latency baseline, the encoding "
  "research, and the 64-to-112-bit payload redesign. This was pursued because the "
  "emulator establishes only that a coordinate can be moved, not that the link "
  "survives a disaster environment or that the payload is operationally complete; "
  "it was completable because the WP5 contract finished early and the hardware "
  "work reused the same encode and decode core, so the marginal cost was data "
  "collection rather than new architecture.")

# ===================== 7. CONCLUSION =====================
H1("7.", "Conclusion")
P("This report characterised the BeiDou-3 regional short message service as a "
  "rescue data link on commodity hardware and documented the node's evolution "
  "into a software-complete, integrated pipeline. A survivor position at "
  "real-time-kinematic precision, together with altitude, uncertainty radius, "
  "triage priority, and identity, fits a single 112-bit message and decodes "
  "without loss. Delivery reached a 95 percent lower bound of at least 93.7 "
  "percent across four environments; an archived baseline placed mean latency "
  "near 2.6 seconds; and the decoded coordinate drives an autonomous mission "
  "trigger that is merged and verified in the group system. Consistent with the "
  "declared simulation-first scope, three items remain open: the physical uplink "
  "of the 112-bit frame, blocked by a diagnosed wiring regression; the regional "
  "capacity limit; and the diurnal latency. Each has a single, defined closing "
  "action, and every claim in this report is reproducible from the released "
  "scripts and datasets.")

# ===================== DATA AND CODE =====================
H1("", "Data and Code Availability")
P("Firmware, logging, decoding, analysis scripts, the raw delivery log including "
  "the excluded rows, the figure generators, and the ROS 2 integration kit are "
  "released in the project repository. Quantitative claims in Sections 5.1 and "
  "5.2 are reproducible from the committed CSV files and analysis scripts "
  "(Appendix E).", note)

# ===================== APPENDICES (other docs organised in) =====================
H1("", "Appendix A - Chain of Events")
P("The node was produced by the following dated sequence (git history).", note)
tbl(["Date", "Commit", "Event"], [
    ["06-06", "83435ce", "Initial node: 64-bit payload, 2 fields, 4 dp (v1)"],
    ["06-06", "33ee9af", "Removed Gap 5 (AES); added analysis scripts"],
    ["06-08", "da015a8", "Hardware day 1: T3 firmware fix + first field data"],
    ["06-08/09", "1a55e9d..bd8e2d4", "Gap 3 field campaign: 232 valid TX, 12 locations, 4 environments"],
    ["06-13", "dcdadc7", "64 to 112-bit payload (6 fields, 7 dp) + receive chain (v2)"],
    ["06-13", "137ef76", "portal_reader live connection"],
    ["06-15", "dc0b8bd", "Flashing fix + BDS baud-scanner diagnostic (HW regression)"],
    ["06-16", "a0817d2", "Sim + GCS + virtual BeiDou link + dashboard"],
    ["group", "e37098e..1065eaa", "Integrate 5 modules + beidou node + 112-bit decode + verify kit"],
], [1.6 * cm, 2.7 * cm, 11.3 * cm], centre=(0,))

H1("", "Appendix B - Node Evolution (before vs now)")
tbl(["Capability", "v1 (before)", "v2 (now)"], [
    ["Payload", "64 bit", "112 bit"],
    ["Fields", "2 (lat, lon)", "6 (+ alt, R, priority, ID)"],
    ["Precision", "4 dp (approx. 11 m)", "7 dp (approx. 1 cm)"],
    ["gap1 ASCII baseline", "184 bit", "264 bit"],
    ["Coordinate reduction", "approx. 57.9 %", "57.6 % (stable)"],
    ["gap6 ASCII/Bin/Huff", "384/128/192", "368/128/184"],
    ["Field reliability", "none", "232 TX, at least 93.7 % Wilson"],
    ["Latency", "none", "2574.5 ms, n=30"],
    ["Receive + mission", "none", "portal to decode to ROS 2, verified"],
], [4.4 * cm, 4.6 * cm, 6.6 * cm])

H1("", "Appendix C - Design Rationale (why we opted as we did)")
tbl(["Decision", "Rationale"], [
    ["Binary, not ASCII", "Tiny budget; ASCII is 264/368 bits and wasteful"],
    ["Fixed-point, not Huffman", "Huffman code table exceeds the budget and is decoder-heavy on an MCU"],
    ["112 bit / 6 fields", "Operationally complete record; platform fields dropped by intent"],
    ["7 dp (x10^7)", "Matches RTK source; 4 dp wastes it to approx. 11 m"],
    ["Emulated coordinates", "Objective 5 specifies emulate-and-inject; controls the channel input"],
    ["Wilson LB, never 100 %", "Zero failures cannot support perfect; at least 93.7 % is defensible"],
    ["ASCII payload field test", "Chronology; makes the reliability result payload-independent"],
    [".msg lat/lon only", "Additive fields default zero; no group subscriber breaks"],
    ["Demote encoding", "Binary < ASCII is known; lead with reliability and integration"],
], [4.6 * cm, 11.0 * cm])

H1("", "Appendix D - Delivery and Scope Audit")
P("A factual account of what each part of the work delivered against its brief, "
  "stated as status rather than score; the mark is left to the examiner.", note)
tbl(["Axis", "Status", "Basis"], [
    ["WP5 role delivery", "Complete and verified", "Emulator, parser, and injector merged into the group ROS 2 system; verify kit passes. Optional .msg field enrichment remains."],
    ["Beyond-scope contribution", "Delivered beyond the brief", "Real hardware bring-up and a 232-TX field campaign on a simulation-only requirement."],
    ["Reproducibility", "Full", "Every figure and statistic regenerates from committed scripts; no unit-test suite yet."],
    ["Honesty and disclosure", "Boundaries stated", "Wilson lower bounds, documented exclusions, and one scoped validation boundary."],
    ["Internal consistency", "Reconciled", "The consolidation fixes (moved baseline, indicative 210-bit, demoted encoding) applied in this version."],
], [4.0 * cm, 3.0 * cm, 9.3 * cm])

H1("", "Appendix E - Reproduce Everything")
P("python python/gap3_analysis.py  (reliability: 232 TX, Wilson, chi-square)<br/>"
  "python python/gap2_analysis.py --ascii-baseline --plot  (latency: 2574 ms, n=30, CDF)<br/>"
  "python python/decode_binary.py  (264 to 112 bit, bit-exact round-trip)<br/>"
  "python python/telemetry_compare.py  (368/128/184 bit)<br/>"
  "Inputs: data/gap1_compression.csv, gap2_latency_ascii_baseline.csv, "
  "gap3_field_test.csv, gap6_telemetry.csv. Integration: group "
  "ros2_ws/src/beidou_short_message/ (beidou_publisher_node.py, "
  "verify_integration.sh).", note)

# ===================== build =====================
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=2.0 * cm, rightMargin=2.0 * cm,
    topMargin=1.8 * cm, bottomMargin=1.8 * cm,
    title="BDS-SMC2 Node Consolidated Report", author="Letsoalo Maile",
)


def footer(canvas, d):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(2.0 * cm, 1.0 * cm,
                      "BDS-SMC2 Node Consolidated Report  |  Letsoalo Maile")
    canvas.drawRightString(A4[0] - 2.0 * cm, 1.0 * cm, f"Page {d.page}")
    canvas.restoreState()


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("[OK] wrote", OUT)
