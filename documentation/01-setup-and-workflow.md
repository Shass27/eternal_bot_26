# 1. Setup and workflow

> **Concept**
> - **URDF** is ROS's robot description format (links, joints, inertia, collisions). **SDF** is Gazebo's native format. Gazebo converts URDF to SDF when it loads a model, and some Gazebo-only features can't be written in URDF.
> - **fusion2urdf** is a Fusion 360 add-on that exports a CAD model as URDF. It copies geometry and mass data, but it knows nothing about contact physics (friction, collision shapes) or controllers.
> - A CAD model that looks right can still behave wrongly in simulation, because the CAD never exercises ground contact.

**Setup (current):** ROS 2 Jazzy, Gazebo Harmonic (gz-sim 8, DART physics engine), `ros_gz_bridge`, and the gz MecanumDrive plugin.
**Setup (original, historical):** `gz_ros2_control` + `diff_drive_controller`. See [chapter 6](06-mecanum-holonomic-switch.md) for the switch.

**Workflow:** model in Fusion 360 → export to URDF with the fusion2urdf add-on → hand-edit the URDF (inertia, wheel axes, collisions, friction) → simulate.
