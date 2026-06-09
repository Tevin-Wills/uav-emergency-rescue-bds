"""
Full rescue simulation launch file.

Thin wrapper that delegates to the bringup package's full_rescue.launch.py, which
launches the five-module ROS 2 topic graph for the integrated rescue demo.

External prerequisites (start separately):
  1. PX4 SITL + Gazebo Harmonic
  2. micro-XRCE-DDS Agent
  3. QGroundControl (for mission-mode flight)

Usage:
  ros2 launch simulation full_rescue_sim.launch.py
  ros2 launch simulation full_rescue_sim.launch.py use_rtk:=false use_detection:=false

Launch args (forwarded to bringup):
  use_rtk        (default true)  -- launch the real rtk_positioning node
  use_detection  (default true)  -- launch the real target_detection node
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    bringup_share = get_package_share_directory("bringup")
    full_rescue = os.path.join(bringup_share, "launch", "full_rescue.launch.py")

    return LaunchDescription([
        DeclareLaunchArgument("use_rtk", default_value="true"),
        DeclareLaunchArgument("use_detection", default_value="true"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(full_rescue),
            launch_arguments={
                "use_rtk": LaunchConfiguration("use_rtk"),
                "use_detection": LaunchConfiguration("use_detection"),
            }.items(),
        ),
    ])
