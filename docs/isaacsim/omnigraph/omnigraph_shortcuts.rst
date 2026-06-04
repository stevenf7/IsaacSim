.. _isaac_sim_app_tutorial_advanced_omnigraph_shortcuts:

==========================================
Commonly Used OmniGraph Shortcuts
==========================================



|isaac-sim_short| has shortcuts for populating some of the most commonly used OmniGraphs. They can be found under **Tools > Robotics > OmniGraph Controllers**. After selecting the graph you want to create, you are prompted to provide a minimal set of parameters to populate the graph. 

The shortcuts are:

:ref:`Controller Graphs <omnigraph_shortcuts_controller_graphs>`

- Joint Position Controller
- Joint Velocity Controller
- Differential Controller
- Open Loop Gripper Controller

.. _omnigraph_shortcuts_ros2bridge_graphs:

For information on how to use ROS Graphs, go to each of the relevant :ref:`isaac_ros2_tutorials_page`.

.. Note::

    - *No* validation is done to detect a graph with the same tasks or that controls the same robot. You must ensure that your graphs are unique in the scene.
    - These are just shortcuts to create the graph. You can always modify the graph after it's created to suit your needs.


To use Python scripting to create these graphs:

  1. Click on the icon next to **Python Script for Graph Generation** on the bottom of the popup window.
     It takes you to the Python script used to generate the graphs for the given shortcut. 
  2. ``make_graph()`` is where the creation occurs. The relevant commands may or may not all be in one continuous block depending on how the shortcut is setup. 

.. _omnigraph_shortcuts_controller_graphs:

Controller Graphs
===================

The controller shortcuts for moving the robots are:

* Articulation (Joint Position and Velocity) Controllers
* Differential Drive Controller
* Gripper Controllers


Articulation Controllers
-------------------------

Both Position and Velocity Controllers issue commands directly to each joint in the articulation. 
 
- **Robot Prim**: The parent prim of the robot. 
- **Graph Path**: The path to the graph generated. It is default to be under an independent tree called "/Graph/{type}_controller". If a graph already exist in the path given, it'll find the next available path by appending a number to the end of that path.
- **Add to Existing Graph** (optional): Default to False. If checked, it'll add the nodes to an existing graph and use an existing tick node if there exist one, but will add new controller nodes regardless of existing ones. 


Use the Articulation Controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use the controller to move the robot:

1. Highlight the **JointCommandArray** node under the newly created graph. 
2. Press *play* to start the simulation.
3. Move the robot by changing the values in the **JointCommandArray** node in the Property Tab.

If you had initial targets for position or velocity saved as part of the USD, it immediately moves towards those targets when you press **play**.

Differential Controller
------------------------

The Differential Controller takes in linear and angular velocities and converts them to individual wheel velocities.

- **Robot Prim**: The Robot Prim.
- **Graph Path**: The path to the graph generated. By default, it is under an independent tree called "/Graph/{type}_controller". If a graph already exist in the path given, it finds the next available path by appending a number to the end of that path.
- **Wheel Radius**: The radius of the wheel in meters.
- **Distance between wheels**: The distance between the two wheels in meters.
- **Left/Right Joint Names** (optional): Names of the joints that control the left and right wheels.
- **Left/Right Joint Index** (optional): The index of the joints that control the left and right wheels in the articulation chain.
- **Use Keyboard Control** (optional): Default to none. If checked, it also populates the graph that receives WASD as keyboard inputs to move the robot forward, backward, spin left, and spin right.
- **Add to Existing Graph** (optional): Defaults to False. If checked, it adds the nodes to an existing graph and uses an existing tick node if there is one, but will add new controller nodes regardless of existing ones. 

Use the Differential Controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- In some robots, there are only two controllable joints, so you do not have to specify joint names or indices. For robots with multiple actuated joints in an articulation chain, you must specify either the names or the indices of the joints that control the left and right wheels. List the left wheel before the right wheel so the order matches the Differential Controller output.

- If you did not include the WASD keyboard control in the graph, you can always test the controller by manually changing the "Desired Angular Velocity" and "Desired Linear Velocity" in the **DifferentialController** node under the newly created graph.

.. image:: /images/isaac_differential_controller_manual_inputs.png
    :align: center
    :height: 600


- If you are using the WASD Keyboard control, there are two scaling values used to scale the binary input from the keyboard to a linear velocity and an angular velocity that make sense for the vehicle's size. The values are inside the nodes "ScaleLinear" and "ScaleAngular" respectively. You can print the output of the "DifferentialController" node to see relative affects of the scaling values. You want to tune them so that the rotating commands results in similar magnitude changes in the wheels' velocities as the forward and backward commands.

.. image:: /images/isaac_differential_controller_scale.png
    :align: center
    :height: 400


- If you are using Isaac Sim Assets, the default values of the wheel radius and distance between wheels can be found on the bottom of the page for Wheeled Robots in :ref:`isaac_assets_robots`



Gripper Controller
------------------

The Gripper Controller works for any end-effector that has only one-degree of actuation per finger. This includes all parallel jaw grippers, as well as any multi-finger, multi-DOF-per-finger hands where each finger has only one degree of actuation.

- **Parent Robot**: The robot that contains the gripper. This could be the gripper itself, or if the gripper is part of an arm, this could be the prim for the entire manipulator.
- **Gripper Root**: The prim that contains all the gripper joints.
- **Graph Path**: The path to the graph generated. It is default to be under an independent tree called "/Graph/{type}_controller". If a graph already exists in the path given, it finds the next available path by appending a number to the end of that path.
- **Gripper Speed**: The speed at which the gripper closes or opens in meters (or radian) per second.
- **Gripper Joint Names**: The names of the joints that control the gripper fingers. List them all out separated by commas.
- **Open/Close Position Limit** (optional): The joint position that's considered fully open. Unit: meter (prismatic) or radian (revolute). If left blank, it defaults to the joint limits inside the asset's USD file.
- **Use Keyboard Control** (optional): Default to none. If checked, it populates the graph that receives "O","C", and "N" as keyboard inputs to open, close, and stop the gripper.
- **Add to Existing Graph** (optional): Defaults to False. If checked, it adds the nodes to an existing graph and uses an existing tick node if one exists, but will add new controller nodes regardless of existing ones. 

.. image:: /images/isim_5.0_full_ref_gui_omnigraph_gripper_controller.png
    :align: center

Use the Gripper Controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If no joint limits are given, the gripper defaults to the joint limits inside the asset's USD file. If the Open Position Limit and Close Position Limit are flipped, the gripper controller automatically corrects for it. The controller makes the assumption that the joint limits for opened position is greater than closed position. So if it is the opposite for your gripper, you would have to either adjust your definition of open and close or modify the Python script accordingly.

- Only uniform speed and same joint limits are supported using the shortcut. If you want variable speed or different joint limits for each of the fingers, you can modify the graph by adding arrays for the speed and joint limit inputs.


- If the articulation chain you are working with contains both an arm and a gripper and you wish to control the arm using the Articulcation Position Controller and the Gripper Controller for the gripper separately:

  1. Remove the joints that control the gripper from the arm controller graph. 
  2. Validate that there is no conflict between the two graphs.
