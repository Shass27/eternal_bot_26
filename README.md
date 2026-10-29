# eternal_bot_26

A 4-wheel **mecanum** robot simulated in Gazebo, driven by keyboard or by Nav2 on a SLAM map.

![ROS 2 Jazzy](https://img.shields.io/badge/ROS_2-Jazzy-22314E) ![Gazebo Harmonic](https://img.shields.io/badge/Gazebo-Harmonic-F58113)

| Gazebo (`arena_obs`) | Nav2 ready RViz (already SLAMed) |
|---|---|
| ![Gazebo](documentation/media/gazebo.png) | ![Nav2](documentation/media/nav2.png) |

## Highlights
- **Mecanum without rollers.** Each wheel is a sphere collision with anisotropic friction: μ=1 along a ±45° `fdir1`, μ=0 across it. The gz MecanumDrive plugin drives the wheel joints.
- **Safe command routing.** twist_mux ranks emergency stop over keyboard teleop over Nav2, and a `/e_stop` lock blocks motion.
- **SLAM.** slam_toolbox maps the arena; the saved pose graph is reused for localization.
- **Nav2.** Holonomic planning on the map, with a collision monitor in front of the mux.

## Architecture
```mermaid
flowchart LR
  KT[key_teleop] -->|/key_vel| NF[nonzero_filter] -->|key_vel_filtered| MUX
  NAV[Nav2 controller] --> CM[collision_monitor] -->|cmd_vel_safe| MUX
  EM[/cmd_vel_emergency/] --> MUX
  ES[/e_stop/] -.lock.-> MUX
  MUX[twist_mux] -->|/cmd_vel| BR[ros_gz_bridge]
  BR --> MD[gz MecanumDrive]
  MD -->|/odom, odom→base_link| BR
  LIDAR[gz lidar] -->|/scan| BR
  BR -->|/scan| SLAM[slam_toolbox] -->|map→odom, /map| NAV
```

Live node graph:

![rqt_graph](documentation/media/rqt_graph.png)

## Quickstart
Requires Ubuntu 24.04, ROS 2 Jazzy and Gazebo Harmonic, plus:
```bash
sudo apt install ros-jazzy-ros-gz ros-jazzy-slam-toolbox ros-jazzy-nav2-bringup \
  ros-jazzy-twist-mux ros-jazzy-key-teleop ros-jazzy-xacro
```
Build, then run each step in its own terminal from the repo root:
```bash
make build
make sim WORLD=arena_obs   # Gazebo + bridge + twist_mux
make slam                  # slam_toolbox (localizes on maps/obs_map2)
make nav                   # Nav2; send goals with RViz "2D Goal Pose"
make rviz
make teleop                # optional keyboard drive
```
`make help` lists every target, including `estop`, `estop-release` and `stop`.

### Render engine
The sim uses Gazebo's `ogre2` renderer by default. It is a launch argument that can be changed at runtime, and it applies to both the Gazebo GUI/server and the lidar sensor:
```bash
make sim RENDER=ogre                                                  # e.g. in a VM without proper GPU support
ros2 launch eternal_bot_description gazebo.launch.py render_engine:=ogre
```
The same `render_engine:=` argument works for `gazebo_min.launch.py`.

## Running on a Raspberry Pi
The laptop runs the simulation and RViz; a Raspberry Pi 5 (Ubuntu Server 24.04, ROS 2 Jazzy ros-base) runs SLAM and Nav2 over an ethernet cable. Both machines need the same `ROS_DOMAIN_ID` (26 in the setup used here). `/clock` comes from the laptop, so the Pi runs on sim time.

| Laptop | Raspberry Pi |
|---|---|
| `make sim WORLD=arena_obs` (Gazebo, bridge, twist_mux) | `ros2 launch eternal_bot_description pi.launch.py` (slam_toolbox localization on `maps/obs_map2_serial` + Nav2) |
| `make rviz`, `make teleop` | — |

The laptop builds the repo as in the Quickstart. On the Pi, once (needs ROS 2 Jazzy installed, see chapter 11):
1. Install the runtime packages. Not rosdep: `package.xml` would pull in Gazebo and RViz.
   ```bash
   sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox \
     ros-jazzy-twist-mux ros-jazzy-robot-state-publisher ros-jazzy-xacro
   ```
2. Clone the repo. `--depth 1` skips the history; the maps, about 7 MB, are still included and needed.
   ```bash
   git clone --depth 1 https://github.com/shass27/eternal_bot_26.git ~/eternal_bot_26
   ```
3. Build only this package, and source it in every new shell.
   ```bash
   cd ~/eternal_bot_26 && colcon build --symlink-install --packages-select eternal_bot_description
   echo "source ~/eternal_bot_26/install/setup.bash" >> ~/.bashrc && source ~/.bashrc
   ```

Then, each in its own terminal:
```bash
make sim WORLD=arena_obs   # laptop; wait for the single eternal_bot model (5 s timer)
ros2 launch eternal_bot_description pi.launch.py   # Pi; Nav2 starts once map→odom is published
make rviz                  # laptop; Fixed Frame map, send goals with "2D Goal Pose"
make teleop                # laptop, optional
```
`pi.launch.py` points slam_toolbox at the installed map, so `config/mapper_params_online_async.yaml` needs no per-machine edit.

See [chapter 11](documentation/11-raspberry-pi.md) for flashing, networking (direct-ethernet shared connection) and troubleshooting.

## Documentation
[`documentation/`](documentation/README.md) is the build log: debugging history, design decisions and chapters on drive, lidar, SLAM and Nav2. Read it before changing physics or the drive.

## License
[MIT](LICENSE)
