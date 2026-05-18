"""
Level 1 RTK positioning simulation launch file.

Starts all four Level 1 nodes:
  base_station_node    — publishes fixed base station coordinate
  simulated_uav_node   — generates square-search UAV path
  rtk_positioning_node — core RTK simulation logic
  logger_node          — saves CSV logs

Run with:
  ros2 launch rtk_positioning level1_rtk_sim.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('rtk_positioning')

    base_station_config = os.path.join(pkg_share, 'config', 'base_station.yaml')
    noise_config        = os.path.join(pkg_share, 'config', 'noise_profiles.yaml')
    level1_config       = os.path.join(pkg_share, 'config', 'level1_rtk_params.yaml')

    return LaunchDescription([

        Node(
            package='rtk_positioning',
            executable='base_station_node',
            name='base_station_node',
            output='screen',
            parameters=[base_station_config],
        ),

        Node(
            package='rtk_positioning',
            executable='simulated_uav_node',
            name='simulated_uav_node',
            output='screen',
            parameters=[level1_config],
        ),

        Node(
            package='rtk_positioning',
            executable='rtk_positioning_node',
            name='rtk_positioning_node',
            output='screen',
            parameters=[base_station_config, noise_config],
        ),

        Node(
            package='rtk_positioning',
            executable='logger_node',
            name='logger_node',
            output='screen',
            parameters=[level1_config],
        ),

    ])
