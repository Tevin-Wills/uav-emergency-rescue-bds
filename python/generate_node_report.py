"""
generate_node_report.py
Builds BDS_SMC2_Node_Report.pdf — a research-report / paper-style document for
the BDS-SMC2 node. Written to the "Lex" academic style: active voice, no em
dashes, no contractions, varied cadence, only verified references, explicit
statements of what is not yet measured.

Figures and numbers come from the repository's real artefacts (figures/*.png,
gap6_telemetry.csv, gap3 analysis, archived gap2 baseline). Latency beyond the
archived ASCII baseline is NOT fabricated; the document states it as pending.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
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
OUT = os.path.join(ROOT, "BDS_SMC2_Node_Report.pdf")

# ---------- styles ----------
ss = getSampleStyleSheet()
INK = colors.HexColor("#1b1f24")
BAND = colors.HexColor("#0d2b45")
GREY = colors.HexColor("#5b6470")

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
abs = ParagraphStyle("abs", parent=body, fontSize=9.6, leading=13,
                     leftIndent=8, rightIndent=8, textColor=INK)
kw = ParagraphStyle("kw", parent=abs, fontName="Times-Italic")
cap = ParagraphStyle("cap", parent=body, fontSize=8.6, leading=11,
                     textColor=GREY, alignment=TA_CENTER, spaceBefore=2,
                     spaceAfter=8)
ref = ParagraphStyle("ref", parent=body, fontSize=9.0, leading=12,
                     leftIndent=14, firstLineIndent=-14, spaceAfter=3)
note = ParagraphStyle("note", parent=body, fontSize=9.0, leading=12,
                      textColor=GREY)

story = []


def P(text, style=body):
    story.append(Paragraph(text, style))


def H1(n, t):
    story.append(Paragraph(f"{n}&nbsp;&nbsp;{t}", h1))


def H2(n, t):
    story.append(Paragraph(f"{n}&nbsp;&nbsp;{t}", h2))


def gap(h=4):
    story.append(Spacer(1, h))


def figure(fname, caption, max_w=15.6 * cm):
    path = os.path.join(FIG, fname)
    iw, ih = PILImage.open(path).size
    w = max_w
    h = w * ih / iw
    story.append(Spacer(1, 4))
    img = Image(path, width=w, height=h)
    img.hAlign = "CENTER"
    story.append(KeepTogether([img, Paragraph(caption, cap)]))


# ============================ TITLE BLOCK ============================
P("A 112-Bit Binary Rescue Payload over BeiDou-3 Short Message "
  "Communication: Environment-Stratified Reliability, Latency, and "
  "Autonomous UAV Integration", title)
P("Letsoalo Maile", authors)
P("BDS-SMC2 Node, Dissertation Objective 5. Correspondence: "
  "Letsoalomaile1@gmail.com", affil)
story.append(HRFlowable(width="100%", thickness=1.1, color=BAND,
                        spaceBefore=4, spaceAfter=8))

# ============================ ABSTRACT ============================
P("<b>Abstract.</b> Disasters routinely destroy the terrestrial "
  "communication infrastructure on which survivors depend, and the opening "
  "hours of a rescue are governed by the cost of locating victims rather than "
  "the cost of reaching them. BeiDou-3 Short Message Communication transmits "
  "short data messages through the satellite constellation without any "
  "terrestrial relay, which makes it a candidate signalling backbone once "
  "cellular and gateway-based links have collapsed. This study characterises "
  "the regional short message service as a rescue data link and reports three "
  "results obtained on commodity hardware. A fixed-point binary payload packs "
  "six operationally complete rescue fields, latitude and longitude at "
  "seven-decimal precision, altitude, position uncertainty, triage priority, "
  "and survivor identity, into 112 bits; the identical record encoded as ASCII "
  "text occupies 368 bits, and dynamic Huffman coding reaches 184 bits without "
  "the code table that practical decoding requires. Across 232 valid "
  "transmissions spanning open sky, light canopy, urban canyon, and indoor "
  "conditions, the satellite segment acknowledged every transmission; because "
  "the campaign recorded zero failures, the defensible claim is a Wilson "
  "95 percent lower bound of at least 93.7 percent per environment, not a point "
  "estimate of perfect delivery. An archived baseline of thirty transmissions "
  "returned a mean end-to-end latency of 2.57 seconds. The decoded coordinate "
  "drives a ROS 2 mission trigger inside a five-module UAV rescue system. "
  "Several claims, namely the physical-layer acceptance of the 112-bit frame, "
  "the regional capacity limit, and latency stability across the operating day, "
  "remain unverified and are reported as such.", abs)
P("<b>Keywords:</b> BeiDou-3; RDSS; short message communication; search and "
  "rescue; unmanned aerial vehicle; binary encoding; delivery reliability; "
  "Wilson interval.", kw)
gap(6)

# ============================ 1. INTRODUCTION ============================
H1("1.", "Introduction")
P("Earthquakes, floods, and landslides remove the cellular base stations and "
  "power feeds that survivors would otherwise use to call for help, and they "
  "do so precisely where demand peaks. Field accounts of the February 2023 "
  "Turkiye earthquakes record large fractions of the mobile network offline in "
  "the worst-hit provinces, with thousands of base stations damaged and "
  "internet traffic in some areas falling by more than ninety percent [6]. The "
  "operational consequence is direct. When the network dies, the search "
  "problem reverts to physical sweeping, and time, the scarcest resource in a "
  "rescue, is spent establishing positions that survivors frequently already "
  "know.")
P("BeiDou-3 supplies a capability that no other global navigation satellite "
  "system offers at equivalent reach: short message communication, in which a "
  "terminal sends a short data message through the constellation with no "
  "dependence on terrestrial relays [1]. The regional service, delivered by "
  "geostationary satellites, carries a small user payload over the "
  "Asia-Pacific region and exhibits a low response delay at the satellite "
  "segment [2]. A payload of this size can, in principle, carry a survivor "
  "position to a coordination point through infrastructure that the disaster "
  "cannot destroy. The qualifier matters. The service budget is far too small "
  "for conventional text encodings of rescue data, and the behaviour of the "
  "link under the obstructed-sky, urban-canyon, and indoor conditions where "
  "rescues actually occur has not been characterised at the application "
  "layer.")
P("This report asks whether BeiDou-3 short message communication can serve as "
  "the backbone of an autonomous unmanned-aerial-vehicle rescue system, in "
  "which a survivor position is encoded into a single message, transmitted by "
  "satellite, decoded at a ground station, and used to trigger a flight to the "
  "survivor. Four subsidiary questions structure the work. Capacity: can a "
  "complete rescue payload fit a single regional message? Reliability: does "
  "delivery survive the propagation environments of real rescues? Latency: "
  "does the message arrive quickly enough for coordination, and is the timing "
  "stable across the day? Integration: can the decoded message drive an "
  "autonomous mission rather than terminating at a human-read display?")
P("The contributions are four. A 112-bit binary rescue payload carries six "
  "operationally complete fields and decodes bit-for-bit against the "
  "ground-truth records. An environment-stratified, application-layer "
  "measurement of regional delivery reliability spans four propagation "
  "classes across twelve locations and reports Wilson bounds rather than point "
  "estimates. A latency characterisation defines transmission delay between "
  "command issue and satellite acknowledgement, with an archived baseline "
  "reported here and diurnal sessions identified as pending. A decoded "
  "coordinate enters a ROS 2 mission pipeline through an unchanged topic "
  "interface. The novelty claim is deliberately narrow. The system-level "
  "campaign of Li and colleagues established global short message feasibility "
  "at scale [1]; the present work is complementary and application-layer, "
  "treating the regional service specifically as a rescue data link.")

# ============================ 2. BACKGROUND ============================
H1("2.", "Background and Related Work")
H2("2.1", "BeiDou-3 short message services and capacity")
P("BeiDou-3 provides two short message services [1]. A regional service "
  "operates through geostationary satellites with a low satellite-segment "
  "response delay [2], and a global service operates through the "
  "medium-Earth-orbit constellation and its inter-satellite links, with a "
  "larger per-message budget [1]. A terminal sends an application message on "
  "an uplink; the space and ground segments route it to a recipient, which in "
  "this work is an operator web portal acting as the coordination endpoint. "
  "The transmitting module reports two locally observable acknowledgements, "
  "command acceptance and a satellite-segment acceptance for delivery. The "
  "interval between the satellite acknowledgement and ground delivery exposes "
  "no telemetry to the user, so the experimental design treats it as a black "
  "box and measures it externally.")
P("The exact regional capacity in bits is contested in the available sources "
  "and depends on the service grade of the transmitting card [2]. This report "
  "therefore reports the 112-bit payload as an absolute count and frames "
  "headroom claims as conditional on the measured limit. I cannot confidently "
  "verify a single fixed regional capacity from the public literature, and "
  "Section 6 treats this as an open measurement.")
H2("2.2", "Encoding for small message budgets")
P("Most prior work on fitting useful data into short messages pursues "
  "compression, including learned resource-allocation schemes for the "
  "satellite layer [3] and text-oriented compressors for maritime safety "
  "information. These approaches assume a text-like payload whose problem is "
  "statistical redundancy. Structured numeric telemetry admits a different "
  "route: abandon character representation and pack fields at their native "
  "binary widths. Section 5.1 tests the two routes head-to-head on identical "
  "rescue data and finds that fixed-point packing wins on size and on decoder "
  "cost, which is the result that matters for a constrained microcontroller.")
H2("2.3", "Satellite distress systems and alternative links")
P("The incumbent infrastructure-free distress system, COSPAS-SARSAT, transmits "
  "a fixed-format 406 MHz beacon message of 112 short or 144 long data bits, "
  "refined on the ground by Doppler or GNSS data. The format carries beacon "
  "identity and a coarse position; it admits no user-definable triage payload. "
  "Commercial satellite messaging such as Iridium Short Burst Data carries "
  "arbitrary payloads at per-message cost over proprietary infrastructure. "
  "Low-power wide-area approaches such as LoRaWAN carry tens to a few hundred "
  "bytes per uplink but require a surviving gateway within range, which "
  "reintroduces the very infrastructure dependence the disaster scenario "
  "removes. A coincidence sharpens the capacity argument: the proposed rescue "
  "payload and the COSPAS-SARSAT short format both occupy 112 bits, yet the "
  "incumbent spends that budget on identity alone while the payload here "
  "carries a complete six-field triage record.")
H2("2.4", "BeiDou and unmanned aerial vehicles in rescue")
P("Short message communication has been combined with emergency platforms to "
  "deliver text and image data, including an urban emergency picture "
  "transmission mechanism built on BeiDou short messages [4], and with "
  "maritime search-and-rescue terminals that use BeiDou as a multimode "
  "communication channel [5]. In these systems the received message terminates "
  "at a human operator. I have not located a published system that closes the "
  "loop from a BeiDou short message to an autonomous unmanned-aerial-vehicle "
  "mission trigger, which is the integration that Section 3.4 describes.")

# ============================ 3. SYSTEM DESIGN ============================
H1("3.", "System Design")
figure("bds_node_workflow.png",
       "Figure 1. End-to-end node pipeline. Survivor position is encoded into a "
       "112-bit frame, transmitted through the BeiDou regional service, read "
       "from the operator portal, decoded, and published as a ROS 2 rescue "
       "trigger. The lower branch is the simulation harness that verified the "
       "chain while the physical uplink remained unconfirmed.")
H2("3.1", "Hardware node")
P("The transmitting node pairs an ESP32 microcontroller with a BeiDou-3 "
  "regional communication module and a circular patch antenna, connected over "
  "a universal asynchronous receiver-transmitter link through an RS232-to-TTL "
  "converter. Firmware timestamps three events on its serial output: command "
  "issue, module acceptance, and the satellite-segment acknowledgement. A "
  "logging host records the stream. The toolchain depends on the Python "
  "standard library for its analysis path, which supports the reproducibility "
  "goal, and the complete firmware, logging, decoding, and analysis code is "
  "released with this report.")
H2("3.2", "The 112-bit rescue payload")
P("The payload packs six fields into fourteen bytes, big-endian, as Table 1 "
  "sets out.")

t1 = [["Bytes", "Field", "Type", "Resolution / range"],
      ["0-3", "Latitude", "int32 x10^7", "7 dp, approx. 1.1 cm"],
      ["4-7", "Longitude", "int32 x10^7", "7 dp"],
      ["8-9", "Altitude", "int16", "1 m, +/- 32 km"],
      ["10-11", "Uncertainty radius R", "uint16", "1 cm, 0-655 m"],
      ["12", "Priority", "uint8", "P0 / P1 / P2 triage class"],
      ["13", "Survivor identifier", "uint8", "0-255"]]
tbl1 = Table(t1, colWidths=[1.7*cm, 4.0*cm, 2.6*cm, 7.3*cm])
tbl1.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "Times-Bold", 9),
    ("FONT", (0, 1), (-1, -1), "Times-Roman", 9),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d2b45")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd4da")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f7")]),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
]))
story.append(tbl1)
story.append(Paragraph("Table 1. The 112-bit rescue payload layout.", cap))
P("Three design choices need justification. The x10^7 coordinate scaling "
  "matches the precision of the real-time-kinematic source. Encoding at four "
  "decimal places, a common choice in ASCII implementations, quantises a fix "
  "to roughly eleven metres and silently discards two orders of magnitude of "
  "positioning investment before transmission. The uncertainty radius is "
  "carried explicitly because it defines the rescuer search area; a coordinate "
  "without an uncertainty figure is operationally incomplete. Three fields "
  "common in telemetry designs, battery, mode, and timestamp, are absent by "
  "intent: the first two describe the transmitting platform and reach its "
  "operator through richer channels, and the receive-time record is created "
  "independently at the portal. The result is 112 bits. Whether this leaves "
  "headroom against the regional limit depends on a capacity figure that this "
  "study has not yet measured (Section 6).")
H2("3.3", "Receive chain")
P("Messages arrive at the operator portal. A reader process polls the portal "
  "interface, removes duplicates, and records message content with receive "
  "time. A decoder unpacks the payload. A status instrument cross-matches each "
  "transmission against portal receipts by exact payload content, which yields "
  "per-message delivery corroboration and an upper bound on ground-segment "
  "transit. The chain as exercised is one-way. The regional service supports "
  "terminal-directed messages, so an application-layer acknowledgement is an "
  "implementation matter that Section 6 quantifies through a repeat policy "
  "rather than dismisses.")
H2("3.4", "ROS 2 integration")
P("The decoded coordinate enters a five-module unmanned-aerial-vehicle rescue "
  "system as a ROS 2 node that publishes the rescue trigger on a latched "
  "topic, which the mission-planning modules consume. The node decodes ASCII, "
  "112-bit binary, and a legacy 64-bit format behind one unchanged interface, "
  "so the integration imposed no change on any consuming module. This boundary "
  "was exercised against the simulation harness; the physical satellite uplink "
  "for the 112-bit frame is not yet confirmed, which Section 6 states as a "
  "primary limitation.")

# ============================ 4. METHODOLOGY ============================
H1("4.", "Methodology")
H2("4.1", "Coordinate source: emulated real-time-kinematic injection")
P("This study evaluates the transmission layer, and position acquisition is "
  "out of scope by design, consistent with the project objective to emulate a "
  "survivor precise location corrected with real-time kinematics and inject it "
  "into BeiDou short messaging. The transmitted coordinates are ground-truth "
  "records produced by the laboratory positioning system and injected at the "
  "encoder boundary at native seven-decimal precision. Controlling the "
  "injected data is the only way to attribute fidelity, loss, and latency to "
  "the channel rather than to the source. The encoder boundary is a defined "
  "interface, so any WGS-84 GNSS source can replace the emulated input without "
  "firmware changes beyond the injection call.")
H2("4.2", "Reliability experiment")
P("Four propagation environments span rescue-relevant conditions: open sky, "
  "light canopy, urban canyon, and indoor. Each environment contributed three "
  "locations, and each location received approximately twenty transmissions at "
  "one message per ten-second cycle, which yielded 232 valid transmissions. "
  "Success was recorded on the satellite-segment acknowledgement. The analysis "
  "uses Wilson score intervals for per-environment success proportions, "
  "selected over the normal approximation because the observed proportions sit "
  "at the boundary, a chi-squared test of homogeneity across environments, and "
  "pairwise Fisher exact tests with Bonferroni correction. The reporting "
  "commits in advance to the Wilson lower bound rather than the observed point "
  "estimate. Thirty-three logged rows from one location and day were excluded "
  "because an instrumentation defect prevented the logger from detecting "
  "acknowledgements before a firmware fix; that location was re-collected in "
  "full, and the complete raw log, including the excluded rows, is published. "
  "No row carrying a detected acknowledgement was excluded.")
H2("4.3", "Latency experiment")
P("End-to-end transmission latency is defined as the interval between command "
  "issue and satellite-segment acknowledgement. The intended design collects "
  "three thirty-transmission sessions, morning, midday, and evening, at a "
  "fixed location on a single day, all carrying the operational 112-bit "
  "payload, compared by one-way analysis of variance. At the time of writing, "
  "only an archived thirty-transmission session collected with the earlier "
  "ASCII payload is available. That session is reported here as a baseline. "
  "The diurnal sessions on the 112-bit payload are pending, so this report "
  "does not claim time-of-day stability; it states the gap.")
H2("4.4", "Delivery corroboration and black-box transit")
P("The firmware acknowledgement is a necessary but self-reported success "
  "criterion. To corroborate it independently, the exact transmitted bytes are "
  "recorded per transmission and matched against portal receipts. A "
  "transmission counts as confirmed when its payload appears verbatim in a "
  "portal message, which proves end-to-end content integrity through the "
  "satellite segment. The interval between satellite acknowledgement and portal "
  "receipt yields a per-message upper bound on ground-segment transit, a "
  "quantity that no user interface exposes. The portal cross-match was "
  "exercised against the simulation harness and the archived portal capture; "
  "the live field-day confirmation rate is pending.")
H2("4.5", "Encoding experiment")
P("Three encodings of identical rescue data are compared by exact bit count: "
  "ASCII text as the baseline, dynamic Huffman coding of the ASCII string as an "
  "entropy-coding benchmark, and the fixed-point binary payload. All three "
  "decode without loss, and the binary round-trip is verified bit-for-bit on "
  "all ground-truth records. The Huffman benchmark carries an implementation "
  "caveat that bears on deployability: dynamic Huffman must convey its code "
  "table, which itself exceeds the message budget, so the reported figure is a "
  "lower bound that practical decoding cannot reach without a pre-agreed static "
  "table.")

# ============================ 5. RESULTS ============================
H1("5.", "Results")
H2("5.1", "Encoding efficiency")
P("Table 2 reports the three encodings of identical rescue data. ASCII text "
  "requires 368 bits. Dynamic Huffman coding reaches 184 bits, with the code "
  "table caveat of Section 4.5. The fixed-point binary payload reaches 112 "
  "bits while carrying the complete six-field record, a reduction of 57.6 "
  "percent against the rescue-payload ASCII form and 69.6 percent against the "
  "full ASCII telemetry string, and 39 percent fewer bits than Huffman while "
  "conveying strictly more information. Round-trip decoding reproduced every "
  "ground-truth record exactly, which confirms lossless encoding at "
  "seven-decimal coordinate precision.")

t2 = [["Encoding", "Size (bits)", "Reduction vs ASCII", "Carries 6 fields"],
      ["ASCII telemetry string", "368", "baseline", "yes"],
      ["Dynamic Huffman", "184", "50.0 %", "yes (table excluded)"],
      ["Fixed-point binary", "112", "69.6 %", "yes"]]
tbl2 = Table(t2, colWidths=[5.2*cm, 2.6*cm, 4.0*cm, 3.8*cm])
tbl2.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "Times-Bold", 9),
    ("FONT", (0, 1), (-1, -1), "Times-Roman", 9),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d2b45")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd4da")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f7")]),
    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
]))
story.append(tbl2)
story.append(Paragraph("Table 2. Bit-exact encoding comparison on identical "
                       "rescue data.", cap))
figure("gap1_encoding_comparison.png",
       "Figure 2. Rescue-payload encoding. Binary packing reduces the "
       "six-field record from 264 bits in ASCII to 112 bits.", max_w=11.5*cm)
figure("gap6_telemetry_comparison.png",
       "Figure 3. Full-telemetry encoding. Against a 368-bit ASCII string, "
       "binary reaches 112 bits and undercuts Huffman while carrying more "
       "fields.", max_w=11.5*cm)
H2("5.2", "Environmental reliability")
P("Across 232 valid transmissions, the satellite segment acknowledged every "
  "transmission in all four environments, with per-environment counts of "
  "sixty-one for open sky and fifty-seven each for light canopy, urban canyon, "
  "and indoor. Zero failures do not license a claim of perfect reliability. "
  "The defensible statement is the 95 percent Wilson lower bound, at least 93.7 "
  "percent per environment and at least 98.4 percent pooled. A chi-squared test "
  "of homogeneity found no difference among environments, with a statistic of "
  "0.000 on three degrees of freedom and a probability of 1.000; pairwise "
  "Fisher exact tests with Bonferroni correction were likewise "
  "non-significant. The correct reading is bounded, not triumphant. Zero "
  "failures in roughly fifty-seven trials per cell bound reliability from "
  "below but cannot distinguish true reliabilities above approximately 94 "
  "percent. The environments tested may not have stressed the link margin, and "
  "deeper fades, in sub-basements, dense reinforced structures, or heavy "
  "precipitation, are identified as the conditions that would localise the "
  "failure boundary.")
figure("gap3_success_rate.png",
       "Figure 4. Delivery by environment with Wilson 95 percent intervals. "
       "Every environment delivered at 100 percent in-sample.", max_w=12.5*cm)
figure("gap3_location_breakdown.png",
       "Figure 5. Per-location delivery. All twelve sites delivered at 100 "
       "percent in-sample, which shows the aggregate is not driven by a single "
       "location.", max_w=14*cm)
H2("5.3", "Latency")
P("The archived ASCII-payload session returned a mean end-to-end latency of "
  "2574.5 ms with a standard deviation of 1094.7 ms over thirty transmissions. "
  "Figure 6 shows the cumulative distribution; every message in this baseline "
  "completed inside a five-second window. This single session is insufficient "
  "to characterise diurnal behaviour, and it was collected on the earlier "
  "payload, so a payload-format difference would confound a direct comparison "
  "with the 112-bit operational frames. The three time-of-day sessions on the "
  "operational payload remain to be collected. I cannot confidently report a "
  "time-of-day effect, a 112-bit latency distribution, or a field-day "
  "confirmation rate until that data exists.")
figure("fig_gap2_cdf.png",
       "Figure 6. Cumulative distribution of end-to-end latency for the "
       "archived ASCII baseline. The result is a baseline only; the diurnal "
       "112-bit sessions are pending.", max_w=12.5*cm)
H2("5.4", "End-to-end demonstration")
P("The full pipeline, encoder through portal reader, decoder, map, waypoint "
  "export, and ROS 2 publication, was exercised end-to-end against a "
  "simulation harness that reproduces byte-identical frames and draws latency "
  "from the measured baseline. The demonstration establishes that the software "
  "chain is complete and internally consistent. It does not establish "
  "physical-layer delivery of the 112-bit frame, which requires hardware "
  "confirmation.")

# ============================ 6. DISCUSSION ============================
H1("6.", "Discussion")
H2("6.1", "Where the regional service sits among rescue links")
P("Among candidate links, independence from surviving ground infrastructure is "
  "the decisive property, and only the satellite systems qualify. COSPAS-"
  "SARSAT qualifies but admits no triage payload. Iridium Short Burst Data "
  "qualifies at per-message cost over proprietary infrastructure. LoRaWAN and "
  "cellular both fail the disaster test because they assume a surviving "
  "gateway or base station. The BeiDou regional service combines a "
  "user-definable triage payload with a single-digit-second satellite-segment "
  "response. The 112-bit coincidence with the COSPAS-SARSAT short format makes "
  "the point concrete: the same budget that the incumbent spends on identity "
  "carries, here, a complete triage record.")
H2("6.2", "Delivery assurance without a return link")
P("The exercised link is one-way. Without an application-layer "
  "acknowledgement, delivery assurance comes from repetition. With a "
  "per-attempt lower bound of 0.937, k independent attempts deliver at least "
  "one message with probability 1 minus (1 minus 0.937) raised to k, which "
  "gives 99.6 percent at two attempts and 99.97 percent at three, at a cost of "
  "one ten-second cycle per repeat. The survivor-identifier field renders "
  "repeats idempotent at the receiver. This reasoning converts a missing "
  "return link from a reliability objection into a quantified design "
  "parameter, although it assumes attempt independence, which correlated "
  "fading would violate.")
H2("6.3", "Integration significance")
P("That the decoded coordinate drives a ROS 2 trigger without modifying any "
  "consuming module argues that the payload functions as a system interface, "
  "not merely as a transmission artefact. The rescue fields beyond position, "
  "altitude, uncertainty, priority, and survivor identity, are decoded and "
  "logged today. Their promotion into the shared message interface, which "
  "would enable search-radius-aware planning and priority-ordered triage, is a "
  "pending interface agreement rather than a technical obstacle.")
H2("6.4", "Limitations")
P("Honesty requires stating the boundaries plainly. First, the physical-layer "
  "acceptance of the 112-bit frame is not confirmed; bring-up of the hardware "
  "uplink remains unresolved, and the end-to-end results rest on a simulation "
  "harness that reproduces the wire format rather than on a satellite-delivered "
  "112-bit message. Second, the regional capacity in bits is not measured, so "
  "every headroom claim is provisional until a payload-growth test fixes the "
  "limit and the card service grade is recorded. Third, the latency story is "
  "incomplete: one archived session on a superseded payload cannot support a "
  "diurnal-stability claim. Fourth, the delivery result is a lower bound; the "
  "tested environments may not have stressed the link, and the zero-failure "
  "outcome cannot resolve reliabilities above approximately 94 percent. Fifth, "
  "a single hardware unit precludes any unit-to-unit variance claim. Sixth, "
  "the input is emulated rather than live real-time-kinematic position, and a "
  "third-party portal sits on the receive path as a single point of failure "
  "with a manual authentication step.")

# ============================ 7. CONCLUSION ============================
H1("7.", "Conclusion")
P("This report characterised the BeiDou-3 regional short message service as a "
  "rescue data link on commodity hardware. A survivor position at "
  "real-time-kinematic precision, together with altitude, uncertainty radius, "
  "triage priority, and identity, fits a single 112-bit message and decodes "
  "without loss. Delivery reached a 95 percent lower bound of at least 93.7 "
  "percent across open-sky, canopy, urban-canyon, and indoor conditions. An "
  "archived baseline placed mean latency near 2.6 seconds. The decoded "
  "coordinate drives an autonomous mission trigger in software. The four "
  "results are conjunctive in intent: a payload that fits, that arrives where "
  "rescues occur, that arrives in time, and that drives a response. They are "
  "not yet conjunctive in proof, because the physical uplink, the capacity "
  "limit, and the diurnal latency remain open. Closing them, replacing the "
  "emulated position with a live fix, and adding a return link define the next "
  "phase of the work.")

# ============================ DATA AVAILABILITY ============================
H1("", "Data and Code Availability")
P("Firmware, logging, decoding, analysis scripts, the raw delivery log "
  "including the excluded rows, and the figure generators are released in the "
  "project repository. Quantitative claims in Sections 5.1 and 5.2 are "
  "reproducible from the committed CSV files and analysis scripts.", note)

# ============================ REFERENCES ============================
H1("", "References")
refs = [
 "[1] G. Li et al., \"Introduction to the global short message communication "
 "service of BeiDou-3 navigation satellite system,\" Advances in Space "
 "Research, vol. 67, no. 5, pp. 1701-1708, 2021. doi:10.1016/j.asr.2020.12.011.",
 "[2] \"Requirement-Oriented TT&C Method for Satellite Based on BDS-3 "
 "Short-Message Communication System,\" Space: Science & Technology, art. "
 "0038, 2022. doi:10.34133/space.0038. (Open access.)",
 "[3] \"BeiDou Short-Message Satellite Resource Allocation Algorithm Based on "
 "Deep Reinforcement Learning,\" Entropy, vol. 23, no. 8, art. 932, 2021. "
 "doi:10.3390/e23080932. (Open access.)",
 "[4] \"Urban Emergency Picture Transmission Mechanism Based on Beidou Short "
 "Message,\" IEEE Xplore document 10019970. Full bibliographic fields require "
 "confirmation from the official record before citation.",
 "[5] \"Design of BeiDou-based Multimode Communication Maritime Search and "
 "Rescue Terminal,\" IEEE Xplore document 10426479. Full bibliographic fields "
 "require confirmation from the official record before citation.",
 "[6] \"Solutions for Sustainable and Resilient Communication Infrastructure "
 "in Disaster Relief and Management Scenarios,\" arXiv:2410.13977, 2024. "
 "(Open access; source for the Turkiye 2023 base-station failure figures.)",
 "[7] \"GNSS real-time precise point positioning with BDS-3 global short "
 "message communication devices,\" GPS Solutions, 2022.",
]
for r in refs:
    story.append(Paragraph(r, ref))
story.append(Spacer(1, 6))
P("Note on sources. References [1], [2], [3], [6], and [7] were verified "
  "online on 23 June 2026. References [4] and [5] exist on IEEE Xplore under "
  "the stated document numbers, but their author lists, venue names, and years "
  "were not independently confirmed and must be checked before submission. "
  "COSPAS-SARSAT, Iridium, and LoRaWAN are cited as published specifications "
  "rather than as primary articles; the precise specification documents should "
  "be added at assembly. No reference, statistic, or digital object identifier "
  "in this document was fabricated.", note)

# ---------- build ----------
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=2.0*cm, rightMargin=2.0*cm,
    topMargin=1.8*cm, bottomMargin=1.8*cm,
    title="BDS-SMC2 Node Report", author="Letsoalo Maile",
)


def footer(canvas, d):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(2.0*cm, 1.0*cm,
                      "BDS-SMC2 Node Report  |  Letsoalo Maile")
    canvas.drawRightString(A4[0] - 2.0*cm, 1.0*cm, f"Page {d.page}")
    canvas.restoreState()


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"[OK] wrote {OUT}")
