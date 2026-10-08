# 2. Diagnosing the problem

> **Historical:** this describes the original skid-steer / `diff_drive_controller` setup, which was later replaced by mecanum ([chapter 6](06-mecanum-holonomic-switch.md)). The method is still how to debug the sim.

> **Concept**
> - **Simulation time** is the clock inside the simulator. It can run slower or faster than the wall clock, so always measure speeds against it.
> - **Ground truth pose** comes straight from Gazebo (`/world/empty/dynamic_pose/info`), not from odometry, which is only an estimate.
> - **`ApplyLinkWrench`** is a Gazebo system that applies a force or torque to a link, so you can ask "how hard is it to rotate this body at all?".
> - **Change one thing at a time** and re-measure, so you know which change mattered.

## Symptoms

- The robot drove forward and backward, but **did not rotate at all** when given an angular command.
- Forward speed **looked inconsistent**.

The CAD model looked fine, and the hand edits to inertia (resistance of a body to rotational acceleration, the rotational equivalent of mass) and wheel axes were correct. The problems all came from things a CAD model never exercises: **ground contact physics** and **controller configuration**.

## How it was diagnosed

1. Launched `gazebo.launch.py`, checked that `joint_state_broadcaster` and `diff_drive_controller` were active, and that `/diff_drive_controller/cmd_vel` has type `geometry_msgs/msg/TwistStamped`.
2. Published commands at 20 Hz and measured the robot's **true pose from Gazebo** (`/world/empty/dynamic_pose/info`) against **simulation time** (the clock inside the simulator, which can run slower or faster than the wall clock).
3. Applied a pure torque (twisting force, in N·m) to `base_link` using Gazebo's `ApplyLinkWrench` system, to see how hard it was to rotate the body at all.
4. Swapped one thing at a time (self-collision off, cylinder collisions, friction values, physics engine, ground friction) and re-measured.

| Variant | Straight (cmd 0.3 m/s) | Spin (cmd 1.0 rad/s) |
|---|---|---|
| Original repo | 0.300 m/s | **0.000 rad/s** |
| `self_collide` removed | 0.300 | 0.000 |
| Bullet physics instead of DART | 0.300 | 0.000 |
| Wheel μ 0.02 (STL mesh collision) | 0.300 | 0.000 |
| Cylinder wheels + anisotropic friction + separation 0.33 | 0.300 | **1.01 / −1.00** |
