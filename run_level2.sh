#!/bin/bash
# Level 2 RTK simulation launcher (requires PX4/Gazebo already running).
# Cleans up any stale ROS 2 processes before starting to avoid DDS port conflicts.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$SCRIPT_DIR/ros2_ws"

echo "[launch] Cleaning up any stale ROS 2 processes..."
pkill -f "rtk_positioning"        2>/dev/null || true
pkill -f "base_station_node"      2>/dev/null || true
pkill -f "px4_pose_adapter"       2>/dev/null || true
pkill -f "rtcm_correction_sim"    2>/dev/null || true
pkill -f "rtk_positioning_node"   2>/dev/null || true
pkill -f "logger_node"            2>/dev/null || true
sleep 1

# Verify DDS ports are not held by unexpected processes.
# MicroXRCEAgent is the PX4-ROS2 bridge and is allowed to hold these ports.
UNEXPECTED=$(ss -ulnp | grep -E ":7400|:7410" | grep -v "MicroXRCEAgent" || true)
if [ -n "$UNEXPECTED" ]; then
    echo "[launch] WARNING: DDS ports held by an unexpected process:"
    echo "$UNEXPECTED"
    echo "[launch] Run: pkill -f ros2   then retry."
    exit 1
fi

echo "[launch] DDS ports clear. Starting Level 2 simulation..."
source /opt/ros/jazzy/setup.bash
source "$WS/install/setup.bash"
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

exec ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
