#!/usr/bin/env python3
"""
Generate the system-integration progress-report figures.

Plots (matplotlib + presentation.mplstyle): P1 RTK error budget, P2 landing-gate timelines.
Diagrams (graphviz dot): D1 architecture, D2 data-flow topic graph, D3 mission FSM.

Style assets adapted from the scientific-visualization skill (Okabe-Ito palette,
publication/presentation mplstyle). Run:  python3 generate_integration_figures.py
"""
import math
import os
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)
plt.style.use(os.path.join(HERE, "presentation.mplstyle"))   # Okabe-Ito, clean spines, 300 dpi

# Okabe-Ito (colorblind-safe)
BLUE, ORANGE, GREEN, RED, GREY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#666666"


# ----------------------------------------------------------------------------- P1
def rtk_sigma(floor, baseline_km, ppm=1.0):
    return math.sqrt(floor ** 2 + (baseline_km * ppm / 1000.0) ** 2)

def floor_for_baseline(baseline_km, fixed_limit=20.0, max_km=50.0):
    if baseline_km > max_km:
        return 1.5
    if baseline_km > fixed_limit:
        return 0.25
    return 0.03

def fig_p1():
    bl = np.linspace(0, 60, 600)
    sig = np.array([rtk_sigma(floor_for_baseline(b), b) for b in bl])

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    # state bands (light, behind)
    for x0, x1, c, lab in [(0, 20, GREEN, "RTK_FIXED"),
                           (20, 50, ORANGE, "RTK_FLOAT"),
                           (50, 60, RED, "GNSS_ONLY")]:
        ax.axvspan(x0, x1, color=c, alpha=0.07, zorder=0)
    ax.plot(bl, sig, color=BLUE, lw=2.8, zorder=3)
    ax.set_yscale("log")
    ax.set_xlim(0, 60)
    ax.set_ylim(0.02, 3)
    ax.set_xlabel("Baseline  (base ↔ drone distance)  [km]")
    ax.set_ylabel("RTK horizontal σ  [m]   (log scale)")
    ax.set_title("RTK error budget — accuracy degrades with baseline (1 ppm model)")
    # state labels, centered in their band, clear of the curve
    ax.text(10, 1.9, "RTK_FIXED\n~3 cm", ha="center", va="top", color=GREEN, fontweight="bold")
    ax.text(35, 1.9, "RTK_FLOAT\n~25 cm", ha="center", va="top", color=ORANGE, fontweight="bold")
    ax.text(55, 1.9, "GNSS_ONLY\n~1.5 m", ha="center", va="top", color=RED, fontweight="bold")
    # threshold markers
    for x, lab in [(20, "FIXED limit\n20 km"), (50, "single-base\nlimit 50 km")]:
        ax.axvline(x, color=GREY, ls="--", lw=1.0, alpha=0.7, zorder=1)
        ax.text(x - 0.6, 0.024, lab, ha="right", va="bottom", fontsize=10, color=GREY)
    ax.grid(True, which="both", axis="y", alpha=0.2, zorder=0)
    fig.savefig(os.path.join(FIG, "p1_rtk_error_budget.png"))
    plt.close(fig)


# ----------------------------------------------------------------------------- P2
def fig_p2():
    phases = ["IDLE", "DISTRESS_RECEIVED", "MISSION_PLANNED", "IN_FLIGHT",
              "TARGET_ACQUIRED", "LANDING", "LANDING_HOLD", "ABORTED", "COMPLETE"]
    yidx = {p: i for i, p in enumerate(phases)}
    tA = [0, 2, 4, 6, 8, 10, 14, 16];  pA = ["DISTRESS_RECEIVED","MISSION_PLANNED","IN_FLIGHT",
          "TARGET_ACQUIRED","LANDING","LANDING_HOLD","LANDING","COMPLETE"]
    tB = [0, 2, 4, 6, 8, 10, 18];      pB = ["DISTRESS_RECEIVED","MISSION_PLANNED","IN_FLIGHT",
          "TARGET_ACQUIRED","LANDING","LANDING_HOLD","ABORTED"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), sharey=True)
    for ax, (t, p, title, col) in zip(axes, [
            (tA, pA, "A · RTK re-converges → lands (COMPLETE)", GREEN),
            (tB, pB, "B · RTK stays degraded → aborts (ABORTED)", RED)]):
        y = [yidx[x] for x in p]
        ax.step(t, y, where="post", color=col, lw=2.8, zorder=3)
        ax.scatter(t, y, color=col, s=55, zorder=4)
        ax.axvspan(10, t[-1], color=col, alpha=0.06, zorder=0)
        ax.axvline(10, color=GREY, ls="--", lw=1.0, alpha=0.7)
        ax.text(10.2, 0.2, "RTK gate\ndecision", fontsize=10, color=GREY, va="bottom")
        ax.set_title(title, fontsize=14)
        ax.set_xlabel("time  [s]")
        ax.set_xlim(-0.5, max(t) + 1)
        ax.grid(True, axis="x", alpha=0.2)
    axes[0].set_yticks(range(len(phases)))
    axes[0].set_yticklabels(phases)
    fig.suptitle("RTK-gated precision landing — verified mission_status behaviour",
                 fontsize=16, fontweight="bold")
    fig.savefig(os.path.join(FIG, "p2_landing_gate_timeline.png"))
    plt.close(fig)


