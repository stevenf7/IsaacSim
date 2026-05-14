Controllers and the RobotState
===============================

This tutorial demonstrates building a complete robot controller using the Motion Generation API's fundamental building blocks: the :class:`RobotState` class and the :class:`BaseController` interface. 

The :class:`BaseController` interface works for mobile robots, articulations, and combined systems such as humanoids. This tutorial creates a differential drive controller for a Jetbot, with optional composition of a low-pass filter controller for improved robustness in noisy conditions.

You'll build a controller that:

* Converts desired robot velocities into wheel commands
* Applies filtering for smooth motion
* Runs in a real-time simulation loop

All code examples come from the complete, runnable file ``mobile_robot_control_example.py``:

.. code-block:: bash

    # Mobile robot controller with differential drive and optional filtering
    ./python.sh standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py

.. note::
   You can run this example with the arguments ``--noise`` and ``--filter`` to see how the Jetbot performs with different combinations of noise and filtering enabled. 
   For example, try running with neither argument to see performance under ideal conditions and no filtering. Try ``--noise`` to see the adverse effects on the controller
   performance under noisy input conditions. Finally, try ``--filter --noise`` to see the controller's robustness under noisy input conditions with filtering enabled:

   .. code-block:: bash

       # Run with noise and filtering enabled
       ./python.sh standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py --noise --filter

Understanding Control Spaces First
-----------------------------------

Before building controllers with the :class:`BaseController` interface, you must understand :class:`RobotState` and **control spaces**. 
Control spaces are fundamental to how the Motion Generation API works, and getting them right from the start will prevent many common issues.

What Are Control Spaces?
#########################

Control spaces represent the **full shared space** that all your controllers will use. They define the ordered list of names (joints, links, or sites) 
that all controllers working together must agree upon.

For example, if you're designing a collection of 6 controllers that will all share control over 9 joints, they all need to know the same ordering of those 9 joints. 
This shared ordering is the **joint space** (``robot_joint_space``). Similarly, if multiple controllers will control links or sites, they must share the same 
**link space** (``robot_link_space``) or **site space** (``robot_site_space``).

When you create any part of a :class:`RobotState` (joints, links, or sites), you must **declare the space** that those components exist in. 
The space you provide must match across all controllers that will work together.

The Ideal Workflow
##################

The recommended workflow is to **define your spaces first**, before creating any controllers:

1. **Define your joint space**: Create an ordered list of all joint names that any controller might control
2. **Define your link space**: Create an ordered list of all link names whose poses you want to control
3. **Define your site space**: Create an ordered list of all site names (end effectors, tool frames, etc.) whose poses you want to control

Then, when you create all your controllers, use these same space definitions. This ensures all controllers share the same understanding of the robot's structure 
and prevents errors when combining states from different controllers.

Control spaces are often obtained from your robot representation (e.g., ``Articulation.dof_names`` for joint space). However, controllers don't depend on these sources; they work with any ordered list of names, making them flexible and usable with any robot definition.

RobotState Structure
####################

:class:`RobotState` is a unified representation that supports controlling different parts of the robot in different ways. A :class:`RobotState` can contain:

* ``joints`` - Joint positions, velocities, and efforts (joint-space control)
* ``sites`` - Poses and twists of specific points on the robot (site-space control)
* ``links`` - Poses and twists of robot links (link-space control)
* ``root`` - Pose and twist of the robot root (root-space control)

Each of these fields are optional; a controller can specify only the parts of the state it wants to control.

Creating RobotStates with Control Spaces
#########################################

You typically create RobotState objects using the component state classes:

