#!/bin/bash
# Starts PX4 SITL + Gazebo Harmonic and the micro-XRCE-DDS Agent.
# Opens each component in a new terminal tab/window.

set -e

# TODO: Set these paths to match your local installation
PX4_AUTOPILOT_PATH="${PX4_AUTOPILOT_PATH:-$HOME/PX4-Autopilot}"
XRCE_AGENT_BIN="${XRCE_AGENT_BIN:-$HOME/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent}"
PX4_INSTANCE="${PX4_INSTANCE:-1}"
PX4_UDP_PORT="${PX4_UDP_PORT:-18571}"

echo "=== UAV Emergency Rescue System — Simulation Launch ==="
echo "[INFO] PX4 path:   $PX4_AUTOPILOT_PATH"
echo "[INFO] XRCE agent: $XRCE_AGENT_BIN"
echo "[INFO] PX4 instance: $PX4_INSTANCE (UDP port $PX4_UDP_PORT)"

# --- 1. Start PX4 + Gazebo ---
echo "[1/2] Starting PX4 SITL + Gazebo Harmonic..."
# TODO: Uncomment and adjust for your environment
# cd "$PX4_AUTOPILOT_PATH"
# PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL=x500 ./build/px4_sitl_default/bin/px4 -i $PX4_INSTANCE &
# PX4_PID=$!

# --- 2. Start micro-XRCE-DDS Agent ---
echo "[2/2] Starting micro-XRCE-DDS Agent on UDP port 8888..."
# TODO: Uncomment when agent binary is available
# "$XRCE_AGENT_BIN" udp4 -p 8888 &

echo ""
echo "=== Simulation running. Open QGroundControl on Windows (UDP $PX4_UDP_PORT). ==="
echo "    In Terminal 2: source ROS2 and run your nodes."
