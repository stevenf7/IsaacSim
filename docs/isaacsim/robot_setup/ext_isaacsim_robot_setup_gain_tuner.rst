..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_gain_tuner:


===============================
Gain Tuner Extension
===============================

The Gain Tuner tunes the stiffness and damping gains of a selected Articulation. Use it when importing a new robot or when fine-tuning the gains of an existing one.

This extension is enabled by default. If it is ever disabled, re-enable it from the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.robot_setup.gain_tuner``. To open it, go to **Tools** > **Robotics** > **Asset Editors** > **Gain Tuner**. Robots on the stage that have the :ref:`Robot Schema <isaac_sim_robot_schema>` applied automatically appear in the **Select Robot** dropdown.

For a hands-on walkthrough that uses the UR10 manipulator, see the :ref:`isaac_sim_app_tutorial_advanced_joint_tuning` tutorial.


.. _isaac_gain_tuner_overview:

Overview
===========

The purpose of the Gain Tuner is to find a pair of stiffness and damping gains for each robot joint so that the robot is able to follow commanded trajectories according to the robot's expected behavior.

The Gain Tuner offers a set of tests that allow you to quickly assess the quality of the current set of gains and a utility for tuning gains manually.

- **Tuning Gains**: A utility for tuning the gains for the robot.
- **Gains Tests**: A suite of tests for evaluating joint behavior:

  - *Snap-to-Limits* --- commands joints to their lower and upper limits to verify they can reach their full range of motion.
  - *Sinusoidal* --- drives joints with continuous sinusoidal trajectories.
  - *Step Function* --- drives joints with step-function trajectories.
  - *Stress Test* --- drives joints with extreme random commands to surface instabilities that can appear during reinforcement learning training.

- **Test Results**: A plot of the results of the gains tests on the tracked joint positions and velocities, compared against the commanded trajectory.


Understanding Joint Drives
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Joint Drives are dual-proportional controllers used to set a joint to a given target. One proportional gain is moderating the error in position, while the other gain is moderating the error in velocity. For historical reasons, these gains are called Stiffness and Damping, respectively.

.. note:: These Joint drives are *implicit* - meaning the position and velocity constraints are imposed by the drive with respect to the current time-step. In engineering this is typically done where it uses a closed loop control with readings of the previous time-step of position and velocity and reacting to it for future control. Refer to `Articulation Joint Drives <https://nvidia-omniverse.github.io/PhysX/physx/5.3.0/docs/Articulations.html#articulation-joint-drives>`_.

**Stiffness** is similar to a spring stiffness constant multiplying the error in position, as if the spring was stretched by that amount. **Damping** comes from the effect of targeting zero velocity and therefore any movement would result in a reaction that attempts to stop it. You can actually have it track a velocity that is different than zero and the effect is the same as stiffness would be in position.

.. math::
    \tau = \text{stiffness} * (q - q_{\text{target}}) + \text{damping} * (\dot{q} - \dot{q}_{\text{target}})

where :math:`q` and :math:`\dot{q}` are the joint position and velocity, respectively. When :math:`\dot{q}_{target} = 0`, the system reduces to a conventional PD controller on the joint position.

This formula applies for both revolute and prismatic joints.

The joint max force will act as a clamp for :math:`\tau`, and finally, the drive type will dictate if the effort will be applied directly as a torque or force, or if it will be converted into an acceleration applied to the bodies connected to the joint.


Drive Modes
+++++++++++++++

This dual-proportional controller provides two main ways to control the robot:

 - **Position target** - used for controlled joints that are driven by defining a target distance/angle that the connected bodies should be.
 - **Velocity target** - usually done for wheels or other free-spinning objects.

To have a position-controlled joint: set Stiffness to something greater than zero and Damping can be any value.
To have a velocity-controlled joint: set Stiffness to zero and Damping to any value greater than zero.


Tools
============

Tuning Gains
^^^^^^^^^^^^^^

