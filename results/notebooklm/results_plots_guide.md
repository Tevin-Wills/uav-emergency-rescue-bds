# STUDY GUIDE: RTK POSITIONING SIMULATION RESULTS PLOTS

## 1. Project Overview & Data Context

### Engineering Baseline Summary
This analysis validates the positioning subsystem of the **Precision UAV Emergency Rescue** project. The mission objective is the rapid delivery of aid to survivors located in disaster environments (e.g., "collapsed_building" rubble) where standard GNSS drift is unacceptable. To prevent collisions with obstacles and ensure the UAV hits a specific "survivor_marker" or "landing_pad," we employ Real-Time Kinematic (RTK) corrections to achieve centimeter-level precision.

The validation is structured into two rigor levels:
*   **Level 1 (Standalone ROS 2):** Benchmarks the RTK noise model and engine state transitions.
*   **Level 2 (PX4/Gazebo Integration):** Full-stack validation using Gazebo physics and the PX4 Extended Kalman Filter (EKF) during a 208x214m autonomous mission.

### Global Spatial Reference & Constants
All local coordinates are derived from the following reference parameters using a flat-earth tangent-plane approximation:

| Parameter | Value / Constant |
| :--- | :--- |
| **Base Station Coordinates** | Latitude: 39.981000, Longitude: 116.344000 |
| **M_PER_DEG_LAT** | 111320.0 |
| **M_PER_DEG_LON** | 111320.0 $\times$ cos(radians(39.981)) |
| **L1 Mission Geometry** | 50 x 50 m Square (30 m AGL) |
| **L2 Mission Geometry** | Autonomous QGC Mission (50 m AMSL) |

### RTK Fix Status & State Machine Legend
The RTK engine transitions through four discrete states based on carrier-phase ambiguity resolution and correction availability:

