..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_newton_actuators_tips:

==================================================
Tips
==================================================

A short collection of practical tips for getting stable, realistic behavior
out of externally-driven Newton actuators.

Add armature for stability and realism
==================================================

Externally-driven joints can excite high-frequency dynamics that the
implicit USD drive normally damps for you.  The simplest fix — and one
that also makes the simulation more physically realistic — is to add a
small **armature** (virtual rotor inertia) to every actuated DOF via
:meth:`~isaacsim.core.experimental.prims.Articulation.set_dof_armatures`.

For a typical DC motor driving a joint through a gearbox, the effective
armature seen at the joint is:

.. math::

   I_\text{armature} \;=\; I_\text{rotor} \cdot N^2

where :math:`I_\text{rotor}` is the motor's rotor inertia and :math:`N`
is the gear ratio.  Real actuators with very high gear ratios contribute
*significant* armature at the joint — often dominating all other inertias
of the robot — so a non-zero armature is closer to physical
reality regardless of stability concerns.

Increase the physics rate for high-gain actuators
==================================================

If your controller gains are very high (stiff PD, aggressive PID, neural
policies that produce large efforts), the physics integrator may
be coarse at the default 60 Hz timestep. Raising the physics
rate will make the integration for accurate. Real actuators often
run in the range of 1-10 kHz to achieve very low tracking errors while
maintaining stability. Such high rates are not are not currently recommended
in |isaac-sim_short|, but increasing the physics rate can still significantly
increase accuracy when very low tracking error is desired.

.. code-block:: python

   from isaacsim.core.simulation_manager import SimulationManager

   SimulationManager.set_physics_dt(1.0 / 120.0)

The cost is proportionally more compute per simulated second.

Symptom: high-frequency vibration
==================================================

If your robot exhibits visible high-frequency oscillation —
typically faster than the natural frequency of the joints — it almost
always means one of the two tips above is being violated:

* The actuated joints are missing armature (or have far less than the
  real hardware would carry through its gearbox).
* The physics rate is too low for the gains you're using.

The fix is one (or both) of:

* Increase the armature on the affected DOFs (start by ~10× the value you
  have, or compute it from the rotor-inertia / gear-ratio formula above).
* Increase the physics rate (e.g. from 60 Hz to 120 or 200 Hz).
