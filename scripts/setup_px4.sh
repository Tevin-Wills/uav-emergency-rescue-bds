#!/bin/bash
# Sets up PX4-Autopilot and micro-XRCE-DDS Agent for the team project.
# Run once on a fresh Ubuntu 24.04 machine (native or WSL2).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== UAV Emergency Rescue System — PX4 Setup ==="

# --- 1. Install PX4 dependencies ---
echo "[1/4] Installing PX4 dependencies..."
# TODO: Uncomment and adjust the path to your PX4-Autopilot clone
# cd ~/PX4-Autopilot && bash ./Tools/setup/ubuntu.sh

# --- 2. Build PX4 SITL ---
echo "[2/4] Building PX4 SITL with Gazebo Harmonic..."
# TODO: Set PX4_AUTOPILOT_PATH to your local PX4 clone
# PX4_AUTOPILOT_PATH=~/PX4-Autopilot
# cd "$PX4_AUTOPILOT_PATH" && make px4_sitl gz_x500

# --- 3. Build micro-XRCE-DDS Agent v2.4.3 ---
echo "[3/4] Building micro-XRCE-DDS Agent v2.4.3..."
# IMPORTANT: Use v2.4.3 specifically — v3.x silently breaks the PX4 bridge
# git clone -b v2.4.3 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git ~/Micro-XRCE-DDS-Agent
# cd ~/Micro-XRCE-DDS-Agent && mkdir -p build && cd build
# cmake .. && make -j$(nproc) && sudo make install

# --- 4. Verify ---
echo "[4/4] Verifying installation..."
# TODO: Add version checks for px4 binary and MicroXRCEAgent

echo ""
echo "=== Setup complete. Run scripts/run_simulation.sh to start the stack. ==="
