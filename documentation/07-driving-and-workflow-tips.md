# 7. Driving and workflow tips

> **Concept**
> - Treat the CAD exporter's output as **generated code**. Anything you fix by hand is at risk of being overwritten on the next export, so keep overrides separate or documented.
> - A **single source of truth** for dimensions (xacro properties) stops the joints, collisions and plugin parameters from drifting apart.
> - A quick **motion test in sim time** after every change catches physics regressions early.

## Driving the robot

```bash
ros2 launch eternal_bot_description gazebo.launch.py
ros2 run teleop_twist_keyboard teleop_twist_keyboard     # plain Twist on /cmd_vel, bridged to the MecanumDrive plugin; hold Shift to strafe
# or directly:
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {y: 0.3}}"
```

Use the `/sim-drive-test` skill to verify motion against sim-time ground truth.

## Workflow suggestions (Fusion 360 → URDF → Gazebo)

1. **Treat the exporter output as generated; never hand-edit it.** Keep the overrides (collisions, inertia fixes, `<gazebo>` friction, ros2_control) in a separate wrapper xacro that includes the export. Re-exporting from Fusion then won't wipe the fixes.
2. **Define dimensions once.** Use xacro properties (`wheel_radius`, `wheel_width`, `track`, `wheelbase`) for the joint origins, collision primitives **and** the controller parameters, so `wheel_separation` can't drift from the geometry. (Today the plugin parameters in `eternal_bot.gazebo` play this role; ros2_control comes back with real hardware.)
3. **Use primitive collisions** (cylinders or spheres for wheels, a box for the chassis) and keep the STLs for visuals. They're faster and give stable, friction-correct contacts.
4. **Check the generated model before launching.** Run `check_urdf` and `gz sdf -p <urdf>`, and confirm that the friction, `fdir1` and collision blocks are what you expect.
5. **Run a 30-second motion test after every export or edit.** Drive straight, strafe and spin, and read the true pose in sim time from `/world/<world>/dynamic_pose/info`.
6. **Design for the drive type.** For skid-steer, a track ≥ wheelbase makes turning much easier, both in simulation and on the real robot. (Mecanum avoids the problem.)
