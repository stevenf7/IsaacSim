..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_motion_generation_rmpflow:

RMPflow
=======

.. admonition:: Deprecated
   :class: warning

   For new development, consider using the newer :doc:`Robot Motion (Experimental) <../../robot_motion_experimental/index>` API, which provides improved interfaces and additional features over Lula.

:ref:`isaac_sim_glossary_rmp` is a set of motion generation tools that underlies most |isaac-sim_short| manipulator controls.
It creates smooth trajectories for the robots with intelligent collision avoidance.

A **Riemannian Motion Policy**, or *RMP*, is an acceleration policy
accompanied by a matrix :math:`M(q, \dot{q})` that is sometimes called an inertia matrix,
borrowing terminology from classical mechanics, but is also closely related to the concept
of a Riemannian metric.

Leveraging the machinery of Riemannian geometry, *RMPflow* is a
framework for combining RMPs representing multiple (possibly competing) objectives and
constraints into a single global acceleration policy.  Within this framework, the local RMPs
can be defined on any number of intermediate task spaces (including the operational space of
the end effector, generalizing operational space control).  For details, refer to
`*RMPflow: A computational graph for automatic motion policy generation* <https://arxiv.org/abs/1811.07049>`_.

Broadly defined, a *motion policy* is a mathematical function that takes the current
state of a robot (for example, position and velocity in generalized coordinates) and returns
a quantity representing a desired change in that state.  Such a policy can depend
implicitly on variables representing one or more objectives or constraints, the state of
the environment.  An *acceleration policy* is a motion policy where the output is
desired acceleration, :math:`\ddot q = \pi(q, \dot{q})`, resulting in a second-order
differential equation.

For the purpose of controlling a robot by position or velocity control, typically motion policies are used
where the output is position or velocity.  Such
policies can be produced from an acceleration policy using a numerical
integration scheme such as Euler integration.

The :ref:`isaac_sim_motion_generation_rmpflow_debugging_features` section reviews functions belonging to RMPflow that are not part of the `MotionPolicy` interface.
You can interact with RMPflow to control a robot that is already supported. If you are interested in the internal
mechanics of RMPflow or want to configure RMPflow for an unsupported robot, continue reading the RMPflow documentation.

After reviewing the basics here, also see the :doc:`RMPflow Tuning Guide <rmpflow_tuning_guide>` for practical advice on configuring RMPflow for a new robot.

.. _isaac_sim_motion_generation_rmpflow_debugging_features:

RMPflow Debugging Features
^^^^^^^^^^^^^^^^^^^^^^^^^^
By directly interacting with an `RmpFlow` instance, you can access features that are not available in other `MotionPolicy` implementations.
It is common for developers to want to decouple a :ref:`isaac_sim_motion_policy` from the simulated robot `Articulation` in |isaac-sim|.
For example, when the simulated robot is moving sluggishly, it is important to determine whether the `MotionPolicy` or the PD gains have been improperly tuned,
but this can be difficult when both the PD gains and the `MotionPolicy` play a role in driving the robot joints  (see :ref:`isaac_sim_motion_policy_joint_targets`).

RMPflow provides visualization functions to clearly show the internal state of the algorithm as part of the stage.  RMPflow uses collision spheres internally to
avoid hitting obstacles in the world.  These spheres can be visualized over time by calling ``RmpFlow.visualize_collision_spheres()``.  The visualization will stop when
``RmpFlow.stop_visualizing_collision_spheres()`` is called.  The nominal end effector position can likewise be visualized with
``RmpFlow.visualize_end_effector_position()`` and ``RmpFlow.stop_visualizing_end_effector()``.

On their own, the visualization functions can be used to make sure that RMPflow's internal representation of the robot is reasonable, but it does not help to decouple the
simulated robot from the `RmpFlow` internal representation of the robot.  

On each frame when ``RmpFlow.compute_joint_targets(active_joint_positions,...)`` is called,
the visualization is updated to use the ``active_joint_positions``.  This behavior can be turned off using ``RmpFlow.set_ignore_state_updates(True)``.  When `RmpFlow`
is "ignoring state updates", it starts ignoring the ``active_joint_positions`` argument, and instead begins internally tracking the believed state of the robot by assuming
that is completely independent of the physical simulation of the robot.  When `RmpFlow` is set to ignore state updates from the simulator, and the visualization functions are used,
it becomes simple to determine if an undesirable robot behavior
comes from `RmpFlow` or from the robot `Articulation` and its PD gains.

