---
name: sim-drive-test
description: Verify eternal_bot drives, strafes and rotates as commanded in Gazebo, measured against simulation-time ground truth. Use after changing URDF/xacro, wheel friction or collisions, the MecanumDrive plugin, the bridge config or gazebo.launch.py, or when the robot "doesn't move/rotate/strafe properly".
---
# sim-drive-test

Manual procedure. It compares a commanded body twist with the model's true motion from
`/world/empty/dynamic_pose/info`, measured in **sim time** (never wall clock).

## Steps
1. Make sure no stale sim is running: `pgrep -fa "[g]z sim"`. If the user has their own sim open, ask before touching it.
2. Launch it: `ros2 launch eternal_bot_description gazebo.launch.py`. Wait until `gz topic -e -t /world/empty/dynamic_pose/info -n 1` lists `name: "eternal_bot"`. Spawning takes at least 5 s, and the sim must not be paused.
3. Publish continuously, never `--once`:
   `ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3, y: 0.0}, angular: {z: 0.0}}"`
4. After about 1.5 s of ramp-up, take two `dynamic_pose/info` snapshots about 2 s apart. For each one, record the header stamp (sim time) and the `eternal_bot` position x, y and orientation quaternion.
5. Compute the results:
   - `dt` = the difference between the two stamps.
   - Yaw from each quaternion, then `dyaw = atan2(sin(y1-y0), cos(y1-y0))`.
   - Rotate the world displacement into the body frame at `yaw0 + dyaw/2`.
   - The body vx, vy and wz are those values divided by `dt`.
   - Keep `|wz|·window < 2.5 rad`, otherwise the ±π wrap makes yaw ambiguous.
6. Run these cases: forward ±0.3, strafe y ±0.3, spin ±1.0, diagonal (0.2, 0.2), arc (0.3, wz 0.5). Each axis should be within 5 % (or 0.02 absolute) of the command, and there should be no drift on axes you didn't command.
7. Clean up with bracket patterns, which only matter for a sim you launched: `pkill -f "[g]azebo.launch"; pkill -9 -f "[g]z sim"; pkill -f "[r]obot_state_publisher"; pkill -f "[p]arameter_bridge"`.

For a ros2_control controller (the hardware phase), publish `geometry_msgs/msg/TwistStamped` to the controller's input topic instead.

## Reading failures
| Symptom | Likely cause |
|---|---|
| forward OK, **wz ≈ 0** on spin | Friction isn't being honoured. Check for STL mesh collisions on the wheels, or isotropic μ on a skid-steer setup. See `documentation/03-skid-steer-errors.md` §1–2. |
| strafe **inverted** or shows up as yaw | The `fdir1` patterns are swapped (FL/RR should be `1 -1 0`, FR/RL `1 1 0`), or joint axis signs are wrong. |
| motion drifts or curves over time | `fdir1` isn't pinned to `base_link`. Check `gazebo.launch.py`'s SDF post-processing. |
| everything ≈ 0 | Commands aren't arriving. Check `ros2 topic info -v /cmd_vel` and the bridge yaml, and whether the model spawned or the sim is paused. |
| speeds scaled by a constant | `wheel_radius`, `wheel_separation` or `wheelbase` don't match the geometry. |

A low RTF (`gz topic -e -t /stats -n 1`) doesn't matter as long as everything is measured in sim time.

## Torque test (isolating friction)
1. Make a copy of `/opt/ros/jazzy/opt/gz_sim_vendor/share/gz/gz-sim8/worlds/empty.sdf` and add `<plugin filename="gz-sim-apply-link-wrench-system" name="gz::sim::systems::ApplyLinkWrench"/>` before the other plugins.
2. Launch with that world. A temporary copy of `gazebo.launch.py` with a different `gz_args` path is enough; don't edit the repo launch file just for this.
3. Apply and clear a torque, then read the yaw:
   ```bash
   gz topic -t /world/empty/wrench/persistent -m gz.msgs.EntityWrench -p 'entity: {name: "eternal_bot::base_link", type: LINK}, wrench: {torque: {z: 5}}'
   sleep 2; gz model -m eternal_bot -p | tail -1
   gz topic -t /world/empty/wrench/clear -m gz.msgs.Entity -p 'name: "eternal_bot::base_link", type: LINK'
   ```
4. Compare with the expected breakaway torque, roughly μ·m·g·0.28 m. If the body resists far more than that, the link μ is being ignored (usually mesh collisions).
