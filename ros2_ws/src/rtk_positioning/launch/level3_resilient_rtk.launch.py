"""
Level 3 resilient RTK positioning launch file.

Supports two scenarios selected via the `scenario` launch argument:

  compound_disaster (default — Run 2):
    Co-occurring multipath + intermittent corrections + progressive degradation.
    This is the core Level 3 engineering demonstration.

  total_failure (Run 3):
    Zero corrections throughout. Elevated noise. Lower bound on system performance.
    Config-only — no additional code required beyond Run 2.

Usage:
  ros2 launch rtk_positioning level3_resilient_rtk.launch.py
  ros2 launch rtk_positioning level3_resilient_rtk.launch.py scenario:=total_failure

Prerequisites (start before running this launch file):
  Terminal 1: ~/launch_sim_24.sh     (PX4 SITL + Gazebo + micro-XRCE-DDS Agent)

Level 1 and Level 2 remain runnable independently:
  ros2 launch rtk_positioning level1_rtk_sim.launch.py
  ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

_GZ_NAVSAT_TOPIC = (
    '/world/default/model/x500_1/link/base_link/sensor/navsat_sensor/navsat'
)
_ROS_NAVSAT_TOPIC = '/gz/navsat'


def _launch_nodes(context, *args, **kwargs):
    scenario  = LaunchConfiguration('scenario').perform(context)
    pkg_share = get_package_share_directory('rtk_positioning')

    base_station_config = os.path.join(pkg_share, 'config', 'base_station.yaml')
    noise_config        = os.path.join(pkg_share, 'config', 'noise_profiles.yaml')

    if scenario == 'total_failure':
        scenario_config = os.path.join(pkg_share, 'config', 'level3_total_failure.yaml')
        scenario_params = scenario_config
    else:
        scenario_config = os.path.join(pkg_share, 'config', 'level3_disaster_scenario.yaml')
        scenario_params = os.path.join(pkg_share, 'config', 'level3_disaster_scenario_params.yaml')

    return [
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
            parameters=[scenario_params],
        ),

        # ── Simulated RTCM correction stream (Level 3 phase profile) ─────────
        # scenario_params has scalar-only params (rcl-safe).
        # config_file points to the full YAML so the node can read phase_profile
        # directly via Python's yaml module — rcl cannot parse lists of dicts.
        Node(
            package='rtk_positioning',
            executable='rtcm_correction_simulator_node',
            name='rtcm_correction_simulator_node',
            output='screen',
            parameters=[scenario_params, {'config_file': scenario_config}],
        ),

        # ── RTK positioning node (Level 3 dynamic uncertainty mode) ──────────
        Node(
            package='rtk_positioning',
            executable='rtk_positioning_node',
            name='rtk_positioning_node',
            output='screen',
            parameters=[base_station_config, noise_config, scenario_params],
        ),

        # ── CSV logger (Level 3) ─────────────────────────────────────────────
        Node(
            package='rtk_positioning',
            executable='logger_node',
            name='logger_node',
            output='screen',
            parameters=[scenario_params],
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'scenario',
            default_value='compound_disaster',
            description=(
                'Level 3 scenario to run: '
                '"compound_disaster" (Run 2, default) or "total_failure" (Run 3)'
            ),
        ),
        OpaqueFunction(function=_launch_nodes),
    ])