The Joint Gains are a pair of Stiffness and Damping values that are used to drive the joint. They are applied to the joint in the form of a drive that applies an effort (Force/Torque) to the joint, based on the error between the desired position and velocity or both. This Effort is computed as:

.. math::
    Effort = K_p * (Position_{Desired} - Position_{Current}) + K_d * (Velocity_{Desired} - Velocity_{Current})

Where :math:`K_p` is the Stiffness and :math:`K_d` is the Damping.

From this formula, you can describe the different modes of the joint drive:

- Position Drive: When the joint drive is in position mode, the desired position is the target position. This requires the stiffness to be greater than ``0``, and the damping to be any value.
- Velocity Drive: When the joint drive is in velocity mode, the desired position is the current position, and the desired velocity is the target velocity. This requires the stiffness to be ``0`` and the damping to be any value.
- None: When the joint drive is in none mode, the joint drive is not active. The joint can still be controlled by applying a direct effort. This requires the stiffness to be ``0`` and the damping to be ``0``.
- Mimic: When the joint drive is in mimic mode, the joint drive is driven by the mimic joint. This means that the joint drive will not be active, but the mimic joint's attributes of Natural Frequency and Damping Ratio can still be configured through the Tuner.

This Dampener-Spring model can also be described in terms of the natural frequency and damping ratio:

.. math::
    \omega_n = \sqrt{\frac{K_p}{m}}

    \zeta = \frac{K_d}{2 m \omega_n}

Where :math:`\omega_n` is the natural frequency and :math:`\zeta` is the damping ratio, and :math:`m` is the computed joint inertia based on the mass of the robot at both sides of the joint. The damping ratio is such that :math:`\zeta = 1.0` is a critically damped system, :math:`\zeta < 1.0` is underdamped, and :math:`\zeta > 1.0` is overdamped.

From the above formula, observe that there are two ways to Tune Gains:

- Directly editing Stiffness and Damping values: On the joints table, you can directly edit the Stiffness and Damping values for each joint.
- Natural Frequency: The Gain tuner can also automatically compute the Stiffness and Damping values for each joint based on the desired natural frequency and damping ratio.

.. Note:: Because the robot is a structure that is made of multiple links and moving joints, the natural frequency of each joint is dependent on the robot's configuration. To establish a standard, the natural frequency of the robot at its home configuration is used.

Tuning Options
+++++++++++++++

In the Tuning Options, you can select the tuning mode between Stiffness and Natural Frequency. On the joints table, observe the following options:

- **Mode**: The mode of the joint drive (Position, Velocity, None, Mimic)
- **Type**: The type of the joint drive (Force, Acceleration). In Force, the effort is applied directly to the joint. In Acceleration, the effort is Normalized by the joint's mass, and is thus invariant to the robot's configuration, behaving as an ideal actuator.
- **Stiffness** (Stiffness Mode): The stiffness of the joint drive. Changing this will lead to a change in the natural frequency of the joint.
- **Damping** (Stiffness Mode): The damping of the joint drive. Changing this will lead to a change in the damping ratio of the joint.
- **Natural Frequency** (Natural Frequency Mode): The natural frequency of the joint drive.
- **Damping Ratio** (Natural Frequency Mode): The damping ratio of the joint drive.

The configurable Degrees of Freedom (DOF) of the robot are displayed in accordance with what is defined in the Robot's Joints list.


.. _isaac_gain_tuner_tuning_workflow:

Tuning Workflow
==================

Gain tuning is an iterative process. The recommended workflow moves through two stages:

#. **Set initial gains** using the position or velocity drive heuristics below.
#. **Tune and evaluate** using the built-in test modes, each targeting a different aspect of joint behavior:

   - **Snap-to-Limits** *(default)* --- commands joints to their lower and upper limits. Use this to verify that gains are strong enough to reach the full range of motion and that limits, gains, and collision geometry are mutually consistent.
   - **Sinusoidal** --- drives joints with a continuous repeating waveform. Use this to evaluate how well gains track smooth motion and to identify underdamping or overdamping from the shape of the tracking curve.
   - **Step Function** --- drives joints with sudden position changes. Use this to evaluate how quickly and accurately gains respond to discrete commands, as a closer approximation of how a policy issues targets during training.

