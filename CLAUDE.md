# eternal_bot_26

4-wheel **mecanum** robot, simulated in Gazebo. Single ament_python package: `src/eternal_bot_description`.
Stack: ROS 2 **Jazzy** + Gazebo **Harmonic** (gz-sim 8, DART physics), running in an Ubuntu VM.

## Layout
- `src/eternal_bot_description/urdf/`
  - `eternal_bot.xacro`: links, joints, inertia, collisions (exported by fusion2urdf, then hand-edited)
  - `eternal_bot.gazebo`: MecanumDrive + JointStatePublisher plugins, per-link friction
  - `materials.xacro`
- `meshes/`: Fusion STLs (visuals, plus base/lidar collisions)
- `config/`: `ros_gz_bridge_gazebo.yaml`, `mapper_params_online_async.yaml` (slam_toolbox), rviz configs
- `maps/`: saved SLAM output for `arena_obs`: `obs_map.pgm/.yaml` (occupancy grid) and `obs_map_serial.posegraph/.data` (slam_toolbox pose graph)
- `launch/`: `gazebo.launch.py` (sim, `world:=arena|arena_obs|empty`, default arena), `gazebo_min.launch.py` (robot in empty world only), `display.launch.py` (rviz + joint GUI), `slam.launch.py` (slam_toolbox on a running sim)
- `worlds/`: `arena.world`, `arena_obs.world` (arena + 4 cylinders), `meshes/arena.dae`. World name is `default`
- `view.sh`: quick urdf-viz preview without ROS
- `cad/eternal_bot_minimal.f3d`: source CAD
- `documentation/README.md`: debugging history and why things are the way they are. **Read it before changing physics or the drive.**

## Commands
```bash
colcon build --symlink-install && source install/setup.bash        # from repo root
ros2 launch eternal_bot_description gazebo.launch.py                # sim, arena world
ros2 launch eternal_bot_description gazebo.launch.py world:=arena_obs  # arena + obstacles (or world:=empty)
ros2 launch eternal_bot_description gazebo_min.launch.py            # robot in empty world only
ros2 launch eternal_bot_description display.launch.py               # rviz only
ros2 run teleop_twist_keyboard teleop_twist_keyboard                # drive; hold Shift to strafe
rviz2 -d src/eternal_bot_description/config/gazebo.rviz --ros-args -p use_sim_time:=true
ros2 launch eternal_bot_description slam.launch.py                  # SLAM, needs the sim running
ros2 run key_teleop key_teleop --ros-args -p twist_stamped_enabled:=false -r key_vel:=cmd_vel
# save map: map_saver_cli -f <path> --ros-args -p use_sim_time:=true; pose graph: /slam_toolbox/serialize_map service (absolute path, no extension)
```
To verify motion after any URDF, friction, plugin or launch change, command `/cmd_vel` and compare against sim-time ground truth (see `.claude/rules/sim-launch.md`, "Debugging motion").

## How driving works
1. `/cmd_vel` (`geometry_msgs/Twist`) goes through `ros_gz_bridge` to the gz **MecanumDrive** plugin, which sets the 4 wheel joint velocities.
2. The rollers are not modelled. They are **emulated by friction**: sphere wheel collisions, μ=1 along a ±45° `fdir1`, μ=0 across it.
3. `/odom` and `/tf` (odom→base_link) come back from the plugin through the bridge; `/joint_states` comes from JointStatePublisher. There is no ros2_control in sim.

## Key dimensions
These are duplicated in the joints, collisions and plugin, so change them together.
- Wheel radius 0.05 m, width 0.05 m.
- Track 0.33 m, measured between wheel centres. The joint origins are at y=±0.14, on the wheels' inner faces.
- Wheelbase 0.44 m.
- Base 14 kg; wheels 0.4 kg each.

## Gotchas
- **Gazebo does not spawn from `/robot_description`.** `gazebo.launch.py` converts the model to SDF, pins `fdir1` to `base_link`, and spawns that. Test model changes through this launch file.
- **Measure speeds in sim time** (`/world/empty/dynamic_pose/info`; `/world/default/...` in the arena worlds). Wall-clock numbers are wrong whenever the real-time factor (RTF) is below 1, which is common on the VM.
- **Keep `--render-engine ogre`** in `gz_args`. It is needed on the VM; native Ubuntu can drop it.
- **Kill the sim with bracket patterns**, e.g. `pkill -9 -f "[g]z sim"`. A plain `pkill -f "gz sim"` also matches and kills the shell running it.
- **The robot spawns after a 5 s timer.** Wait for the `eternal_bot` model before commanding it.
- **RViz needs `--ros-args -p use_sim_time:=true`.** Without `--ros-args -p` the flag is ignored and nothing displays (TF/scan are stamped in sim time). Set Fixed Frame to `map` once SLAM runs.
- **`key_teleop` publishes `TwistStamped` on `/key_vel`.** The bridge wants `Twist` on `/cmd_vel`, so use `twist_stamped_enabled:=false` and the `key_vel:=cmd_vel` remap.
- **Large map files.** `maps/*.posegraph` is about 7 MB. Do not `git add .` blindly when saving new maps.
- **The URDF comes from the CAD exporter.** Keep hand edits minimal, and record non-obvious ones in `documentation/README.md`.

## Rules and skills
These load only when relevant:
- `.claude/rules/urdf-gazebo.md`: collisions, friction, mecanum emulation, validation
- `.claude/rules/sim-launch.md`: launch pipeline, bridge, sim time, debugging
- `.claude/rules/sensors-nav.md`: lidar, SLAM, Nav2 (roadmap)
- `.claude/rules/ros2-control.md`: real-hardware controllers (roadmap)

## Roadmap
lidar/sensors in sim (done) → SLAM (slam_toolbox, done) → Nav2 → real hardware (ros2_control).
