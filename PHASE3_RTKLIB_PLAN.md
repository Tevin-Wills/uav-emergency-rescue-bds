# Phase 3 — RTKLIB Validation Against Real BeiDou RINEX Data
**Project:** UAV Emergency Rescue BDS — RTK Positioning Module  
**Author:** Tevin Wills (Student 1)  
**Date:** 2026-06-04  
**Status:** Planning — not yet started

---

## Objective

Validate the simulation noise model parameters used in Levels 1–3 against real BeiDou (BDS) GNSS measurements. This is done by post-processing RINEX observation files from a pair of IGS MGEX reference stations through RTKLIB and comparing the measured accuracy in each fix state against the values assumed in the simulation.

The core validation question is: **Are the simulation parameters realistic?**

| Simulation Parameter | Assumed Value | To be compared against real BDS measurement |
|---|---|---|
| GNSS Only noise (σ) | 1.50 m | Real BDS SPP horizontal error |
| RTK Float accuracy | ~0.25 m | Real BDS float solution error |
| RTK Fixed accuracy | ~0.03 m | Real BDS fixed solution error |
| Disaster-zone noise (σ) | 2.00–2.75 m | Real BDS error under poor conditions |

---

## Why RTKLIB?

RTKLIB is the standard open-source GNSS post-processing toolkit used in academic and commercial RTK research. It is chosen over alternatives for the following reasons:

- **BeiDou support** — native BDS-2/BDS-3 constellation support (constellation flag `-sys B`)
- **RINEX 3.x compatible** — reads the format produced by IGS MGEX stations directly
- **Three solution modes** — SPP (GNSS Only), DGNSS/Float, and Integer Fixed, matching the three states modelled in the simulation
- **Command-line interface** — `rnx2rtkp` can be scripted from Python for reproducible processing
- **Well-documented** — RTKLIB manual v2.4.3 provides exact parameter descriptions
- **Free and open** — no licencing barriers; can be committed alongside the project code

---

## Step 1 — Select IGS MGEX Station Pair

### Criteria
- Both stations must track BeiDou (BDS-2 or BDS-3) and provide RINEX 3.x observation files
- Baseline between rover and base must be short (≤ 30 km) for realistic RTK processing
- Both stations must have published precise reference coordinates (ITRF2020)
- Data must be freely accessible via CDDIS or IGS FTP

### Recommended Station Pairs

**Primary choice: JFNG + WUHN (Wuhan, China)**
- JFNG: Jiufeng, Wuhan — BDS-3 tracking, IGS MGEX, ~0 km from WUHN (co-located pair)
- WUHN: Wuhan University — long-running MGEX station, BDS-heavy tracking
- Baseline: ~0–5 km. Use JFNG as rover, WUHN as base.
- Data URL: `https://cddis.nasa.gov/archive/gnss/data/campaign/mgex/daily/rinex3/`

**Fallback choice: BJFS + BJF1 (Beijing)**
- BJFS: Beijing Fangshan — IGS core station, BDS tracking
- BJF1: Beijing — MGEX extension, ~15 km baseline
- Use if JFNG/WUHN files are unavailable for the chosen date

### Date to Process
Choose a clear-sky day with no known space weather events:
- Suggested: any weekday in 2026 where Kp index ≤ 2
- Avoid: days around geomagnetic storms (Kp ≥ 5), which inflate ionospheric errors
- Check Kp index: https://www.swpc.noaa.gov/products/planetary-k-index

---

## Step 2 — Download RINEX Files

### Files Required per Station

| File Type | Format | Description |
|---|---|---|
| Observation file (rover) | `.rnx` / `*MO.rnx` | Raw pseudorange and carrier-phase measurements |
| Observation file (base) | `.rnx` / `*MO.rnx` | Same for the reference station |
| Navigation file (BDS) | `*MN.rnx` or mixed `*MX.rnx` | BDS satellite broadcast ephemerides |

### Download Command (example for JFNG, day-of-year 154, 2026)
```bash
# CDDIS requires Earthdata account — log in first:
# https://urs.earthdata.nasa.gov/

STATION=JFNG
YEAR=2026
DOY=154   # day-of-year for 2026-06-03

wget -r -np -nH --cut-dirs=8 \
  "https://cddis.nasa.gov/archive/gnss/data/campaign/mgex/daily/rinex3/${YEAR}/${DOY}/" \
  -A "${STATION}*_R_${YEAR}${DOY}*_01D_*.rnx.gz"
```

