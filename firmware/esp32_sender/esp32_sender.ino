
// ESP32 BDS-SMC Sender
// Sends BeiDou Short Message payloads via UART to BDS module
// Wiring: BDS RS232-TTL RXD->GPIO16, TXD->GPIO17, VCC->3.3V, GND->GND
//         Green LED G -> GPIO27

#include <HardwareSerial.h>

// --- PIN CONFIG ---
#define BDS_TX_PIN 17
#define BDS_RX_PIN 16
#define BDS_BAUD   9600
#define GREEN_LED  27

HardwareSerial BDSSerial(2); // UART2

// --- PAYLOAD MODE ---
// 0 = ASCII   (Gap 1 baseline)
// 1 = BINARY  (112-bit rescue payload — OPERATIONAL DEFAULT)
// 2 = HUFFMAN (Gap 6 dynamic compression)
// Option B (2026-06-12): all Gap 2 sessions (morning/midday/evening) are
// collected in MODE 1 so the latency ANOVA runs on the operational payload.
// The old 30-TX ASCII baseline is archived as gap2_latency_ascii_baseline.csv.
int MODE = 1;

// --- TEST COORDINATE: Lab system T001 (ground-truth reference, Table 5) ---
// double required: 7dp coordinates exceed float's ~7 significant digits.
// Hardware-test values only — the group sim derives coordinates from the
// shared Zurich datum (bringup/config/datum.yaml), never from here.
double   lat         = 49.0068822;
double   lon         = 8.4383287;
float    alt_m       = 114.2;  // metres AMSL
uint16_t r_cm        = 160;    // uncertainty radius R in centimetres (1.6 m)
uint8_t  priority    = 1;      // 0=P0, 1=P1, 2=P2
uint8_t  survivor_id = 1;      // T001

unsigned long lastSendTime = 0;
int sendCount = 0;

// BDS response buffering for T3 detection
static char  bdsBuf[128];
static int   bdsBufLen   = 0;
static bool  t2Seen      = false;
static int   burstCount  = 0;

// --- Gap 6: Huffman tree structures ---
#define HUFF_MAX_NODES 63
struct HNode { int freq; int8_t ch; int16_t left, right; };
static HNode hnodes[HUFF_MAX_NODES];
static int   hnodeCount;
struct HCode { uint32_t bits; uint8_t len; };
static HCode hcodes[128];

// Forward declarations
void    sendASCII();
void    sendBinary();
void    sendHuffman();
String  calcChecksum(const char* s);
static void hGenCodes(int idx, uint32_t code, uint8_t depth);
static int  hBuild(const char* s);

// -------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  BDSSerial.begin(BDS_BAUD, SERIAL_8N1, BDS_RX_PIN, BDS_TX_PIN);
  pinMode(GREEN_LED, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  delay(1000);
  Serial.println("[INIT] ESP32 BDS-SMC sender ready");
  Serial.print("[MODE] "); Serial.println(MODE);
}

void loop() {
  if (millis() - lastSendTime >= 10000) {
    lastSendTime = millis();
    sendCount++;

    t2Seen = false;
    burstCount = 0;
    bdsBufLen = 0;

    // Flush any stale BDS data before TX so it does not pollute T1 line
    while (BDSSerial.available()) BDSSerial.read();
    delay(50);

    Serial.println();
    Serial.println("---TX---");
    unsigned long t1 = millis();
    Serial.print("[T1] "); Serial.println(t1);

    if      (MODE == 0) sendASCII();
    else if (MODE == 1) sendBinary();
    else if (MODE == 2) sendHuffman();

    Serial.print("[TX#] "); Serial.println(sendCount);
  }

  // Buffered BDS response reader — detects T2 and T3 markers
  while (BDSSerial.available()) {
    char c = BDSSerial.read();
    // Serial.write(c); // disabled: raw forwarding floods logger

    // Buffer printable ASCII only
    if (c >= 32 && c < 127 && bdsBufLen < 126) {
      bdsBuf[bdsBufLen++] = c;
    }

    // Process on newline or buffer full
    if (c == '\n' || c == '\r' || bdsBufLen >= 126) {
      bdsBuf[bdsBufLen] = '\0';
      String line = String(bdsBuf);
      bdsBufLen = 0;

      if (line.length() > 2) {
        burstCount++;

        // T2: module accepted the command
        if (!t2Seen && (line.indexOf("OK") >= 0 || line.indexOf("$CC") >= 0 ||
                        line.indexOf("CCTXM") >= 0)) {
          Serial.println("\n[T2] module-ack");
          t2Seen = true;
        }

        // T3: satellite delivered — second data burst from BDS module
        if (t2Seen && (line.indexOf("RDTXA") >= 0 || line.indexOf("RDTX") >= 0 ||
                       line.indexOf("Send") >= 0   || line.indexOf("0500") >= 0 ||
                       line.indexOf("0100") >= 0   || burstCount >= 3)) {
          Serial.println("\n[T3] Send Success");
          digitalWrite(GREEN_LED, HIGH);
          delay(300);
          digitalWrite(GREEN_LED, LOW);
          t2Seen = false;
          burstCount = 0;
        }
      }
    }
  }
}

