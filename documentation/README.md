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

Chapters 2, 3 and 5 describe the earlier skid-steer / `diff_drive_controller` setup. It was superseded by the mecanum setup in chapter 6, but the physics lessons (collision geometry, anisotropic friction, sim time) still apply.
