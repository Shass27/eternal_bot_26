# 5. Skid-steer results

> **Historical:** measured on the skid-steer / `diff_drive_controller` setup. For the current mecanum results see [chapter 6](06-mecanum-holonomic-switch.md).

> **Concept**
> All numbers are in **simulation time**, read from Gazebo's ground-truth pose, so they are not distorted by a slow VM (real-time factor below 1).

| Command | Measured |
|---|---|
| straight +0.3 / −0.3 m/s | 0.300 m/s |
| spin +1.0 rad/s | 1.010 rad/s |
| spin −1.0 rad/s | −0.998 rad/s |
| arc 0.3 m/s + 0.5 rad/s via `/cmd_vel` (Twist) | 0.290 m/s, 0.500 rad/s |
