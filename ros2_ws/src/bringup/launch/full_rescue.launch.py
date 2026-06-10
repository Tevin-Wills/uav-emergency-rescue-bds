"""
full_rescue.launch.py — Stage-1 integrated rescue pipeline.

Launches the five-module ROS 2 topic graph for the UAV Emergency Rescue System:

  BeiDou distress coordinate -> mission state machine -> path -> RTK + target detection

Light stub/real nodes (always launched, no external deps):
  beidou_short_message  beidou_publisher_node  -> /target/emergency_coordinate, /rescue/beidou_message
  qgc_control           mission_status_node    -> /mission/status, /mission/waypoints
  path_planning         path_planning_node     -> /planner/path

Heavy real nodes (toggle with launch args; need the PX4/Gazebo backbone):
  rtk_positioning  -> full Level 3 chain via level3_resilient_rtk.launch.py
                      -> /uav/rtk_position, /uav/rtk_status, /rtk/mission_viability  (use_rtk:=true)
  target_detection_tracking target_detection_node -> /target/detection, /target/location (use_detection:=true)

External prerequisites (start separately, see README):
  - PX4 SITL + Gazebo Harmonic
  - micro-XRCE-DDS Agent
  - QGroundControl (for mission-mode flight)

Usage:
  ros2 launch bringup full_rescue.launch.py
  ros2 launch bringup full_rescue.launch.py use_rtk:=false use_detection:=false   # stubs-only smoke test
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    use_rtk = LaunchConfiguration("use_rtk")
    use_detection = LaunchConfiguration("use_detection")
    scenario = LaunchConfiguration("scenario")
    px4_ns = LaunchConfiguration("px4_ns")
    rgb_gz_topic = LaunchConfiguration("rgb_gz_topic")
    # PX4 publishes /fmu/* under its instance namespace (launch_sim_24.sh uses -i 1
    # -> px4_1). target_detection's local-pose topic is built from this.
    # NOTE: this PX4 build uses versioned topics with a "_v1" suffix
    # (/px4_1/fmu/out/vehicle_local_position_v1, type px4_msgs/VehicleLocalPosition).
    # If a different PX4 version is used, adjust the suffix here.
    local_pos_topic = ["/", px4_ns, "/fmu/out/vehicle_local_position_v1"]

    # Shared geographic datum applied to every node (/** wildcard in the file).
    datum = os.path.join(get_package_share_directory("bringup"), "config", "datum.yaml")
    # RTK's own validated Level 3 launch (full chain: base_station + px4_pose_adapter
    # + rtcm_sim + rtk_positioning_node + logger). We call it rather than starting the
    # bare node, which would have no inputs.
    rtk_launch = os.path.join(
        get_package_share_directory("rtk_positioning"),
        "launch", "level3_resilient_rtk.launch.py")
    # target_detection's own launch brings up the camera + depth ros_gz bridges AND
    # the detection node — we include it (like RTK) rather than the bare node, which
    # would have no image feed.
    td_launch = os.path.join(
        get_package_share_directory("target_detection_tracking"),
        "launch", "target_detection_sim.launch.py")

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_rtk", default_value="true",
            description="Launch the full RTK Level 3 chain (needs PX4/Gazebo backbone)."),
        DeclareLaunchArgument(
            "use_detection", default_value="true",
            description="Launch the real target_detection node (needs camera + YOLO deps)."),
        DeclareLaunchArgument(
            "scenario", default_value="compound_disaster",
            description="RTK Level 3 scenario: compound_disaster | total_failure."),
        DeclareLaunchArgument(
            "px4_ns", default_value="px4_1",
            description="PX4 uXRCE instance namespace (launch_sim_24.sh uses -i 1 -> px4_1)."),
        DeclareLaunchArgument(
            # Model-dependent: with gz_x500_depth confirm via `gz topic -l` on the
            # NATIVE GPU PC (model name may be x500_depth_*, sensor may differ).
            "rgb_gz_topic",
            default_value="/world/default/model/x500_1/link/camera_link/sensor/IMX214/image",
            description="Gazebo RGB camera topic to bridge (confirm with `gz topic -l`)."),

        # --- Light nodes: the integration backbone, no external deps ---
        # parameters=[datum] injects the shared geographic datum (/** wildcard).
        Node(
            package="beidou_short_message", executable="beidou_publisher_node",
            name="beidou_publisher_node", output="screen", parameters=[datum]),
        Node(
            package="qgc_control", executable="mission_status_node",
            name="mission_status_node", output="screen", parameters=[datum]),
        Node(
            package="path_planning", executable="path_planning_node",
            name="path_planning_node", output="screen", parameters=[datum]),

        # --- RTK: full Level 3 resilient chain via RTK's own validated launch ---
        # (base_station + px4_pose_adapter + rtcm_sim + rtk_positioning_node + logger).
        # No parameters=[datum] here: the L3 scenario configs already set RTK's
        # world_origin to the same Zurich datum.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(rtk_launch),
            launch_arguments={"scenario": scenario}.items(),
            condition=IfCondition(use_rtk)),

        # --- Perception: target_detection's own launch (camera+depth bridges + node) ---
        # Included like RTK; starts the RGB + depth ros_gz bridges and points the node
        # at the PX4 instance-namespaced, versioned local-position topic.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(td_launch),
            launch_arguments={
                "local_position_topic": local_pos_topic,
                "rgb_gz_topic": rgb_gz_topic,
                "start_rgb_bridge": "true",
                "start_depth_bridge": "true",
            }.items(),
            condition=IfCondition(use_detection)),
    ])
