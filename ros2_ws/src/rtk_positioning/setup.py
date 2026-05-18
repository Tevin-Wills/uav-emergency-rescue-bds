from setuptools import find_packages, setup

package_name = 'rtk_positioning'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', [
            'config/base_station.yaml',
            'config/noise_profiles.yaml',
            'config/level1_rtk_params.yaml',
        ]),
        ('share/' + package_name + '/launch', [
            'launch/level1_rtk_sim.launch.py',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Tevin Wills',
    maintainer_email='tevinlemalasia254@gmail.com',
    description='Level 1 RTK positioning simulation for UAV Emergency Rescue System',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'base_station_node    = rtk_positioning.base_station_node:main',
            'simulated_uav_node   = rtk_positioning.simulated_uav_node:main',
            'rtk_positioning_node = rtk_positioning.rtk_positioning_node:main',
            'logger_node          = rtk_positioning.logger_node:main',
        ],
    },
)
