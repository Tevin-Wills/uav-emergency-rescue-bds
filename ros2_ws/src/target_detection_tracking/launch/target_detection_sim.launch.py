"""Launch target detection for PX4 Gazebo RGB plus depth simulation."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("target_detection_tracking")
    config_path = os.path.join(pkg_share, "config", "target_detection_sim.yaml")

    rgb_topic = LaunchConfiguration("rgb_topic")
    depth_topic = LaunchConfiguration("depth_topic")
    rgb_gz_topic = LaunchConfiguration("rgb_gz_topic")
    start_rgb_bridge = LaunchConfiguration("start_rgb_bridge")
    start_depth_bridge = LaunchConfiguration("start_depth_bridge")
    model_path = LaunchConfiguration("model_path")
    confidence_threshold = LaunchConfiguration("confidence_threshold")

    rgb_bridge_arg = PythonExpression([
        "'",
        rgb_gz_topic,
        "@sensor_msgs/msg/Image@gz.msgs.Image'",
    ])
    depth_bridge_arg = PythonExpression([
        "'",
        depth_topic,
        "@sensor_msgs/msg/Image@gz.msgs.Image'",
    ])

    return LaunchDescription([
        DeclareLaunchArgument(
            "rgb_topic",
            default_value="/camera/image_raw",
            description="ROS 2 RGB image topic consumed by target detection",
        ),
        DeclareLaunchArgument(
            "depth_topic",
            default_value="/depth_camera",
            description="ROS 2 depth image topic consumed by target detection",
        ),
        DeclareLaunchArgument(
            "rgb_gz_topic",
            default_value="/world/default/model/x500_1/link/camera_link/sensor/IMX214/image",
            description="Gazebo RGB camera topic. Override after checking `gz topic -l`.",
        ),
        DeclareLaunchArgument(
            "start_rgb_bridge",
            default_value="false",
            description="Start ros_gz_bridge for the Gazebo RGB camera topic",
        ),
        DeclareLaunchArgument(
            "start_depth_bridge",
            default_value="false",
            description="Start ros_gz_bridge for the Gazebo depth camera topic",
        ),
        DeclareLaunchArgument(
            "model_path",
            default_value="",
            description="YOLO weights path. Empty uses the packaged KITTI person model.",
        ),
        DeclareLaunchArgument(
            "confidence_threshold",
            default_value="0.25",
            description="YOLO confidence threshold",
        ),

        ExecuteProcess(
            condition=IfCondition(start_rgb_bridge),
            cmd=[
                "ros2",
                "run",
                "ros_gz_bridge",
                "parameter_bridge",
                rgb_bridge_arg,
                "--ros-args",
                "-r",
                PythonExpression(["'", rgb_gz_topic, ":=", rgb_topic, "'"]),
            ],
            output="screen",
        ),

        ExecuteProcess(
            condition=IfCondition(start_depth_bridge),
            cmd=[
                "ros2",
                "run",
                "ros_gz_bridge",
                "parameter_bridge",
                depth_bridge_arg,
            ],
            output="screen",
        ),

        Node(
            package="target_detection_tracking",
            executable="target_detection_node",
            name="target_detection_node",
            output="screen",
            parameters=[
                config_path,
                {
                    "rgb_topic": rgb_topic,
                    "depth_topic": depth_topic,
                    "model_path": model_path,
                    "confidence_threshold": ParameterValue(
                        confidence_threshold,
                        value_type=float,
                    ),
                },
            ],
        ),
    ])
