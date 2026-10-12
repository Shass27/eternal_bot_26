---
paths:
  - "**/urdf/**"
  - "**/launch/**"
  - "**/config/**"
---
# Sensors and navigation

## Lidar on `lidar_1`
- Add a `<sensor type="gpu_lidar">` under `<gazebo reference="lidar_1">`. Give it `<topic>scan</topic>`, `<gz_frame_id>lidar_1</gz_frame_id>`, an update rate, and ray/range settings.
- `lidar_1` is attached with a fixed joint, so the converter **merges it into `base_link`**. Check the frame in the SDF output, and that `/scan`'s `header.frame_id` matches a TF frame.
- Done: the sensor and the `gz-sim-sensors-system` plugin (ogre) live in `urdf/eternal_bot.gazebo`, `/scan` is bridged, and `lidar_1` sits at z=0.1062 so the scan clears the wheel tops. See `documentation/08-lidar.md`. Loading the sensors plugin from the model works with `empty.sdf`.
- Bridge `/scan` with `sensor_msgs/msg/LaserScan` ↔ `gz.msgs.LaserScan`, GZ→ROS.
- Any new sensor must survive the URDF→SDF conversion in `gazebo.launch.py`. Grep the converted SDF to check.

## SLAM (done)
- `launch/slam.launch.py` includes slam_toolbox `online_async_launch.py` with `config/mapper_params_online_async.yaml` and `use_sim_time:=true`. Start it after `gazebo.launch.py`. It consumes `/scan` and the bridged `odom→base_link` TF, and publishes `/map` and `map→odom`.
- Teleop for mapping: `key_teleop` defaults to `TwistStamped` on `/key_vel`. Run it with `-p twist_stamped_enabled:=false -r key_vel:=cmd_vel`.
- Saving: occupancy grid with `nav2_map_server map_saver_cli -f <path>`; pose graph with the `/slam_toolbox/serialize_map` service (absolute path, no extension). Both go in `maps/` in the package (installed via `setup.py`). A map yaml's `image:` is relative to the yaml.
- Resuming/localizing: set `mode: localization` and `map_file_name: <path without extension>` in the params file, plus `map_start_at_dock` or `map_start_pose`.
- RViz: Map display on `/map` is Transient Local. Fixed Frame `map` only works once slam_toolbox is running.

## Nav2 (roadmap)
- odom→base_link already comes from the MecanumDrive plugin. If you add `robot_localization` (EKF), turn off the plugin's TF or the EKF's `publish_tf`, so only one source publishes it.
- `slam_toolbox` / AMCL provide map→odom. Every node needs `use_sim_time: True`.
- The robot is holonomic. Use the MPPI controller with `motion_model: "Omni"`, and set `vy` limits in the controller and in `velocity_smoother`. A DWB/DiffDrive setup will never strafe.
- Nav2 publishes plain Twist on `/cmd_vel` by default (configurable), which matches the current bridge.