* :meth:`JointState.from_name` - For joint-space control (requires ``robot_joint_space``)
* :meth:`SpatialState.from_name` - For link-space or site-space control (requires ``robot_link_space`` or ``robot_site_space``)
* :class:`RootState` - For root-space control (no control space required, as there's only one root)

When creating state components, you provide the full control space (the ordered list of all names) and specify which parts you want to control. 
This allows you to create partial states; you can control only specific joints, links, or sites, and only the properties you need. 
For example, with joints you might control some via position and others via velocity. To skip a control mode entirely, pass ``None``.

Combining RobotStates
---------------------

The :func:`combine_robot_states` function lets you merge two :class:`RobotState` objects together. This enables different 
controllers to control different parts of the robot simultaneously.

For example, one controller might control the robot's arm joints while another controls the gripper, and a third controls the base position. 
The combine function will return ``None`` if the states cannot be combined. This only happens in two cases:

* Two :class:`RobotState` objects try to define the same property of the same joint or frame (i.e., both try to define the velocity of the same joint, or orientation of the same site).
* The defined control spaces don't match (e.g. defined and mismatching ``robot_joint_space`` definitions, defined and mismatching ``robot_link_space`` definitions, defined and mismatching ``robot_site_space`` definitions).

This is why defining your spaces first is critical - if controllers use different space definitions, their states cannot be combined.

The Controller Interface
-------------------------

Now that you understand control spaces, let's look at the :class:`BaseController` interface. Controllers are the heart of the Motion Generation API. 
They compute desired robot states based on the current state and optional setpoints. 

Every controller in the Motion Generation API implements the :class:`BaseController` interface, which defines two essential methods:

:meth:`reset` - Initializes the controller to a safe starting state. Called once immediately before the controller starts running.

:meth:`forward` - Computes the desired robot state for the next time step. Called every time step with 

* the current clock time
* the current estimated :class:`RobotState`, and 
* an optional setpoint :class:`RobotState` (the goal). 

The :meth:`forward` method returns a :class:`RobotState` representing the next desired state, or ``None`` if it cannot produce a valid output.

Controller Composition
-----------------------

The API provides several convenient classes to compose controllers together in common patterns:

Parallel Controllers
####################

:class:`ParallelController` runs multiple controllers simultaneously and combines their outputs. This is perfect when you want different controllers 
to control different parts of the robot. The :class:`ParallelController` automatically merges the outputs - as long as controllers don't try to control 
the same joints or frames, their states are combined seamlessly.

Sequential Controllers
#######################

:class:`SequentialController` runs multiple controllers in sequence. The output of one controller becomes the setpoint for the next. This is useful 
for filtering or processing controller outputs. For example, you might have a filter which smooths noisy input data, followed by a PID-like controller which drives the robot to the filtered input.

Controller Containers
#####################

:class:`ControllerContainer` allows you to switch between different controllers at runtime. This is useful for integrating with higher-level control systems such as state machines or behavior trees. 
By packaging multiple controllers into a single container, you can create complex behaviors for manipulation tasks, or other tasks that require many phases.
The container automatically calls :meth:`reset` on the new controller when switching.

Nesting Controllers
-------------------

Since all composition classes are themselves controllers, you can nest them to build complex control hierarchies. For example, you might 
have a :class:`ParallelController` containing a :class:`SequentialController` and another controller, all wrapped in a :class:`ControllerContainer` for runtime switching.

Building Our Mobile Robot Controller
-------------------------------------

Now that we understand the core concepts - control spaces, :class:`RobotState`, and the :class:`BaseController` interface - let's start building our mobile robot controller. 
We'll build it step by step, starting with the core differential drive controller, then adding filtering, and finally putting it all together in a complete control loop.

Defining Our Control Space
###########################

Following the ideal workflow, we first define our control space. For this mobile robot controller, we need to control the robot's joints (the wheel joints). 
We get the joint space from the robot articulation (e.g., ``robot.dof_names``). This ``robot_joint_space`` defines the ordered list of all joints in our robot. 
All controllers we create will use this same space definition, ensuring they can work together and their states can be combined.

Now let's see how we'll use this space when creating :class:`RobotState` objects. We'll need to create :class:`RobotState` objects in two key places:

* When reading the current state from the robot (joint-space)
* When setting desired velocities for our robot (root-space)

Here's how we'll read the current robot state and create a :class:`RobotState`:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-create-robotstate-from-robot-snippet>
   :end-before: <end-create-robotstate-from-robot-snippet>
   :language: python

Notice that we provide the full ``robot_joint_space`` and specify all joints with their positions, velocities, and efforts. This creates a complete joint state that matches the robot's current configuration.

Here's how we'll create a :class:`RobotState` with a desired root state to set desired velocities for our mobile robot:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-create-robotstate-root-space-snippet>
   :end-before: <end-create-robotstate-root-space-snippet>
   :language: python

This creates a :class:`RobotState` with a desired root state (linear and angular velocities), leaving joints undefined.

Step 1: The Differential Drive Controller
############################################

Our mobile robot uses a differential drive system - two wheels that can be controlled independently. Our first controller will convert desired 
robot velocities (how fast we want the robot to move forward and turn) into individual wheel velocities. This is the core of our mobile robot controller.

Initialization: Parameterizing the Controller
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We need to parameterize the controller based on the geometry of our particular robot. The differential drive controller needs to know the wheel radius, 
the distance between wheels (wheel base). We also need to know which joints control the left and right wheels:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-differential-drive-init-snippet>
   :end-before: <end-differential-drive-init-snippet>
   :language: python

The :meth:`reset` Method: Initializing the Controller
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`DifferentialDriveController` is stateless, so we don't actually need to do anything here. The :meth:`reset` method simply returns ``True``:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-differential-drive-reset-snippet>
   :end-before: <end-differential-drive-reset-snippet>
   :language: python

The :meth:`forward` Method: Computing Wheel Velocities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :meth:`forward` method is where the controller does its work. We first verify the inputs:

* if there is no root state, we return ``None``
* if the input joint state doesn't use the same ``robot_joint_space`` as our controller, we return ``None``. 
* Otherwise, we compute the wheel speeds using differential drive kinematics and return the desired :class:`RobotState`:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-differential-drive-forward-snippet>
   :end-before: <end-differential-drive-forward-snippet>
   :language: python

The controller uses differential drive kinematics to convert root velocities to wheel velocities.

Step 2: Adding Smoothing with a Low-Pass Filter
#################################################

Our differential drive controller works, but the wheel commands might be jerky if the input velocities change suddenly. We'll add a low-pass filter controller, which will smooth the wheel velocity commands
at the expense of adding some lag into the system dynamics.
This filter controller is generic and can be reused any other time we may want joint filtering - it's not specific to differential drive controllers.

Initialization: Configuring the Filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The low-pass filter controller needs to know the robot's joint space and the filter coefficient (alpha). The alpha parameter controls how much filtering 
is applied - smaller values mean more filtering (smoother but more lag in the system response):

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-low-pass-filter-init-snippet>
   :end-before: <end-low-pass-filter-init-snippet>
   :language: python

The :meth:`reset` Method: Initializing the Filter State
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We reset the initial filter state to be exactly the underlying joint-data array from the estimated state. This prevents jerky motions in the robot - 
if the filter is initialized to match the exact state of the robot, then the robot will smoothly transition into following the filter as soon as it starts running:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-low-pass-filter-reset-snippet>
   :end-before: <end-low-pass-filter-reset-snippet>
   :language: python

The :meth:`forward` Method: Applying the Filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :meth:`forward` method applies the low-pass filter to the entire underlying data array of the setpoint state, filtering all joint outputs (positions, velocities, 
and efforts) simultaneously. If there is no setpoint state, we return ``None``:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-low-pass-filter-forward-snippet>
   :end-before: <end-low-pass-filter-forward-snippet>
   :language: python

The filter controller applies a low-pass filter to the entire underlying data array, smoothing all joint outputs simultaneously.

Step 3: Composing the Controllers
##################################

If the ``--filter`` argument is passed, we'll combine our two controllers using :class:`SequentialController`; the differential drive controller computes the wheel velocities, 
and then the filter smooths them before they're sent to the robot. Otherwise, we'll use the differential drive controller alone.

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-sequential-controller-snippet>
   :end-before: <end-sequential-controller-snippet>
   :language: python


Step 4: The Complete Control Loop
###################################

Now we have all the pieces - the differential drive controller, the filter, and they're composed together. The final step is to put it all together 
in a control loop that runs in real-time. 

First, this is how we will apply the desired state to the robot:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-apply-desired-state-to-robot-snippet>
   :end-before: <end-apply-desired-state-to-robot-snippet>
   :language: python

And finally, here's the complete control loop that brings everything together. We set the setpoint linear and angular
velocities (``v_linear`` and ``v_angular``) to be constant numbers, which should make the robot follow a circular path.
If the ``--noise`` argument is passed, we add noise to the setpoint velocities.

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/mobile_robot_control_example.py
   :start-after: <start-mobile-control-loop-snippet>
   :end-before: <end-mobile-control-loop-snippet>
   :language: python


The loop:

1. Gets the current estimated state from the robot
2. Creates a root velocity setpoint (linear and angular velocities)
3. Calls the controller's :meth:`forward` method
4. Applies the desired state to the robot
5. Repeats every simulation step

You've now built a complete mobile robot controller from the ground up, using :class:`RobotState` to represent robot states and the :class:`BaseController` interface to compute desired commands. 
The controller converts high-level velocity commands into smooth wheel motions, demonstrating how the Motion Generation 
API's concepts work together in practice.

Observing the Controller Performance
------------------------------------

When you run the standalone example, you can observe how the controller performs under different conditions. 
The motion becomes jerky when you add the ``--noise`` argument, as the noisy input affects the controller's ability to produce 
smooth commands. However, when you add both ``--noise`` and ``--filter`` arguments, the motion becomes smooth again, 
demonstrating how the low-pass filter controller rejects the high-frequency noise.

.. figure:: images/isim_6.0_full_tut_viewport_mobile_control.webp
   :align: center
   :width: 100%

   Running the controller with no noise and no filtering.

.. figure:: images/isim_6.0_full_tut_viewport_mobile_control_noise.webp
   :align: center
   :width: 100%

   Running the controller with noise and no filtering.

.. figure:: images/isim_6.0_full_tut_viewport_mobile_control_noise_filter.webp
   :align: center
   :width: 100%

   Running the controller with noise and filtering.

Next Steps
----------

See detailed examples of the :class:`Path` and :class:`Trajectory` interfaces and the :class:`TrajectoryFollower` controller:

* :doc:`trajectory_planning` - Running trajectories with the Trajectory interface
