# Design — Auto-Sender (CSV row → automatic BDS transmission)

**Goal:** the moment a coordinate is appended to a CSV, the BDS-SMC node transmits it —
no manual step. The operator only watches the dashboard for red (error) rows.

```
upstream (lab system / Objective N)  ──writes a row──►  data/outgoing_coords.csv
                                                              │  watcher notices (~0.5 s)
                                                              ▼
                                              auto_sender.py  ──"TX,...\n" over USB──►  ESP32
                                                              │                          │ encodes 112-bit
                                                              │   reads T1/T2/T3          │ transmits via BDS
                                                              ▼                          ▼
                                  data/gap2_latency.csv + live_state.json   →   tx_dashboard.py (green/red)
```

---

## 1. The outgoing-coordinates file  `data/outgoing_coords.csv`

One survivor per row. Header + rows:
```
lat,lon,alt,r_cm,priority,survivor_id
49.0068822,8.4383287,114.2,160,1,1
49.0070078,8.4382004,113.5,1190,2,2
```
Whatever produces coordinates (lab system, another objective, a live RTK feed) just
appends a line here. That single append is the trigger.

## 2. Serial protocol  (PC ⇄ ESP32)

**PC → ESP32** (one line, newline-terminated):
```
TX,<lat>,<lon>,<alt_m>,<r_cm>,<priority>,<survivor_id>\n
e.g.  TX,49.0068822,8.4383287,114.2,160,1,1
```

**ESP32 → PC** (its existing markers — unchanged):
```
[T1] <millis>            ← command fired
[BINARY TX] $CCTXM,0,BIN:1D35DB56...   ← payload echoed
OK / $CC...              ← module ack (T2)
[T3] Send Success        ← satellite ack
```

## 3. Firmware change  (esp32_sender.ino — additive, ~30 lines)

Add to `loop()`: when a `TX,...` line arrives on the USB serial, parse the six fields
into the existing globals and fire one transmission. Disable the 10 s auto-timer when
in command mode so it only sends on demand.

```cpp
// in loop(), before the timer block:
if (Serial.available()) {
  String cmd = Serial.readStringUntil('\n');
  if (cmd.startsWith("TX,")) {
    // TX,lat,lon,alt,r_cm,priority,id
    double la, lo; float al; unsigned int r, pr, id;
    if (sscanf(cmd.c_str(), "TX,%lf,%lf,%f,%u,%u,%u",
               &la,&lo,&al,&r,&pr,&id) == 6) {
      lat=la; lon=lo; alt_m=al; r_cm=(uint16_t)r;
      priority=(uint8_t)pr; survivor_id=(uint8_t)id;
      Serial.println("\n---TX---");
      Serial.print("[T1] "); Serial.println(millis());
      sendBinary();                 // existing 112-bit encoder
    }
  }
}
#define COMMAND_MODE 1   // when 1, skip the timer-based auto-send
```

This is **additive**: with `COMMAND_MODE 0` the node behaves exactly as now (timer test
mode); with `1` it sends only when the watcher commands it.

## 4. The watcher  `auto_sender.py`

```
seen = number of rows already in outgoing_coords.csv   (skip the backlog on start)
open serial (or mock)
loop forever:
    rows = read outgoing_coords.csv
    for each row index >= seen:
        payload = encode 112-bit from the row
        send "TX,...\n" over serial          (mock: simulate)
        read responses → capture T1/T2/T3    (mock: timed simulation)
        append to gap2_latency.csv (session='auto', + payload)
        update live_state.json through the stages   (dashboard live row)
    seen = len(rows)
    sleep(poll)      # 0.5 s default — sub-second trigger
```

- **One process owns the serial port** — the watcher both *sends* and *reads responses*
  (you can't have two scripts on COM14). It is serial_logger + a CSV-watch + a send step.
- **Mock mode** replaces the serial port with a timed simulation of the ESP32, so the
  full loop runs and drives the dashboard with **no hardware**.

## 5. What the operator sees

Only the dashboard. Each appended coordinate becomes a row that climbs the journey dots:
- **green CONFIRMED** = sent, delivered, bit-perfect → nothing to do
- **red TIMEOUT** = that one failed → investigate

Hands-off otherwise. Drop coordinates in the file; they fly; you watch for red.

## 6. Swapping the source (why this scales to the group)

`outgoing_coords.csv` is the seam. Today a script/feeder appends the lab records; later a
live RTK or ROS feed appends instead — the watcher, firmware, and dashboard never change.
That is the "emulate now, live later" path, and the point where another objective's CSV
plugs in: it simply writes rows to `outgoing_coords.csv`.
