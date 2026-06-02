# Level 2 PX4 Integration Notes

## 1. Integration Approach

Level 2 connects the RTK module to the PX4/Gazebo simulation stack through `ros_gz_bridge`. The bridge exposes the Gazebo navsat sensor as a standard ROS 2 `sensor_msgs/NavSatFix` topic without requiring `px4_msgs`.

```
PX4 SITL + Gazebo Harmonic
        ↓
Gazebo navsat sensor  (gz.msgs.NavSat, ~30 Hz)
        ↓
gz_navsat_bridge      (ros_gz_bridge parameter_bridge)
        ↓
/gz/navsat            (sensor_msgs/msg/NavSatFix)
        ↓
px4_pose_adapter_node (WGS84 → ENU via wgs84_to_enu())
        ↓
/uav/ground_truth     (nav_msgs/msg/Odometry, 10 Hz)
        ↓
rtk_positioning_node  (unchanged from Level 1)
```

---

## 2. Why ros_gz_bridge Instead of /fmu/out/vehicle_odometry

The PX4 uXRCE-DDS bridge publishes vehicle state on `/fmu/out/vehicle_odometry` as `px4_msgs/msg/VehicleOdometry`. This requires the `px4_msgs` ROS 2 package to be installed.

On this machine, `px4_msgs` is not installed. The Gazebo navsat sensor approach was chosen instead because:

1. `ros_gz_bridge` is already installed (`ros-jazzy-ros-gz-bridge`)
2. The Gazebo navsat sensor provides the raw GPS signal — more appropriate for RTK simulation than the PX4 EKF-filtered odometry output
3. No additional package installation is required

To verify: `ros2 pkg list | grep ros_gz`

---

## 3. Gazebo World and UAV Model

The PX4 simulation uses the default world at the ETH Zurich location.

| Parameter | Value |
|---|---|
| World origin latitude | 47.397971057728981° N |
| World origin longitude | 8.5461637398001447° E |
| World origin altitude | 0.0 m |
| UAV model name | `x500_1` (PX4 instance 1, launched with `-i 1`) |

These values were sampled live from the running Gazebo simulation during Phase 1 inspection.

The `px4_pose_adapter_node` uses these as the ENU reference origin. UAV position on `/uav/ground_truth` is expressed as (east_m, north_m, up_m) relative to this origin.

---

## 4. Gazebo Topics Used

| Gazebo topic | Type | Rate | Used by |
|---|---|---|---|
| `/world/default/model/x500_1/link/base_link/sensor/navsat_sensor/navsat` | `gz.msgs.NavSat` | ~30 Hz | `gz_navsat_bridge` |

The bridge remaps this topic to `/gz/navsat` as `sensor_msgs/msg/NavSatFix`.

Other Gazebo topics observed but not used:

| Topic | Reason not used |
|---|---|
| `/world/default/dynamic_pose/info` | `gz.msgs.Pose_V` — no direct NavSat; would need world-frame ENU extraction |
| `/model/x500_1/odometry_with_covariance` | No publisher active during inspection |
| `/fmu/out/vehicle_odometry` (ROS 2) | Requires `px4_msgs`, not installed |

---

## 5. micro-XRCE-DDS Agent

The agent bridges PX4 uORB topics to DDS at UDP port 8888.

Binary location: `~/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent`

Started automatically by `~/launch_sim_24.sh`. The agent is running when Level 2 is used but its topics are not consumed by the RTK module (px4_msgs not installed).

---

## 6. Full Run Sequence

### Terminal 1 — PX4 SITL + Gazebo

```bash
~/launch_sim_24.sh
```

Wait until the Gazebo window shows the UAV and the PX4 console prints boot messages.

### Terminal 2 — Level 2 RTK module

```bash
cd ~/uav-emergency-rescue-bds/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
```

### Verification commands

```bash
# In a third terminal (with ROS 2 sourced)
ros2 topic list
ros2 topic echo /uav/ground_truth --once
ros2 topic echo /rtk/simulated_rtcm --once
ros2 topic echo /uav/rtk_position --once
ros2 topic echo /uav/rtk_status --once
ls ~/uav-emergency-rescue-bds/results/logs/rtk_positioning/level2/
```

### Level 1 (no PX4/Gazebo needed)

```bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

---

## 7. Known Limitations

| Limitation | Explanation |
|---|---|
| UAV must be armed and moving for meaningful RTK data | When PX4 is idle on the ground, the navsat sensor reports a fixed coordinate — errors will be near zero |
| No real RTCM injection | Correction quality is simulated; PX4's internal GNSS state is not affected |
| Flat-earth approximation | `wgs84_to_enu()` uses a tangent-plane model, accurate to ~1 m over 1 km range |
| Single UAV instance | Launch script uses `-i 1`; if instance number changes, the Gazebo topic suffix (`x500_1`) must be updated in `level2_rtk_params.yaml` and the launch file |

---

## 8. Future Real RTK Integration Path

When real RTK hardware becomes available, the following changes would be needed:

1. Replace `gz_navsat_bridge` + `px4_pose_adapter_node` with a real GNSS receiver driver publishing `NavSatFix` on `/gz/navsat` (or remap directly to `/uav/ground_truth`)
2. Replace `rtcm_correction_simulator_node` with a node that reads real RTCM binary data and forwards it via MAVLink `GPS_RTCM_DATA` to PX4
3. Replace the `SimulatedRtcm`-based status logic in `rtk_positioning_node` with status derived from the real receiver's fix type

The RTK core logic (`gnss_noise_model`, `rtk_correction_model`, `coordinate_transform`, `rtk_status_manager`) does not need to change.
