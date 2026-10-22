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
- Done: the sensor and the `gz-sim-sensors-system` plugin (`render_engine` launch arg, default ogre2) live in `urdf/eternal_bot.gazebo`, `/scan` is bridged, and `lidar_1` sits at z=0.1062 so the scan clears the wheel tops. See `documentation/08-lidar.md`. Loading the sensors plugin from the model works with `empty.sdf`.
- Bridge `/scan` with `sensor_msgs/msg/LaserScan` ↔ `gz.msgs.LaserScan`, GZ→ROS.
- Any new sensor must survive the URDF→SDF conversion in `gazebo.launch.py`. Grep the converted SDF to check.

## SLAM (done)
- `launch/slam.launch.py` includes slam_toolbox `online_async_launch.py` with `config/mapper_params_online_async.yaml` and `use_sim_time:=true`. Start it after `gazebo.launch.py`. It consumes `/scan` and the bridged `odom→base_link` TF, and publishes `/map` and `map→odom`.
- Teleop for mapping: `key_teleop` defaults to `TwistStamped` on `/key_vel`. Run it with `-p twist_stamped_enabled:=false`; `nonzero_filter` strips idle zeros from `key_vel` into `key_vel_filtered`, which twist_mux forwards to `/cmd_vel`.
- Saving: occupancy grid with `nav2_map_server map_saver_cli -f <path>`; pose graph with the `/slam_toolbox/serialize_map` service (absolute path, no extension). Both go in `maps/` in the package (installed via `setup.py`). A map yaml's `image:` is relative to the yaml.
- Resuming/localizing: set `mode: localization` and `map_file_name: <path without extension>` in the params file, plus `map_start_at_dock` or `map_start_pose`.
- RViz: Map display on `/map` is Transient Local. Fixed Frame `map` only works once slam_toolbox is running.

## Nav2 (done)
- Full write-up: `documentation/10-nav2.md`. Run order: `gazebo.launch.py` → `slam.launch.py` (localization) → `nav.launch.py`; send goals from RViz "2D Goal Pose". `nav.launch.py` blocks until `map→odom` exists.
- `mapper_params_online_async.yaml` `map_file_name` is absolute; fix it for your checkout or localization (and so Nav2) never starts.
- odom→base_link already comes from the MecanumDrive plugin. If you add `robot_localization` (EKF), turn off the plugin's TF or the EKF's `publish_tf`, so only one source publishes it.
- `slam_toolbox` / AMCL provide map→odom. Every node needs `use_sim_time: True`.
- The robot is holonomic. Use the MPPI controller with `motion_model: "Omni"`, and set `vy` limits in the controller and in `velocity_smoother`. A DWB/DiffDrive setup will never strafe.
- Nav2 runs via `launch/nav.launch.py` with `config/nav2_params.yaml` (copy of the stock file). Chain: controller → `cmd_vel_nav` → velocity_smoother → `cmd_vel_smoothed` → collision_monitor → `cmd_vel_safe` (plain `Twist`) → twist_mux → `/cmd_vel`. `collision_monitor` must not write `cmd_vel_nav` (smoother input, loop).
- Params changed from stock for this robot: `base_frame_id: base_link` (no `base_footprint`), `motion_model: Omni`, vy enabled in velocity_smoother and `min_y_velocity_threshold`, `robot_radius: 0.30`, inflation 0.5 (the start-strip gap is ~0.8 m). No map_server/amcl: slam_toolbox localization supplies `/map` and map→odom.
- Map extent comes from slam_toolbox pose-graph poses, so keep margin around the spawn when mapping or the costmap clips the robot ("Robot is out of bounds of the costmap").
