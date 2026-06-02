"""
Level 2 RTK positioning simulation launch file.

Starts all Level 2 nodes:
  gz_navsat_bridge              — ros_gz_bridge: Gazebo navsat → /gz/navsat (ROS 2)
  base_station_node             — publishes fixed base station coordinate
  px4_pose_adapter_node         — converts Gazebo navsat → /uav/ground_truth
  rtcm_correction_simulator_node — publishes simulated GPS_RTCM_DATA-style corrections
  rtk_positioning_node          — core RTK simulation (Level 2 correction-based mode)
  logger_node                   — saves Level 2 CSV logs

Prerequisites (start before running this launch file):
  Terminal 1: ~/launch_sim_24.sh     (PX4 SITL + Gazebo + micro-XRCE-DDS Agent)

Run:
  cd ~/uav-emergency-rescue-bds/ros2_ws
  source /opt/ros/jazzy/setup.bash
  source install/setup.bash
  ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py

Level 1 remains runnable independently:
  ros2 launch rtk_positioning level1_rtk_sim.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

# Gazebo navsat topic to bridge into ROS 2
_GZ_NAVSAT_TOPIC = (
    '/world/default/model/x500_1/link/base_link/sensor/navsat_sensor/navsat'
)
_ROS_NAVSAT_TOPIC = '/gz/navsat'


def generate_launch_description():
    pkg_share = get_package_share_directory('rtk_positioning')

    base_station_config = os.path.join(pkg_share, 'config', 'base_station.yaml')
    noise_config        = os.path.join(pkg_share, 'config', 'noise_profiles.yaml')
    level2_config       = os.path.join(pkg_share, 'config', 'level2_rtk_params.yaml')

    return LaunchDescription([

        # ── Bridge: Gazebo navsat sensor → ROS 2 sensor_msgs/NavSatFix ──────
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_navsat_bridge',
            arguments=[
                f'{_GZ_NAVSAT_TOPIC}@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat'
            ],
            remappings=[
                (_GZ_NAVSAT_TOPIC, _ROS_NAVSAT_TOPIC),
            ],
            output='screen',
        ),

        # ── Base station ─────────────────────────────────────────────────────
        Node(
            package='rtk_positioning',
            executable='base_station_node',
            name='base_station_node',
            output='screen',
            parameters=[base_station_config],
        ),

        # ── PX4/Gazebo pose adapter ───────────────────────────────────────────
        Node(
            package='rtk_positioning',
            executable='px4_pose_adapter_node',
            name='px4_pose_adapter_node',
            output='screen',
            parameters=[level2_config],
        ),

        # ── Simulated RTCM correction stream ─────────────────────────────────
        Node(
            package='rtk_positioning',
            executable='rtcm_correction_simulator_node',
            name='rtcm_correction_simulator_node',
            output='screen',
            parameters=[level2_config],
        ),

        # ── RTK positioning node (Level 2 mode) ──────────────────────────────
        Node(
            package='rtk_positioning',
            executable='rtk_positioning_node',
            name='rtk_positioning_node',
            output='screen',
            parameters=[base_station_config, noise_config, level2_config],
        ),

        # ── CSV logger (Level 2) ─────────────────────────────────────────────
        Node(
            package='rtk_positioning',
            executable='logger_node',
            name='logger_node',
            output='screen',
            parameters=[level2_config],
        ),

    ])
