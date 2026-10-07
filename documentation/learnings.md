# Learnings: getting eternal_bot to drive in Gazebo

**Setup:** ROS 2 Jazzy, Gazebo Harmonic (gz-sim 8, DART physics engine), `gz_ros2_control`, `diff_drive_controller`.
**Workflow:** model in Fusion 360 → export to URDF with the fusion2urdf add-on → hand-edit the URDF (inertia, wheel axes) → simulate.

## Symptoms

- The robot drove forward and backward, but **did not rotate at all** when given an angular command.
- Forward speed **looked inconsistent**.

The CAD model looked fine, and the hand edits to inertia (resistance of a body to rotational acceleration, the rotational equivalent of mass) and wheel axes were correct. The problems all came from things a CAD model never exercises: **ground contact physics** and **controller configuration**.

---

## How it was diagnosed

1. Launched `gazebo.launch.py`, checked that `joint_state_broadcaster` and `diff_drive_controller` were active, and that `/diff_drive_controller/cmd_vel` has type `geometry_msgs/msg/TwistStamped`.
2. Published commands at 20 Hz and measured the robot's **true pose from Gazebo** (`/world/empty/dynamic_pose/info`) against **simulation time** (the clock inside the simulator, which can run slower or faster than the wall clock).
3. Applied a pure torque (twisting force, in N·m) to `base_link` using Gazebo's `ApplyLinkWrench` system, to see how hard it was to rotate the body at all.
4. Swapped one thing at a time (self-collision off, cylinder collisions, friction values, physics engine, ground friction) and re-measured.

| Variant | Straight (cmd 0.3 m/s) | Spin (cmd 1.0 rad/s) |
|---|---|---|
| Original repo | 0.300 m/s | **0.000 rad/s** |
| `self_collide` removed | 0.300 | 0.000 |
| Bullet physics instead of DART | 0.300 | 0.000 |
| Wheel μ 0.02 (STL mesh collision) | 0.300 | 0.000 |
| Cylinder wheels + anisotropic friction + separation 0.33 | 0.300 | **1.01 / −1.00** |

---

## Errors found and why they mattered

### 1. Wheel collision was the exported STL mesh, so wheel friction was ignored

The exporter copies the visual mesh into `<collision>` (the geometry the physics engine uses for contact). With mesh collisions, Gazebo ignored the wheel's `mu1`/`mu2` (friction coefficients: the ratio of the maximum friction force to the normal force (the force pressing two surfaces together)) and effectively used the ground plane's default μ = 1.0.

- **Evidence:** with wheel μ set to 0.2 or 0.02, a 20 N·m torque still could not rotate the robot. With the same μ = 0.02 on **cylinder** collisions, 2 N·m spun it freely. On a low-friction ground (μ 0.05), 5 N·m spun it even with mesh wheels.
- **Fix:** replace each wheel's collision with a primitive `<cylinder radius="0.05" length="0.05"/>`. The STL is still used for visuals.

### 2. Skid-steer geometry locks rotation when friction is the same in every direction

This is a 4-wheel **skid-steer** robot (no steering; it turns by driving the left and right sides at different speeds, so the wheels must **scrub**, i.e. slide sideways, across the ground).

