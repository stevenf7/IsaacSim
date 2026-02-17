.. _isaac_sim_app_tutorial_advanced_joint_tuning:

==========================================
Tutorial 11: Tuning Joint Drive Gains
==========================================

Learning Objectives
===================

In this tutorial, you learn how to use the Gain Tuner to tune joints on a robot so that it behaves as expected. For a more detailed explanation of how the Gain Tuner works and the physics behind it, see :ref:`isaac_gain_tuner`.

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


You can import any robot on the library and work on the joint drive parameters. For a more isolated test, you can also author a simple prismatic joint connected to a fixed base and model gains based on a rigid body with a given mass that moves along this prismatic joint. Remember you need to apply ::ref:`Robot Schema <isaac_sim_robot_schema>` to the robot before the Gain Tuner can recognize the relevant joints and links.


Gain Tuning
===========

Tuning the joint drive gains is a process of finding the optimal values that balances the trade-off between stability and responsiveness. For example, low damping and stiffness may not be able to overcome the robot's inertia, and the measured value will be offset from the target value, and too high of a stiffness may cause the robot to overshoot and oscillate around the target. Here we provide some tips in tuning position and velocity driven robots. 

.. note:: The specific tuning process may vary based on the characteristics of the robot and its control system.


Position Drive
--------------

For each joint of the robot:

#. Start by setting the damping to zero and only tuning the stiffness. This will help you establish a stable response without the influence of the derivative term.
#. Increase the stiffness until the joint is able to converge near the target position.
#. Reduce the stiffness by one order of magnitude.
#. After setting the stiffness, add damping with one order of magnitude lower than stiffness. This will be your baseline for the parameters and in general should not overshoot. If you want a faster response, reduce damping further.
#. Fine-tune both gains around this established baseline to achieve the desired performance, considering factors such as stability, response time, and overshoot.
#. If you want to emulate a control that includes gravity compensation, select all rigid bodies of the robot and check `Disable Gravity` in the properties panel.


Velocity Limit and Industrial Robots
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many robots, including the majority of Industrial robots, come with pre-tuned PD control for their joint drives and can be set up to have perfect position control response, always driving at the given joint velocity limit. To reproduce this behavior, we can increase the joint stiffness from the previous tuning heuristic by a factor of two and define the maximum joint velocity in the **Joint** > **Advanced** > **Maximum Joint velocity** in the **Properties** panel. Run the simulation to verify the joint velocity is meeting the specification and fine-tune the stiffness until the joint max velocity limit is within tolerance. If stiffness is too high, the max velocity may still be violated, so it is not advised to just add infinite stiffness to the joint, and instead operate with stiffness similar to the ones calibrated without a max joint velocity. 

Velocity Drive
--------------

For each joint of the robot:

#. Start by setting the **Stiffness** to zero and only tuning the damping. 
#. Increase the damping until the joint is able to converge near the target velocity.
#. If the robot may carry additional load, slightly increase the damping (for example, add 10% extra) to account for the extra load.
#. You can limit the joint's output by either setting the max joint velocity, or restrict the max joint force to impose a maximum joint load effort. 


Saving Gains to the Asset
==========================

Following the |isaac-sim| :ref:`Asset Structure <isaac_sim_app_reference_asset_structure>`, Joint gains would be a physics configuration, and should ideally be saved on the physics configuration layer. To facilitate this, The ``Save Gains to Physics Layer`` button on the UI searches for the Asset's physics layer where the joint is defined, and applies the updated gains to that layer. If you don't want or don't have permission to save on that file, you can just save the currently open stage instead to author an override to the joint target values locally. 


Visualize Results
==========================

The results of the tests are visualized in the form of a plot, where the tracked Joint Positions and Velocities are compared against the commanded trajectory. Select the desired joint to visualize the results on the left panel, and their respective test results will be displayed on the plots. The test results are color-coded by joint, with the measured values being a faded version of the commanded trajectory's color. 

Even if the joint is not listed on the Robot Schema, it will still be visualized in the plots, if it's part of the physical robot.

To select more than one joint, users can hold down the control key and click on the desired joint, or select the first joint and then hold down the shift key and click on the last desired joint, and all joints between them will be selected.

.. image:: /images/isim_5.0_full_ref_gui_gains_tuner_plots.png
    :align: center
    :alt: Gain Tuner Results for a poorly tuned UR10e robot.

.. note::
    The visualization results are only available when the tests are finished running, so depending on the configuration of the tests, it may take some time to get the results.
    


Tips
======

- A reasonable goal is to find a set of gains that is able to ramp to position but keep overshoot within 1% of the target.
- Disable Gravity if your robot has built-in gravity compensation or you have a separate gravity compensation controller.
- Group the joints that are expected to move together, and tune the gains for each group individually first, then combine them for the final test. For example, for a humanoid robot, you may want to separate the legs and arms because they are not expected to be moving at the same time with high tracking accuracy.
- Reduce the maximum speed of a joint that you are tuning if it is not expected to be commanded to move that fast in practice. Most of the default maximum velocities written inside the USD are likely impractically high.

Further Learning
=================

- Read :ref:`isaac_gain_tuner` for more details on the physical mechanics relating joint gains to derived motions, and how the Gain Tuner works.