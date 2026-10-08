# 6. Switch to holonomic (mecanum) simulation

> **Concept**
> - **Holonomic** means the robot can move in any planar direction (forward, sideways, spin) independently. A mecanum robot can strafe, and a skid-steer robot can't.
> - **Mecanum wheels** have small rollers set at 45° around the rim. Each wheel pushes the robot along its roller direction, and the four wheels' pushes add up to forward, sideways or rotation, depending on the wheel speeds.
> - **Why emulate:** modelling real rollers is expensive and unstable. Instead, the wheel is a plain sphere whose friction is high along the roller direction and zero across it, which gives the same net force.
> - **`fdir1`** is the friction direction. It rotates with the wheel link by default, which would make it spin with the wheel. `gz:expressed_in="base_link"` pins it to the chassis.
> - **`ros_gz_bridge`** forwards topics between ROS 2 and Gazebo.

- Replaced `gz_ros2_control` + `diff_drive_controller` with the Gazebo `gz-sim-mecanum-drive-system` plugin: wheels stay plain cylinders, the plugin maps body Twist (x, y, yaw) to wheel velocities.
- Plugin consumes `Twist` directly, so the TwistStamped relay and ros2_control config were removed; cmd_vel, odom, tf and joint_states go through `ros_gz_bridge`.
- The plugin only sets wheel joint velocities, so plain wheels skid instead of strafing. Rollers are emulated like gz's `mecanum_drive.sdf`: sphere wheel collisions, mu=1 along +-45deg `fdir1`, mu2=0 across (FL/RR `1 -1 0`, FR/RL `1 1 0`).
- `fdir1` rotates with the wheel link by default, so it needs `gz:expressed_in="base_link"`. URDF can't express that (the converter drops it), so `gazebo.launch.py` converts URDF->SDF, tags `fdir1`, and spawns with `-string`.
- Verified on ground truth (`/world/empty/dynamic_pose/info`): 0.3 m/s forward, strafe-left and spin all move as commanded with no drift.
