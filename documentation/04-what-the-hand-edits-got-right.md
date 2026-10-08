# 4. What the hand edits got right

> **Concept**
> - **Inertia** is a body's resistance to rotational acceleration. Wrong inertia makes a sim robot feel too floppy or too stiff.
> - **Box:** I = m(a² + b²)/12 about each axis, where a and b are the two other side lengths.
> - **Solid cylinder about its axle:** I = ½ m r².
> - **Joint axis:** the direction a wheel joint spins about. By the right-hand rule, a positive spin about +y moves the bottom contact point backward, which pushes the robot forward (+x).

- **Base inertia:** for a 14 kg box of 0.58 × 0.28 × 0.0512 m, the box formula I = m(a² + b²)/12 gives ixx 0.0945, iyy 0.3955, izz 0.4839. These match.
- **Wheel inertia:** iyy = ½ m r² = ½ · 0.4 · 0.05² = 0.0005 (a solid cylinder about its axle). Correct.
- **Wheel axis +y on all four joints:** a positive spin about +y moves the contact point backward, which pushes the robot forward (+x). Correct for both sides.
