#!/usr/bin/env bash
# verify_integration.sh — pre-integration check for the beidou_short_message node.
# Run from the ros2_ws workspace root AFTER:
#   colcon build --packages-select interfaces beidou_short_message
#   source install/setup.bash
#
# Checks:
#   1. Default datum-derived sim behaviour (what the group bringup expects)
#   2. 112-bit binary rescue payload decode (T001)
#   3. Legacy 64-bit binary decode
# Exit code 0 = ready for integration.

set -u
PASS=0
FAIL=0

check() {  # check <name> <raw_message|-> <expected_grep_in_topic_echo>
    local name="$1" rawmsg="$2" expect="$3"
    local logfile node_pid echo_out

    logfile=$(mktemp)
    if [ "$rawmsg" = "-" ]; then
        ros2 run beidou_short_message beidou_publisher_node >"$logfile" 2>&1 &
    else
        ros2 run beidou_short_message beidou_publisher_node --ros-args \
            -p raw_message:="$rawmsg" >"$logfile" 2>&1 &
    fi
    node_pid=$!
    sleep 3   # node publishes immediately + heartbeat every 2 s

    echo_out=$(timeout 6 ros2 topic echo /target/emergency_coordinate --once 2>/dev/null)
    kill "$node_pid" 2>/dev/null
    wait "$node_pid" 2>/dev/null

    if echo "$echo_out" | grep -q "$expect"; then
        echo "[PASS] $name"
        PASS=$((PASS+1))
    else
        echo "[FAIL] $name — expected '$expect' on /target/emergency_coordinate"
        echo "------ node log ------"; cat "$logfile"; echo "----------------------"
        echo "------ topic echo ----"; echo "$echo_out"; echo "----------------------"
        FAIL=$((FAIL+1))
    fi
    rm -f "$logfile"
}

echo "=== beidou_short_message integration verification ==="

# 1. Default sim behaviour: Zurich datum + offset -> lat ~47.398
check "default datum-derived coordinate (group sim contract)" \
      "-" \
      "latitude: 47.39"

# 2. 112-bit rescue payload, lab record T001 -> lat 49.0068822 at 7dp
check "112-bit binary rescue payload (T001)" \
      '$CCTXM,0,BIN:1D35DB5605079637007200A00101*CS' \
      "latitude: 49.0068822"

# 3. Legacy 64-bit payload (old firmware logs) -> lat 30.4196
check "legacy 64-bit binary payload" \
      '$CCTXM,0,BIN:0004A44400125B21*CS' \
      "latitude: 30.4196"

echo
if [ "$FAIL" -eq 0 ]; then
    echo "ALL CHECKS PASSED — ready for integration ($PASS/3)"
    exit 0
else
    echo "$FAIL CHECK(S) FAILED — fix before the joint session"
    exit 1
fi
