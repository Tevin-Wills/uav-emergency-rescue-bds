#!/bin/bash
# Level 1 RTK simulation launcher.
# Cleans up any stale ROS 2 processes before starting to avoid DDS port conflicts.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$SCRIPT_DIR/ros2_ws"

echo "[launch] Cleaning up any stale ROS 2 processes..."
pkill -f "rtk_positioning"    2>/dev/null || true
pkill -f "base_station_node"  2>/dev/null || true
pkill -f "simulated_uav_node" 2>/dev/null || true
pkill -f "logger_node"        2>/dev/null || true
pkill -f "rtk_positioning_node" 2>/dev/null || true
sleep 1

# Verify DDS ports are free
if ss -ulnp | grep -qE ":7400|:7410"; then
    echo "[launch] WARNING: DDS ports still held by another process:"
    ss -ulnp | grep -E ":7400|:7410"
    echo "[launch] Run: pkill -f ros2   then retry."
    exit 1
fi

echo "[launch] DDS ports clear. Starting Level 1 simulation..."
source /opt/ros/jazzy/setup.bash
source "$WS/install/setup.bash"
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

exec ros2 launch rtk_positioning level1_rtk_sim.launch.py
