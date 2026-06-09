"""
Generates Glossary of Key Terms PDF for BDS-SMC2 Research Brief.
Run: python generate_glossary.py
Output: BDS_SMC2_Glossary.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import datetime

OUTPUT = "BDS_SMC2_Glossary.pdf"
W, H = A4

DARK  = colors.HexColor("#1a3a5c")
MID   = colors.HexColor("#2e5fa3")
LGRAY = colors.HexColor("#f4f7fb")
BORDER= colors.HexColor("#c8d8ea")
GREEN = colors.HexColor("#1a4d1a")

def S(name, **kw):
    base = dict(fontName="Helvetica", fontSize=10, leading=14,
                textColor=colors.HexColor("#1a1a1a"), alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(name, **base)

TITLE  = S("T",  fontName="Helvetica-Bold", fontSize=20, leading=25,
            textColor=DARK, alignment=TA_CENTER, spaceAfter=4)
SUB    = S("ST", fontSize=10, leading=13, textColor=MID,
            alignment=TA_CENTER, spaceAfter=2)
META   = S("M",  fontSize=8, leading=11, textColor=colors.grey,
            alignment=TA_CENTER)
CAT    = S("CA", fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=colors.white, alignment=TA_LEFT)
TERM   = S("TM", fontName="Helvetica-Bold", fontSize=9.5, leading=13,
            textColor=DARK, alignment=TA_LEFT)
ABBR   = S("AB", fontName="Helvetica-Bold", fontSize=9, leading=13,
            textColor=MID, alignment=TA_CENTER)
DEFN   = S("DF", fontSize=9.5, leading=13, alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#2a2a2a"))

def rule(c=BORDER, t=0.5): return HRFlowable(width="100%", thickness=t, color=c, spaceAfter=6)

def cat_header(label, color):
    tbl = Table([[Paragraph(label, CAT)]], colWidths=[15.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), color),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    return tbl

def entry(term, abbr, definition):
    row = [[
        Paragraph(term, TERM),
        Paragraph(abbr, ABBR),
        Paragraph(definition, DEFN),
    ]]
    tbl = Table(row, colWidths=[4.0*cm, 1.8*cm, 9.7*cm])
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LINEBELOW",     (0,0), (-1,-1), 0.4, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("BACKGROUND",    (0,0), (-1,-1), colors.white),
    ]))
    return KeepTogether([tbl])

def header_row():
    tbl = Table([[
        Paragraph("Term", S("H", fontName="Helvetica-Bold", fontSize=9,
                             textColor=colors.white, alignment=TA_LEFT)),
        Paragraph("Abbr.", S("H", fontName="Helvetica-Bold", fontSize=9,
                              textColor=colors.white, alignment=TA_CENTER)),
        Paragraph("Definition", S("H", fontName="Helvetica-Bold", fontSize=9,
                                   textColor=colors.white, alignment=TA_LEFT)),
    ]], colWidths=[4.0*cm, 1.8*cm, 9.7*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), DARK),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    return tbl

# ── GLOSSARY ENTRIES ──────────────────────────────────────────────────────────

sections = [

    ("BDS-3 System & Protocol",
     colors.HexColor("#1a3a5c"),
     [
        ("BeiDou Navigation\nSatellite System",
         "BDS / BDS-3",
         "China's independently developed global navigation satellite system. BDS-3 "
         "achieved global operational status on 31 July 2020. Unlike GPS, GLONASS, or "
         "Galileo, BDS-3 includes a built-in two-way messaging capability called Short "
         "Message Communication (SMC)."),

        ("Short Message\nCommunication",
         "SMC",
         "The two-way messaging service built into BDS-3. Allows a user terminal to "
         "transmit a short data payload (text, coordinates, telemetry) to a ground "
         "control centre via satellite and receive a response — without any terrestrial "
         "network infrastructure."),

        ("Radio Determination\nSatellite Service",
         "RDSS",
         "The active two-way positioning and messaging protocol used by BDS. The user "
         "terminal transmits an uplink signal; the satellite relays it to the Ground "
         "Control Centre (GCC), which computes the user's position and returns it via "
         "downlink. Unlike passive GNSS (GPS), RDSS is bidirectional."),

        ("Regional Short Message\nCommunication",
         "RSMC",
         "The high-capacity BDS-3 SMC service served by three Geostationary (GEO) "
         "satellites covering the Asia-Pacific region. Supports up to 14,000 bits "
         "(≈ 1,000 Chinese characters) per message with ≤ 1-second round-trip latency. "
         "Used in this experiment."),

        ("Global Short Message\nCommunication",
         "GSMC",
         "The global BDS-3 SMC service served by 14 Medium Earth Orbit (MEO) satellites. "
         "Provides worldwide coverage but is limited to 560 bits (≈ 40 Chinese characters) "
         "per message — making payload efficiency critical for multi-field telemetry."),

        ("Ground Control Centre",
         "GCC",
         "The ground-based facility that processes RDSS uplink signals from user "
         "terminals. The GCC measures signal time-of-flight from two or more GEO "
         "satellites plus a Digital Elevation Model (DEM) to compute the terminal's "
         "2D+altitude position, then returns it via the satellite downlink."),

        ("Geostationary\nEarth Orbit Satellite",
         "GEO",
         "A satellite positioned at approximately 35,786 km altitude that remains "
         "stationary relative to Earth. BDS-3 uses three GEO satellites (C59, C60, C61) "
         "for RSMC service. From Hangzhou, these appear in the southern sky at "
         "elevations of approximately 38–52°."),

        ("Medium Earth\nOrbit Satellite",
         "MEO",
         "Satellites orbiting at approximately 19,000–24,000 km altitude. BDS-3 uses "
         "14 MEO satellites for GSMC global coverage. MEO satellites provide better "
         "geometric diversity than GEO but at lower per-satellite processing capacity."),

        ("$CCTXM Command",
         "AT Cmd",
         "The NMEA-style AT command used to trigger a BDS-3 short message transmission. "
         "Format: $CCTXM,<destID>,<payload>*<XOR_checksum>\\r\\n. A destination ID of 0 "
         "routes the message to the GCC relay for forwarding to the web platform."),

        ("XOR Checksum",
         "CS",
         "A simple error-detection value computed by XOR-ing all characters between "
         "the $ and * in an NMEA-style command. Used to detect transmission corruption "
         "between the ESP32 and the BDS module over the UART connection."),
    ]),

    ("Encoding & Compression",
     colors.HexColor("#1a4d1a"),
     [
        ("ASCII Encoding",
         "ASCII",
         "American Standard Code for Information Interchange. Represents each character "
         "as 8 bits. Default format for coordinate transmission: "
         "LAT:30.4196,LON:120.2977 uses approximately 208 bits — a 69% overhead "
         "compared to binary encoding of the same data."),

        ("Binary Fixed-Point\nEncoding",
         "BIN",
         "A compact coordinate representation where latitude and longitude are each "
         "multiplied by 10,000 and stored as signed 32-bit integers. Preserves 4 "
         "decimal place precision (±11 m accuracy) in exactly 64 bits total — "
         "a 69% reduction vs ASCII."),

        ("Huffman Encoding",
         "HUF",
         "A lossless data compression algorithm that assigns shorter bit codes to more "
         "frequently occurring characters. In this project, a dynamic Huffman tree is "
         "built at runtime from the character frequency distribution of the telemetry "
         "string, achieving up to 77% reduction vs ASCII."),

        ("Payload",
         "—",
         "The actual data content carried inside a BDS-3 SMC message — the coordinate, "
         "telemetry fields, or encrypted bytes. Distinguished from the message overhead "
         "(command header, checksum, framing) which is transmitted but carries no "
         "information."),

        ("Bit Budget",
         "—",
         "The maximum number of bits available for the payload in a single BDS-3 SMC "
         "message. RSMC: 14,000 bits. GSMC: 560 bits. Efficient encoding maximises "
         "the information that can be transmitted within this fixed limit."),

        ("Fixed-Point Arithmetic",
         "—",
         "A method of representing decimal numbers as integers by scaling them by a "
         "fixed factor. Example: 30.4196° × 10,000 = 304,196 stored as an integer. "
         "Avoids floating-point format overhead while preserving the required precision."),

        ("Telemetry",
         "—",
         "A structured set of measurement fields transmitted from the rescue terminal "
         "to the ground station. In this project: latitude, longitude, altitude, "
         "battery percentage, mode, flags, and timestamp — 7 fields total."),

        ("Message Fragmentation",
         "—",
         "The splitting of a payload that exceeds the single-message bit limit into "
         "multiple sequential messages. BDS-3 has no native fragment reassembly "
         "protocol — if any fragment is lost, the entire payload is unrecoverable."),
    ]),

    ("Hardware & System",
     colors.HexColor("#3d2a00"),
     [
        ("ESP32 DevKitC V4",
         "ESP32",
         "A dual-core 240 MHz microcontroller with built-in WiFi and Bluetooth, "
         "manufactured by Espressif Systems. Used in this project to run the firmware, "
         "generate AT commands, and communicate with the BDS module via UART2 "
         "(GPIO 16 RX, GPIO 17 TX)."),

        ("BDS EVBKIT V3",
         "EVBKIT",
         "The BeiDou-3 Short Message evaluation board used in this experiment. "
         "Contains the BDS-3 communication module, SIM card slot, RS232 interface, "
         "and DC power input. Connects to the ESP32 via an RS232-to-TTL adapter."),

        ("RS232-to-TTL Adapter",
         "MAX232",
         "A signal level converter board that translates between RS232 voltage levels "
         "(±12V) used by the BDS module and TTL voltage levels (0/3.3V) used by the "
         "ESP32. Wiring: VCC→3.3V (red), GND→GND (black), RXD→GPIO17 (blue), "
         "TXD→GPIO16 (green)."),

        ("UART2",
         "UART",
         "Universal Asynchronous Receiver-Transmitter — the serial communication "
         "protocol used between the ESP32 and the BDS module. Configured at 9600 baud, "
         "8 data bits, no parity, 1 stop bit (SERIAL_8N1) on pins GPIO 16 and 17."),

        ("XCOM V2.0",
         "XCOM",
         "A serial port debugging assistant (serial monitor) used to view raw "
         "BDS module responses in real time. Set to 115200 baud to match the ESP32 "
         "Serial Monitor output. Displays $RDTXA acknowledgements and error codes."),

        ("NMEA-0183",
         "NMEA",
         "A serial communication standard originally designed for marine navigation "
         "instruments. BDS modules output position data as NMEA sentences "
         "(e.g. $GNGGA, $GNRMC). The $CCTXM command uses NMEA-style framing with "
         "a $ prefix and *checksum suffix."),

        ("Line-of-Sight",
         "LOS",
         "An unobstructed direct path between the user terminal's antenna and the "
         "satellite. Required for RSMC transmission. Obstructions (buildings, trees, "
         "terrain) attenuate or block the L-band signal, reducing or preventing "
         "successful transmission."),
    ]),

    ("Experiment & Analysis",
     colors.HexColor("#1a3a5c"),
     [
        ("End-to-End Latency",
         "E2E",
         "The total time elapsed from when the ESP32 sends the $CCTXM command to when "
         "the decoded coordinate is available on the receiving system. Composed of: "
         "UART serialisation + BDS module processing + satellite uplink + GCC processing "
         "+ satellite downlink + web platform relay."),

        ("Success Rate",
         "SR",
         "The proportion of BDS-3 SMC transmission attempts that result in a confirmed "
         "acknowledgement ($RDTXA or 'OK') within the 30-second timeout window. "
         "Expressed as a percentage with a 95% confidence interval."),

        ("95% Confidence\nInterval",
         "95% CI",
         "A statistical range within which the true population success rate is expected "
         "to fall with 95% probability. Computed as: p ± 1.96 × √(p(1-p)/n), where p "
         "is the observed success rate and n is the number of trials."),

        ("Compression Ratio",
         "CR",
         "The ratio of the original (ASCII) payload size to the compressed payload size. "
         "Example: 208 bits ASCII / 64 bits binary = 3.25× compression ratio, "
         "representing a 69% size reduction."),

        ("serial_logger.py",
         "—",
         "Python script that reads the ESP32 Serial Monitor output over COM13 and logs "
         "all messages with PC-side timestamps to a CSV file. Used to capture [T1] "
         "transmission markers and BDS module responses for latency analysis."),

        ("field_test_logger.py",
         "—",
         "Python script that auto-detects ESP32 [TX#] transmission events over serial "
         "and logs success/fail/latency for each attempt to gap3_field_test.csv. "
         "Supports timeout detection (30 s) and failure logging."),

        ("telemetry_compare.py",
         "—",
         "Python script that encodes the same 7-field telemetry struct in ASCII, Binary, "
         "and Huffman formats, measures bit sizes for each, and saves results "
         "to gap6_telemetry.csv for Gap 4 analysis."),
    ]),
]

# ── Build story ───────────────────────────────────────────────────────────────
story = [
    Spacer(1, 0.3*cm),
    Paragraph("Glossary of Key Terms", TITLE),
    Paragraph("BDS-SMC2 UAV Rescue System — Lab 7 BeiDou Short Message Communication", SUB),
    HRFlowable(width="100%", thickness=2, color=DARK, spaceAfter=10),
]

for cat_name, cat_color, entries in sections:
    story.append(Spacer(1, 0.2*cm))
    story.append(cat_header(cat_name, cat_color))
    story.append(header_row())
    for term, abbr, defn in entries:
        story.append(entry(term, abbr, defn))
    story.append(Spacer(1, 0.3*cm))

story += [
    rule(DARK, 1.5),
    Paragraph(
        f"BDS-SMC2 Research Brief  |  Lab 7  |  "
        f"{datetime.date.today().strftime('%B %d, %Y')}  |  "
        f"{sum(len(e) for _,_,e in sections)} terms across {len(sections)} categories",
        META),
]

doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=2.0*cm, rightMargin=2.0*cm,
    topMargin=1.8*cm,  bottomMargin=1.8*cm,
    title="BDS-SMC2 Glossary", author="BDS Lab 7",
)

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2.0*cm, 1.0*cm, "BDS-SMC2 Glossary of Key Terms")
    canvas.drawRightString(W - 2.0*cm, 1.0*cm, f"Page {doc.page}")
    canvas.restoreState()

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"[DONE] Saved to {OUTPUT}")
