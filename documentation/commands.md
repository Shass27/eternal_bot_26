# Commands cheat sheet

Run everything from the repo root. Every terminal needs `source install/setup.bash` first.

## Build

```bash
colcon build --symlink-install && source install/setup.bash   # symlink-install: config/launch edits need no rebuild; new files, setup.py and package.xml edits do
```

## Sequences

### A. Sim only
```bash
ros2 launch eternal_bot_description gazebo.launch.py                   # arena world (default); robot spawns after 5 s
ros2 launch eternal_bot_description gazebo.launch.py world:=arena_obs  # arena + 4 cylinders
ros2 launch eternal_bot_description gazebo.launch.py world:=empty      # Gazebo empty.sdf
ros2 launch eternal_bot_description gazebo_min.launch.py               # robot in empty world only (no twist_mux, so /cmd_vel is raw)
```

### B. Sim + RViz
```bash
# T1
ros2 launch eternal_bot_description gazebo.launch.py                   # starts sim, bridge, twist_mux, nonzero_filter
# T2
rviz2 -d src/eternal_bot_description/config/gazebo.rviz --ros-args -p use_sim_time:=true   # without --ros-args -p nothing displays
```

### C. Sim + SLAM + RViz + teleop
```bash
# T1
ros2 launch eternal_bot_description gazebo.launch.py world:=arena_obs  # wait for the robot to spawn
# T2
ros2 launch eternal_bot_description slam.launch.py                     # slam_toolbox; publishes /map and map->odom
# T3
rviz2 -d src/eternal_bot_description/config/gazebo.rviz --ros-args -p use_sim_time:=true   # set Fixed Frame to map once SLAM runs
# T4
ros2 run key_teleop key_teleop --ros-args -p twist_stamped_enabled:=false   # must be Twist, not TwistStamped
```

Variant of C, T4 for a from-scratch mapping run: bypass the mux and publish straight to `/cmd_vel` (no priorities, no e-stop):
```bash
ros2 run key_teleop key_teleop --ros-args -p twist_stamped_enabled:=false -r key_vel:=cmd_vel
```

### D. Driving and twist_mux tests
Priority: `cmd_vel_safe` (10, Nav2 output) < `key_vel_filtered` (20, key_teleop) < `cmd_vel_emergency` (255). The `/e_stop` lock blocks nav + teleop.
```bash
ros2 topic echo /cmd_vel --field linear.x                              # watch the mux output
ros2 run key_teleop key_teleop --ros-args -p twist_stamped_enabled:=false   # keyboard; idle zeros are dropped by nonzero_filter
ros2 topic pub -r 10 /cmd_vel_safe geometry_msgs/msg/Twist '{linear: {x: 0.1}}'          # nav source; key presses override it
ros2 topic pub -r 10 /cmd_vel_emergency geometry_msgs/msg/Twist '{}'                    # zero Twist wins over everything
ros2 topic pub -r 10 /e_stop std_msgs/msg/Bool '{data: true}'                           # lock engaged; Ctrl+C this first, then release:
ros2 topic pub --once /e_stop std_msgs/msg/Bool '{data: false}'                         # lock released
ros2 topic info /cmd_vel -v                                            # only twist_mux should publish
ros2 run teleop_twist_keyboard teleop_twist_keyboard                   # alternative teleop; needs -r cmd_vel:=key_vel_filtered to go through the mux
```

### E. Preview without the sim
```bash
ros2 launch eternal_bot_description display.launch.py                  # rviz + joint_state_publisher GUI
ros2 launch eternal_bot_description display.launch.py gui:=False       # same without the joint GUI
./src/eternal_bot_description/view.sh                                  # urdf-viz preview, no ROS needed
```

## Cleanup

```bash
pkill -9 -f "[g]z sim"                 # bracket pattern so pkill doesn't kill its own shell
pkill -f "[p]arameter_bridge"          # leftover ros_gz_bridge
pkill -f "[r]obot_state_publisher"     # leftover state publisher
pkill -f "[t]wist_mux"                 # leftover mux
pkill -f "[n]onzero_filter"            # leftover key_teleop zero filter
pkill -f "[g]azebo.launch"             # the launch process itself
pgrep -fa "[g]z sim"                   # confirm nothing stale before relaunching
```

## Quick reference

| Command | Purpose | Needs |
|---|---|---|
| `colcon build --symlink-install` | Build/install the package | repo root |
| `gazebo.launch.py [world:=...]` | Sim + bridge + twist_mux + filter | nothing |
| `gazebo_min.launch.py` | Robot in empty world only | nothing |
| `slam.launch.py` | slam_toolbox on `/scan` | sim running |
| `rviz2 -d .../gazebo.rviz --ros-args -p use_sim_time:=true` | Visualise sim | sim running |
| `key_teleop ... twist_stamped_enabled:=false` | Keyboard drive via mux | sim running |
| `topic pub /cmd_vel_safe` | Nav-priority command | sim running |
| `topic pub /cmd_vel_emergency` | Zero Twist at top priority | sim running |
| `topic pub /e_stop (Bool)` | Lock out nav + teleop | sim running |
| `display.launch.py [gui:=False]` | RViz + joint GUI, no sim | nothing |
| `view.sh` | urdf-viz preview | `urdf-viz`, `xacro` |
| `pkill -9 -f "[g]z sim"` | Kill the simulator | nothing |
