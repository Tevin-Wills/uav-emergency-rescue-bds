# BDS-SMC2 — Hardware Day Walkthrough (zero-assumptions guide)
**For someone who has never used the BeiDou portal or done these steps before.**
Print this. Follow it top to bottom. Each step says WHAT YOU SEE so you always know it worked.
Nothing here can damage anything — the worst case is "nothing happens, try again."

---

## PART 1 — The website (do this at home, the night before; ~15 min)

You are getting three secret "tokens" from the BeiDou portal so your software can read
messages without logging in every time. Think of it like copying a temporary password.

### Step 1.1 — Open the portal
- Open **Google Chrome** (or Edge).
- Go to:  **http://bdrd.hwasmart.com**
- A login page appears (it may be in Chinese — that's fine).

### Step 1.2 — Log in
- Username: **RCSSTEAP_3058_SM_1**
- Password: **123456**
- Click the login button.
- ✅ YOU SEE: a dashboard / message list page. You are now logged in.

### Step 1.3 — Open the "developer tools" (this is the only unfamiliar bit)
- Press the **F12** key on your keyboard.
- A panel opens on the right or bottom of the screen — lots of tabs and code. Don't panic, you won't break anything.
- Along the top of that panel, find and click the tab called **Application**
  (if you don't see it, click the little **>>** arrows to reveal hidden tabs).

### Step 1.4 — Find the three tokens
- On the LEFT side of that Application panel, find **Local Storage** and click the little arrow to expand it.
- Click the entry that says **http://bdrdserver.hwasmart.com**
- ✅ YOU SEE: a table with names on the left and values on the right.
- Find these three rows (names in the "Key" column):
  - **data**
  - **access_token**
  - **refresh_token**
- For each one: click it, then copy the long value on the right (right-click → Copy, or select and Ctrl+C).

### Step 1.5 — Paste them into the config file
- Open the file **python\portal_config.json** in VS Code (it's already in your project).
- It looks like this:
  ```
  {
   "uid": "PASTE localStorage 'data' VALUE HERE",
   "access_token": "PASTE localStorage 'access_token' HERE",
   "refresh_token": "PASTE localStorage 'refresh_token' HERE"
  }
  ```
- Replace each PASTE... text with the value you copied. Keep the quote marks "" around each value.
  - `data` value goes into **uid**
  - `access_token` value goes into **access_token**
  - `refresh_token` value goes into **refresh_token**
- Save the file (Ctrl+S).

### Step 1.6 — Test it
- Open a terminal in VS Code (menu: Terminal → New Terminal).
- Type exactly:  `python python\portal_reader.py --dump`  and press Enter.
- ✅ YOU SEE: a wall of text (JSON) showing real messages from the portal — these are your old Gap 3 messages.
- ❌ IF YOU SEE an error or "SETUP" message: the tokens are wrong or expired. Redo Steps 1.3–1.5. Tokens can expire — if it worked before and stops, just grab fresh ones the same way.
- **IMPORTANT: copy that --dump output and send it to Claude before the field day** — one small code tweak may be needed to match the portal's exact format. (This is the only step that might need a follow-up.)

**Part 1 done = your ground station can receive. You never have to touch F12 again unless the tokens expire.**

---

## PART 2 — Flash the firmware (home, before leaving; ~10 min)

This puts the 112-bit rescue program onto the ESP32 chip.

### Step 2.1 — Wiring for flashing
- Disconnect the two wires on GPIO16 and GPIO17 (the firmware upload needs them free).
- Plug the ESP32 into the computer with the USB cable.

### Step 2.2 — Open Arduino IDE
- Open **Arduino IDE**.
- Open the file:  **firmware\esp32_sender\esp32_sender.ino**
- Top of the file already says `int MODE = 1;` — that is the 112-bit rescue mode. Don't change it.

### Step 2.3 — Set the upload options (one time)
- Tools → Board → select your ESP32 board.
- Tools → Port → select the COM port (likely **COM14**).
- Tools → Flash Mode → **DIO**
- Tools → Upload Speed → 40MHz region setting if shown.

### Step 2.4 — Upload
- Click the **Upload** arrow (top-left).
- When the bottom says **"Connecting......"**, hold the **BOOT** button on the ESP32, and tap **RESET**, then release BOOT.
- ✅ YOU SEE: a progress bar, then **"Done uploading."**
- ❌ IF "failed to connect": repeat the BOOT+RESET timing — it often takes two tries.

### Step 2.5 — Reconnect wiring
- Unplug USB. Reconnect the GPIO16 and GPIO17 wires.
- **The firmware is now flashed. You only do Part 2 once.**

---

## PART 3 — The field day (one outing; three sessions)

Go to the SAME outdoor spot you used for the original baseline. Take: laptop, ESP32 + antenna,
USB cable, this sheet, the printed Field Sheet, and a power bank if no mains.

### Step 3.1 — Open THREE terminals in VS Code
(Terminal menu → New Terminal, three times. You'll run one command in each.)

**Terminal 1 — the message sender/logger** (paste, but DON'T press Enter yet):
```
python python\serial_logger.py --port COM14 --baud 115200 --session morning --n 30
```

**Terminal 2 — the portal reader** (press Enter now — it just watches):
```
python python\portal_reader.py --poll 10
```

**Terminal 3 — the dashboard:**
```
python python\tx_dashboard.py
```
Then open a browser to **http://localhost:8765** — this is your live screen.

### Step 3.2 — Power on and wait
- Connect the ESP32 + antenna, antenna with a clear view of the sky.
- Power it on. **Wait 2 full minutes** (the satellite module needs to warm up). Don't skip this.

### Step 3.3 — Start the morning session
- Go to Terminal 1 and press **Enter**.
- The node now sends one message every 10 seconds, 30 times, then stops on its own.

### Step 3.4 — Watch the dashboard (the exciting part)
On http://localhost:8765, for the FIRST message, watch the row climb its 4 dots:
1. Dot 1 lights (yellow "IN FLIGHT", payload shows "loaded: T001...") — sending
2. **Dot 2 lights — THIS IS THE BIG MOMENT.** It means the BeiDou module accepted your new 112-bit message.
   - ✅ Dot 2 lights → the upgrade works. Continue happily.
   - ❌ The node shows an error / dot 2 never comes → STOP. The module rejected the longer message. Message Claude — a smaller "fallback" firmware is ready. Don't waste the day; this is the one thing to check first.
3. Dot 3 + green LED on the node → satellite confirmed
4. Row turns **green "CONFIRMED"** → the message reached the ground station and decoded back to the rescue record.

### Step 3.5 — One check on the portal
- For one message, go back to http://bdrd.hwasmart.com and open the received message.
- Note whether it shows the binary/hex, and tick the box on Field Sheet 3 ("packed binary" or "ASCII hex text").
- Take a screenshot of one green CONFIRMED dashboard row — that's evidence for your paper.

### Step 3.6 — Power-cycle and repeat at midday and evening
- After 30 TX, power the node OFF.
- **Midday (12:00–14:00):** edit Terminal 1's command, change `--session morning` to `--session midday`, repeat Steps 3.2–3.4.
- **Evening (after 18:00, same day):** change to `--session evening`, repeat.
- Keep Terminals 2 and 3 running all day.

### Step 3.7 — That evening: get your results
- In a terminal:  `python python\gap2_analysis.py --plot`
- ✅ YOU SEE: a stats table, an ANOVA line, and a "[PASTE THESE]" block of numbers.
- Those numbers fill the blanks in your paper draft. **Paper 1 data is now complete.**

---

## If anything goes wrong — the 4 most likely things

| What you see | What it means | Fix |
|---|---|---|
| `python is not recognized` | Python not on this terminal | Close/reopen VS Code terminal; or use `py` instead of `python` |
| portal_reader "SETUP" message | tokens missing/expired | Redo Part 1 (grab fresh tokens) |
| Dashboard shows nothing | logger/reader not running, or no TX yet | Check Terminals 1 & 2 are running; wait for first TX |
| Node sends but dot 2 never lights | module rejected 112-bit message | STOP, message Claude — fallback firmware ready |
| Wrong COM port | not COM14 on your machine | Arduino IDE → Tools → Port shows the real number; use that in the commands |

**Remember:** nothing you do here can break the hardware or lose data. If a step fails, you just redo it.
The whole day is "press start, watch dots turn green, repeat three times."
