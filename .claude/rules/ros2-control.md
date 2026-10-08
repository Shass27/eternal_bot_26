---
paths:
  - "**/*.ros2control"
  - "**/controllers*.yaml"
  - "**/hardware/**"
---
# ros2_control rules (real-hardware phase)

## Real robot vs sim
- The physical mecanum wheels have real rollers. The friction emulation in `eternal_bot.gazebo` is **sim-only**; don't carry it over.
- Keep the hardware-only pieces (`<ros2_control>` block, hardware plugin) behind a xacro arg, e.g. `use_sim`, so sim and real share one description.

## Controller
- Use `mecanum_drive_controller` from ros2_controllers.
- In Jazzy, ros2_controllers drive controllers take **`geometry_msgs/TwistStamped`** only, and `use_stamped_vel` is ignored. Check the input topic with `ros2 topic info -v`, e.g. `/<controller>/reference` or `/<controller>/cmd_vel`.
  - Plain Twist publishers such as teleop or Nav2 need `-p stamped:=true`, Nav2's `enable_stamped_cmd_vel`, or a relay.
  - The removed `twist_to_stamped` node in commit 1752d97 is such a relay.
- Commands time out after about 0.5 s (`cmd_vel_timeout` / `reference_timeout`), so publish continuously.
- Wheel separation and wheelbase are measured between wheel **centres**: 0.33 / 0.44, not the joint offsets of 0.28.
- For a working Jazzy `diff_drive_controller` + `gz_ros2_control` setup to start from, see commit 1752d97.

## Packaging
- `setup.cfg` must install scripts to `lib/eternal_bot_description`. The fusion2urdf template had `lib/fusion2urdf_ros2`, which breaks `ros2 run`.
- Add new controller/hardware packages to `package.xml` as `exec_depend`.