- Wheelbase (front-to-rear wheel distance) = 0.44 m, track (left-to-right wheel distance) = 0.33 m.
- Gazebo/DART uses a **friction pyramid** (friction limited separately along two perpendicular directions, instead of a true circular **Coulomb friction cone**).
- **Turning moment** (torque about the robot's vertical axis) the wheels can produce ≈ 4 · μ_rolling · N · (track/2) = 4 · μ · N · 0.165.
- **Resisting moment** from sideways friction ≈ 4 · μ_lateral · N · (wheelbase/2) = 4 · μ · N · 0.22.
- With μ_rolling = μ_lateral, resistance (0.22) > drive (0.165), so the body **can never yaw** (rotate about the vertical axis), however fast the wheels spin. They just slip in place, and any small imbalance shows up as a slow forward/backward drift.
- **Fix:** **anisotropic friction** (different friction in different directions):
  - `fdir1` = `0 0 1`: the first friction direction, set along the wheel axle. It is the cylinder's local z axis, because the cylinder is rotated 90° about x.
  - `mu1 = 0.3` (lateral/sideways), `mu2 = 1.0` (rolling direction).
  - Rule of thumb: μ_lateral < (track / wheelbase) · μ_rolling = 0.75 · μ_rolling, with margin.
- **Real-world note:** the physical robot has the same geometry, so it will also need a lot of torque and tyre scrub to turn. Real tyres follow a friction cone and deform, so it won't lock completely, but turning will be harsh.

### 3. `wheel_separation` was measured to the joint origins, not the tread centres

- The joint origins are at y = ±0.14 on the inner face of each wheel. The wheel mesh spans y = 0.14 → 0.19, so the tread centre (where the tyre touches the ground) is at ±0.165.
- Correct `wheel_separation` = 0.33 (it was 0.28). With the wrong value, the controller computes the wrong left/right speed difference for a given angular velocity, so turns come out the wrong size and **odometry** (pose estimated by integrating wheel rotation) drifts.

### 4. Jazzy's `diff_drive_controller` only accepts `TwistStamped`

- In Jazzy, `~/cmd_vel` is always `geometry_msgs/msg/TwistStamped`. The `use_stamped_vel: false` parameter no longer exists and does nothing.
- Tools like `teleop_twist_keyboard` publish plain `Twist` on `/cmd_vel` by default, so those commands never reach the controller.
- **Fix:** added a small node, `twist_to_stamped`, that forwards `/cmd_vel` (Twist) to `/diff_drive_controller/cmd_vel` (TwistStamped). The launch file starts it.

### 5. `cmd_vel_timeout` stops the robot after 0.5 s

- If no command arrives for `cmd_vel_timeout` seconds, the controller commands zero velocity (a safety feature).
- A single `ros2 topic pub --once` therefore moves the robot for only about 0.5 s. Publish continuously (`-r 10`) instead.

### 6. "Inconsistent speed" was a timing illusion

- Measured in **simulation time**, the speed was exactly 0.300 m/s.
- Measured by wall clock it looked like ~0.2 m/s and varied, because the VM ran the simulation slower than real time. The **real-time factor** (RTF: simulated seconds per real second) dropped below 1 under load.
- **Lesson:** measure speeds against sim time (`/clock`, or message header stamps), and check RTF in `/stats`.

### 7. Exporter leftovers

- `self_collide: true` was set on every link (whether links of the same robot can collide with each other). The wheels touch the chassis at y = ±0.14, so this risks phantom contacts. Removed.
- The placeholder `mu 0.2` everywhere was not a real material value.
- `setup.cfg` still installed scripts to `lib/fusion2urdf_ros2`, so `ros2 run`/launch could not find this package's executables. Fixed to `lib/eternal_bot_description`.
- `robot_state_publisher` wasn't using sim time. Added `use_sim_time: true`.

---

## What the hand edits got right

- **Base inertia:** for a 14 kg box of 0.58 × 0.28 × 0.0512 m, the box formula I = m(a² + b²)/12 gives ixx 0.0945, iyy 0.3955, izz 0.4839. These match.
- **Wheel inertia:** iyy = ½ m r² = ½ · 0.4 · 0.05² = 0.0005 (a solid cylinder about its axle). Correct.
- **Wheel axis +y on all four joints:** a positive spin about +y moves the contact point backward, which pushes the robot forward (+x). Correct for both sides.

---

## Final results (sim time)

| Command | Measured |
|---|---|
| straight +0.3 / −0.3 m/s | 0.300 m/s |
| spin +1.0 rad/s | 1.010 rad/s |
| spin −1.0 rad/s | −0.998 rad/s |
| arc 0.3 m/s + 0.5 rad/s via `/cmd_vel` (Twist) | 0.290 m/s, 0.500 rad/s |

---

## Workflow suggestions (Fusion 360 → URDF → Gazebo)

1. **Treat the exporter output as generated; never hand-edit it.** Keep the overrides (collisions, inertia fixes, `<gazebo>` friction, ros2_control) in a separate wrapper xacro that includes the export. Re-exporting from Fusion then won't wipe the fixes.
2. **Define dimensions once.** Use xacro properties (`wheel_radius`, `wheel_width`, `track`, `wheelbase`) for the joint origins, collision primitives **and** the controller parameters, so `wheel_separation` can't drift from the geometry.
3. **Use primitive collisions** (cylinders for wheels, a box for the chassis) and keep the STLs for visuals. They're faster and give stable, friction-correct contacts.
4. **Check the generated model before launching.** Run `check_urdf` and `gz sdf -p <urdf>`, and confirm that the friction, `fdir1` and collision blocks are what you expect.
5. **Run a 30-second motion test after every export or edit.** Drive straight, spin and arc, and read the true pose in sim time from `/world/<world>/dynamic_pose/info`.
6. **Design for the drive type.** For skid-steer, a track ≥ wheelbase makes turning much easier, both in simulation and on the real robot.

## Driving the robot

```bash
ros2 launch eternal_bot_description gazebo.launch.py
ros2 run teleop_twist_keyboard teleop_twist_keyboard          # plain Twist on /cmd_vel, relayed
# or directly (publish continuously, not --once):
ros2 topic pub -r 10 /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped "{twist: {angular: {z: 1.0}}}"
```
