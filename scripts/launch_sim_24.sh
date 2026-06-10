#!/bin/bash
# Launch the PX4 SITL + Gazebo + micro-XRCE-DDS Agent backbone (Ubuntu 24.04, PX4 instance 1).
# Requires: PX4 built, micro-XRCE-DDS Agent built, (QGC on the GCS host for mission-mode flight).
#
# Sim model is switchable via SIM_MODEL (default gz_x500 = GPS only, no camera):
#   ./scripts/launch_sim_24.sh                      # RTK tier (no camera) — runs headless on WSL
#   SIM_MODEL=gz_x500_depth ./scripts/launch_sim_24.sh   # perception tier (camera+depth) — NEEDS a GPU host
#
# NOTE for the perception tier (gz_x500_depth): the Gazebo model name and sensor
# topics may change (e.g. x500_depth_*). After launch, confirm the real topics:
#   gz topic -l | grep -iE "navsat|image|depth"
# then pass the RGB topic to bringup:  rgb_gz_topic:=<actual gz RGB topic>
# and, if the model name changed, update the navsat bridge topic in
# rtk_positioning/launch/level3_resilient_rtk.launch.py accordingly.

set -e

SIM_MODEL="${SIM_MODEL:-gz_x500}"
PX4_DIR="$HOME/PX4-Autopilot"
BUILD_DIR="$PX4_DIR/build/px4_sitl_default"

# Strip Windows paths and ROS 2 env to prevent protobuf conflict during PX4 launch.
CLEAN_PATH=$(echo "$PATH" | tr ':' '\n' | grep -v '/mnt/c' | grep -v '/opt/ros' | tr '\n' ':' | sed 's/:$//')
export PATH="$CLEAN_PATH"
unset AMENT_PREFIX_PATH
unset CMAKE_PREFIX_PATH
unset PYTHONPATH
unset ROS_DISTRO

# Source Gazebo environment
source "$BUILD_DIR/rootfs/gz_env.sh"

echo "[launch] Starting PX4 SITL + Gazebo (model=$SIM_MODEL, instance 1, GCS port 18571, headless)..."
PX4_SIM_MODEL="$SIM_MODEL" GZ_IP=127.0.0.1 HEADLESS=1 "$BUILD_DIR/bin/px4" -i 1 &
PX4_PID=$!

# Wait for PX4 to initialize before starting the bridge
echo "[launch] Waiting for PX4 to come up..."
sleep 8

# micro-XRCE-DDS Agent (PX4 <-> ROS 2 bridge). Try the local build, then a system install.
AGENT_BIN="$HOME/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent"
[ -x "$AGENT_BIN" ] || AGENT_BIN="$(command -v MicroXRCEAgent || echo /usr/local/bin/MicroXRCEAgent)"
if [ -x "$AGENT_BIN" ]; then
    echo "[launch] Starting micro-XRCE-DDS Agent ($AGENT_BIN)..."
    "$AGENT_BIN" udp4 -p 8888 &
    AGENT_PID=$!
else
    echo "[launch] WARNING: micro-XRCE-DDS Agent not found — skipping ROS 2 bridge"
fi

echo ""
echo "[launch] Simulation stack running."
echo "  Sim model    : $SIM_MODEL"
echo "  PX4 instance : 1  (MAV_SYS_ID=2, topics under /px4_1/*)"
echo "  GCS UDP port : 18571  (point QGC here)"
echo "  ROS 2 bridge : source /opt/ros/jazzy/setup.bash, then run the ROS 2 nodes"
echo ""
echo "Press Ctrl+C to stop all processes."

cleanup() {
    echo "[launch] Shutting down..."
    kill $PX4_PID 2>/dev/null
    kill $AGENT_PID 2>/dev/null
    wait
    exit 0
}
trap cleanup SIGINT SIGTERM

wait $PX4_PID