Once gains are satisfactory across all three test modes, run the **Stress Test** to confirm they are robust under the extreme commands typical of reinforcement learning training before moving to Isaac Lab.

.. note:: The specific tuning process may vary based on the characteristics of the robot and its control system.


Position Drive
--------------

For each joint of the robot:

#. Start by setting the damping to zero and only tuning the stiffness. This will help you establish a stable response without the influence of the derivative term.
#. Increase the stiffness until the joint is able to converge near the target position.
#. Reduce the stiffness by one order of magnitude.
#. After setting the stiffness, add damping with one order of magnitude lower than stiffness. This will be your baseline for the parameters and in general should not overshoot. If you want a faster response, reduce damping further.
#. Fine-tune both gains around this established baseline to achieve the desired performance, considering factors such as stability, response time, and overshoot.
#. If you want to emulate a control that includes gravity compensation, select all rigid bodies of the robot and check **Disable Gravity** in the properties panel.


Velocity Limit and Industrial Robots
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many robots, including the majority of industrial robots, come with pre-tuned PD control for their joint drives and can be set up to have a perfect position control response, always driving at the given joint velocity limit. To reproduce this behavior, increase the joint stiffness from the previous tuning heuristic by a factor of two and define the maximum joint velocity in **Joint** > **Advanced** > **Maximum Joint Velocity** in the **Properties** panel. Run the simulation to verify the joint velocity is meeting the specification and fine-tune the stiffness until the joint max velocity limit is within tolerance. If stiffness is too high, the max velocity may still be violated, so it is not advised to add infinite stiffness to the joint --- instead operate with stiffness similar to the values calibrated without a max joint velocity.


Velocity Drive
--------------

For each joint of the robot:

#. Start by setting the **Stiffness** to zero and only tuning the damping.
#. Increase the damping until the joint is able to converge near the target velocity.
#. If the robot may carry additional load, slightly increase the damping (for example, add 10% extra) to account for the extra load.
#. You can limit the joint's output by either setting the max joint velocity, or restricting the max joint force to impose a maximum joint load effort.


Saving Gains to the Asset
---------------------------

Following the |isaac-sim| :ref:`Asset Structure <isaac_sim_app_reference_asset_structure>`, joint gains are a physics configuration and ideally should be saved on the physics layer. To facilitate this, the **Save Gains to Physics Layer** button on the UI searches for the asset's physics layer where the joint is defined and applies the updated gains to that layer.


Gains Tests
^^^^^^^^^^^^^^^^^^^^^^

The Gains Tests are a suite of tests that allow you to quickly assess the quality of the current set of gains under different conditions. Each test is divided by *sequences*, where a sequence is a group of joints tested together. The sequence is defined per joint and is an index of the order in which the test runs. For each sequence the robot resets to its initial configuration before the test begins.

All tests send position commands for position drives and velocity commands for velocity drives. In position commands the target velocities are always zero, so that joint damping is properly evaluated. In a real control scenario a proper trajectory command should be sent, where the velocity command is equivalent to the integrated positions of the designated trajectory.

The three tuning test modes share the same setup steps:

#. Enable the **Test** checkbox for the joints you want to evaluate in the joint table.
#. Assign joints to sequences. Joints in the same sequence are tested simultaneously; joints in different sequences are tested one group at a time, with the robot resetting to its home configuration between sequences. Group joints that are expected to move together.
#. Select the desired test mode in the test mode selector, configure parameters, and press **Play**, then **Run Test**.

Repeat --- adjust gains, re-run, observe --- until results are satisfactory. Each test mode surfaces different information, so it is useful to work across all three rather than treating any one as definitive.

