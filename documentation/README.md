# eternal_bot documentation

Debugging history and design notes for the eternal_bot Gazebo simulation. **Read the relevant chapter before changing physics or the drive.**

| # | Chapter | Status | Summary |
|---|---|---|---|
| 1 | [Setup and workflow](01-setup-and-workflow.md) | current | Stack, and the Fusion 360 → URDF → Gazebo pipeline |
| 2 | [Diagnosing the problem](02-diagnosing-the-problem.md) | historical | Symptoms, method, and the variant table |
| 3 | [Skid-steer errors](03-skid-steer-errors.md) | historical | The seven errors found and why they mattered |
| 4 | [What the hand edits got right](04-what-the-hand-edits-got-right.md) | current | Inertia and wheel-axis checks |
| 5 | [Skid-steer results](05-skid-steer-results.md) | historical | Final sim-time measurements |
| 6 | [Mecanum (holonomic) switch](06-mecanum-holonomic-switch.md) | current | Gazebo MecanumDrive plugin and friction-emulated rollers |
| 7 | [Driving and workflow tips](07-driving-and-workflow-tips.md) | current | How to drive the bot, and lessons for CAD → sim |
| 8 | [2D lidar](08-lidar.md) | current | gpu_lidar on lidar_1, /scan bridge, mount height and the hand edits to the URDF |
| 9 | [SLAM and localization](09-slam.md) | current | slam_toolbox mapping, saved maps, and how to localize on an existing map (reference) |
| 10 | [Nav2](10-nav2.md) | current | Nav2 on slam_toolbox localization, Omni MPPI, the cmd_vel chain through twist_mux, and params changed from stock |
| 11 | [Raspberry Pi](11-raspberry-pi.md) | current | Ubuntu 24.04 + Jazzy on a Pi 5 over direct ethernet, laptop sims while the Pi runs SLAM + Nav2, and the setup problems hit along the way |

Chapters 2, 3 and 5 describe the earlier skid-steer / `diff_drive_controller` setup. It was superseded by the mecanum setup in chapter 6, but the physics lessons (collision geometry, anisotropic friction, sim time) still apply.

## Arena worlds and `gazebo_min`
- `worlds/arena.world` and `worlds/arena_obs.world` (arena + 4 cylinders) load `worlds/meshes/arena.dae` through a relative URI, so they resolve next to the installed world file. `setup.py` installs `worlds/*.world` and `worlds/meshes/*`.
- Both worlds were edited from the originals: the `ogre2` Sensors plugin is removed (the robot model loads Sensors, with the engine from `render_engine`), and `arena_obs`'s absolute `file:///home/team89/...` mesh path is now relative.
- `gazebo.launch.py` takes `world:=arena` (default), `arena_obs` or `empty`; `--render-engine` follows the `render_engine` launch argument (`ogre2` default, `ogre` for VMs) in every case.
- `gazebo_min.launch.py` is the original pipeline with `empty.sdf` only.
- The arena worlds are named `default`, so ground truth is on `/world/default/dynamic_pose/info` (not `/world/empty/...`). Bridge topics are world-independent.