### File sizes
- Observation file (1 day, 30 s epoch): ~20–60 MB compressed
- Navigation file: ~2–5 MB
- Uncompress: `gunzip *.gz`

---

## Step 3 — Install and Build RTKLIB

```bash
git clone https://github.com/tomojitakasu/RTKLIB.git --depth=1
cd RTKLIB/app/rnx2rtkp/gcc
make
# Binary at: RTKLIB/app/rnx2rtkp/gcc/rnx2rtkp
```

Verify:
```bash
./rnx2rtkp --help 2>&1 | head -20
```

Expected: RTKLIB version string and usage synopsis.

---

## Step 4 — RTKLIB Configuration File

Create `rtklib_bds.conf` in the project config folder:

```ini
# RTKLIB configuration — BDS RTK post-processing
pos1-posmode       =2          # kinematic RTK
pos1-frequency     =1          # L1 only (safe for single-freq RINEX)
pos1-soltype       =0          # forward solution
pos1-elmask        =10         # elevation mask 10 degrees
pos1-snrmask_r     =0          # no SNR mask
pos1-navsys        =8          # BDS only (GPS=1, BDS=8, GPS+BDS=9)
pos1-exclsats      =           # no excluded satellites

pos2-armode        =3          # fix-and-hold (most permissive for fixed solution)
pos2-gloarmode     =0          # GLONASS AR off (not using GLONASS)
pos2-arthres       =3.0        # AR threshold
pos2-arlockcnt     =0
pos2-arelmask      =0
pos2-arminfix      =10         # min epochs for fix hold

out-solformat      =llh        # output lat/lon/height
out-outhead        =on
out-outopt         =on
out-timesys        =gpst
out-timeform       =tow
out-timendec       =3
out-degform        =deg
out-fieldsep       =
out-height         =ellipsoidal
out-geoid          =internal
```

### Key parameters to vary for the three solution modes:

| Mode | pos1-posmode | pos2-armode | Expected output |
|---|---|---|---|
| GNSS Only (SPP) | 0 (single) | N/A | Quality flag = 1 |
| RTK Float | 2 (kinematic) | 0 (off) | Quality flag = 2 |
| RTK Fixed | 2 (kinematic) | 3 (fix-and-hold) | Quality flag = 5 |

---

## Step 5 — Run RTKLIB Processing

### GNSS Only (Single-Point Positioning)
```bash
./rnx2rtkp -p 0 -sys B -ti 30 \
  JFNG_rover.rnx \
  BDS_nav.rnx \
  -o phase3_gnss_only.pos
```

### RTK Float
```bash
./rnx2rtkp -p 2 -f 1 -sys B -ti 30 \
  -k rtklib_bds.conf \
  JFNG_rover.rnx BDS_nav.rnx WUHN_base.rnx \
  -r <base_lat> <base_lon> <base_alt> \
  -o phase3_rtk_float.pos
```
(Replace `-k rtklib_bds.conf` with `pos2-armode=0` inline via `-opt` if needed)

### RTK Fixed
```bash
./rnx2rtkp -p 2 -f 1 -sys B -ti 30 \
  -k rtklib_bds.conf \
  JFNG_rover.rnx BDS_nav.rnx WUHN_base.rnx \
  -r <base_lat> <base_lon> <base_alt> \
  -o phase3_rtk_fixed.pos
```

### Output `.pos` file format (space-separated)
```
% (GPST)        latitude(deg)  longitude(deg)  height(m)  Q  ns  sdn(m)  sde(m)  sdu(m)  sdne(m)  sdeu(m)  sdun(m)  age(s)  ratio
2026/06/03 00:00:00.000  39.98100000  116.34400000   50.123   5  10  0.012  0.015  0.031 ...
```

Column `Q`: 1 = GNSS Only, 2 = DGNSS/Float, 5 = RTK Fixed

---

## Step 6 — Python Analysis Script (`analyse_rtklib.py`)