.. note::

    If you do not see all available columns in the Gains Tuner table, try expanding the Gain Tuner panel or increasing the overall width of the Isaac Sim application window. Some columns may be hidden if the window is too narrow.


.. _isaac_gain_tuner_snap_to_limits:

Snap-to-Limits
++++++++++++++++

The recommended starting point for evaluating a new or modified robot. It commands each joint to its lower limit, holds, then to its upper limit, holds, and finally returns to the home position. The test validates that authored joint limits, drive gains, and collision geometry are all mutually consistent.

Each joint approaches its target and waits to stabilize before the hold phase begins. If a joint does not settle within ten seconds, the test proceeds to the hold phase regardless. During the hold phase, position error is sampled continuously and reported as mean and maximum error over the full hold duration, making the metric robust to residual oscillation.

After the hold, each joint receives one of three classifications:

- **Pass**: Both limits reached within tolerance.
- **Fail**: A limit was not reached and the joint was still moving or oscillating, indicating a gains or dynamics issue.
- **Blocked**: A limit was not reached and the joint was stalled, typically caused by self-collisions or other physical constraints rather than a gains issue.

The total test time is variable: fast robots settle quickly and the test finishes in seconds, while slow or weak drives consume the full timeout per phase.

Per-joint results include settling time (reported separately for the lower and upper limit phases) and mean and maximum hold error at each limit.

**Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 25 55 20

   * - Parameter
     - Description
     - Default
   * - **Hold Duration**
     - Seconds to hold at each target after the joints have settled.
     - 1.0
   * - **Tolerance**
     - Position error threshold (rad or m) for the settling check and pass/fail determination.
     - 0.01
   * - **Disable Self-Collisions**
     - Temporarily disable self-collisions on the articulation during the test. Useful for distinguishing a Blocked result caused by collision geometry from a Fail result caused by insufficient gains.
     - Off
   * - **Disable Velocity Limits**
     - Temporarily set joint max velocity limits to a very large value for the test duration. Useful for isolating whether a Fail result is caused by insufficient gains or by velocity limits preventing the joint from reaching its target in time.
     - Off


**Interpreting Results:**

Each classification points to a different part of the system and suggests a different remedy.

- **Pass with long settling time**: The joint reaches its target but slowly, indicating the system is overdamped. Try increasing stiffness or reducing damping, then re-run to confirm settling time improves without introducing oscillation. Residual oscillation will appear as elevated mean hold error even on a passing joint.

- **Pass with high hold error**: The joint reached the limit closely enough to pass the tolerance check but is not holding cleanly --- likely underdamped with residual oscillation. Try increasing damping.

- **Fail**: The joint did not reach its target and was still moving at the end of the timeout. First re-run with **Disable Velocity Limits** enabled. If the joint passes, the velocity limit is preventing the joint from reaching its target in time and the remedy is raising the velocity limit rather than adjusting gains. If the joint still fails, stiffness is insufficient and should be increased.

- **Blocked**: The joint stalled before reaching its limit. Re-run with **Disable Self-Collisions** enabled. If the joint passes, the limit is set beyond what the collision geometry allows --- tighten the joint limit in USD rather than adjusting gains. If the joint remains blocked with collisions disabled, examine whether a mimic joint coupling, another joint in the same sequence, or an incorrectly authored limit is constraining motion.

.. note::
    These tests identify that something is wrong and roughly where, but the magnitude of any gain adjustment still requires iteration: change gains, re-run, and observe whether the metric improves. The tests are diagnostic tools, not optimizers.


.. _isaac_gain_tuner_sinusoidal:

Sinusoidal
+++++++++++

Drives joints with a continuous sinusoidal trajectory for the test duration. Useful for evaluating how well gains track smooth, repeating motion across a joint's range.

**Parameters:**