# ----------------------------------------------------------------------------- diagrams
_COMMON = (
    'graph [fontname="Helvetica", fontsize=13, labelloc="t", bgcolor="white", '
    'nodesep=0.45, ranksep=0.7, pad=0.3];\n'
    'node  [fontname="Helvetica", fontsize=12, shape=box, style="rounded,filled", '
    'height=0.6, margin="0.18,0.10", penwidth=1.2, color="#444444"];\n'
    'edge  [fontname="Helvetica", fontsize=10, color="#555555", penwidth=1.1, arrowsize=0.8];\n'
)

DOTS = {
"d1_architecture": (
'digraph D1 {\n  rankdir=TB; splines=spline; ' + _COMMON +
'  label="System architecture — tools, bridges, and the 5 ROS 2 modules";\n'
'  subgraph cluster_op { label="Operator (Windows)"; style="rounded,dashed"; color="#999999"; fontsize=12;\n'
'    QGC [label="QGroundControl\\n(UDP 18571)", fillcolor="#D6E4F7"]; }\n'
'  subgraph cluster_app { label="ROS 2 application (Jazzy)"; style="rounded,dashed"; color="#009E73"; fontsize=12;\n'
'    BEI [label="beidou_publisher", fillcolor="#D9EFE3"];\n'
'    MIS [label="mission_status\\n(RTK-gated landing)", fillcolor="#D9EFE3"];\n'
'    PP  [label="path_planning\\n(RRT*)", fillcolor="#D9EFE3"];\n'
'    RTK [label="rtk_positioning (L3)", fillcolor="#D9EFE3"];\n'
'    TD  [label="target_detection\\n(YOLO)", fillcolor="#D9EFE3"]; }\n'
'  subgraph cluster_br { label="Bridges"; style="rounded,dashed"; color="#E69F00"; fontsize=12;\n'
'    GZB [label="ros_gz_bridge", fillcolor="#FBE7C6"];\n'
'    XRCE[label="micro-XRCE-DDS Agent\\n(UDP 8888)", fillcolor="#FBE7C6"]; }\n'
'  PX4 [label="PX4 SITL", fillcolor="#F7D9CC"];\n'
'  GZ  [label="Gazebo Harmonic\\n(GPS · camera · depth)", fillcolor="#F7D9CC"];\n'
'  GZ -> PX4 [label="physics"]; GZ -> GZB [label="sensors"]; PX4 -> XRCE [label="uORB"];\n'
'  GZB -> RTK [label="/gz/navsat"]; GZB -> TD [label="/camera,/depth"];\n'
'  XRCE -> TD [label="/px4_1/fmu/out/*_v1"];\n'
'  BEI -> MIS; MIS -> PP; RTK -> MIS [label="viability"]; RTK -> TD; TD -> MIS [label="detection"];\n'
'  PX4 -> QGC [label="MAVLink"]; QGC -> PX4 [label=".plan"];\n}\n'),

"d2_dataflow": (
'digraph D2 {\n  rankdir=LR; splines=spline; ' + _COMMON +
'  label="ROS 2 data flow — modules and the topics between them";\n'
'  node [fillcolor="#D9EFE3"];\n'
'  BEI [label="beidou_\\npublisher"]; MIS [label="mission_\\nstatus"];\n'
'  PP [label="path_\\nplanning"]; RTK [label="rtk_\\npositioning"]; TD [label="target_\\ndetection"];\n'
'  OUT [label="flight\\n(C4 / mission mode)", fillcolor="#EDEDED"];\n'
'  { rank=same; BEI; RTK; }\n'
'  BEI -> MIS [label="/target/emergency_coordinate"];\n'
'  BEI -> PP  [label="(same)"];\n'
'  RTK -> MIS [label="/rtk/mission_viability\\n/uav/rtk_status"];\n'
'  RTK -> PP  [label="/uav/rtk_position"];\n'
'  RTK -> TD  [label="/uav/rtk_*"];\n'
'  MIS -> PP  [label="/mission/waypoints"];\n'
'  MIS -> TD  [label="/mission/status"];\n'
'  TD  -> MIS [label="/target/detection"];\n'
'  TD  -> PP  [label="/target/location"];\n'
'  PP  -> OUT [label="/planner/path"];\n}\n'),

"d3_mission_fsm": (
'digraph D3 {\n  rankdir=LR; splines=spline; ' + _COMMON +
'  label="Mission state machine — RTK-gated precision landing";\n'
'  node [fillcolor="#D6E4F7"];\n'
'  IDLE -> DISTRESS_RECEIVED [label="coordinate"];\n'
'  DISTRESS_RECEIVED -> MISSION_PLANNED -> IN_FLIGHT;\n'
'  IN_FLIGHT -> TARGET_ACQUIRED [label="detection"];\n'
'  TARGET_ACQUIRED -> LANDING;\n'
'  LANDING -> COMPLETE [label="LANDING_VIABLE"];\n'
'  LANDING -> LANDING_HOLD [label="degraded (gate)"];\n'
'  LANDING_HOLD -> COMPLETE [label="re-converged"];\n'
'  LANDING_HOLD -> ABORTED [label="timeout"];\n'
'  COMPLETE [fillcolor="#D9EFE3"]; ABORTED [fillcolor="#F7D9CC"]; LANDING_HOLD [fillcolor="#FBE7C6"];\n}\n'),
}

def render_dots():
    for name, dot in DOTS.items():
        src = os.path.join(FIG, name + ".dot")
        with open(src, "w") as f:
            f.write(dot)
        subprocess.run(["dot", "-Tpng", "-Gdpi=160", src,
                        "-o", os.path.join(FIG, name + ".png")], check=True)


if __name__ == "__main__":
    fig_p1()
    fig_p2()
    render_dots()
    print("figures written to", FIG)
    for f in sorted(os.listdir(FIG)):
        if f.endswith(".png"):
            print("  ", f)
