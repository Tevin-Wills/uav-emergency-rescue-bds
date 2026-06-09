from glob import glob
from setuptools import find_packages, setup


package_name = "target_detection_tracking"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml", "README.md"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/docs", glob("docs/*.md")),
        ("share/" + package_name + "/models", glob("models/*.pt")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Student 3",
    maintainer_email="student3@example.com",
    description="RGB plus depth target detection and geolocation for UAV rescue simulation",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "target_detection_node = target_detection_tracking.target_detection_node:main",
        ],
    },
)