- **Test**: Check to include the joint in the test.
- **Period**: The period of the waveform.
- **Phase**: The phase of the waveform.
- **Amplitude**: The amplitude of the waveform, from 0 to 100%.
- **Offset**: The offset of the waveform, from 0 to 100%.

**Interpreting Results:**

Use the result plots to guide adjustments:

- **Measured position closely tracks commanded position**: gains are well-tuned for this waveform. Consider tightening the period or increasing amplitude to stress the joint further.
- **Measured position lags the command or undershoots**: stiffness is likely too low. Increase stiffness and re-run.
- **Measured position oscillates or overshoots**: damping is likely too low. Increase damping and re-run.
- **Measured position is offset from the command at steady state**: the joint drive may be saturating at its max force limit. Check the joint max force setting in the Properties panel.


.. _isaac_gain_tuner_step_function:

Step Function
++++++++++++++

Drives joints with a repeating step-function trajectory, alternating between a minimum and maximum position. Useful for evaluating how quickly and accurately gains respond to sudden position changes.

**Parameters:**

- **Test**: Check to include the joint in the test.
- **Period**: The period of the waveform.
- **Phase**: The phase of the waveform.
- **Step Minimum**: The minimum value of the waveform, in the joint value units of measurement.
- **Step Maximum**: The maximum value of the waveform, in the joint value units of measurement.

**Interpreting Results:**

Use the result plots to guide adjustments:

- **Measured position reaches the step target and holds cleanly**: gains are well-tuned for this step size and period.
- **Measured position overshoots and oscillates before settling**: damping is too low. Increase damping.
- **Measured position approaches the target slowly or does not reach it within the period**: stiffness is too low, or the period is shorter than the joint's velocity limit allows. Try increasing stiffness or lengthening the period.
- **Measured position reaches the step target but with a consistent steady-state offset**: the joint drive may be saturating. Check the joint max force setting.

.. note::
    A reasonable goal across all three test modes is to find gains that reach the commanded position with overshoot within 1% of the target. The specific tolerance depends on your application.


.. _isaac_gain_tuner_stress_test:

Stress Test
++++++++++++

The stress test subjects joints to extreme random commands to surface PhysX solver instabilities that may appear during reinforcement learning training but are invisible during normal GUI testing. When training a policy with many parallel environments, the exploration space is large and joints may receive rapid, unconstrained commands across their full range. Finding these instabilities in the GUI --- where iteration time is fast and the robot inspector is available --- is significantly easier than diagnosing them during a training run.

Two sub-modes are available:

**Random Walk** --- Every physics step, a Gaussian-distributed delta is added to each joint's current position target. Commands are clamped to joint limits. This simulates unconstrained neural-net exploration during early policy training. The standard deviation (sigma) is expressed as a percentage of each joint's range, so wider joints receive proportionally larger perturbations.

**Adversarial** --- Every *N* physics steps, all active joints are simultaneously snapped to randomly chosen lower or upper limits (50/50 per joint). This maximizes worst-case solver load by driving extreme correlated configurations that the random walk would only hit rarely, targeting the same failure modes that arise when many parallel training environments simultaneously drive a robot to opposing extremes.

Per-joint instability detection runs every step:

- Velocity exceeding the configurable threshold marks the joint as **Unstable**.
- NaN in position or velocity marks the joint as **Unstable**.
- If neither occurs over the full duration the joint is classified as **Stable**.

The RNG seed is logged so destabilizing runs can be reproduced exactly.

**Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 25 55 20

   * - Parameter
     - Description
     - Default
   * - **Sub-mode**
     - Random Walk or Adversarial.
     - Random Walk
   * - **Duration**
     - Simulation-time seconds to run.
     - 10.0
   * - **Velocity Threshold**
     - Absolute velocity (rad/s or m/s) above which a joint is flagged as Unstable.
     - 100.0
   * - **Sigma (% range)**
     - Standard deviation of the per-step Gaussian delta in Random Walk mode, expressed as a percentage of each joint's range.
     - 1.0
   * - **Snap Interval**
     - Physics steps between random snaps in Adversarial mode.
     - 10
   * - **Seed**
     - RNG seed for reproducibility. Logged in results so a destabilizing run can be reproduced exactly.
     - 42
   * - **Disable Self-Collisions**
     - Temporarily disable self-collisions on the articulation during the test. Useful for distinguishing instabilities caused by contact events from those caused by gains.
     - Off
   * - **Disable Velocity Limits**
     - Temporarily set joint max velocity limits to a very large value for the test duration. Useful for isolating whether instabilities are caused by gains or by velocity limits producing large per-step correction errors.
     - Off


**Interpreting Results:**

- **Stable across both modes**: Positive evidence that the gains are unlikely to cause solver instabilities during Isaac Lab training at the configured sigma and snap interval. Document the test parameters alongside the result --- a robot that is stable at 1% sigma may not be stable at 5% sigma, and this distinction matters when estimating safety margins for policy training.

- **Unstable with self-collisions enabled, Stable with them disabled**: The instability is contact-driven rather than gains-driven. Do not adjust gains in response to this result. Instead, examine whether the joint limits allow configurations where self-contact occurs and tighten limits or adjust collision geometry accordingly.

- **Unstable with self-collisions disabled**: Gains are implicated. Examine the logged time-to-instability and triggering command. A very short time-to-instability at low sigma indicates the gains are marginal even under mild perturbation and significant adjustment is needed. A long time-to-instability at high sigma indicates the gains are robust under realistic conditions and the instability is only reachable at perturbation levels a trained policy would rarely produce.

- **Unstable in Random Walk but Stable in Adversarial (or vice versa)**: The failure mode differs between the two sub-modes and the results can help narrow the diagnosis. Random Walk instabilities tend to arise from the target drifting into a problematic region incrementally. Adversarial instabilities tend to arise from the solver struggling with simultaneous extreme configurations across coupled joints.

**Isolating the responsible joints:**

When an instability is found, use the logged RNG seed to reproduce the run exactly. Then use the sequencer to re-run the test on progressively smaller subsets of the articulation, binary searching toward the minimal set of joints that reproduces the instability. This isolates which part of the kinematic chain is responsible and is significantly faster than reasoning about the full-robot result. The Robot Inspector can assist in examining the isolated subsystem.

.. note::
    A Stable result is meaningful only at the sigma and snap interval values used. Record these parameters alongside results when assessing readiness for Isaac Lab training.


Visualizing Results
====================

The results of the tests are visualized as plots, where tracked joint positions and velocities are compared against the commanded trajectory. Select the desired joint in the left panel to display its results in the plots. Results are color-coded by joint, with measured values shown as a faded version of the commanded trajectory's color.

Even if a joint is not listed in the Robot Schema, it is still visualized in the plots if it is part of the physical robot.

To select more than one joint, hold **Ctrl** and click on the desired joints, or select the first joint and hold **Shift** and click the last joint to select all joints between them.

.. note::
    Visualization results are only available after tests have finished running. Depending on test configuration, this may take some time.


Tips
======

- Disable gravity if your robot has built-in gravity compensation or a separate gravity compensation controller.
- Group joints that are expected to move together and tune each group individually first, then combine them for a final test. For a humanoid robot, for example, you may want to separate the legs and arms.
- Reduce the maximum speed of a joint that you are tuning if it is not expected to be commanded to move that fast in practice. Most default maximum velocities in USD are likely impractically high.
- When running the Stress Test, document the highest sigma at which all joints are Stable --- this is a practical safety margin for your Isaac Lab training configuration.
- If a joint is Blocked in Snap-to-Limits, use **Disable Self-Collisions** to confirm the cause before adjusting gains.


Further Learning
=================
- The :ref:`isaac_sim_app_tutorial_advanced_joint_tuning` tutorial for a hands-on walkthrough using the UR10 manipulator.