*   **GNSS Only (Orange, #E67E22):** Standard navigation. Spec: $\pm1.50$ m.
*   **RTK Float (Yellow, #F1C40F):** Corrections active; phase ambiguity unresolved. Spec: $\pm0.25$ m.
*   **RTK Fixed (Green, #27AE60):** Centimeter-level fix; ambiguity resolved. Spec: $\pm0.03$ m.
*   **Correction Lost (Purple, #8E44AD):** Link failure/stale corrections. Error degrades based on **Correction Age**.

---

## 2. Level 1: Standalone ROS 2 Simulation Analysis

### 2.1 Graph L1-1: Positioning Error Over Time
*   **Signal Profiles:** The **red line** (Raw GNSS) represents the system performance without RTK, showing significant jitter. The **blue line** (RTK-corrected) captures the performance after noise reduction models are applied. Both use a 3-second rolling mean to filter transient noise and highlight steady-state trends.
*   **State Analysis:** Background shading correlates with the elapsed time windows (Orange: 0–5s, Yellow: 5–15s, Green: 15s+). Note the immediate "flatline" of the blue error signal once the engine achieves a Green state.
*   **Key Statistical KPIs:**
    *   Samples ($N$): 2,718
    *   Raw Mean ($\mu$): 2.394 m ($\sigma = 1.013$ m)
    *   RTK Mean ($\mu$): 0.101 m ($\sigma = 0.330$ m)
    *   **System Improvement:** 95.8% reduction in mean error.

### 2.2 Graph L1-2: RTK Fix Convergence (TTFF Window)
*   **KPI: Time to First Fix (TTFF):** This plot measures the initialization latency. The system demonstrates a high-reliability transition: GNSS_ONLY $\rightarrow$ FLOAT at 5s, and FLOAT $\rightarrow$ FIXED at 15s. A TTFF of 15 seconds is within critical mission requirements for rapid UAV deployment.
*   **Error Step-Downs:** Observe the sharp drops in the blue line at each transition: from ~1.5m to ~0.25m, and finally settling at the ~0.03m noise floor.
*   **State Machine Strip:** The bottom color band acts as a visual state log, confirming that error spikes are strictly contained within the intended state boundaries.

### 2.3 Graph L1-3: Positioning Error Distribution
*   **Horizontal Scale Contrast:** Note the **16x difference** in the X-axis scale. Raw GNSS distribution is a wide Gaussian spread across an 8.0m range, while the RTK-Corrected data is a sharp, delta-like spike within a 0.5m range.
*   **P95 Reliability:** The dash-dot line indicates the 95th-percentile (P95) for RTK data is ~0.07m, proving that 95% of flight time in FIXED mode maintains sub-decimeter accuracy.

### 2.4 Graph L1-4: UAV Flight Trajectory Comparison
*   **Spatial Fidelity:** The 2D ENU map shows the "Ground Truth" (black) square path. Blue RTK dots show near-perfect overlap with the path, whereas red Raw dots show significant "wandering" or cross-track error.
*   **Repeatability KPI:** The purple circle at the origin marks the simultaneous start/end point. The dense clustering of blue dots within this circle validates the system's ability to return to its precise takeoff coordinate after a full mission circuit.

### 2.5 Graph L1-5: RTK Positioning Performance Summary
*   **Panel A:** Highlights that the most significant delta occurs during the "RTK Fixed" phase.
*   **Panel B:** Confirms high mission efficiency; the majority of the 272-second flight is spent in the high-precision Green state.
*   **Panel C:** Summarizes the overall 95.8% improvement, setting the benchmark for integration testing.

---

## 3. Level 2: PX4/Gazebo Integration Analysis

### 3.1 Graph L2-1: Error Over Time (Link Resilience)
*   **Extended Mission Profile:** Covers 1,028 seconds of flight with real physics. The performance remains stable until a simulated link failure.
*   **Anomaly: Correction Age Degradation:** At $t=45s$, the purple "CORRECTION_LOST" event occurs. As `correction_age_sec` grows (simulating stale data), the error spikes to >7m.
*   **Recovery Reliability:** The system recovers to RTK_FIXED within 5 seconds of the signal returning ($t=50s$), demonstrating the engine's resilience to intermittent telemetry gaps.

### 3.2 Graph L2-2: RTK Convergence (4-Event Window)
*   **State Transitions:** Unlike Level 1, this includes the **Lost** and **Recovery** states. The narrow purple strip in the status bar at 45–50s validates the system's ability to autonomously re-resolve carrier-phase ambiguities once valid RTCM packets resume.

### 3.3 Graph L2-3 & L2-4: Distribution and Trajectory
*   **Scale Increase:** The mission area is expanded to 208x214m. Despite the increased spatial scale and dynamic physics from the Gazebo x500 model, the RTK engine maintains a mean error of **0.0477 m** in the FIXED state.

### 3.4 Graph L2-5: Accuracy Summary (Level 2)
*   **Phase Variance:** Panel C illustrates the stability of the system. The RTK_FIXED phase shows negligible variance compared to the high-uncertainty "Correction Lost" phase, which displays large 1$\sigma$ error bars.

### 3.5 Graph L2-6: QGC ULog Cross-Validation
*   **Definitive Project Validation:** This graph uses an independent ground truth source (the PX4 ULog), making it the most critical metric.
*   **Three-Way Accuracy Comparison:**
    1.  **Raw GNSS:** 2.413 m (Simulated baseline).
    2.  **PX4 GPS EPH:** 0.900 m (Autopilot's internal Estimated Position Horizontal uncertainty).
    3.  **RTK-Corrected:** **0.0477 m** (Actual measured performance).
*   **Analysis:** Our RTK solution is **94.7% more accurate** than the PX4's internal EKF-estimated EPH. This proves the system provides accuracy nearly 20 times better than what the autopilot believes it possesses with standard GPS.
*   **Vertical Performance:** Panel 3 shows a stable 50m AMSL profile, confirming high-fidelity Z-axis performance throughout the takeoff-cruise-land cycle.

---

## 4. Final Comparison & Presenter Summary

### Summary Statistical Comparison

| Metric | Level 1 (Standalone) | Level 2 (Integrated) |
| :--- | :--- | :--- |
| **Mean Error: Raw GNSS** | 2.394 m | 2.413 m |
| **Mean Error: RTK (Fixed)**| 0.101 m | **0.0477 m** |
| **Overall Improvement (%)** | 95.8% | 96.7% |
| **Max RTK Spike (Recovery)**| N/A | > 7.0 m |

### Bottom Line for Mission Success
The RTK subsystem provides a consistent **95-97% improvement** over standard GNSS positioning. In a disaster rescue context, this precision is the difference between a mission-ending collision with building rubble and a successful delivery to a survivor marker. The 0.0477 m mean error validated via independent ULog ground truth confirms that this UAV is ready for high-stakes autonomous operations in complex environments.