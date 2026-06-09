#!/bin/bash
# Level 3 RTK simulation launcher — resilient RTK for disaster rescue.
# Requires PX4/Gazebo already running before calling this script.
#
# Usage:
#   ./run_level3.sh                    # Run 2: compound disaster scenario (default)
#   ./run_level3.sh total_failure      # Run 3: total failure / GNSS_ONLY lower bound
#
# Run both scenarios (sequential — wait for Ctrl-C between runs):
#   ./run_level3.sh && ./run_level3.sh total_failure

set -e

SCENARIO="${1:-compound_disaster}"

if [[ "$SCENARIO" != "compound_disaster" && "$SCENARIO" != "total_failure" ]]; then
    echo "[launch] ERROR: Unknown scenario '$SCENARIO'."
    echo "[launch] Valid values: compound_disaster  total_failure"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$SCRIPT_DIR/ros2_ws"

echo "[launch] Cleaning up any stale ROS 2 processes..."
pkill -f "rtk_positioning"             2>/dev/null || true
pkill -f "base_station_node"           2>/dev/null || true
pkill -f "px4_pose_adapter"            2>/dev/null || true
pkill -f "rtcm_correction_simulator"   2>/dev/null || true
pkill -f "rtk_positioning_node"        2>/dev/null || true
pkill -f "logger_node"                 2>/dev/null || true
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

echo "[launch] DDS ports clear. Starting Level 3 — scenario: $SCENARIO"
source /opt/ros/jazzy/setup.bash
source "$WS/install/setup.bash"
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

exec ros2 launch rtk_positioning level3_resilient_rtk.launch.py scenario:="$SCENARIO"
