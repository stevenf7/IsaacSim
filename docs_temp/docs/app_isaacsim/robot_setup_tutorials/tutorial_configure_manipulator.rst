==========================================
Tutorial 7: Configure a Manipulator
==========================================


Learning Objectives
=======================

This is the second manipulator tutorial in a series of four tutorials. This tutorial shows how to configure physics, joint effort limits, and gains for the UR10e robot from Universal Robots and the 2F-140 gripper from Robotiq.

*30 Minutes Tutorial*

Prerequisites
===============

- Review :doc:`tutorial_import_assemble_manipulator` tutorial prior to beginning this tutorial. The steps here continue from the asset built in the previous tutorial.

.. note::
    If you have not completed the previous tutorial, you can find the prebuilt asset in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/Import_Manipulator/ur10e/ur/ur_gripper.usd``.


Adjust the Articulation for Manipulation Tasks
================================================

Adjust the articulation for the UR10e robot to make it more stable and accurate for manipulation tasks. Open the physics layer for the UR10e robot. 
The physics layer is located in the ``configuration`` folder with subfix ``_physics``.

#. In the Stage panel, select the **ur/root_joint** prim.
#. In the Property Editor at the bottom right, scroll down to the **Physics/Articulation** section.
#. Select **Articulation Enabled**.
#. Increase the **Solver Position Iterations Count** to ``64``.
#. Increase the **Solver Velocity Iterations Count** to ``4``.

   .. note::
      
      The **Solver Position Iterations Count** and **Solver Velocity Iterations Count** are used to control the accuracy of the simulation. 
      
      For a complex robot with many degrees of freedoms and mimic joints, increasing these values will make the simulation more accurate at the cost of performance. 
      See `articulation documentation <https://nvidia-omniverse.github.io/PhysX/physx/5.6.0/docs/Articulations.html#articulation-drive-stability>`_ for more information.

#. Decrease **Sleep Threshold** to ``0.00005``, this lowers the threshold for the robot to go to sleep when it is not moving. see `rigid body dynamics documentation <https://nvidia-omniverse.github.io/PhysX/physx/5.6.0/docs/RigidBodyDynamics.html#sleeping>`_ for more information.
#. Decrease the **Stabilization Threshold** to ``0.00001``, this lowers the threshold for the robot to start stabilizing itself when it is not moving. see `articulation documentation <https://nvidia-omniverse.github.io/PhysX/physx/5.6.0/docs/Articulations.html#articulation-drive-stability>`_ for more information.
#. **Ctrl + S** to save the changes.

   .. image:: /images/isim_5.0_full_tut_gui_articulation_properties.png
      :width: 80%
      :align: center


.. note:: 
   See `PhysX Best Practice Guide <https://nvidia-omniverse.github.io/PhysX/physx/5.6.0/docs/BestPractices.html#jointed-objects-are-unstable>`_ for tuning the articulation for manipulation tasks.


Add Physics Materials
================================================

Add physics materials to the robot gripper to make it more realistic and stable for manipulation tasks. 

#. Open the physics layer from the 2F-140 gripper asset from the last tutorial. It is located in the ``configuration`` folder with suffix ``_physics``.

   .. note:: 
      If you have not completed the previous tutorial, you can find the prebuilt asset in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/ robotiq_2f_140/configuration/robotiq_2f_140_physics.usd``.

#. Right click on the **robotiq_arg2f_140_model** prim and select **Create** > **Physics** > **Physics Material**, select **Rigid Body Material**. This will add a physics material attribute to the gripper. 
#. Drag the physics material to the **robotiq_arg2f_140_model/Looks** folder.
#. In the properties panel, scroll down to the **Physics/Rigid Body Material** section and set the **static friction** to **1.0** and **dynamic friction** to **1.0**. For your robot, match the friction values to the robot's surface friction coefficients.

#. Apply the physics material to the gripper finger tip. 
   - Select the ``colliders/left_inner_finger/mesh_1/box`` and in the properties panel, scroll down to the **Physics/Physics material on selected Material** section.
   - Select the **Physics Material** you just created at ``/World/robotiq_arg2f_140_model/Looks/finger``.

