# WSL2 Ubuntu 24.04 Setup

## Overview

Some team members work on Windows machines and use WSL2 with Ubuntu 24.04 as their development environment. This guide covers WSL2-specific considerations, limitations, and workarounds.

---

## When WSL2 Is Acceptable

- Developing and testing individual ROS 2 modules independently.
- Writing and debugging Python or C++ code without running the full Gazebo simulation.
- Running `colcon build` and `ros2 topic` commands for unit-level work.

---

## When Native Ubuntu Is Preferred

- Running the full PX4 SITL + Gazebo Harmonic simulation.
- Final integration testing across all five modules.
- Recording simulation outputs or capturing video demonstrations.

---

## File Path Notes

Windows drives are mounted in WSL2 at `/mnt/`:

```
C:\Users\you\project  →  /mnt/c/Users/you/project
```

Keep all project work inside the WSL2 filesystem (e.g., `~/`), not on `/mnt/c/`, to avoid slow I/O and permission issues.

---

## GUI Support (Gazebo)

Ubuntu 24.04 on WSL2 uses WSLg for GUI applications. If Gazebo renders a black screen:

```bash
export QT_QPA_PLATFORM=xcb
```

Add to `~/.bashrc` for persistence. If rendering remains broken, fall back to software rendering:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
```

> Software rendering is stable but slow. For full simulation, use native Ubuntu.

---

## QGroundControl on WSL2

Install and run QGroundControl on Windows, not inside WSL2.

- QGroundControl connects to PX4 running in WSL2 via UDP.
- Default UDP port: `18571` (PX4 instance 1).
- WSL2 bridges UDP to Windows automatically — no extra configuration needed.

---

## Networking Notes

- WSL2 uses a virtual network adapter. Most UDP communication works out of the box.
- If connection issues occur, verify you are on WSL2 (not WSL 1):

```bash
wsl --version
```

- If MAVLink or ROS 2 discovery fails, check that your Windows firewall allows UDP on the relevant ports.

---

## Project Setup Steps (WSL2)

Follow the same setup order as native Ubuntu:

1. [`ros2_jazzy_setup.md`](ros2_jazzy_setup.md)
2. [`gazebo_harmonic_setup.md`](gazebo_harmonic_setup.md) — limited GPU support in WSL2
3. [`px4_setup.md`](px4_setup.md)
4. [`qgroundcontrol_setup.md`](qgroundcontrol_setup.md) — install on Windows side

---

## Known Caveats

| Issue | Cause | Workaround |
|---|---|---|
| Gazebo black screen | WSLg rendering | `export QT_QPA_PLATFORM=xcb` |
| Slow 3D rendering | No direct GPU in WSLg | `export LIBGL_ALWAYS_SOFTWARE=1` |
| QGC can't find PX4 | Firewall or wrong port | Check Windows firewall, use port 18571 |
| WSL1 confusion | Running WSL1 not WSL2 | `wsl --set-default-version 2` |
