#!/bin/bash
# Launches the full UAV Emergency Rescue System:
# PX4 + Gazebo + micro-XRCE-DDS Agent + all ROS2 modules via bringup.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(dirname "$SCRIPT_DIR")/ros2_ws"

echo "=== UAV Emergency Rescue System — Full System Launch ==="

# Check ROS2 is sourced
if [ -z "$ROS_DISTRO" ]; then
    echo "[ERROR] ROS2 is not sourced. Run: source /opt/ros/jazzy/setup.bash"
    exit 1
fi

# Check workspace is built
if [ ! -f "$WS_DIR/install/setup.bash" ]; then
    echo "[ERROR] Workspace not built. Run: scripts/build_ros2.sh"
    exit 1
fi

source "$WS_DIR/install/setup.bash"

# --- 1. Start simulation stack ---
echo "[1/2] Starting simulation stack..."
# TODO: Call run_simulation.sh or inline PX4 + agent startup here
bash "$SCRIPT_DIR/run_simulation.sh" &

# Brief wait for PX4 to initialize before launching ROS2 nodes
sleep 5

# --- 2. Launch all ROS2 modules ---
echo "[2/2] Launching all ROS2 modules via bringup..."
# TODO: Uncomment when bringup package is implemented
# ros2 launch bringup full_system.launch.py

echo ""
echo "=== Full system is running. Monitor topics with: ros2 topic list ==="