#. Repeat the same process for the ``colliders/right_inner_finger/mesh_1/box`` prim.

.. Note::
   See :ref:`isaac_sim_app_tutorial_core_adding_props` for more information on how to add physics materials to the robot.

Configure Joint Effort Limits
================================================

In the physics layer of the robotiq_arg2f_140_model asset from the previous step, let's configure the joint effort limits for the gripper.

#. In the **Stage** panel, select the ``robotiq_arg2f_140_model/joints/finger_joint`` prim. This is the joint that controls the gripper fingers, all other gripper joints are ``Mimic`` joints.
#. In the **Property Editor** at the bottom right, scroll down to the ``Drive/Angular/Max Force`` section.
#. Set the **Max Force** to ``200``. This is the maximum force that can be applied to the gripper fingers. For your robot, match the max force to the robot's joint torque limits.
#. **Ctrl + S** to save the changes.

.. Note::
   When the max force is very high, you might need to increase the physics step frequency (``Time Step per Second``) to avoid penetration and instabilities. 

Inspect the Robot Articulation
===============================

Let's inspect the robot articulation to verify the joint effort limits are applied correctly. Open the top level ``ur`` asset that you built in the previous tutorial.
This asset references the physics layers that you modified, so all the changes you made to the physics layer will be reflected in this asset.

.. Note::
   You can find the prebuilt asset in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd``.

#. Open the **Physics Inspector** through **Tools** > **Physics** > **Physics Inspector**.
#. Select the UR articulation in the stage, click on the circular arrow icon to refresh the articulation.
#. Try changing the target position with the blue slider and verify that the DOF position reaches the target specified.

   .. image:: /images/isim_5.0_full_tut_gui_physics_inspector.png
      :width: 90%
      :align: center

#. Close the **Physics Inspector** window/panel (discarding any changes authored by this tool, if prompted).

   .. warning::

      Since the Physics Inspector partially initializes ``omni.physx``, it is expected for general simulations to not behave properly when the tool is opened.

Tune Gains Using the Gain Tuner
=================================

Use the :ref:`isaac_gain_tuner` to verify the gains for the UR robot and the gripper fingers.
To critically damp the robot gains, set the ``Nat. Freq.`` to ``0.5`` and the ``Damping Ratio`` to ``1.0``.

#. Go to **Tools** > **Robotics** > **Asset Editors** >  **Gain Tuner**.
#. On the **Gain Tuner** window, on the **Select Robot** dropdown, select the **ur** articulation in the stage.
#. In the **Tune Gains** panel, you can adjust the gains for the robot and the gripper fingers joints. Test it with the **Test Gains Settings** panel.

.. hint::

   We recommend determining the gains for a small group of joints first, if it is difficult to tune the gains for the whole robot. Below are some tips for tuning the gains:

   * If the resulting plot shows the robot is undershooting the target position, you can increase the ``Nat. Freq.`` slightly.
   * If the resulting plot shows the robot is overshooting the target position, you can decrease the ``Nat. Freq.`` slightly and increase the ``Damping Ratio``.
   * Disabling gravity can help you see the gains more clearly.
   * Only gain test the joints that are expected to be moving together, the gain test order can be selected by the **Sequence** dropdown.
   * Reduce the maximum speed of a joint that you are tuning, if it is not expected to be commanded to move that fast in practice. The default values in the Gains Test are the maximum velocity written into the USD.

.. image:: /images/isim_5.0_full_tut_gui_gain_tuner_ur10e.png
   :width: 80%
   :align: center

.. note::
   See :ref:`isaac_gain_tuner` for more information on the Gain Tuner.

   See :ref:`isaac_sim_app_tutorial_advanced_joint_tuning` for more information on how to tune the gains for the robot.

   The complete asset for this tutorial can be found in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd``.

Summary
=======

In this tutorial, you learned how to configure the physics, joint effort limits, and gains for the UR10e robot from Universal Robots and the 2F-140 gripper from Robotiq using the Gain Tuner.
You added physics materials to the robot gripper to make it more realistic and stable for manipulation tasks.
You inspected the robot articulation and tuned the gains for the robot and the gripper fingers joints using the Physics Inspector. 









