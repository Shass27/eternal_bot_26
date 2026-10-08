# 3. Skid-steer errors and why they mattered

> **Historical:** these errors were found on the skid-steer / `diff_drive_controller` setup, before the switch to mecanum ([chapter 6](06-mecanum-holonomic-switch.md)). §1, §2 and §6 still apply to the current sim. Other files cite these section numbers, so keep them.

> **Concept**
> - **Collision geometry** is the shape the physics engine uses for contact. It can differ from the visual mesh, and primitives (cylinder, sphere, box) are faster and more reliable than meshes.
> - **Friction coefficient μ** is the ratio of the maximum friction force to the normal force (the force pressing two surfaces together).
> - **Friction pyramid vs cone:** real friction is a circular cone. Gazebo/DART limits friction separately along two perpendicular directions (a pyramid), so the two directions matter.
> - **Anisotropic friction** means different μ in different directions. `fdir1` picks the first direction, `mu1` is the friction along it and `mu2` the friction across it.
> - **Skid-steer** robots have no steering. They turn by driving the left and right sides at different speeds, so the wheels have to scrub sideways across the ground.

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
- **Fix:** added a small node, `twist_to_stamped`, that forwards `/cmd_vel` (Twist) to `/diff_drive_controller/cmd_vel` (TwistStamped). The launch file starts it. (Removed later with the mecanum switch.)

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
