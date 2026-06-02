# UAV Emergency Rescue System: RTK Positioning Simulation Briefing

This briefing document provides a comprehensive analysis of the development and testing of a high-precision UAV positioning system for emergency rescue operations. It synthesizes technical simulation data, architecture notes, and project objectives to outline the system's performance and future development path.

## Executive Summary

The project, titled "UAV Emergency Rescue System Based on BeiDou Navigation and Short Message Communication," addresses the critical need for rapid and precise survivor location and aid delivery in disaster-stricken areas. A core component of this system is the Real-Time Kinematic (RTK) GNSS positioning module, which provides the centimeter-level accuracy required for autonomous flight and precision landing.

Development is structured into two simulation levels:
*   **Level 1:** A standalone ROS 2 simulation verifying the core RTK logic and demonstrating a **95.8% improvement** in positioning accuracy over standard GNSS.
*   **Level 2:** An integrated PX4/Gazebo simulation that replaces synthetic data with real UAV poses and message-driven transitions, achieving a **96.7% accuracy improvement**.

The simulation results confirm that while standard GNSS errors average ~2.4 meters, the RTK-corrected system consistently achieves mean errors as low as **0.048 meters** during "RTK Fixed" periods.

---

## Detailed Analysis of Key Themes

### 1. Multi-Level Simulation Strategy
The project utilizes a tiered simulation approach to ensure architectural robustness and ease of integration. 

*   **Level 1 (Standalone Logic):** Designed to run without heavy dependencies like PX4 or Gazebo. It focuses on the mathematical models for noise and correction. It uses time-based status transitions (e.g., GNSS Only for 5 seconds, followed by RTK Float) to verify that the `rtk_positioning_node` correctly applies corrections.
*   **Level 2 (Integration & Event Handling):** Connects the module to the PX4/Gazebo stack via `ros_gz_bridge`. It introduces complexity by modeling "MAVLink-style" correction behavior. Transitions are driven by simulated RTCM quality and availability rather than simple timers.

### 2. RTK Status and Performance Metrics
The system categorizes positioning quality into four distinct states. The simulation applies specific noise profiles based on these states to model real-world hardware behavior.

| Status | Description | Noise Std Dev (m) | Typical Performance |
| :--- | :--- | :--- | :--- |
| **GNSS_ONLY** | Standard satellite positioning; no corrections. | 1.50 m | 1–5 m error |
| **RTK_FLOAT** | Corrections received; carrier-phase ambiguity not yet resolved. | 0.25 m | 0.2–0.5 m error |
| **RTK_FIXED** | Full RTK fix; ambiguity resolved. | 0.03 m | 0.02–0.05 m error |
| **CORRECTION_LOST**| Link interruption; results in a rapid error spike. | 2.50 m | Degraded accuracy |

### 3. Reliability and "Correction Lost" Recovery
A critical feature of the Level 2 simulation is the handling of signal interruptions. 
*   **The Event:** At $t = 45$ seconds, the system simulates a 5-second loss of correction data.
*   **System Response:** The error spikes significantly (documented peak of $7.0+$ meters in some samples), and the status transitions to `CORRECTION_LOST`.
*   **Recovery:** At $t = 50$ seconds, once corrections are restored with high quality ($0.95$), the system successfully recovers to `RTK_FIXED` status, demonstrating the resilience of the position filtering logic.

### 4. Integration with the Rescue Workflow
The RTK module is one of five integrated ROS 2 modules. The end-to-end rescue mission follows a specific sequence:
1.  **Coordinate Reception:** Rescue targets are received via BeiDou Short Message Service, bypassing destroyed terrestrial infrastructure.
2.  **Path Planning:** An obstacle-free route is generated toward the coordinates.
3.  **High-Precision Transit:** The RTK module ensures the UAV follows the planned path with centimeter-level fidelity.
4.  **Target Acquisition:** Onboard cameras detect the survivor marker.
5.  **Precision Landing:** The UAV executes a fixed-point landing at the target location.

---

## Important Quotes and Context

### On Simulation Fidelity
> "Level 2 is still a software simulation. It does not use real RTK hardware, does not decode real RTCM binary data, and does not simulate real BeiDou or GPS satellite RF signals." 
*   **Context:** This disclaimer is vital for managing stakeholder expectations. It clarifies that while the *behavior* and *interfaces* (MAVLink-style quality thresholds) are realistic, the underlying signal processing is still mathematically modeled.

### On Architectural Readiness
> "The RTK core logic (gnss_noise_model, rtk_correction_model, coordinate_transform, rtk_status_manager) does not need to change [when moving to real hardware]."
*   **Context:** This highlights the "hardware-agnostic" design. By standardizing the ROS 2 topic interfaces early, the team ensures that the transition to physical sensors will only require swapping the "adapter" nodes, not the central positioning logic.

### On Tactical Advantages of UAVs
> "UAVs fly over debris, flooded roads, and unstable terrain that blocks ground vehicles... Standard GPS alone is insufficient for precision rescue operations."
*   **Context:** This provides the operational justification for the project. It explains that the high precision afforded by RTK is not just a technical goal but a necessity for landing in complex, hazardous disaster environments.

---

## Accuracy Comparison Summary

Based on the cross-validation of Level 2 CSV logs and QGC ULog data, the system achieves the following accuracy benchmarks:

| Metric | Raw GNSS (Simulated) | PX4 GPS (EPH Reported) | RTK-Corrected (Fixed) |
| :--- | :--- | :--- | :--- |
| **Mean Error** | 2.394 m — 2.413 m | 0.900 m | **0.048 m** |
| **Standard Deviation ($\sigma$)** | 1.013 m | N/A | **0.012 m** |

**Total Accuracy Improvement:** The RTK system provides a **94.7% improvement** specifically when compared to the PX4 GPS reported uncertainty (EPH), and a **96.7% improvement** compared to raw, uncorrected simulated GNSS.

---

## Actionable Insights

### 1. Prioritize Native Ubuntu for Full Integration
The simulation workflow notes indicate that while individual modules can be developed on WSL2, the final integrated simulation involving Gazebo Harmonic and the full rescue stack is "not recommended" for WSL2. 
*   **Action:** Ensure the designated "integration computer" is running a native Ubuntu 24.04 (Noble Numbat) or later environment to support the 3D physics rendering requirements.

### 2. Standardize Coordinate Reference Origins
The Level 2 simulation uses the ETH Zurich world origin as its ENU (East-North-Up) reference. 
*   **Action:** All modules (Path Planning, BeiDou SMS, and RTK) must explicitly align their coordinate transforms to this origin to avoid "drift" or "offset" errors during the autonomous flight phase.

### 3. Implement Simulation World Assets
The "earthquake rescue world" SDF file and specific models (collapsed buildings, survivor markers, and landing pads) are currently listed as placeholders in the documentation.
*   **Action:** The simulation team must prioritize the creation of these Gazebo models to allow the `target_detection_tracking` and `path_planning` modules to be tested against realistic visual and physical obstacles.

### 4. Transition to Message-Driven Quality Thresholds
Level 2 introduced the `SimulatedRtcm.msg` which carries quality scores ($0.0$ to $1.0$).
*   **Action:** Refine the `rtk_positioning_node` parameters (`float_quality_threshold`, `fixed_quality_threshold`) based on future hardware data-sheets to ensure the simulated state machine accurately mirrors real-world ambiguity resolution timing.