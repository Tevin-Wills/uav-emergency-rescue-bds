#!/bin/bash
# Launch the PX4 SITL + Gazebo + micro-XRCE-DDS Agent backbone (Ubuntu 24.04, PX4 instance 1).
# Requires: PX4 built, micro-XRCE-DDS Agent built, (QGC on the GCS host for mission-mode flight).
#
# Sim model is switchable via SIM_MODEL (default gz_x500 = GPS only, no camera):
#   ./scripts/launch_sim_24.sh                      # RTK tier (no camera) — runs headless on WSL
#   SIM_MODEL=gz_x500_depth ./scripts/launch_sim_24.sh   # perception tier (camera+depth)
#
# Perception tier (gz_x500_depth) runs on this WSL box via hardware OpenGL on the
# NVIDIA GPU (the MESA d3d12 exports below). With -i 1 the depth model spawns as
# "x500_depth_1"; the navsat bridge and bringup RGB default already target that name,
# so no manual topic edit is needed. To sanity-check after launch:
#   gz topic -l | grep -iE "navsat|image|depth"
# If you switch back to gz_x500 (GPS only), pass gz_model_name:=x500_1 to the RTK launch.

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

# Hardware OpenGL on WSL2: route Gazebo's GL through the d3d12 (Dozen) driver on the
# NVIDIA GPU. Without this, WSL falls back to llvmpipe (software GL) and the camera/
# depth sensors render empty or far too slowly to be usable. Harmless for gz_x500
# (GPS only). Override per-shell if you need a different adapter.
export MESA_LOADER_DRIVER_OVERRIDE="${MESA_LOADER_DRIVER_OVERRIDE:-d3d12}"
export GALLIUM_DRIVER="${GALLIUM_DRIVER:-d3d12}"
export MESA_D3D12_DEFAULT_ADAPTER_NAME="${MESA_D3D12_DEFAULT_ADAPTER_NAME:-NVIDIA}"

# GPU preflight: if we're routing GL through the d3d12 (NVIDIA/dxgkrnl) path, probe
# it with a single bounded glxinfo call BEFORE Gazebo starts. A broken d3d12/dxgkrnl
# state can crash the entire WSL VM when Gazebo renders sensors; this fails loudly and
# early instead, so you keep your shell and a readable error. Only runs for the d3d12
# path — software GL (llvmpipe) skips it entirely.
gpu_preflight() {
    if [ "$GALLIUM_DRIVER" != "d3d12" ]; then
        echo "[preflight] GL driver is '$GALLIUM_DRIVER' (software) — skipping GPU probe."
        return 0
    fi
    if ! command -v glxinfo >/dev/null 2>&1; then
        echo "[preflight] WARNING: glxinfo not found (apt install mesa-utils) — cannot verify GPU; continuing."
        return 0
    fi

    echo "[preflight] Probing d3d12 GPU path (adapter=${MESA_D3D12_DEFAULT_ADAPTER_NAME})..."
    local out renderer
    # timeout bounds the probe so a hung/faulting driver can't stall (or take down) launch.
    out=$(timeout 15 glxinfo -B 2>/dev/null) || true
    renderer=$(echo "$out" | grep -i "OpenGL renderer" | sed 's/.*: //')

    if [ -z "$renderer" ]; then
        echo "[preflight] ERROR: GL probe returned nothing — the d3d12/dxgkrnl path is not responding."
        echo "[preflight] This is the state that crashes the WSL VM. Aborting before Gazebo starts."
        echo "[preflight] Fixes: (1) run 'wsl --shutdown' from Windows and retry, or"
        echo "[preflight]        (2) run on software GL:  GALLIUM_DRIVER=llvmpipe MESA_LOADER_DRIVER_OVERRIDE=swrast $0"
        exit 1
    fi

    if echo "$renderer" | grep -qi "llvmpipe"; then
        echo "[preflight] ERROR: requested d3d12 (NVIDIA) but GL fell back to software '$renderer'."
        echo "[preflight] Sensor rendering would be unusably slow and the GPU path is unhealthy. Aborting."
        echo "[preflight] Run 'wsl --update' + 'wsl --shutdown' from Windows, or launch with llvmpipe explicitly."
        exit 1
    fi

    echo "[preflight] GPU OK — renderer: $renderer"
}

gpu_preflight

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
