# 9. SLAM (slam_toolbox) and localization

> **Concept**
> - **SLAM** builds a map and estimates the robot's pose in it at the same time. In 2D it needs a laser scan (`/scan`) and an odometry source (`odom→base_link`); both already exist in the sim.
> - **slam_toolbox `online_async`** processes scans as fast as it can and drops what it can't keep up with, so the map never blocks driving. It publishes `/map` (occupancy grid) and the **`map→odom`** transform. The chain is `map → odom → base_link`; the MecanumDrive plugin owns the second link.
> - **The `map` frame starts at the robot's first pose.** Mapping from the spawn point (0, 0, yaw 0) means `map` and the Gazebo world coordinates coincide only if the robot spawned at the world origin, which `gazebo.launch.py` does.
> - **Two map formats.** The *occupancy grid* (`.pgm` + `.yaml`) is a picture for planners and AMCL. The *serialized pose graph* (`.posegraph` + `.data`) is slam_toolbox's own state (every scan and constraint) and is the only one slam_toolbox can resume from.
> - **Localization** means finding the pose in an *existing* map without changing it. slam_toolbox does it from the pose graph; AMCL does it from the occupancy grid.

## What changed, by commit
| Commit | Date | What |
|---|---|---|
| `c57db22` / `b7a4d13` | Oct 9 | Lidar done: `/scan` bridged, lidar at z=0.1062 (chapter 8). Prerequisite for SLAM. |
| `b9bce79`, `0fd6353` | Oct 11 | Arena worlds (`arena`, `arena_obs`) and the `world:=` argument. SLAM needs walls and obstacles to match against; the empty world gives nothing to map. |
| `bac0bec` | Oct 12 | `slam.launch.py`, `config/mapper_params_online_async.yaml`, Map display in `gazebo.rviz`, first saved map of `arena_obs` (in `maps/`, installed via `setup.py`). |
| `7b95040` | Oct 12 | SLAM commands, gotchas and the map-saving procedure written into `CLAUDE.md` and `.claude/rules/sensors-nav.md`. |
| `1e0d21a` | Oct 13 | twist_mux: teleop now goes through `key_vel_filtered` (see below). |

## What was done, by phase
1. **Prove the inputs.** `/scan` frame is `lidar_1`, the TF chain `odom → base_link → lidar_1` exists, and Gazebo publishes `/clock`. slam_toolbox needs all three; nothing else had to be added to the model.
2. **Launch wrapper.** `launch/slam.launch.py` just includes slam_toolbox's `online_async_launch.py` with `slam_params_file` set to our yaml and `use_sim_time: true`. It does not start the sim; run it after `gazebo.launch.py`.
3. **Parameters.** `config/mapper_params_online_async.yaml` is slam_toolbox's stock file with the frames set to this robot: `odom_frame: odom`, `map_frame: map`, `base_frame: base_link`, `scan_topic: /scan`, `mode: mapping`. Other values worth knowing:
   - `resolution: 0.05` (5 cm cells), `max_laser_range: 12.0` (matches the lidar), `map_update_interval: 5.0` s.
   - `minimum_travel_distance` / `minimum_travel_heading: 0.5`: a scan is only added after the robot moved 0.5 m or turned 0.5 rad, so a stationary robot adds nothing.
   - `do_loop_closing: true`, `loop_search_maximum_distance: 3.0`: closes loops within 3 m of the current pose.
   - `stack_size_to_use: 40000000`: serializing a big graph needs a large stack.
4. **RViz.** `gazebo.rviz` got a Map display on `/map` (Durability **Transient Local**, otherwise the latched map is never received) and `/map_updates`. Fixed Frame must be `map`, which only exists once slam_toolbox publishes it.
5. **Drive and map.** Teleop through key_teleop around `arena_obs`, closing a loop so the graph is corrected.
6. **Save.** Two artifacts, because they serve different consumers (below). Both live in `maps/` inside the package and are installed by a `setup.py` `maps/*` glob.

## Running it
```bash
ros2 launch eternal_bot_description gazebo.launch.py world:=arena_obs   # T1; wait for the spawn
ros2 launch eternal_bot_description slam.launch.py                      # T2
rviz2 -d src/eternal_bot_description/config/gazebo.rviz --ros-args -p use_sim_time:=true   # T3; Fixed Frame: map
ros2 run key_teleop key_teleop --ros-args -p twist_stamped_enabled:=false                  # T4
```
Drive slowly; fast spins make scan matching jump. Cover each wall from more than one side and return to the start so the loop closes.

## Saving the map
```bash
# occupancy grid -> obs_map.pgm + obs_map.yaml (for Nav2 / AMCL / viewing)
ros2 run nav2_map_server map_saver_cli -f <path>/obs_map --ros-args -p use_sim_time:=true

# pose graph -> obs_map_serial.posegraph + .data (to resume SLAM or localize in slam_toolbox)
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '/abs/path/obs_map_serial'}"
```
- The service path must be **absolute and without extension**; slam_toolbox appends `.posegraph` and `.data`.
- `obs_map2.yaml`'s `image:` is relative to the yaml, so keep the pair together. Its `origin: [-2.846, -0.501, 0]` is the pgm's lower-left corner in the `map` frame (the first set, `obs_map`, was cropped at y=-0.031 and clipped the robot at spawn).
- The `.posegraph` is about 7 MB. Don't `git add .` after saving new maps without checking.