// -------------------------------------------------------------------
// Gap 1 BASELINE: ASCII
// Format: $CCTXM,<destID>,LAT:<lat>,LON:<lon>*<CS>\r\n
// -------------------------------------------------------------------
void sendASCII() {
  char content[40];
  snprintf(content, sizeof(content), "LAT:%.4f,LON:%.4f", lat, lon);
  String cmd = "$CCTXM,0," + String(content);
  cmd += "*" + calcChecksum(cmd.c_str()) + "\r\n";
  BDSSerial.print(cmd);
  Serial.print("[ASCII TX] "); Serial.print(cmd);
  Serial.print("[ASCII bits] "); Serial.println((int)(strlen(content) + 10) * 8);
}

// -------------------------------------------------------------------
// 112-bit BINARY RESCUE PAYLOAD (Gap 1 / Gap 6 upgrade)
// Bytes 0-3  lat  (int32, x10,000,000 -> 7dp, ~1cm)
// Bytes 4-7  lon  (int32, x10,000,000)
// Bytes 8-9  alt  (int16, metres)
// Bytes 10-11 R   (uint16, centimetres, 0-655m)
// Byte  12   priority (0=P0, 1=P1, 2=P2)
// Byte  13   survivor_id (0-255)
// Total: 14 bytes = 112 bits
// -------------------------------------------------------------------
void sendBinary() {
  int32_t lat_i = (int32_t)llround(lat * 10000000.0);
  int32_t lon_i = (int32_t)llround(lon * 10000000.0);
  int16_t alt_i = (int16_t)lroundf(alt_m);

  uint8_t payload[14];
  payload[0]  = (lat_i >> 24) & 0xFF; payload[1]  = (lat_i >> 16) & 0xFF;
  payload[2]  = (lat_i >>  8) & 0xFF; payload[3]  =  lat_i        & 0xFF;
  payload[4]  = (lon_i >> 24) & 0xFF; payload[5]  = (lon_i >> 16) & 0xFF;
  payload[6]  = (lon_i >>  8) & 0xFF; payload[7]  =  lon_i        & 0xFF;
  payload[8]  = (alt_i >>  8) & 0xFF; payload[9]  =  alt_i        & 0xFF;
  payload[10] = (r_cm  >>  8) & 0xFF; payload[11] =  r_cm         & 0xFF;
  payload[12] = priority;
  payload[13] = survivor_id;

  char hex[29];
  for (int i = 0; i < 14; i++) snprintf(hex + i*2, 3, "%02X", payload[i]);
  hex[28] = '\0';

  char buf[64];
  snprintf(buf, sizeof(buf), "$CCTXM,0,BIN:%s", hex);
  String cmd = String(buf) + "*" + calcChecksum(buf) + "\r\n";
  BDSSerial.print(cmd);
  Serial.print("[BINARY TX] "); Serial.print(cmd);
  Serial.println("[BINARY bits] 112 (lat lon alt R priority survivor_id)");
}

