---
paths:
  - "**/urdf/**"
  - "**/launch/**"
  - "**/config/**"
---
# Sensors and navigation (roadmap)

## Lidar on `lidar_1`
- Add a `<sensor type="gpu_lidar">` under `<gazebo reference="lidar_1">`. Give it `<topic>scan</topic>`, `<gz_frame_id>lidar_1</gz_frame_id>`, an update rate, and ray/range settings.
- `lidar_1` is attached with a fixed joint, so the converter **merges it into `base_link`**. Check the frame in the SDF output, and that `/scan`'s `header.frame_id` matches a TF frame.
- The sensor needs the `gz-sim-sensors-system` plugin with `<render_engine>ogre</render_engine>` on the VM. Put it in a custom world or the model's `<gazebo>` block; `empty.sdf` does not load it.
- Bridge `/scan` with `sensor_msgs/msg/LaserScan` ↔ `gz.msgs.LaserScan`, GZ→ROS.
- Any new sensor must survive the URDF→SDF conversion in `gazebo.launch.py`. Grep the converted SDF to check.

## Nav2 / SLAM
- odom→base_link already comes from the MecanumDrive plugin. If you add `robot_localization` (EKF), turn off the plugin's TF or the EKF's `publish_tf`, so only one source publishes it.
- `slam_toolbox` / AMCL provide map→odom. Every node needs `use_sim_time: True`.
- The robot is holonomic. Use the MPPI controller with `motion_model: "Omni"`, and set `vy` limits in the controller and in `velocity_smoother`. A DWB/DiffDrive setup will never strafe.
- Nav2 publishes plain Twist on `/cmd_vel` by default (configurable), which matches the current bridge.
