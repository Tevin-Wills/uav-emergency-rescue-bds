# target_detection_tracking

**Owner:** Student 3  
**Responsibility:** Camera-based target detection, tracking, geolocation, and later fixed-point landing support.

## Overview

This package integrates the earlier `UAVrescuesystem/target_detection` work into the group simulation workflow. The runtime path is middleware-aware only at the edge:

```text
Gazebo RGB image
  -> YOLO person detector
  -> bbox ROI in Gazebo depth image
  -> camera-frame xyz: x forward, y left, z up
  -> PX4 local pose/heading + RTK fix
  -> /target/detection and /target/location
```

The core detection/geolocation modules under `src/target_detection_tracking/` do not import `rclpy`, `rospy`, or PX4 messages. The current wrapper is ROS 2 because the group repo is ROS 2, but the same core can later be wrapped with ROS 1 `rospy` if path planning and collision avoidance move to ROS 1.

The simulation version uses Gazebo's Oak-D Lite RGB plus `/depth_camera` output. This replaces KITTI-style left/right disparity at runtime while preserving the stereo-depth geolocation concept.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/target/detection` | `std_msgs/Bool` | `true` when a target has a valid RGB detection and depth estimate |
| `/target/location` | `geometry_msgs/PoseStamped` | Closest target pose in local ENU, `frame_id=px4_local_enu` |

## Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/camera/image_raw` | `sensor_msgs/Image` | RGB image bridged from Gazebo |
| `/depth_camera` | `sensor_msgs/Image` | Oak-D Lite simulated depth image in metres |
| `/fmu/out/vehicle_local_position` | `px4_msgs/VehicleLocalPosition` | UAV local NED position and heading |
| `/uav/rtk_position` | `sensor_msgs/NavSatFix` | Current RTK-corrected global position from the actual RTK module |
| `/uav/rtk_status` | `std_msgs/String` | RTK status string for logs |
| `/mission/status` | `std_msgs/String` | Optional mission phase gate |

## Quick Start

Install the vision runtime into the ROS Python environment:

```bash
python3 -m pip install ultralytics numpy
```

Build the package:

```bash
cd ~/Projects/UAVsim/uav-emergency-rescue-bds/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select target_detection_tracking
source install/setup.bash
```

Launch with already-bridged camera topics:

```bash
ros2 launch target_detection_tracking target_detection_sim.launch.py
```

Launch and bridge depth plus RGB from Gazebo:

```bash
ros2 launch target_detection_tracking target_detection_sim.launch.py \
  start_depth_bridge:=true \
  start_rgb_bridge:=true \
  rgb_gz_topic:=/world/default/model/x500_1/link/camera_link/sensor/IMX214/image
```

Use `gz topic -l | grep IMX214` to confirm the actual RGB topic for the current world/model name. The `/depth_camera` topic is explicit in the PX4 Oak-D Lite model and normally matches the default bridge argument.

## Model

The default model is imported from:

```text
UAVrescuesystem/target_detection/runs/detect/kitti_person_yolov8n/weights/best.pt
```

and installed as:

```text
models/kitti_person_yolov8n_best.pt
```

Override it with:

```bash
ros2 launch target_detection_tracking target_detection_sim.launch.py \
  model_path:=/path/to/other_weights.pt
```

## Outputs

Runtime evidence is written under:

```text
results/screenshots/target_detection_tracking/
results/logs/target_detection_tracking/detections.jsonl
```

Screenshots are lightweight `.ppm` files so the node does not require OpenCV just to save evidence.

See [simulation_integration_workflow.md](docs/simulation_integration_workflow.md) for the full integration workflow and ROS 1 adaptation notes.