Write a Python script that:

1. **Reads the `.pos` output files** — parse with `pandas`, extract lat/lon/height and quality flag
2. **Converts to ENU** — compute horizontal error relative to the published IGS reference coordinates for the rover station (known precise coordinates from IGS SINEX files)
3. **Bins by quality flag** — Q=1 → GNSS Only, Q=2 → RTK Float, Q=5 → RTK Fixed
4. **Computes accuracy statistics per state**:
   - Mean horizontal error (m)
   - Standard deviation (m)
   - 95th-percentile error (m)
   - Sample count
5. **Builds the validation table** — compare real measurements vs simulation parameters
6. **Generates validation figures**:
   - Error time series (same format as Level 1/2/3 plots)
   - Error distribution histograms (KDE) per state
   - Validation table plot (side-by-side real vs simulated)

Script location: `results/graphs/rtk_positioning/analyse_rtklib.py`  
Output folder: `results/graphs/rtk_positioning/phase3/`

---

## Step 7 — Validation Table and Report Update

The output of the analysis is a validation table comparing real BDS measurements against the simulation model:

| Fix State | Real BDS Mean Error | Simulation σ | Ratio | Status |
|---|---|---|---|---|
| GNSS Only (SPP) | ? m | 1.50 m | ? | TBD |
| RTK Float | ? m | 0.25 m | ? | TBD |
| RTK Fixed | ? m | 0.03 m | ? | TBD |

**Interpretation criteria:**
- Ratio within 0.5–2.0× → simulation parameters are within a factor of two of reality → **acceptable model**
- Ratio > 2.0× → simulation understates real error → noise model needs upward recalibration
- Ratio < 0.5× → simulation overstates real error → noise model is conservative

The validation result (acceptable / needs recalibration) is then inserted into the final report as the Phase 3 evidence that the simulation is grounded in real GNSS behaviour.

---

## Deliverables

| Deliverable | Location | Notes |
|---|---|---|
| `rtklib_bds.conf` | `ros2_ws/src/rtk_positioning/config/` | RTKLIB configuration file |
| `analyse_rtklib.py` | `results/graphs/rtk_positioning/` | Processing + validation script |
| RINEX data (rover + base + nav) | `results/logs/phase3/` | Raw downloaded files |
| `.pos` output files (3 modes) | `results/logs/phase3/` | RTKLIB output |
| Phase 3 validation figures (PNG) | `results/graphs/rtk_positioning/phase3/` | 3–5 figures |
| Updated progress report | `results/RTK_Positioning_Progress_Report.docx` | Add Phase 3 section |

---

## Estimated Time

| Step | Estimated Duration |
|---|---|
| Station selection + CDDIS account setup | 1–2 hours |
| RINEX download | 30 minutes |
| RTKLIB build + test | 1 hour |
| RTKLIB processing (all 3 modes) | 1–2 hours |
| Write `analyse_rtklib.py` | 3–4 hours |
| Generate figures + validation table | 1–2 hours |
| Update progress report | 1 hour |
| **Total** | **~10–12 hours** |

---

## Blockers and Risks

| Risk | Mitigation |
|---|---|
| CDDIS requires Earthdata login | Register at https://urs.earthdata.nasa.gov/ before starting |
| JFNG/WUHN files unavailable for chosen date | Fall back to BJFS/BJF1 station pair or try adjacent date |
| RTKLIB build fails on WSL2 | Install `build-essential` and `libgfortran-dev`; RTKLIB has no external deps |
| RTK Fixed solution rate is low (< 50%) | Reduce elevation mask to 5°, extend processing to 24 h, or accept float-heavy result |
| Real BDS error much higher than simulation | Re-document as "simulation is optimistic" and recommend noise model recalibration in final report |

---

## Status Checklist

- [ ] Step 1: Station pair selected — JFNG + WUHN
- [ ] Step 2: RINEX files downloaded
- [ ] Step 3: RTKLIB built and verified
- [ ] Step 4: Config file written (`rtklib_bds.conf`)
- [ ] Step 5: All three processing modes run (SPP / Float / Fixed)
- [ ] Step 6: `analyse_rtklib.py` written and run
- [ ] Step 7: Validation table completed and report updated
