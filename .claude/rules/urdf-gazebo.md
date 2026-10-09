---
paths:
  - "**/urdf/**"
  - "**/*.xacro"
  - "**/*.gazebo"
---
# URDF and Gazebo model rules

## Collisions
- **Never use STL meshes for collisions that need tuned friction.** With mesh contacts, Gazebo ignores the link's `mu1`/`mu2` and uses the ground's μ=1.0. This was proven with a torque test; see `documentation/03-skid-steer-errors.md` §1.
- Use primitives instead. Wheels are **spheres** r=0.05 in an **unrotated** frame (`rpy="0 0 0"`), offset 0.025 outboard along y.
- Base and lidar may stay as meshes, since they don't touch the ground.
- Don't use `self_collide`. The wheel inner faces touch the base sides at y=±0.14.

## Mecanum roller emulation (sim only)
- Each wheel uses `mu1=1.0`, `mu2=0.0` and a ±45° `fdir1`: grip along the roller axis, free slip across it.
  - FL and RR: `1 -1 0`
  - FR and RL: `1 1 0`
- Swapping the patterns inverts or mixes up strafing. After touching them, re-check forward, strafe and spin speeds in sim time.
- `fdir1` is expressed in the collision frame and spins with the wheel. URDF can't change that, and the converter drops `gz:expressed_in`.
  - So `gazebo.launch.py` adds `gz:expressed_in="base_link"` to **every** `<fdir1>` after `gz sdf -p`.
  - Any new `<fdir1>`, e.g. on a caster, gets pinned to `base_link` as well.
- Rotating the wheel collision frame changes what `fdir1` means. Spheres need no rotation, so keep them unrotated.

## Keep these in sync
- The MecanumDrive `<wheel_separation>` 0.33, `<wheelbase>` 0.44 and `<wheel_radius>` 0.05 must match the joints and collisions.
- Track is measured between wheel **centres**, not joint origins.
- If you change one, change all of them. Prefer moving them into xacro properties.

## Validating a change
Check the friction blocks survived conversion:
```bash
xacro src/eternal_bot_description/urdf/eternal_bot.xacro > /tmp/eb.urdf && gz sdf -p /tmp/eb.urdf | grep -A8 "<friction>"
```
Then confirm behaviour by driving forward, strafe and spin and measuring in sim time.

## If you go back to skid-steer / diff-drive
- With a wheelbase (0.44) longer than the track (0.33) and equal friction both ways, the body cannot yaw.
- Use cylinder wheels with `fdir1` along the axle, and lateral μ below 0.75 × rolling μ.
- See `documentation/03-skid-steer-errors.md` §2.
