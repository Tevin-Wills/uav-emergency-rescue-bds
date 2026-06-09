from setuptools import find_packages, setup

package_name = 'qgc_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Tevin Wills',
    maintainer_email='tevinlemalasia254@gmail.com',
    description='QGC / mission control for the UAV Emergency Rescue System',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Stage-1 integration stub: mission phase state machine + waypoints.
            'mission_status_node = qgc_control.mission_status_node:main',
            # Yvonne's MAVROS control node (PX4 bridge decision deferred -- see
            # interfaces/integration_contract.md Reconciliation Log [C]).
            'uav_control_node    = qgc_control.uav_control_node:main',
        ],
    },
)
