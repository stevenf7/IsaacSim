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

The :ref:`isaac_gain_tuner` is used to tune the stiffness and damping gains of a selected Articulation. This extension is useful when importing any new robot or when needing to fine tune the gains of an existing robot.

This page provides the explanation of the function behind the Gain Tuner. For more detail about the step-by-step usage of the Gain Tuner, refer to :ref:`isaac_sim_app_tutorial_advanced_joint_tuning` tutorial page.


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


Gains Tests
^^^^^^^^^^^^^^^^^^^^^^

The Gains Tests are a suite of tests that allow you to quickly assess the quality of the current set of gains under different conditions. Each test is divided by *sequences*, where a sequence is a group of joints tested together. The sequence is defined per joint and is an index of the order in which the test runs. For each sequence the robot resets to its initial configuration before the test begins.

All tests send position commands for position drives and velocity commands for velocity drives. In position commands the target velocities are always zero, so that joint damping is properly evaluated. In a real control scenario a proper trajectory command should be sent, where the velocity command is equivalent to the integrated positions of the designated trajectory.

.. image:: /images/isim_5.0_full_ref_gui_gains_tuner_test_settings.png

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


Further Learning
=================
- The :ref:`isaac_sim_app_tutorial_advanced_joint_tuning` tutorial for detailed instructions on how to use the Gain Tuner.
