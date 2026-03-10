..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_motion_generation_rmpflow_tuning_guide:

RMPflow Tuning Guide
====================

.. note::
   For new development, consider using the newer :doc:`cuMotion Integration <../../cumotion/index>`, which provides improved interfaces and additional features over Lula. This
   page is still a valid tuning guide for RMPflow in |cumotion|.

Given the number of parameters involved in fully specifying a complete set of RMPs,
tuning an RMPflow-based motion policy for a new robot or task can be intimidating.
In practice, however, parameters that work well for one robot are likely to work well
for other robots with similar morphology.  Furthermore, for a given robot, it is
generally possible to choose a set of parameters that work well for a wide variety
of tasks.

To review RMPflow and its features see, :doc:`RMPflow <rmpflow>`.

|isaac-sim| includes example RMPflow configuration files for multiple robot arms, including
the 7-DOF Franka Emika Panda and the 6-DOF Universal Robots UR10.  When tuning RMPflow for a
new manipulator, it's usually best to start with one of these two files.  If the new robot
is significantly larger or smaller than the one used as a reference, it might be necessary
to rescale any parameters that have units of length.  If the number of joints differ, the
`c-space_target_rmp/robust_position_term_thresh` parameter might also have to be adjusted.
Often, these steps are sufficient to produce a working motion policy.

If adapting an existing RMPflow configuration fails to produce acceptable results, use
the following procedure to tune a new policy from scratch:

.. hint::

  It can helpful to play with parameter values for an existing robot (for example, the Franka).

1. Turn off all RMPs.  

2. Each RMP has a parameter called either `metric_weight` or `metric_scalar`. Setting this parameter to zero will disable the corresponding RMP. For the target RMP, set the parameters `min_metric_scalar`, `max_metric_scalar`, and `min_metric_alpha` all to zero.

3. Set all inertia terms to zero (that is, `c-space_target_rmp/inertia` and `damping_rmp/inertia`).

4. Re-enable RMPs one at a time, in the following suggested order:

   1. **c-space_target_rmp:** To get the robot moving to a configuration in c-space robustly.
      The magnitude of the metric scalar should be kept relatively small (for example, in the range 1 to 100), because
      this sets the global scale of all RMPs.
      Remember to set the default configuration in the robot description file (YAML) to a reasonable natural
      “ready” posture. This will be the default posture that the robot will favor while moving from place to place.
   2. **target_rmp:** To get the end effector moving to a target robustly while continuing
      to use the c-space target RMP for redundancy resolution.

      a. Set `target_rmp/min_metric_alpha` to zero and `target_rmp/metric_alpha_length_scale`
         to a large value relative to the size of the robot (in meters), such as 100,000.  This effectively turns
         off the directional :math:`S` term in the metric, reducing :math:`M` to a simpler isotropic metric.
      b. Set `target_rmp/proximity_metric_boost_length_scalar` to 1 to turn off priority boosting.
      c. Set `target_rmp/max_metric_scalar` to a large value relative to `c-space_target_rmp/metric_scalar`
         so it dominates.  This will effectively make the c-space target RMP operate purely in the
         nullspace of the target RMP.
      d. Tune `target_rmp/accel_p_gain`, `target_rmp/accel_d_gain`, and `target_rmp/accel_norm_eps` until
         good attractor behavior for the end effector has been achieved.
      e. Experiment with reducing `target_rmp/max_metric_scalar` to ensure that it's not too large.  As
         `max_metric_scalar` is increased toward a suitable value, convergence accuracy should progressively
         improve.  If convergence accuracy saturates at small constant error before the chosen `max_metric_scalar`
         value is reached, then it is probably set too high.  This will be relevant when re-enabling the directional
         term in the target RMP metric below, ensuring that it makes a difference when the metric scalar decreases.

   3. **collision_rmp:** Enable the collision avoidance RMP by setting `collision_rmp/metric_scalar` to a value
      comparable to `target_rmp/max_metric_scalar`.  It can be useful to plot the formulas for the acceleration
      and metric to gain some understanding of the roles of the various parameters.
   4. **target_rmp (redux):** After the collision RMP is enabled, the system will probably drag near obstacles
      more slowly than it usually moves because the target RMP is fighting with the collision RMPs.
      Turning on the directional term in the metric will correct that effect.

      a. Plot the target RMP metric (as a function of distance from target)
         to build understanding.  Try this first without the boosting term, noting how the metric transitions
         from the reduced-rank far metric to the full-rank near metric.
      b. Set `target_rmp/min_metric_alpha` to a non-zero value and reduce the value of
         `target_rmp/metric_alpha_length_scale` until good behavior is achieved.

   5. **axis_target_rmp:** If an orientation target is set, the axis target RMP will be used to bring
      the orientation of the control frame (for example, end effector) into alignment with the target orientation.
      This RMP includes a "priority boosting" factor that depends on distance to the current
      position target, if one is set.  This allows the robot to make progress toward the position
      target before zeroing in on the desired orientation.
   6. **joint_limit_rmp:** When properly tuned, behavior should be unchanged, except that joint
      limits will be avoided.
   7. **damping_rmp:** Enable the damping RMP as well as `target_rmp/inertia` to reduce jerk as necessary.

Throughout this process, referring to an existing RMPflow configuration file is helpful.


