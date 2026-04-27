..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_advanced_joint_tuning:

==========================================
Tutorial 11: Tuning Joint Drive Gains
==========================================

Learning Objectives
===================

In this tutorial, you learn how to use the Gain Tuner to tune joints on a robot so that it behaves as expected, and how to validate the tuned gains with the Stress Test. For a more detailed explanation of how the Gain Tuner works and the physics behind it, see :ref:`isaac_gain_tuner`.

.. figure:: /images/isim_5.0_full_ref_gui_gains_tuner_ui.png
    :align: center
    :alt: Gain Tuner Overview


Prerequisite
------------------

- If the robot is in URDF format, follow :ref:`isaac_sim_app_tutorial_advanced_import_urdf` to import a URDF file into Isaac Sim.
- The Gain Tuner extension is designed to be used on Robot assets, which are USD assets that contain the :ref:`Robot Schema <isaac_sim_robot_schema>` applied.
- We also encourage you to setup your robot based on recommended :ref:`isaac_sim_app_reference_asset_structure`.
- This extension is enabled by default. If it is ever disabled, it can be re-enabled from the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.robot_setup.gain_tuner``.
- To access this Extension, go to the top menu bar and click **Tools** > **Robotics** > **Asset Editors** > **Gain Tuner**. The robots that are available for tuning will automatically populate under the Gain Tuner **Select Robot** Dropdown menu.


You can import any robot on the library and work on the joint drive parameters. For a more isolated test, you can also author a simple prismatic joint connected to a fixed base and model gains based on a rigid body with a given mass that moves along this prismatic joint. Remember you need to apply :ref:`Robot Schema <isaac_sim_robot_schema>` to the robot before the Gain Tuner can recognize the relevant joints and links.


Overview of the Tuning Workflow
================================

Gain tuning is an iterative process. The recommended workflow moves through two stages:

#. **Set initial gains** using the position or velocity drive heuristics below.
#. **Tune and evaluate** using the three built-in test modes, each targeting a different aspect of joint behavior:

   - **Snap-to-Limits** *(default)* --- commands joints to their lower and upper limits. Use this to verify that gains are strong enough to reach the full range of motion and that limits, gains, and collision geometry are mutually consistent.
   - **Sinusoidal** --- drives joints with a continuous repeating waveform. Use this to evaluate how well gains track smooth motion and to identify underdamping or overdamping from the shape of the tracking curve.
   - **Step Function** --- drives joints with sudden position changes. Use this to evaluate how quickly and accurately gains respond to discrete commands, as a closer approximation of how a policy issues targets during training.

Once gains are satisfactory across all three test modes, run the **Stress Test** to confirm they are robust under the extreme commands typical of reinforcement learning training before moving to Isaac Lab.


Gain Tuning
===========

Tuning the joint drive gains is a process of finding the optimal values that balance the trade-off between stability and responsiveness. For example, low damping and stiffness may not be able to overcome the robot's inertia, causing the measured value to be offset from the target, while too high a stiffness may cause the robot to overshoot and oscillate around the target. Here we provide some tips for tuning position and velocity driven robots.

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
==========================

Following the |isaac-sim| :ref:`Asset Structure <isaac_sim_app_reference_asset_structure>`, joint gains are a physics configuration and ideally should be saved on the physics layer. To facilitate this, the **Save Gains to Physics Layer** button on the UI searches for the asset's physics layer where the joint is defined and applies the updated gains to that layer.


Tuning with the Gains Tests
============================

The three tuning test modes share the same setup steps:

#. Enable the **Test** checkbox for the joints you want to evaluate in the joint table.
#. Assign joints to sequences. Joints in the same sequence are tested simultaneously; joints in different sequences are tested one group at a time, with the robot resetting to its home configuration between sequences. Group joints that are expected to move together.
#. Select the desired test mode in the test mode selector, configure parameters, and press **Play**, then **Run Test**.

Repeat --- adjust gains, re-run, observe --- until results are satisfactory. Each test mode surfaces different information, so it is useful to work across all three rather than treating any one as definitive.


Snap-to-Limits
---------------

The default test when the Gain Tuner is opened. Commands each joint to its lower limit, holds until stabilized, commands it to its upper limit, holds, then returns to home. Unlike the sinusoidal and step function tests, Snap-to-Limits requires no manual per-joint amplitude or period configuration --- it reads limits directly from USD and automatically classifies each joint's result.

Use Snap-to-Limits to answer: *can my gains drive every joint to its full range of motion, and are limits, gains, and collision geometry all consistent with each other?*

Each joint is classified as **Pass**, **Fail**, or **Blocked**. If any joints report **Fail** or **Blocked**, use the **Disable Self-Collisions** and **Disable Velocity Limits** toggles to isolate the cause before adjusting gains. For a full explanation of what each classification means, the settling time and hold error metrics, and the recommended diagnostic steps for each outcome, see :ref:`isaac_gain_tuner_snap_to_limits`.


