from setuptools import find_packages, setup

package_name = 'beidou_short_message'

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
    description='BeiDou short-message decode and ROS 2 publishing for the UAV Emergency Rescue System',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'beidou_publisher_node = beidou_short_message.beidou_publisher_node:main',
        ],
    },
)
