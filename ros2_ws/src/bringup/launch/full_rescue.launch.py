"""
full_rescue.launch.py — Stage-1 integrated rescue pipeline.

Launches the five-module ROS 2 topic graph for the UAV Emergency Rescue System:

  BeiDou distress coordinate -> mission state machine -> path -> RTK + target detection

Light stub/real nodes (always launched, no external deps):
  beidou_short_message  beidou_publisher_node  -> /target/emergency_coordinate, /rescue/beidou_message
  qgc_control           mission_status_node    -> /mission/status, /mission/waypoints
  path_planning         path_planning_node     -> /planner/path

Heavy real nodes (toggle with launch args; need the PX4/Gazebo backbone):
  rtk_positioning       rtk_positioning_node   -> /uav/rtk_position, /uav/rtk_status   (use_rtk:=true)
  target_detection_tracking target_detection_node -> /target/detection, /target/location (use_detection:=true)

External prerequisites (start separately, see README):
  - PX4 SITL + Gazebo Harmonic
  - micro-XRCE-DDS Agent
  - QGroundControl (for mission-mode flight)

Usage:
  ros2 launch bringup full_rescue.launch.py
  ros2 launch bringup full_rescue.launch.py use_rtk:=false use_detection:=false   # stubs-only smoke test
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_rtk = LaunchConfiguration("use_rtk")
    use_detection = LaunchConfiguration("use_detection")

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_rtk", default_value="true",
            description="Launch the real rtk_positioning node (needs PX4/Gazebo backbone)."),
        DeclareLaunchArgument(
            "use_detection", default_value="true",
            description="Launch the real target_detection node (needs camera + YOLO deps)."),

        # --- Light nodes: the integration backbone, no external deps ---
        Node(
            package="beidou_short_message", executable="beidou_publisher_node",
            name="beidou_publisher_node", output="screen"),
        Node(
            package="qgc_control", executable="mission_status_node",
            name="mission_status_node", output="screen"),
        Node(
            package="path_planning", executable="path_planning_node",
            name="path_planning_node", output="screen"),

        # --- Heavy real nodes: gated by launch args ---
        Node(
            package="rtk_positioning", executable="rtk_positioning_node",
            name="rtk_positioning_node", output="screen",
            condition=IfCondition(use_rtk)),
        Node(
            package="target_detection_tracking", executable="target_detection_node",
            name="target_detection_node", output="screen",
            condition=IfCondition(use_detection)),
    ])
