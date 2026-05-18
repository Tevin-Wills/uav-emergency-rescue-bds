#!/bin/bash
# Builds all ROS2 packages in the workspace.
# Source ROS2 Jazzy before running this script.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(dirname "$SCRIPT_DIR")/ros2_ws"

echo "=== UAV Emergency Rescue System — ROS2 Build ==="

# Check ROS2 is sourced
if [ -z "$ROS_DISTRO" ]; then
    echo "[ERROR] ROS2 is not sourced. Run: source /opt/ros/jazzy/setup.bash"
    exit 1
fi

echo "[INFO] ROS_DISTRO: $ROS_DISTRO"
echo "[INFO] Workspace: $WS_DIR"

cd "$WS_DIR"

# --- Build ---
echo "[1/2] Building workspace with colcon..."
colcon build --symlink-install

# --- Source ---
echo "[2/2] Build complete. To use the workspace, run:"
echo "  source $WS_DIR/install/setup.bash"
