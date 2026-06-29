"""
generate_workflow_diagram.py
Renders the end-to-end BDS-SMC2 node pipeline as a single figure:
figures/bds_node_workflow.png

The diagram links every component actually built in this node:
survivor data -> 112-bit encode -> ESP32 firmware -> BDS-3 RDSS module ->
satellite -> portal -> portal reader -> decoder -> map / waypoint ->
ROS 2 EmergencyCoordinate -> UAV mission. The simulation / GCS branch
(emulator -> virtual portal -> dashboard) is shown as the verified path
used while the RF uplink was blocked.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---- palette -------------------------------------------------------------
C_SURV = "#1b6ca8"   # survivor / position side
C_TX = "#d9822b"     # transmission (RF / space)
C_GCS = "#2e8b57"    # ground station software
C_UAV = "#7a3b9b"    # UAV mission side
C_SIM = "#b03a4b"    # simulation / emulation branch
C_EDGE = "#33373d"
C_TEXT = "#1b1f24"
GREY = "#5b6470"

fig, ax = plt.subplots(figsize=(16, 9.5), dpi=200)
ax.set_xlim(0, 160)
ax.set_ylim(0, 100)
ax.axis("off")
fig.patch.set_facecolor("white")


def box(x, y, w, h, title, sub, color, fs=11, sfs=8.5):
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.6,rounding_size=2.2",
        linewidth=1.8, edgecolor=color, facecolor=color + "22",
    )
    ax.add_patch(p)
    cx, cy = x + w / 2, y + h / 2
    ax.text(cx, cy + (h * 0.16), title, ha="center", va="center",
            fontsize=fs, fontweight="bold", color=C_TEXT)
    if sub:
        ax.text(cx, cy - (h * 0.22), sub, ha="center", va="center",
                fontsize=sfs, color=GREY)
    return (x, y, w, h)


def arrow(p1, p2, color=C_EDGE, label=None, lw=2.2, style="-|>",
          rad=0.0, label_dy=2.4):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=18,
                        linewidth=lw, color=color,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)
    if label:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax.text(mx, my + label_dy, label, ha="center", va="bottom",
                fontsize=8, color=color, fontweight="bold")


def rcen(b):  # right-centre point of a box
    x, y, w, h = b
    return (x + w, y + h / 2)


def lcen(b):  # left-centre
    x, y, w, h = b
    return (x, y + h / 2)


def tcen(b):
    x, y, w, h = b
    return (x + w / 2, y + h)


def bcen(b):
    x, y, w, h = b
    return (x + w / 2, y)


# ---- title ---------------------------------------------------------------
ax.text(80, 95.5, "BDS-SMC2 Node — End-to-End Rescue Data Pipeline",
        ha="center", fontsize=18, fontweight="bold", color=C_TEXT)
ax.text(80, 91.5, "Survivor position  →  112-bit BeiDou short message  →  satellite  →  ground station  →  UAV mission",
        ha="center", fontsize=10.5, color=GREY)

# ---- legend (horizontal strip) ------------------------------------------
legend = [
    (C_SURV, "Position & encoding"),
    (C_TX, "RF transmission (BeiDou RDSS)"),
    (C_GCS, "Ground station software"),
    (C_UAV, "UAV mission integration"),
    (C_SIM, "Simulation / verification"),
]
lx = 6
for c, t in legend:
    ax.add_patch(FancyBboxPatch((lx, 85), 2.4, 1.9,
                 boxstyle="round,pad=0.1", facecolor=c + "55",
                 edgecolor=c, linewidth=1.3))
    ax.text(lx + 3.3, 85.9, t, va="center", fontsize=8.6, color=C_TEXT)
    lx += 3.3 + len(t) * 1.32 + 4

BW, BH = 26, 12
TOP = 60  # main pipeline row y

# ---- main pipeline (left -> right) --------------------------------------
b1 = box(2,  TOP, BW, BH, "Survivor position",
         "lat/lon 7dp, alt, R,\npriority, survivor_id", C_SURV)
b2 = box(35, TOP, BW, BH, "112-bit encoder",
         "decode_binary.py\n6 fields packed >iihHBB", C_SURV)
b3 = box(68, TOP, BW, BH, "ESP32 firmware",
         "esp32_sender.ino\n$CCTXM,0,BIN:..*cs", C_TX)
b4 = box(101, TOP, BW, BH, "BDS-3 RDSS module",
         "EVBKIT_V3 + patch antenna\nT1/T2/T3 timing", C_TX)
b5 = box(134, TOP, 24, BH, "BeiDou\nsatellite (GEO)",
         "RDSS short message", C_TX)

arrow(rcen(b1), lcen(b2), C_SURV)
arrow(rcen(b2), lcen(b3), C_SURV)
arrow(rcen(b3), lcen(b4), C_TX, "serial 9600")
arrow(rcen(b4), lcen(b5), C_TX, "uplink")

# satellite -> portal (down the right side)
MID = 37
b6 = box(134, MID, 24, BH, "BDS portal",
         "bdrd.hwasmart.com\nmessage inbox", C_GCS)
arrow(bcen(b5), tcen(b6), C_TX, "downlink", rad=0.0, label_dy=0.5)

# portal -> reader -> decoder -> outputs (right -> left along middle row)
b7 = box(101, MID, BW, BH, "Portal reader",
         "portal_reader.py\npoll + de-dup -> CSV", C_GCS)
b8 = box(68, MID, BW, BH, "Decoder / detect",
         "gcs/decoder/detect.py\nBIN / ASCII / text", C_GCS)
b9 = box(35, MID, BW, BH, "Map + waypoint",
         "map_view.py (Leaflet)\nQGC WPL 110", C_GCS)
b10 = box(2, MID, BW, BH, "ROS 2 node",
          "EmergencyCoordinate\n/target/emergency_coordinate", C_UAV)

arrow(lcen(b6), rcen(b7), C_GCS)
arrow(lcen(b7), rcen(b8), C_GCS)
arrow(lcen(b8), rcen(b9), C_GCS)
arrow(lcen(b9), rcen(b10), C_UAV, "lat/lon")

# UAV mission box (bottom-left)
BOT = 16
b11 = box(2, BOT, BW, BH, "UAV mission",
          "waypoint dispatch\nfly to survivor", C_UAV)
arrow(bcen(b10), tcen(b11), C_UAV)

# ---- simulation / GCS verification branch (bottom row) -------------------
sb1 = box(35, BOT, BW, BH, "Module emulator",
          "bds_module_emulator.py\nT2 ack + modelled T3", C_SIM)
sb2 = box(68, BOT, BW, BH, "Virtual portal",
          "virtual_portal.py\nPortalStore", C_SIM)
sb3 = box(101, BOT, BW, BH, "Live dashboard",
          "tx_dashboard.py\nper-msg lifecycle", C_SIM)

# inject from encoder into emulator (sim path used when RF blocked)
arrow(bcen(b3), (sb1[0] + sb1[2] / 2, sb1[1] + sb1[3]), C_SIM,
      "emulated\nuplink", rad=-0.15, label_dy=0.5, style="-|>")
arrow(rcen(sb1), lcen(sb2), C_SIM)
arrow(rcen(sb2), lcen(sb3), C_SIM)
# dashboard feeds same decoder path
arrow(tcen(sb3), bcen(b7), C_SIM, rad=-0.2)

# injection interface contract note (Objective 4 -> 5)
ax.text(15, 76.5,
        "Injection contract (Objective 4 → 5):\ndata/outgoing_coords.csv → node transmits",
        ha="center", va="center", fontsize=8.2, color=C_SURV,
        style="italic")
arrow((15, 74.5), tcen(b1), C_SURV, lw=1.6)

# ---- footer: headline results -------------------------------------------
ax.plot([4, 156], [9.5, 9.5], color="#cfd4da", lw=1.2)
ax.text(4, 8.2, "Headline results:", fontsize=10, fontweight="bold",
        color=C_TEXT, va="top")
results = (
    "112-bit payload = 69.6% smaller than ASCII, 98 bits under the BDS-3 210-bit limit   |   "
    "delivery 232/232 valid TX (Wilson 95% LB ≥ 93.7%; χ²=0.000, p=1.000, 4 envs)   |   "
    "latency baseline n=30, mean ≈ 2.57 s   |   full chain verified in software"
)
ax.text(4, 4.6, results, fontsize=8.3, color=C_TEXT, va="top",
        linespacing=1.5)

fig.tight_layout()
out = "figures/bds_node_workflow.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
print(f"[OK] wrote {out}")
