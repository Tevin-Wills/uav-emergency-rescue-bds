# Report Outline — RTK Positioning

## Chapter 1 — Introduction
- Project background
- Importance of precision positioning in UAV rescue
- Objectives of this module

## Chapter 2 — Background
- GNSS fundamentals
- RTK positioning principles
- RTCM correction protocol
- Related work / prior systems

## Chapter 3 — System Design
- RTK base station configuration
- RTK rover configuration
- RTCM correction flow into PX4
- ROS 2 node architecture for rtk_positioning

## Chapter 4 — Simulation Implementation
- GNSS simulation setup in Gazebo / PX4 SITL
- RTK correction injection method
- ROS 2 topic publication (rtk_position, rtk_status)
- Launch file and configuration

## Chapter 5 — Results and Analysis
- RTK fix acquisition time
- Horizontal and vertical positioning error
- Comparison: GPS-only vs RTK Float vs RTK Fixed
- Data from sample_rtk_log.csv

## Chapter 6 — Integration with Other Modules
- How rtk_positioning feeds path_planning and qgc_control
- Interface compatibility verification

## Chapter 7 — Conclusion
- Summary of results
- Limitations and future improvements

## References

<!-- Add references here -->