Sinusoidal
-----------

Drives joints with a continuous repeating sinusoidal waveform. Use this to evaluate how well gains track smooth motion and to identify underdamping or overdamping from the shape of the tracking curve.

Use Sinusoidal to answer: *do my gains track smooth, continuous motion accurately, and is the system over- or underdamped?*

Use the result plots to guide adjustments:

- **Measured position closely tracks commanded position**: gains are well-tuned for this waveform. Consider tightening the period or increasing amplitude to stress the joint further.
- **Measured position lags the command or undershoots**: stiffness is likely too low. Increase stiffness and re-run.
- **Measured position oscillates or overshoots**: damping is likely too low. Increase damping and re-run.
- **Measured position is offset from the command at steady state**: the joint drive may be saturating at its max force limit. Check the joint max force setting in the Properties panel.


Step Function
--------------

Drives joints with sudden alternating position changes between a configurable minimum and maximum. Use this to evaluate how quickly and accurately gains respond to discrete commands --- a closer approximation of how a policy issues targets during training than a smooth waveform.

Use Step Function to answer: *do my gains respond quickly and accurately to sudden position changes, without excessive overshoot or settling delay?*

Use the result plots to guide adjustments:

- **Measured position reaches the step target and holds cleanly**: gains are well-tuned for this step size and period.
- **Measured position overshoots and oscillates before settling**: damping is too low. Increase damping.
- **Measured position approaches the target slowly or does not reach it within the period**: stiffness is too low, or the period is shorter than the joint's velocity limit allows. Try increasing stiffness or lengthening the period.
- **Measured position reaches the step target but with a consistent steady-state offset**: the joint drive may be saturating. Check the joint max force setting.

.. note::
    A reasonable goal across all three test modes is to find gains that reach the commanded position with overshoot within 1% of the target. The specific tolerance depends on your application.


Stress Testing Gains for Reinforcement Learning
==================================================

Once gains are satisfactory across all three tuning test modes, run the **Stress Test** before moving to Isaac Lab. Gains that appear well-tuned in the GUI can produce instabilities during reinforcement learning training, where neural-net policies issue rapid, extreme commands across many parallel environments simultaneously. Finding these instabilities in the GUI --- where iteration time is fast and the Robot Inspector is available --- is significantly easier than diagnosing them during a training run.

#. Select **Stress Test** in the test mode selector.
#. Choose a sub-mode:

   - **Random Walk** --- adds a Gaussian-distributed delta to each joint's position target every physics step, simulating unconstrained neural-net exploration. Start with the default sigma (1% of joint range) and increase gradually to assess your safety margin.
   - **Adversarial** --- snaps all active joints simultaneously to randomly chosen lower or upper limits every *N* steps, targeting the worst-case correlated configurations that arise when many parallel training environments drive a robot to opposing extremes.

#. Configure duration, velocity threshold, and seed. Press **Run Test**.

Each joint is classified as **Stable** or **Unstable**. The RNG seed is logged so any destabilizing run can be reproduced exactly. For a full explanation of how to interpret each result combination and which part of the system each failure mode implicates, see :ref:`isaac_gain_tuner_stress_test`.


Isolating the Responsible Joints
----------------------------------

When an instability is found, use the sequencer to narrow down which joints are responsible rather than trying to diagnose the full-robot result directly:

#. Note the logged RNG seed from the result.
#. Re-run the stress test on a subset of the articulation using the sequencer --- for example, proximal joints only.
#. If the subset is stable, expand to include more joints. If still unstable, reduce further.
#. Binary search toward the minimal set of joints that reproduces the instability.
#. Tune the responsible joints and re-run the full-body test to confirm the fix.

The **Robot Inspector** can assist in examining the isolated subsystem in detail between iterations.


Visualizing Results
==========================

The results of the tests are visualized as plots, where tracked joint positions and velocities are compared against the commanded trajectory. Select the desired joint in the left panel to display its results in the plots. Results are color-coded by joint, with measured values shown as a faded version of the commanded trajectory's color.

Even if a joint is not listed in the Robot Schema, it is still visualized in the plots if it is part of the physical robot.

To select more than one joint, hold **Ctrl** and click on the desired joints, or select the first joint and hold **Shift** and click the last joint to select all joints between them.

.. image:: /images/isim_5.0_full_ref_gui_gains_tuner_plots.png
    :align: center
    :alt: Gain Tuner results for a poorly tuned UR10e robot.

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

- Read :ref:`isaac_gain_tuner` for more details on the physical mechanics relating joint gains to derived motions, the full parameter reference for each test, and guidance on interpreting test results.
