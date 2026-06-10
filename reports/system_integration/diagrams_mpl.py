#!/usr/bin/env python3
"""
Slide-grade system diagrams (hand-drawn matplotlib, flat-design).

Produces D1 architecture, D2 data-flow, D3 mission FSM as PNG (300 dpi) + SVG.
Reproducible, no external services. Design: rounded cards + soft drop shadow,
coherent role-based palette, clipped arrows, labelled edges on white chips.

Run:  python3 diagrams_mpl.py     (or imported by generate_integration_figures.py)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"

# Role palette: (fill, edge, text)
ROLE = {
    "module":   ("#E8F1FC", "#2F6DB5", "#143A63"),   # ROS 2 nodes
    "bridge":   ("#FCEFD6", "#C8881E", "#6E4A0A"),   # ros_gz / xrce
    "sim":      ("#ECEFF1", "#607D8B", "#2F4048"),   # gazebo / px4 (external)
    "operator": ("#E4F3EA", "#2E8B57", "#1B5733"),   # QGC
    "good":     ("#DFF3E4", "#2E8B57", "#1B5733"),
    "bad":      ("#FBE3DA", "#C0392B", "#7A2418"),
    "hold":     ("#FCEFD6", "#C8881E", "#6E4A0A"),
    "state":    ("#E8F1FC", "#2F6DB5", "#143A63"),
    "io":       ("#ECEFF1", "#90A4AE", "#37474F"),
}
ARROW = "#56657A"
EDGE_LABEL_BG = dict(boxstyle="round,pad=0.18", fc="white", ec="#D5DBE2", lw=0.8)


def canvas(w_in, h_in):
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    ax.set_aspect("auto")
    return fig, ax


def band(ax, y0, y1, color, label):
    ax.add_patch(FancyBboxPatch((2, y0), 96, y1 - y0,
        boxstyle="round,pad=0.02,rounding_size=1.2", fc=color, ec="none", zorder=0))
    ax.text(3.5, y1 - 1.6, label, ha="left", va="top", fontsize=11,
            color="#7A8794", fontweight="bold", style="italic", zorder=1)


def card(ax, cx, cy, w, h, text, role="module", fontsize=12.5):
    fill, edge, tcol = ROLE[role]
    x, y = cx - w / 2, cy - h / 2
    # soft drop shadow
    ax.add_patch(FancyBboxPatch((x + 0.5, y - 0.7), w, h,
        boxstyle="round,pad=0.02,rounding_size=1.6", fc="#0a0a0a", ec="none",
        alpha=0.10, zorder=2))
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=1.6",
        fc=fill, ec=edge, lw=2.0, zorder=3)
    ax.add_patch(p)
    ax.text(cx, cy, text, ha="center", va="center", color=tcol,
            fontsize=fontsize, fontweight="bold", zorder=4, linespacing=1.15)
    p._cx, p._cy = cx, cy
    return p


def link(ax, a, b, label=None, rad=0.0, lblpos=0.5, dx=0, dy=0):
    arr = FancyArrowPatch((a._cx, a._cy), (b._cx, b._cy),
        patchA=a, patchB=b, shrinkA=2, shrinkB=2,
        arrowstyle="-|>", mutation_scale=16, lw=1.8, color=ARROW,
        connectionstyle=f"arc3,rad={rad}", zorder=2)
    ax.add_patch(arr)
    if label:
        mx = a._cx + (b._cx - a._cx) * lblpos + dx
        my = a._cy + (b._cy - a._cy) * lblpos + dy
        ax.text(mx, my, label, ha="center", va="center", fontsize=9.5,
                color="#33414F", zorder=5, bbox=EDGE_LABEL_BG)


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".png"), dpi=300, bbox_inches="tight",
                facecolor="white", pad_inches=0.15)
    fig.savefig(os.path.join(FIG, name + ".svg"), bbox_inches="tight",
                facecolor="white", pad_inches=0.15)
    plt.close(fig)


# ============================================================ D1 — architecture
def d1():
    fig, ax = canvas(13, 9)
    ax.text(50, 98, "System Architecture — tools, bridges, and the 5 ROS 2 modules",
            ha="center", va="top", fontsize=16, fontweight="bold", color="#1f2d3d")

    band(ax, 80, 93, "#EAF3EE", "OPERATOR")
    band(ax, 60, 77, "#EAF1FB", "ROS 2 APPLICATION")
    band(ax, 44, 57, "#FCF3E2", "BRIDGES")
    band(ax, 28, 41, "#EEF1F3", "AUTOPILOT")
    band(ax, 10, 25, "#EEF1F3", "SIMULATION")

    qgc = card(ax, 22, 86.5, 26, 8, "QGroundControl\n(UDP 18571)", "operator")
    # 5 modules row
    mods_y = 68.5
    bei = card(ax, 16, mods_y, 17, 9, "beidou_\npublisher", "module", 11.5)
    mis = card(ax, 35, mods_y, 18, 9, "mission_status\n(RTK-gated landing)", "module", 11)
    pp  = card(ax, 54, mods_y, 17, 9, "path_planning\n(RRT*)", "module", 11.5)
    rtk = card(ax, 73, mods_y, 17, 9, "rtk_positioning\n(Level 3)", "module", 11.5)
    td  = card(ax, 90.5, mods_y, 16, 9, "target_\ndetection\n(YOLO)", "module", 10.5)
    gzb = card(ax, 70, 50.5, 22, 8, "ros_gz_bridge", "bridge")
    xrce= card(ax, 40, 50.5, 28, 8, "micro-XRCE-DDS Agent\n(UDP 8888)", "bridge", 11)
    px4 = card(ax, 50, 34.5, 26, 8, "PX4 SITL", "sim")
    gz  = card(ax, 50, 17.5, 40, 9, "Gazebo Harmonic\n(GPS · camera · depth sensors)", "sim", 12)

    link(ax, gz, px4, "physics", rad=0.0, dx=-7)
    link(ax, gz, gzb, "sensors", rad=-0.15, dx=8, dy=-1)
    link(ax, px4, xrce, "uORB", rad=0.0, dx=-5)
    link(ax, xrce, td, "/px4_1/fmu/out/*_v1", rad=-0.2, lblpos=0.47, dx=0, dy=1)
    link(ax, gzb, rtk, "/gz/navsat", rad=0.0, dx=-9, dy=-1)
    link(ax, gzb, td, "/camera,/depth", rad=0.14, lblpos=0.62, dx=5, dy=-1)
    link(ax, rtk, mis, "viability", rad=0.15, dy=4)
    link(ax, td, mis, "detection", rad=0.2, dy=5)
    link(ax, bei, mis)
    link(ax, mis, pp, "/mission/waypoints", dy=-3.0)
    link(ax, px4, qgc, "MAVLink", rad=-0.25, dx=-22)
    save(fig, "d1_architecture")


# ============================================================ D2 — data flow
def d2():
    fig, ax = canvas(13, 7.5)
    ax.text(50, 97, "ROS 2 Data Flow — modules and the topics between them",
            ha="center", va="top", fontsize=16, fontweight="bold", color="#1f2d3d")
    bei = card(ax, 12, 78, 17, 11, "beidou_\npublisher", "module", 12)
    rtk = card(ax, 12, 30, 17, 11, "rtk_\npositioning", "module", 12)
    mis = card(ax, 40, 64, 18, 12, "mission_\nstatus", "module", 12.5)
    td  = card(ax, 50, 34, 17, 11, "target_\ndetection", "module", 12)
    pp  = card(ax, 75, 50, 17, 12, "path_\nplanning", "module", 12.5)
    out = card(ax, 75, 18, 22, 9, "flight\n(C4 / mission mode)", "io", 11)

    link(ax, bei, mis, "/target/emergency_coordinate", lblpos=0.55, dy=4)
    link(ax, bei, pp,  rad=0.22)
    link(ax, rtk, mis, "/rtk/mission_viability\n/uav/rtk_status", rad=0.12, lblpos=0.42, dx=-2)
    link(ax, rtk, pp,  "/uav/rtk_position", rad=-0.36, lblpos=0.2, dy=-6)
    link(ax, rtk, td,  "/uav/rtk_*", lblpos=0.72, dy=4)
    link(ax, mis, td,  "/mission/status", rad=0.12, lblpos=0.5, dx=6)
    link(ax, mis, pp,  "/mission/waypoints", lblpos=0.5, dy=4)
    link(ax, td,  mis, "/target/detection", rad=0.18, lblpos=0.5, dx=-7)
    link(ax, td,  pp,  "/target/location", rad=-0.12, lblpos=0.55, dy=-4)
    link(ax, pp,  out, "/planner/path", lblpos=0.5, dx=10)
    save(fig, "d2_dataflow")


# ============================================================ D3 — mission FSM
def d3():
    fig, ax = canvas(13, 6.2)
    ax.text(50, 96, "Mission State Machine — RTK-gated precision landing",
            ha="center", va="top", fontsize=16, fontweight="bold", color="#1f2d3d")
    y = 68
    idle = card(ax, 9,  y, 14, 9, "IDLE", "state", 12)
    dis  = card(ax, 27, y, 16, 9, "DISTRESS_\nRECEIVED", "state", 11)
    pln  = card(ax, 46, y, 16, 9, "MISSION_\nPLANNED", "state", 11)
    flt  = card(ax, 65, y, 14, 9, "IN_FLIGHT", "state", 11.5)
    tac  = card(ax, 86, y, 16, 9, "TARGET_\nACQUIRED", "state", 11)
    land = card(ax, 65, 40, 14, 9, "LANDING", "state", 12)
    hold = card(ax, 40, 22, 16, 9, "LANDING_\nHOLD", "hold", 11)
    comp = card(ax, 86, 40, 15, 9, "COMPLETE", "good", 11.5)
    abrt = card(ax, 18, 22, 14, 9, "ABORTED", "bad", 12)

    link(ax, idle, dis, "coordinate", dy=4.5)
    link(ax, dis, pln)
    link(ax, pln, flt)
    link(ax, flt, tac, "detection", dy=4.5)
    link(ax, tac, land, rad=0.15)
    link(ax, land, comp, "LANDING_VIABLE", dy=4)
    link(ax, land, hold, "degraded (gate)", rad=0.1, dx=-2, dy=2)
    link(ax, hold, comp, "re-converged", rad=0.0, lblpos=0.5, dy=2.6)
    link(ax, hold, abrt, "timeout", dy=4)
    save(fig, "d3_mission_fsm")


if __name__ == "__main__":
    d1(); d2(); d3()
    print("diagrams written:")
    for f in ("d1_architecture", "d2_dataflow", "d3_mission_fsm"):
        print("  ", f + ".png", "+", f + ".svg")