## Localization on an existing map (reference; not done on this project)
Two routes. Pick by what you plan to build next.

### A. slam_toolbox localization mode (uses the pose graph)
Best when you only need a pose and want the same stack as mapping.
1. Copy `localization` settings into the params file (or make a second file, e.g. `config/mapper_params_localization.yaml`):
   ```yaml
   mode: localization
   map_file_name: /abs/path/obs_map2_serial    # pose graph, no extension
   map_start_pose: [0.0, 0.0, 0.0]            # x, y, yaw in the MAP frame where the robot starts
   #map_start_at_dock: true                   # alternative; mutually exclusive with map_start_pose
   ```
2. Start the sim (same world the map was made in), then slam_toolbox in localization mode:
   ```bash
   ros2 launch slam_toolbox localization_launch.py slam_params_file:=<localization yaml> use_sim_time:=true
   ```
   (`slam.launch.py` includes `online_async_launch.py`, which runs the mapping node; the localization node is a different executable, `localization_slam_toolbox_node`.)
3. In RViz, Fixed Frame `map`. The saved map appears and `map→odom` is published, correcting the drift of `odom`.

Notes:
- **Start pose matters.** slam_toolbox does not search the whole map. If the robot spawns far from `map_start_pose`, matching fails or snaps to a wrong place. Spawn at the same place as when mapping (`-x 0 -y 0 -Y 0` in `gazebo.launch.py`), or give the real pose.
- **Localization mode still adds scans** to a local, temporary graph around the robot; the saved map file is not modified unless you serialize again.
- Use `ros2 service call /slam_toolbox/deserialize_map ...` if you want to load a graph into a node that is already running.

### B. Nav2 map_server + AMCL (uses the occupancy grid)
This is the route Nav2 expects, and it is what the roadmap's Nav2 step will use.
```bash
ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=<path>/obs_map.yaml -p use_sim_time:=true
ros2 run nav2_amcl amcl --ros-args -p use_sim_time:=true -p scan_topic:=/scan
ros2 lifecycle set /map_server configure && ros2 lifecycle set /map_server activate
ros2 lifecycle set /amcl configure && ros2 lifecycle set /amcl activate
```
- Give the initial pose with RViz's *2D Pose Estimate* tool, or the `/initialpose` topic. AMCL is a particle filter and needs a rough starting pose.
- For a holonomic robot set AMCL's `robot_model_type` to `nav2_amcl::OmniMotionModel`; the default differential model will fight sideways motion.
- Normally the nav2 `lifecycle_manager` does the configure/activate steps; the manual commands above are for trying it by hand.

### Which one
| | slam_toolbox localization | AMCL |
|---|---|---|
| Map input | `.posegraph` + `.data` | `.pgm` + `.yaml` |
| Pose search | Local around start pose | Particles; recovers from kidnapping |
| Fits Nav2 as-is | Works (provides `map→odom`) | Default Nav2 setup |
| Extra nodes | None | map_server + AMCL (+ lifecycle) |

## Gotchas
- **RViz shows nothing.** It needs `--ros-args -p use_sim_time:=true` (without `--ros-args -p` the flag is ignored). Fixed Frame `map` only works once SLAM is running; with no SLAM use `odom`.
- **Map never appears in RViz.** The Map display's Durability must be Transient Local, since `/map` is latched and only published every `map_update_interval`.
- **Robot doesn't respond to keys.** key_teleop publishes `TwistStamped` on `/key_vel`. Use `twist_stamped_enabled:=false`. Without a remap the keys go through the mux: twist_mux listens to `key_vel_filtered`, fed from `/key_vel` by the `nonzero_filter` node started in `gazebo.launch.py`. To bypass the mux, add `-r key_vel:=cmd_vel` (see next gotcha).
- **Two ways to drive while mapping.** Default is through twist_mux (key_teleop on `/key_vel`, as in *Running it*). For a from-scratch mapping run you may want to bypass the mux: `ros2 run key_teleop key_teleop --ros-args -p twist_stamped_enabled:=false -r key_vel:=cmd_vel` publishes straight to `/cmd_vel`, as in the header comment of `launch/slam.launch.py`. Nothing is arbitrated then: `/e_stop` and `cmd_vel_emergency` do not stop a bypassing publisher, and Nav2 (`cmd_vel_nav`) would compete with it. Use it only when the keyboard is the sole driver.
- **One TF publisher only.** The MecanumDrive plugin publishes `odom→base_link`. If an EKF (`robot_localization`) is added, disable one of them. slam_toolbox publishes only `map→odom`.
- **Real-time factor below 1** makes `ros2 topic hz` look slow; the map is built from sim time, so it is unaffected.
- **Wheel-slip drift.** Rollers are friction-emulated, so odometry drifts more on strafes/spins than a real mecanum. Scan matching corrects most of it; if the map smears, drive slower.

## Files
| File | Role |
|---|---|
| `launch/slam.launch.py` | Includes slam_toolbox `online_async_launch.py` with our params, sim time on |
| `config/mapper_params_online_async.yaml` | Mapping-mode parameters |
| `config/gazebo.rviz` | LaserScan, TF and Map displays |
| `maps/obs_map2.{pgm,yaml}` | Occupancy grid of `arena_obs` |
| `maps/obs_map2_serial.{posegraph,data}` | slam_toolbox pose graph of `arena_obs` |
