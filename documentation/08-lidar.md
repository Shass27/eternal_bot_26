# 8. 2D lidar (gpu_lidar on lidar_1)

> **Concept**
> - **Lidar** measures distance by casting rays and timing the return. A **2D lidar** casts one horizontal ring of rays and outputs `sensor_msgs/LaserScan` (one range per angle), which is what SLAM and Nav2 expect.
> - **`gpu_lidar`** is the Gazebo sensor that does this on the GPU by rendering depth. It needs the **sensors system** (`gz-sim-sensors-system`) running, or the sensor exists but never produces data.
> - **Fixed joints collapse in SDF.** A link joined by a `fixed` joint is merged into its parent when `gz sdf -p` converts the URDF. `lidar_1` stops being a link and becomes a `<frame>`; its mesh and the sensor live on `base_link`.
> - **`gz_frame_id`** sets the `frame_id` in the scan header. Without it the header holds Gazebo's scoped name (`eternal_bot/base_link/lidar`), which does not exist in TF, so RViz and SLAM cannot place the points.
> - **The bridge** (`ros_gz_bridge`) maps `gz.msgs.LaserScan` to `sensor_msgs/msg/LaserScan`.

## What was done, by phase
0. **Inspect the conversion.** `gz sdf -p` on the xacro output shows `lidar_1` as `<frame name='lidar_1' attached_to='lidar_joint'>` and its mesh lumped into `base_link`. A sensor placed under `<gazebo reference="lidar_1">` lands on `base_link` at the joint's offset.
1. **Sensors system.** `gz-sim-sensors-system` with `<render_engine>ogre</render_engine>` was added to the model's `<gazebo>` block in `eternal_bot.gazebo`. `empty.sdf` does not load it, and loading it from the model works, so no custom world is needed. The plugin logs nothing on its own; the proof is `/scan` appearing once a sensor exists.
2. **Sensor.** `<sensor name="lidar" type="gpu_lidar">` under `<gazebo reference="lidar_1">`: topic `scan`, `gz_frame_id` `lidar_1`, 10 Hz, 360 samples over ±π, range 0.12 to 12 m.
3. **Bridge.** `/scan` was added to `config/ros_gz_bridge_gazebo.yaml` as `sensor_msgs/msg/LaserScan` ↔ `gz.msgs.LaserScan`, GZ→ROS.
4. **Verify.** `gz topic -e -t /scan`, `ros2 topic echo /scan --once` (`frame_id: lidar_1`), `tf2_echo base_link lidar_1`, then RViz with shapes in the world. Driving was re-tested: forward, strafe, spin, diagonal and arc, both directions, all within 5 % of the command and no drift on uncommanded axes.

## Gotchas
- **Self-hit ring.** The first mount put the scan plane at `z=0.0512` above `base_link`. The wheel spheres (radius 0.05, centre z=0.0256) reach up to z≈0.076, so about a quarter of the beams hit the robot's own wheels at ~0.29 m. The lidar mesh spans `z=0.0512 … 0.1012`, so the fix is to put the scan plane at the top of the mesh.
- **Hand edit to the CAD-exported URDF** (record this; a re-export from Fusion overwrites it). `lidar_1` was moved to the sensor height, with the mesh kept in place:
  - `lidar_joint` origin z: `0.0512` → `0.1062`
  - lidar `visual` and `collision` origin z: `-0.0512` → `-0.1062`
  - lidar `inertial` origin z: `0.025` → `-0.03`

  Doing it by moving the frame, rather than offsetting the sensor, keeps the sensor, `frame_id` and TF in agreement.
- **`gz_frame_id` warning.** `gz sdf -p` prints "XML Element[gz_frame_id] … not defined in SDF. Copying". It is copied through and works; ignore it.
- **Measured rate looks low.** `ros2 topic hz /scan` shows ~7.5 Hz against the 10 Hz setting. That is wall-clock time with a real-time factor below 1, not a fault.
- **"Detected jump back in time. Clearing TF buffer" in RViz** means the sim clock restarted while RViz stayed open, or RViz is not on sim time. Close RViz before relaunching Gazebo, start it only once `/scan` is listed, and always pass `--ros-args -p use_sim_time:=true`. `display.launch.py` does not set sim time and has no `/scan`; use it for the URDF only.

## Viewing it
```bash
ros2 launch eternal_bot_description gazebo.launch.py        # wait ~10 s for the spawn
rviz2 -d src/eternal_bot_description/config/gazebo.rviz --ros-args -p use_sim_time:=true
```
`gazebo.rviz` already has the LaserScan (`/scan`) and TF displays, fixed frame `odom`. If no points show, set the LaserScan reliability to Best Effort. The Gazebo GUI's "Visualize Lidar" draws the rays without the bridge, but can be unreliable on the VM's ogre renderer.