// -------------------------------------------------------------------
// Gap 6: Dynamic Huffman Encoding
// Builds frequency table from full telemetry string, encodes bit by bit
// -------------------------------------------------------------------
static void hGenCodes(int idx, uint32_t code, uint8_t depth) {
  if (hnodes[idx].ch >= 0) {
    hcodes[(uint8_t)hnodes[idx].ch] = {code, depth};
    return;
  }
  if (hnodes[idx].left  >= 0) hGenCodes(hnodes[idx].left,  (code << 1),       depth + 1);
  if (hnodes[idx].right >= 0) hGenCodes(hnodes[idx].right, (code << 1) | 1,   depth + 1);
}

static int hBuild(const char* s) {
  int freq[128] = {0};
  for (const char* p = s; *p; p++)
    if ((uint8_t)*p < 128) freq[(uint8_t)*p]++;

  hnodeCount = 0;
  int active[HUFF_MAX_NODES], activeN = 0;
  for (int c = 0; c < 128; c++) {
    if (freq[c] > 0) {
      hnodes[hnodeCount] = {freq[c], (int8_t)c, -1, -1};
      active[activeN++] = hnodeCount++;
    }
  }

  // Merge two lowest-frequency nodes until one root remains
  while (activeN > 1) {
    int m1 = 0;
    for (int i = 1; i < activeN; i++)
      if (hnodes[active[i]].freq < hnodes[active[m1]].freq) m1 = i;
    int i1 = active[m1]; active[m1] = active[--activeN];

    int m2 = 0;
    for (int i = 1; i < activeN; i++)
      if (hnodes[active[i]].freq < hnodes[active[m2]].freq) m2 = i;
    int i2 = active[m2]; active[m2] = active[--activeN];

    hnodes[hnodeCount] = {hnodes[i1].freq + hnodes[i2].freq, -1,
                          (int16_t)i1, (int16_t)i2};
    active[activeN++] = hnodeCount++;
  }
  return active[0]; // root index
}

void sendHuffman() {
  // Full telemetry ASCII string
  char ascii[80];
  snprintf(ascii, sizeof(ascii),
           "LAT:%.4f,LON:%.4f,ALT:0,BAT:100,MODE:2,TS:%lu",
           lat, lon, millis() / 1000UL);

  // Build tree and generate codes
  memset(hcodes, 0, sizeof(hcodes));
  int root = hBuild(ascii);
  hGenCodes(root, 0, 0);

  // Encode bit by bit into packed bytes
  uint8_t encoded[64] = {0};
  int bitPos = 0;
  for (const char* p = ascii; *p && bitPos < 512; p++) {
    HCode& bc = hcodes[(uint8_t)*p];
    for (int b = bc.len - 1; b >= 0 && bitPos < 512; b--) {
      if ((bc.bits >> b) & 1)
        encoded[bitPos / 8] |= (1 << (7 - bitPos % 8));
      bitPos++;
    }
  }
  int encodedBytes = (bitPos + 7) / 8;

  char hex[130] = {0};
  for (int i = 0; i < encodedBytes; i++)
    snprintf(hex + i*2, 3, "%02X", encoded[i]);

  char buf[200];
  snprintf(buf, sizeof(buf), "$CCTXM,0,HUF:%s", hex);
  String cmd = String(buf) + "*" + calcChecksum(buf) + "\r\n";
  BDSSerial.print(cmd);
  Serial.print("[HUFFMAN TX] "); Serial.print(cmd);
  Serial.print("[HUFFMAN bits] "); Serial.print(bitPos);
  Serial.print(" encoded vs "); Serial.print((int)strlen(ascii) * 8);
  Serial.println(" ASCII");
}

// -------------------------------------------------------------------
// NMEA-style XOR checksum over characters after '$'
// -------------------------------------------------------------------
String calcChecksum(const char* s) {
  uint8_t cs = 0;
  for (int i = 1; s[i] != '\0'; i++) cs ^= (uint8_t)s[i];
  char out[3];
  snprintf(out, sizeof(out), "%02X", cs);
  return String(out);
}
