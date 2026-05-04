:orphan:

.. _isaac_franka_pick_place:

=============================
Franka Pick and Place Example
=============================

Overview
========

The Franka pick-and-place example demonstrates a simple, linear action sequence for robotic manipulation. This example shows how to send and retrieve actions, sequence them together, and can serve as a guide for implementing different action sequences.

Learning Objectives
=======================

This example demonstrates how to:

- Set up a Franka robot with gripper in Isaac Sim
- Implement a linear pick and place sequence
- Control robot movements and gripper actions
- Sequence multiple actions together in a simple workflow
- Use the example as a foundation for more complex manipulation tasks


Code Structure
==============

The Franka pick-and-place example follows a simple, direct code structure:

.. code-block:: text

    # Interactive Example
    isaacsim.examples.interactive/franka_pick_place_interactive.py
    ↓
    isaacsim.robot.experimental.manipulators.examples/franka/pick_place.py (single script)

    # Standalone Example
    standalone_examples/api/isaacsim.robot.experimental.manipulators/franka/pick_place.py
    ↓
    isaacsim.robot.experimental.manipulators.examples/franka/pick_place.py (single script)


How to Run the Examples
========================

Interactive Example
-------------------

1. Open Isaac Sim
2. Go to **Window > Examples > Robotics Examples**
3. Navigate to **Manipulation > Franka Pick Place**
4. Click **LOAD** to open the scene
5. Use the following controls:

   - **START PICK PLACE**: Start the pick and place sequence
   - **RESET**: Reset the world to initial state

Standalone Example
------------------

To run the standalone example from the command line:

.. tab-set::
   .. tab-item:: Linux

         .. code-block:: bash

            ./python.sh standalone_examples/api/isaacsim.robot.experimental.manipulators/franka/pick_place.py

   .. tab-item:: Windows

         .. code-block:: bash

            .\python.bat standalone_examples\api\isaacsim.robot.experimental.manipulators\franka\pick_place.py

What the Example Does
======================

The Franka pick and place example demonstrates:

1. **Robot Setup**: Initializes a Franka robot with gripper
2. **Scene Creation**: Sets up a cube to be picked up and a target location
3. **Pick Sequence**: 

   - Moves to pre-grasp position
   - Opens gripper
   - Moves to grasp position
   - Closes gripper
4. **Place Sequence**:

   - Moves to pre-place position
   - Moves to place position
   - Opens gripper to release object
   - Moves slightly upward along the Z-axis

This linear sequence shows the fundamental building blocks of robotic manipulation tasks.

Next Steps and Further Reading
===============================

This example demonstrates a very simplistic approach to task execution. For more sophisticated operations, consider exploring:

- **Cortex**: Isaac Sim's task orchestrator for complex, multi-step robotic operations
- **State Machines**: Implement more complex task logic
- **Task Planning**: Use advanced planning algorithms for complex manipulation sequences
- **Task and Motion Planning**: Advanced algorithms for complex manipulation scenarios

**Related Documentation:**

- :ref:`isaac_sim_app_tutorial_cortex_4_franka_block_stacking` - Advanced Franka examples using Cortex
- :ref:`isaac_sim_motion_generation_rmpflow` - Motion generation with RMPFlow

The current example serves as an excellent starting point for understanding the basics of robotic manipulation in Isaac Sim before moving to more complex implementations.


