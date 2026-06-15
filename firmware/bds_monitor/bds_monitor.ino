// bds_monitor.ino — DIAGNOSTIC tool for the BDS-SMC2 hardware bring-up.
// Purpose: find out whether the BDS module is talking to the ESP32 at all,
//          and at what baud — the one thing the main firmware can't tell us.
//
// What it does, on a loop:
//   1. BAUD SCAN: opens UART2 at each candidate baud and listens ~4s for ANY
//      bytes from the module. Prints byte count + printable text + hex.
//      Most BeiDou RDSS modules emit periodic status/NMEA, so the baud that
//      yields readable text is the module's real baud.
//   2. COMMAND PROBE: at each baud it also sends the test $CCTXM command once
//      and listens for a reply, so we see if/how the module answers.
//
// Wiring (same as esp32_sender): module-TX -> GPIO16 (RX2), module-RX <- GPIO17 (TX2),
//   common GND. Disconnect GPIO16/17 before flashing (module noise corrupts the boot).
//
// Read the output in the Arduino Serial Monitor at 115200, or via the project's
// raw reader. Nothing is written to the module except the one probe command.

#include <HardwareSerial.h>

#define BDS_TX_PIN 17
#define BDS_RX_PIN 16
HardwareSerial BDSSerial(2); // UART2

// Candidate bauds, most-likely first for a BeiDou RDSS eval board.
const long BAUDS[] = {115200, 9600, 19200, 38400, 57600, 4800};
const int  N_BAUDS = sizeof(BAUDS) / sizeof(BAUDS[0]);

const unsigned long LISTEN_MS = 4000;   // listen window per phase

// The exact command the main firmware sends (112-bit lab T001 payload).
const char* PROBE_CMD = "$CCTXM,0,BIN:1D35DB5605079637007200A00101*05";

void listenAndDump(const char* tag, unsigned long ms) {
  unsigned long start = millis();
  int count = 0;
  String printable = "";
  String hexdump   = "";
  while (millis() - start < ms) {
    while (BDSSerial.available()) {
      uint8_t b = BDSSerial.read();
      count++;
      if (b >= 32 && b < 127) printable += (char)b;
      else if (b == '\r')     printable += "\\r";
      else if (b == '\n')     printable += "\\n";
      else                    printable += '.';
      char h[4]; snprintf(h, sizeof(h), "%02X ", b);
      if (hexdump.length() < 360) hexdump += h;  // cap so we don't flood
    }
  }
  Serial.print("    ["); Serial.print(tag); Serial.print("] bytes=");
  Serial.println(count);
  if (count > 0) {
    Serial.print("      text: "); Serial.println(printable);
    Serial.print("      hex : "); Serial.println(hexdump);
  } else {
    Serial.println("      (silence — nothing received)");
  }
}

void setup() {
  Serial.begin(115200);
  delay(800);
  Serial.println();
  Serial.println("=========================================");
  Serial.println("  BDS MONITOR / BAUD SCANNER (diagnostic)");
  Serial.println("  GPIO16<-moduleTX  GPIO17->moduleRX");
  Serial.println("=========================================");
}

void loop() {
  for (int i = 0; i < N_BAUDS; i++) {
    long baud = BAUDS[i];
    Serial.println();
    Serial.print(">>> BAUD "); Serial.println(baud);

    BDSSerial.end();
    BDSSerial.begin(baud, SERIAL_8N1, BDS_RX_PIN, BDS_TX_PIN);
    delay(150);
    while (BDSSerial.available()) BDSSerial.read(); // flush

    // Phase 1: passive — does the module emit anything on its own?
    listenAndDump("PASSIVE", LISTEN_MS);

    // Phase 2: active — send the probe command, watch for a reply.
    while (BDSSerial.available()) BDSSerial.read();
    BDSSerial.print(PROBE_CMD);
    BDSSerial.print("\r\n");
    Serial.print("    -> sent probe: "); Serial.println(PROBE_CMD);
    listenAndDump("REPLY", LISTEN_MS);
  }
  Serial.println();
  Serial.println("--- scan complete, repeating in 3s ---");
  delay(3000);
}