.. _isaac_sim_motion_generation_rmpflow_configuration:

RMPflow Configuration
^^^^^^^^^^^^^^^^^^^^^^

Three files are necessary to configure RMPflow for use with a new robot:

  * A **URDF** (universal robot description file), used for specifying robot kinematics
     as well as joint and link names.  Position limits for each joint are also required.
     Other properties in the URDF are ignored and can be omitted; these include masses,
     moments of inertia, visual, and collision meshes.
  * A **supplementary robot description file** in YAML format.  In addition to enumerating
     the list of actuated joints that define the configuration space (c-space) for the robot,
     this file includes sections for specifying the default c-space configuration
     and sets of collision spheres used for collision avoidance.  This file can also
     be used to specify fixed positions for unactuated joints.
  * A **RMPflow configuration file** in YAML format, containing parameters for all enabled RMPs.

As a general mathematical framework, RMPflow does not prescribe the form that individual RMPs
must take.  The particular implementation of RMPflow in Lula (and by extension |isaac-sim|) does
however expose a pre-specified set of RMPs that have been constructed and empirically found
to produce smooth reactive behaviors for a variety of manipulation tasks.  




C-Space Target RMP (`c-space_target_rmp`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** Specifies a default c-space configuration for the robot, used for redundancy resolution.

**Definition:** Acceleration for this RMP is given by an equation similar to a PD controller, with a
position gain and damping gain, but the magnitude of the position term is capped when the C-space
distance exceeds a threshold.  This cap avoids excessive forces when the configuration is far away
from the target.  Defining :math:`q` to be the full configuration vector:

.. math::

   \ddot q = k_p r(q_0 - q) - k_d \dot q\,,

where the "robust capping function" :math:`r(p)` is given by:

.. math::

   r(p) = \left \{ \begin{array}{cl}
   p, & ||p|| < \theta \\
   \theta\, p / ||p|| & \textrm{otherwise.}
   \end{array} \right.

The inertia matrix is proportional to the identity:

.. math::

   M = \mu I

The `c-space_target_rmp` section of the RMPflow configuration file contains an additional
`inertia` parameter :math:`m`.  When this parameter is nonzero, it results in the introduction of
a conceptually separate RMP corresponding to zero c-space acceleration, :math:`\ddot q = 0`, with inertia
matrix given by :math:`M = mI`.

**Parameters:**

Units assume revolute joints where :math:`q` is expressed in radians.  If joints are instead prismatic,
`robust_position_term_thresh` will have units of meters.

=============================  ==============  ============  =======
Name                           Symbol           Units         Meaning
=============================  ==============  ============  =======
`metric_scalar`                :math:`\mu`     \-            Priority weight relative to other RMPs
`position_gain`                :math:`k_p`     s\ :sup:`-2`  Position gain, determining how strongly configuration is pulled toward target
`damping_gain`                 :math:`k_d`     s\ :sup:`-1`  Damping gain, determining amount of "drag"
`robust_position_term_thresh`  :math:`\theta`  rad           Distance in c-space at which the position correction vector is capped
`inertia`                      :math:`m`       \-            Additional c-space inertia
=============================  ==============  ============  =======


Target RMP (`target_rmp`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** Drives end effector toward specified position target.

**Definition:** Similar to the c-space target RMP, acceleration for this RMP resembles a PD
controller, albeit with a slightly different strategy for capping the magnitude of the position
correction vector.

.. math::
   \ddot x = k_p (x_0 - x) / (||x_0-x|| + \epsilon) - k_d \dot x

The inertia matrix blends between a rank-deficient metric :math:`S = n n^T``, where :math:`n` is
the direction vector toward the target, and the identity :math:`I`.  

Intuitively, :math:`S` cares
only about the direction toward the target (letting other RMPs such as the obstacle avoidance RMP
control the orthogonal directions).

:math:`I` cares about all directions.  

The contribution of
:math:`S` is larger farther from the goal, allowing obstacles to push the system more effectively,
while :math:`I` dominates near the goal, encouraging faster convergence.  

Blending is
controlled by a radial basis function, specifically a Gaussian, that transitions from a minimum
constant value far from the target to 1 near the target.

Near the target, an additional nonlinear “proximity boost” multiplier turns on.  This
factor takes the form of a Gaussian:

.. math::
   M = \left[\beta(x) b + (1-\beta(x))\right] \left[\alpha(x) M_\textrm{near} + (1-\alpha(x)) M_\textrm{far} \right]

where

.. math::
   \begin{array}{l}
   \alpha(x) = (1-\alpha_\textrm{min})\exp \left(\frac{-||x_0-x||^2}{2 \sigma_a^2}\right) + \alpha_\textrm{min} \\
   \beta(x) = \exp \left(-\frac{||x_0 - x||^2}{2 \sigma_b^2}\right) \\
   M_\textrm{near} = \mu_\textrm{near} I \\
   M_\textrm{far} = \mu_\textrm{far} S = \frac{\mu_\textrm{far}}{||x_0-x||^2} (x_0-x)(x_0-x)^T\,.
   \end{array}

**Parameters:**

=====================================  ===========================  =============  =======
Name                                   Symbol                       Units          Meaning
=====================================  ===========================  =============  =======
`accel_p_gain`                         :math:`k_p`                  m/s\ :sup:`2`  Position gain
`accel_d_gain`                         :math:`k_d`                  s\ :sup:`-1`   Damping gain
`accel_norm_eps`                       :math:`\epsilon`             m              Length scale controlling transition between constant acceleration region far from target and linear region near target
`metric_alpha_length_scale`            :math:`\sigma_a`             m              Length scale of the Gaussian controlling blending between :math:`S` and :math:`I`
`min_metric_alpha`                     :math:`\alpha_\textrm{min}`  \-             Controls the minimum contribution of the isotropic :math:`M_\textrm{near}` term to the metric (inertia matrix)
`max_metric_scalar`                    :math:`\mu_\textrm{near}`    \-             Metric scalar for the isotropic :math:`M_\textrm{near}` contribution to the metric (inertia matrix)
`min_metric_scalar`                    :math:`\mu_\textrm{far}`     \-             Metric scalar for the directional :math:`M_\textrm{far}` contribution to the metric (inertia matrix)
`proximity_metric_boost_scalar`        :math:`b`                    \-             Scale factor controlling the strength of boosting near the target
`proximity_metric_boost_length_scale`  :math:`\sigma_b`             m              Length scale of the Gaussian controlling boosting near the target
`xi_estimator_gate_std_dev`            \-                           \-             Unused parameter (to be removed in a future release)
=====================================  ===========================  =============  =======


Axis Target RMP (`axis_target_rmp`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** Drives x-, y-, or z-axis of end effector frame toward target orientation.  This
RMP is used for general orientation targets (where an axis target RMP is added for each of the
three axes) as well as for "partial pose" targets where only alignment of a single axis is
desired.

.. note::
  Partial pose targets are not supported by the Motion Generation extension.

**Definition:**

Similar to the (position) target RMP, the axis target RMP supports "proximity boosting,"
but only when a target RMP is active at the same time.  In this case, it's the distance to
the position target (:math:`||x_0-x||`) that controls the strength of boosting.

The current and desired axis orientations are represented by unit vectors, denoted
by :math:`n` and :math:`n_0` respectively.  Acceleration is given by:

.. math::
   \ddot n = k_p (n_0 - n) - k_d \dot n\,

If a position target (that is, target RMP) is active, the metric has the form:

.. math::
   M_\textrm{boosted} = \left[\beta(x) b + (1-\beta(x))\right] \mu I\,

where:

.. math::
   \beta(x) = \exp \left(-\frac{||x_0 - x||^2}{2 \sigma_b^2}\right)\,

When no position target is active, this simplifies to:

.. math::
   M = \mu I\,.

**Parameters:**

=====================================  ===========================  ============  =======
Name                                   Symbol                       Units         Meaning
=====================================  ===========================  ============  =======
`accel_p_gain`                         :math:`k_p`                  s\ :sup:`-2`  Position gain
`accel_d_gain`                         :math:`k_d`                  s\ :sup:`-1`  Damping gain
`metric_scalar`                        :math:`\mu`                  \-            Priority weight relative to other RMPs
`proximity_metric_boost_scalar`        :math:`b`                    \-            Scale factor controlling the strength of boosting near the position target
`proximity_metric_boost_length_scale`  :math:`\sigma_b`             m             Length scale of the Gaussian controlling boosting near the position target
=====================================  ===========================  ============  =======


Joint Limit RMP (`joint_limit_rmp`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** Avoids joint limits.

**Definition:** This is a one-dimensional RMP that depends on a single
c-space coordinate (joint) and a corresponding upper or lower joint limit as specified in
the URDF for the robot.  If a robot has :math:`N` joints, it follows that a total of :math:`2N`
joint limit RMPs will be introduced.  The joint limits specified in the URDF can be padded
(that is, made more conservative) by entering positive padding values in the `joint_limit_buffers`
array in the RMPflow configuration file.  For a given joint, the same padding value is used
for both upper and lower limits.

The task space for this RMP consists of a shifted and scaled c-space coordinate, measuring
the scaled distance to either the upper or lower joint limit.  Without loss of generality,
we consider a lower joint limit RMP.  If :math:`q` is the c-space coordinate for a given
joint, and :math:`q_\textrm{upper}` and :math:`q_\textrm{lower}` are the upper and lower
limits for that joint, respectively, we define:

.. math::
   x = \frac{q - q_\textrm{lower}}{q_\textrm{upper} - q_\textrm{lower}}\,

The acceleration for that coordinate is then given by:

.. math::
   \ddot x = \frac{k_p}{x^2/\ell_p^2 + \epsilon_p} - k_d \dot x\,

The metric (inertia matrix) is a scalar given by:

.. math::
   m = \left(1 - \frac{1}{1+\exp(-\dot x/v_m)}\right) \frac{\mu}{x/\ell_m + \epsilon_m}\,

**Parameters:**

=======================================  ==================  ============  =======
Name                                     Symbol              Units         Meaning
=======================================  ==================  ============  =======
`metric_scalar`                          :math:`\mu`         \-            Overall priority weight relative to other RMPs
`metric_length_scale`                    :math:`\ell_m`      \-            Length scale controlling ramp-up of metric as joint limit is approached
`metric_exploder_eps`                    :math:`\epsilon_m`  \-            Offset determining :math:`x` value at which metric diverges
`metric_velocity_gate_length_scale`      :math:`v_m`         s\ :sup:`-1`  Scale determining rate at which metric increases with velocity in direction of barrier
`accel_damper_gain`                      :math:`k_d`         s\ :sup:`-1`  Damping gain
`accel_potential_gain`                   :math:`k_p`         s\ :sup:`-2`  Gain multiplying position barrier term
`accel_potential_exploder_length_scale`  :math:`\ell_p`      \-            Length scale controlling steepness of position barrier
`accel_potential_exploder_eps`           :math:`\epsilon_p`  \-            Offset limiting divergence of position barrier strength
=======================================  ==================  ============  =======


Joint Velocity Limit RMP (`joint_velocity_cap_rmp`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** Limits maximum joint velocity.

**Definition:** This RMP applies damping when the magnitude of the velocity of a given joint
approaches the specified limit.

This is a one-dimensional RMP with acceleration given by:

.. math::
   \ddot q = -k_d\,\textrm{sgn}(\dot q) \left(|\dot q| - (v_\textrm{max} - v_r)\right)\,

The metric (inertia matrix) is a scalar given by:

.. math::
   m = \left \{ \begin{array}{cl}
   0, & |\dot q| < (v_\textrm{max} - v_r) \\
   \frac{\mu}{1 - \left(|\dot q| - (v_\textrm{max} - v_r)\right)^2 / v_r^2} & \textrm{otherwise.}
   \end{array} \right

The metric is zero outside you-specified damping region, thereby disabling this RMP.
In addition, clipping is applied to avoid divergence of the metric as :math:`\dot q` approaches :math:`v_\textrm{max}`.

**Parameters:**

Units assume revolute joints where :math:`q` is expressed in radians.  If joints are instead prismatic,
`max_velocity` and `velocity_damping_region` will have units of m/s.

=========================  ======================  ============  =======
Name                       Symbol                  Units         Meaning
=========================  ======================  ============  =======
`max_velocity`             :math:`v_\textrm{max}`  rad/s         Maximum allowed velocity magnitude
`velocity_damping_region`  :math:`v_r`             rad/s         Defines width of velocity region affect by damping
`damping_gain`             :math:`k_d`             s\ :sup:`-1`  Damping gain
`metric_weight`            :math:`\mu`             \-            Overall priority weight relative to other RMPs
=========================  ======================  ============  =======


Collision Avoidance RMP (`collision_rmp`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** Avoids collision with obstacles in the environment.

**Definition:** This is a one-dimensional RMP where the task space consists of a single
coordinate measuring distance from a given collision sphere on the robot (specified in the
robot description YAML file) to an obstacle in the environment.  Denoting that coordinate
as :math:`x`, the acceleration is given by:

.. math::
   \ddot x = k_p \exp(-x / \ell_p) - k_d \left[1 - \frac{1}{1 + \exp(-\dot x/v_d)} \right] \frac{\dot x}{x/\ell_d + \epsilon_d}\,

The metric (inertia matrix) is a scalar given by:

.. math::
   m = \left[1 - \frac{1}{1 + \exp(-\dot x/v_d)} \right] g(x) \frac{\mu}{x / \ell_m + \epsilon_m}\,

where :math:`g(x)` is a piecewise polynomial that varies smoothly from 1 to 0 as :math:`x` varies from 0 to :math:`r`

.. math::
   g(x) = \left \{ \begin{array}{cl}
   x^2/r^2 -2s/r + 1, & x\le r \\
   0, & x\gt r
   \end{array} \right.

**Parameters:**

====================================  ==================  =============  =======
Name                                  Symbol              Units          Meaning
====================================  ==================  =============  =======
`damping_gain`                        :math:`k_d`         s\ :sup:`-1`   Damping gain
`damping_std_dev`                     :math:`\ell_d`      m              Length scale controlling increase in acceleration as obstacle is approached
`damping_robustness_eps`              :math:`\epsilon_d`  \-             Offset determining :math:`x` value at which acceleration diverges (before clipping)
`damping_velocity_gate_length_scale`  :math:`v_d`         m/s            Scale determining velocity dependence of "velocity gating" function
`repulsion_gain`                      :math:`k_p`         m/s\ :sup:`2`  Gain for position repulsion term
`repulsion_std_dev`                   :math:`\ell_p`      m              Length scale controlling distance dependence of repulsion
`metric_modulation_radius`            :math:`r`           m              Length scale determining distance from obstacle at which RMP is disabled completely
`metric_scalar`                       :math:`\mu`         \-             Overall priority weight relative to other RMPs
`metric_exploder_std_dev`             :math:`\ell_m`      m              Length scale controlling increase in metric as obstacle is approached
`metric_exploder_eps`                 :math:`\epsilon_m`  \-             Offset determining :math:`x` value at which metric diverges (before clipping)
====================================  ==================  =============  =======


Damping RMP (`damping_rmp`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** Contributes additional nonlinear damping based on control frame
(for example, end effector) velocity relative to target.

**Definition:** This is a one-dimensional RMP where the task space consists of a single coordinate
:math:`x` measuring distance from the origin of the control frame to the target.
The acceleration is given by:

.. math::
   \ddot x = -k_d |\dot x|\dot x

and the metric by:

.. math::
   M = \mu |\dot x| I\,

The `damping_rmp` section of the RMPflow configuration file contains an additional
`inertia` parameter :math:`m`.  When this parameter is nonzero, it results in the introduction of
a conceptually separate RMP corresponding to zero acceleration, :math:`\ddot x = 0`, with inertia
matrix given by :math:`M = mI`.

**Parameters:**

===============  ===========  ================  =======
Name             Symbol       Units             Meaning
===============  ===========  ================  =======
`accel_d_gain`   :math:`k_d`  m\ :sup:`-1`      Nonlinear damping gain
`metric_scalar`  :math:`\mu`  (m/s)\ :sup:`-1`  Priority weight relative to other RMPs
`inertia`        :math:`m`    \-                Additional inertia
===============  ===========  ================  =======


Further Reading
^^^^^^^^^^^^^^^

Refer to the :doc:`RMPflow Tuning Guide <rmpflow_tuning_guide>` for practical advice on configuring RMPflow for a new robot.
