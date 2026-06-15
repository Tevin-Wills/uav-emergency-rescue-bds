# BDS-SMC2 Hardware Bring-up Plan (112-bit firmware)
_Last updated: 2026-06-15 — module not yet responding; resume tomorrow._

## 1. What is CONFIRMED working
| Item | Status | Evidence |
|------|--------|----------|
| ESP32 chip identity | ✅ classic ESP32-D0WD-V3 (rev 3.1), 4MB, 40MHz xtal, MAC 04:83:08:0e:ee:d0 | esptool read |
| Firmware flashed | ✅ 112-bit build, hash verified | esptool write-flash OK |
| Firmware transmitting | ✅ MODE 1, `$CCTXM,0,BIN:1D35DB5605079637007200A00101*05`, 112 bits, every 10 s | serial capture |
| ESP32 → PC serial (UART0, 115200) | ✅ clean once data wires off RX/TX | serial capture |
| Module powered | ✅ green LEDs lit | photo |
| SIM/service card | ✅ inserted | photo (北斗 SIM卡 slot) |
| Software pipeline | ✅ decode round-trip OK; gap2_analysis OK (n=30 baseline, mean 2574 ms) | re-run 2026-06-15 |

## 2. The PROBLEM
**Module sends nothing back — no `[T2]`/`[T3]` in any configuration; module's green LED does NOT blink when ESP32 transmits.** Ruled out: power, SIM present, sky view, both ESP32 crossover orientations, ESP32 firmware. Main firmware can't show raw module output (raw-forward disabled, line 101).

## 3. Module on the bench
- **EVBKIT_V3** BeiDou RDSS eval board, **SN 30787123**, date 2138.
- Has TTL pads (`TX`, `RX(S)`) AND a DB9 RS232 port. SIM slot (北斗 SIM卡). 12V powered.
- **RESOLVED 2026-06-15: SAME module that produced earlier data; supervisor changed nothing.** → command `$CCTXM` and baud 9600 are TRUSTED (worked on this exact board). Regression is therefore PHYSICAL or environmental, not protocol.
- **Strong clue:** at start of today's session the data wires were on the WRONG pins (RX/TX = GPIO1/3), not 16/17 → rig was NOT in last-working state; wiring had been disturbed. We are rebuilding the connection and a physical error likely remains.

## 4. Wiring structure (current)
```
        ESP32 (classic, COM14, USB->laptop = power + debug @115200)
          GPIO16 RX2 ─ green ─┐
          GPIO17 TX2 ─ blue  ─┤   [blue "RS232 TO TTL" board]
          3V3        ─ red   ─┤    header: VCC RXD TXD GND
          GND        ─ black ─┘
                         blue board DB9 ─ UGREEN coiled RS232 cable ─ module DB9
                                                                      │
                                              [EVBKIT_V3 module] ─ 12V supply
                                                                  ─ SIM card
                                                                  ─ green patch antenna
```
Correct UART2 crossover: module-TX → GPIO16 (RX2); module-RX ← GPIO17 (TX2); common GND.

## 5. Possible problems (ranked)
_Update 2026-06-15: same module confirmed → #1/#2/#3 DOWNGRADED (baud/cmd trusted). Now top suspects: **#4 physical connection** (wires were found on wrong pins), then **#6 card quota/rate-limit** and **#8 satellite lock**._
| # | Possible cause | Likely if... | How to test tomorrow |
|---|----------------|--------------|----------------------|
| 1 | **Different module** than firmware was written for → wrong command/baud | supervisor swapped the module | Confirm SN with supervisor; run `bds_monitor` scan |
| 2 | **Baud mismatch** (fw 9600 vs module's real rate) | eval board defaults to 115200 | `bds_monitor` baud scan |
| 3 | **Command format** `$CCTXM` not what module expects | even same module, untested cmd path | `bds_monitor` probe; check module manual (`$CCTXA`/`$TXSQ`?) |
| 4 | **Physical break** (DB9 half-seated, wire on wrong pin) | introduced during rewiring/moving | reseat DB9 both ends; `bds_monitor` PASSIVE shows if module emits anything |
| 5 | **RS232 cable** straight vs null-modem (TX/RX not crossed right) | — | covered by trying both crossovers + `bds_monitor` |
| 6 | **Card rate-limit (频度)** — 10 s TX too fast / quota used | sends silently dropped | ask supervisor card freq; slow TX interval |
| 7 | **Dest address `0`** invalid | module needs real recipient addr | module manual; set valid address |
| 8 | **No satellite lock** | module needs open sky + lock LED | check module's satellite LED outdoors |
| 9 | **Wrong serial port** — should use module TTL pads not DB9 RS232 | — | check manual; try ESP32 direct to TX/RX(S) |

## 6. TO-DO (in order)
| Step | Task | Owner | Done? |
|------|------|-------|-------|
| 0 | Get module **model + manual + baud + card freq** from supervisor | user | ☐ |
| 0b | Confirm bench module SN = 30787123 (same as before?) | user | ☐ |
| 1 | Disconnect GPIO16/17, flash `firmware/bds_monitor/bds_monitor.ino` | both | ☐ |
| 2 | Reconnect GPIO16/17; run scan; read which baud shows module text | both | ☐ |
| 3 | If module emits text → note baud + protocol; if probe gets reply → cmd OK | both | ☐ |
| 4 | Set `BDS_BAUD` (+ command format if needed) in `esp32_sender.ino`; reflash | both | ☐ |
| 5 | Confirm `[T2]`/`[T3]` appear (112-bit acceptance) | both | ☐ |
| 6 | Run Gap 2 sessions: morning/midday/evening (30 TX each, power-cycle between) | user | ☐ |
| 7 | `python python/gap2_analysis.py` → fill Paper 1 §V slots | both | ☐ |

## 7. Flashing reminders (learned the hard way)
- **Disconnect GPIO16/17 data wires before flashing** (module noise → esptool "Invalid head of packet").
- Board is **classic ESP32** → Arduino board = "ESP32 Dev Module", esptool `--chip esp32 --flash-mode dio --flash-freq 40m`.
- If auto-reset fails: hold BOOT, tap RST, release BOOT to enter download mode.
- Arduino 1.8.19 builds to `%LOCALAPPDATA%/Temp/arduino_build_*/` — flash the newest `*.merged.bin`.
