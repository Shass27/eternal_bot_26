---
paths:
  - "**/launch/**"
  - "**/config/**"
---
# Sim launch, bridge and debugging rules

## gazebo.launch.py pipeline
1. `xacro.process_file` produces the URDF, which goes to `robot_state_publisher` (`use_sim_time: True`).
2. The URDF is written to a temp file and run through `gz sdf -p`. If `gz` isn't on PATH, it falls back to `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`.
3. A regex rewrites `<fdir1>` to `<fdir1 gz:expressed_in="base_link">` and adds the `xmlns:gz` namespace.
4. `ros_gz_sim create -string <sdf>` runs after a 5 s `TimerAction`.
5. Gazebo is started with `gz_args: -r -v 4 --render-engine ogre empty.sdf`. Keep `ogre` on the VM.

## Bridge (`config/ros_gz_bridge_gazebo.yaml`)
Current pairs:

| ROS type | gz type | Direction |
|---|---|---|
| `rosgraph_msgs/Clock` | `gz.msgs.Clock` | GZ→ROS |
| `geometry_msgs/Twist` | `gz.msgs.Twist` | ROS→GZ |
| `nav_msgs/Odometry` | `gz.msgs.Odometry` | GZ→ROS |
| `tf2_msgs/TFMessage` | `gz.msgs.Pose_V` | GZ→ROS |
| `sensor_msgs/JointState` | `gz.msgs.Model` | GZ→ROS |

- Only **one** node may publish odom→base_link. Today that is the MecanumDrive plugin via `/tf`.
- Every ROS node you add needs `use_sim_time: True`.

## Debugging motion
- Get ground truth in **sim time**: `gz topic -e -t /world/empty/dynamic_pose/info -n 1` gives the stamp and the `eternal_bot` pose.
- Check RTF with `gz topic -e -t /stats -n 1 | grep real_time_factor`. Wall-clock speed measurements are misleading when RTF < 1.
- `gz model -m eternal_bot -p` / `-l <link>` / `-j <joint>` inspect the live model.
- To isolate friction (torque test): launch a copy of `empty.sdf` with `<plugin filename="gz-sim-apply-link-wrench-system" name="gz::sim::systems::ApplyLinkWrench"/>` added, then:
  ```bash
  gz topic -t /world/empty/wrench/persistent -m gz.msgs.EntityWrench -p 'entity: {name: "eternal_bot::base_link", type: LINK}, wrench: {torque: {z: 5}}'
  sleep 2; gz model -m eternal_bot -p | tail -1
  gz topic -t /world/empty/wrench/clear -m gz.msgs.Entity -p 'name: "eternal_bot::base_link", type: LINK'
  ```
  The expected breakaway torque is roughly μ·m·g·0.28 m. Far more resistance means link μ is being ignored (usually mesh collisions).
- Publish commands continuously (`-r 10`+), not `--once`.

## Process cleanup
- Use bracketed patterns so pkill doesn't match its own shell: `pkill -f "[g]azebo.launch"; pkill -9 -f "[g]z sim"; pkill -f "[r]obot_state_publisher"; pkill -f "[p]arameter_bridge"`.
- Stale gz servers from earlier runs will mix their poses into your readings. Check `pgrep -fa "[g]z sim"` before you launch.
