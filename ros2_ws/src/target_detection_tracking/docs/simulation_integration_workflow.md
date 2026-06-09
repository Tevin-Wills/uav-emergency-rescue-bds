# Target Detection Simulation Integration Workflow

## Runtime Method

The original standalone target-detection work used KITTI stereo images:

```text
left image + right image -> disparity -> depth -> camera xyz
```

The simulation runtime uses the PX4 Gazebo Oak-D Lite model:

```text
RGB image + /depth_camera -> depth -> camera xyz
```

This keeps the stereo/depth geolocalization concept, but Gazebo provides the depth image directly. KITTI scripts remain useful for offline validation and model development; they are not required for the ROS runtime.

## Launch Order

1. Start PX4 SITL and Gazebo with a depth-capable x500:

```bash
cd ~/Projects/PX4-Autopilot
make px4_sitl gz_x500_depthlight_walls
```

2. Start Micro XRCE-DDS Agent in a separate terminal.

3. Start the RTK Level 2 simulator:

```bash
cd ~/Projects/UAVsim/uav-emergency-rescue-bds/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
```

4. Find the Gazebo RGB image topic:

```bash
gz topic -l | grep IMX214
```

5. Launch target detection:

```bash
ros2 launch target_detection_tracking target_detection_sim.launch.py \
  start_depth_bridge:=true \
  start_rgb_bridge:=true \
  rgb_gz_topic:=/world/default/model/x500_1/link/camera_link/sensor/IMX214/image
```

Replace `rgb_gz_topic` with the value found in step 4 if the world or model name differs.

## Verification

Check incoming sensor streams:

```bash
ros2 topic hz /camera/image_raw
ros2 topic hz /depth_camera
ros2 topic echo /fmu/out/vehicle_local_position --once
ros2 topic echo /uav/rtk_position --once
```

Check target outputs:

```bash
ros2 topic echo /target/detection
ros2 topic echo /target/location
```

Evidence files:

```text
results/screenshots/target_detection_tracking/
results/logs/target_detection_tracking/detections.jsonl
```

## Coordinate Contract

The core uses the project camera convention:

```text
x: forward
y: left
z: up
```

PX4 local position is received in NED:

```text
x: north
y: east
z: down
```

The public `/target/location` output is `geometry_msgs/PoseStamped` in local ENU:

```text
pose.position.x = east metres
pose.position.y = north metres
pose.position.z = up metres
frame_id = px4_local_enu
```

## ROS 1 Adaptation Path

The reusable modules in `src/target_detection_tracking/` are ROS-agnostic. A future ROS 1 wrapper should:

- Subscribe to the equivalent ROS 1 `sensor_msgs/Image`, `sensor_msgs/NavSatFix`, `std_msgs/String`, and vehicle-pose source.
- Convert ROS 1 messages into the same core dataclasses.
- Publish `/target/detection` as `std_msgs/Bool`.
- Publish `/target/location` as `geometry_msgs/PoseStamped`.
- Keep frame remapping in the wrapper if ROS 1 path planning expects a different local frame.

Because the public messages are standard ROS messages, `ros1_bridge` is also a viable integration path if ROS 2 target detection and ROS 1 path planning must run side by side.

## Troubleshooting

- If `/camera/image_raw` is silent, run `gz topic -l | grep IMX214` and override `rgb_gz_topic`.
- If `/depth_camera` is silent, confirm the simulation target is `gz_x500_depth` or `gz_x500_depthlight`.
- If the node logs `Detector unavailable`, install `ultralytics` into the same Python environment used by ROS 2 or pass a valid `model_path`.
- If `/target/detection` is true but `/target/location` is absent, check `/fmu/out/vehicle_local_position`; the default config requires a fresh local pose before publishing a location.
