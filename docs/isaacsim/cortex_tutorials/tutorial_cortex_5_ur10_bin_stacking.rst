..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_app_tutorial_cortex_5_ur10_bin_stacking:

==============================
Walkthrough: UR10 Bin Stacking
==============================



This tutorial walks through a complete bin stacking application using the UR10 robot. In this
example, we use a pre-designed USD environment containing a conveyor belt, a pallet where the bins
should be stacked, and a UR10 robot with a suction gripper. Our application doesn't add to the scene
(aside from invisible collision obstacles), and instead controls the existing USD elements in the
pre-designed USD environment.

In all command line examples, we use the abbreviation ``isaac_python`` for the Isaac Sim python
script (``<isaac_sim_root>/python.sh`` on Linux and ``<isaac_sim_root>\python.bat`` on Windows).
The command lines are written relative to the working directory
``standalone_examples/api/isaacsim.cortex.framework``.

Run the following demo

.. code-block:: bash

    isaac_python demo_ur10_conveyor_main.py

Press play once Isaac Sim has started up. You'll see the bin stacking demo running.

This tutorial will step through the demo.

.. raw:: html

   <div style="width: 100%;display: inline-block;position: relative;">
      <div id="dummy" style="margin-top: 56%;"></div>
      <div align="center">
      <div id="kaltura_player_1" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
      <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
      <script type="text/javascript">
         try {
         var kalturaPlayer = KalturaPlayer.setup({
         targetId: "kaltura_player_1",
         provider:
         { partnerId: 2935771, uiConfId: 46302491 }
         });
         kalturaPlayer.loadMedia(
         {entryId: '1_gjyv862h'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>


The setting is a UR10 robot with a suction gripper moving bins from a conveyor to a pallet. Bins
need to be stacked upside down, so any bin that that comes right-side up is flipped at a flip
station before stacking.

This demo uses a shallow decider network with a top-level dispatch node choosing among multiple
sequential state machines.

The individual behaviors demonstrate a common RMPflow programming technique where obstacle regions
are automatically toggled on and off strategically to shape the motion behavior. These obstacle
regions are modeled in the scene USD but are invisible by default. Try toggling their visibility. Go
to ``World/Ur10Table/Obstacles`` and toggle the visibility of the ``FlipStationSphere``,
``NavigationDome``, ``NavigationBarrier``, and ``NavigationFlipStation`` to see them.

The bin placement behavior also leverages the reactivity of RMPflow in conjunction with its approach
direction parameters to create an automatic adjustment behavior to correct on the fly for
misalignment between bins.


Top-level dispatch
==================

The entry point to the decider network is the ``Dispatch`` node as we can see in the construction.
``DfNetwork`` is the decider network structure; it's passed the root (the ``Dispatch`` node) and the
context object that will be available as a member within every decider/state node:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking/top_level_dispatch.py
    :language: python

The context object gives each node access to the robot's command API as well as any logical state
extracted by its monitors. The ``Dispatch`` node's ``decide()`` logic is pretty simple given the
logical state. 

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking/top_level_dispatch.py
    :language: python

The logical state includes:

* **stack_complete:** Notes whether all bins are on the pallet.
* **active_bin:** The bin that's currently in play. The bin remains active until it's been placed on
  the stack. Then a new bin is selected from the bins at the end of the conveyor.
* **active_bin.is_attached:** Indicates whether the active bin is attached to the end-effector via
  the suction gripper.
* **active_bin.needs_flip:** Indicates whether the bin attached to the end-effector is right-side-up
  (needs flip) or up-side-down (doesn't need flip).

The decision logic becomes simply: If the stack is complete or there's no active bin, then go home.
Otherwise, if there's an active bin, pick the bin if it's not already in the gripper, and flip it if
it needs to be flipped. Then place the bin on the stack. Decider networks make it easy to write this
decision logic in a readable form.

Sequential state machines
=========================

The sequential state machines that implement the pick, flip and place behaviors are each similar in
structure. 

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking/sequential_state_machines.py
    :language: python

One feature to note is the use of locking and unlocking the decider network. Decider networks are
reactive by nature, so atomic state machine behaviors that shouldn't be preempted need to be
explicitly locked. The sequential state machines make use of ``DfSetLockState`` to lock and unlock
the decider network. Additionally, ``PlaceBin`` uses ``DfWriteContextState`` to call a context
function which marks the active bin as complete once it's performed the placement procedure.


Navigation obstacle monitors
============================

The underlying motion generator for the ``MotionCommander`` is ``RMPflow`` which will automatically
avoid registered obstacles. However, there are times where those obstacles need to be turned off to
enable interaction. E.g. en route we want to avoid a manipulable object as obstacle, but once we're
there we should grab it. The ``ObstacleMonitor`` and ``ObstacleMonitorContext`` classes of
``isaacsim.cortex.framework/isaacsim/cortex/framework/obstacle_monitor_context.py`` facilitate developing obstacle
monitors which automatically toggle obstacles on and off based on programmed conditions.

Take a look at the ``ObstacleMonitor`` implementation in the file listed above. On construction it
takes a set of obstacles which it will monitor as well as the context object, and the API requires
deriving classes to implement ``is_obstacle_required()`` to define when the obstacles should be
enabled and disabled based on information accessible from the context object. The method has access
to the context as ``self.context`` similar to the decider / state objects. The API also supplies
``activate_autotoggle()`` and ``deactivate_autotoggle()`` to activate and deactivate the monitor.
When active, it'll automatically enable and disable the obstacles based on the truth value of
``is_obstacle_required()``. When deactivated, the obstacles will be disabled and remain disabled
until the monitor is reactivated.

``ObstacleMonitorContext`` is a convenient base class which adds a ``monitor_obstacles`` logical
state monitor automatically, so deriving classes only need to add the obstacle monitor objects using
``add_obstacle_monitors()``.

The ``BinStackingContext`` object derives from ``ObstacleMonitorContext`` and adds two obstacle
monitors which it uses to shape both the navigation behavior moving between the pallet and the
conveyor and the navigation around the bin flip station while flipping the bin. They're constructed
and added in the ``BinStackingContext`` constructor:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking/navigation_obstacle_monitors.py
    :language: python

Both monitors have simple logic:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking/navigation_obstacle_monitors.py
    :language: python

The ``FlipStationObstacleMonitor`` monitors the ``flip_station_sphere`` which is a spherical
obstacle around the flip station. When active, it'll enable the obstacle until the end-effector is
descending along the approach direction of its motion command toward the pose target. The monitor is
used to avoid the flip station and bin (resting on the station) after releasing it from the bottom
and moving to pick it from the top. It's activated on entry to the ``ReachToPick`` class (used any
time the bin needs to be picked, independent of whether the bin is on the flip station) and
deactivated on exit.

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking/navigation_obstacle_monitors.py
    :language: python

Similarly, the ``NavigationObstacleMonitor`` monitors a collection of obstacles which shape the
navigation behavior between the pallet and conveyor (both directions) to avoid the robot base and
current bin stack in transit. They're needed while moving from one to the other, but not needed once
the arm reaches the region of its destination (either the pallet or conveyor).

The ``MoveWithNavObs`` state object extends the ``Move`` state with entry and exit conditions that
automatically toggle the navigation obstacle:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking/def_stepself.py
    :language: python

This class is the base class for both the ``ReachToPick`` state and the ``ReachToPlace`` state used
by ``PickBin`` and ``PlaceBin`` listed above.


Robustness reactivity on placement
==================================

The bin attachment to the end-effector and the stacking alignment of the bins are both physically
simulated. Just blindly grasping and moving the bin to a target without adjusting for errors will
result in slightly misaligned bins which don't rest against each other correctly. Since we're using
a reactive motion generator (RMPflow), implementing reactive adjustments is straightforward. In
``ReachToPlace`` the adjustments are made every cycle in the ``step()`` method:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking/robustness_reactivity_on_placement.py
    :language: python

If we're placing a bin on top of another bin (``bin_under``) this code adjusts the end-effector
target based on the xy position alignment error between the bin in the gripper and the bin under
it. (The orientational alignment generally is already sufficient for successful placement.)

Additionally, RMPflow is configured to take reactive state feedback from the simulator, and we use
tight approach parameters for reaching the target (``std_dev=0.005``) so it needs to follow a narrow
funnel on approach. If the bin is misaligned on first approach, the bin physics will shove the
end-effector out of that funnel and it'll attempt the approach again.

In combination, this gets the robot to reactively adjust the positioning of the bin and retry the
approach (repeatedly if needed) until it gets it right. Often the adjustment process is sufficient,
but periodically it needs to retry the approach. Usually a single retry suffices. This is a subtle
behavior and the code is concise, but it's the difference between approximately 85% successful bin
placement and 100% success.

.. raw:: html

   <div style="width: 100%;display: inline-block;position: relative;">
      <div id="dummy" style="margin-top: 56%;"></div>
      <div align="center">
      <div id="kaltura_player_2" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
      <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
      <script type="text/javascript">
         try {
         var kalturaPlayer = KalturaPlayer.setup({
         targetId: "kaltura_player_2",
         provider:
         { partnerId: 2935771, uiConfId: 46302491 }
         });
         kalturaPlayer.loadMedia(
         {entryId: '1_yul5ho8f'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>



Logical state context
=====================

The ``BinStackingContext`` object additionally monitors all logical state needed to support the
above behaviors. These monitors are set up in the constructor and the logical state is
reset/initialized in the ``reset()`` method:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking/logical_state_context.py
    :language: python

These monitors perform the following:

#. **Monitor bins:** If there's no active bin, it checks whether there's a bin at the end of the
   conveyor and activates it if so.

#. **Monitor the active bin:** Deactivates a bin if it's dropped on the floor.

#. **Monitor the grasp transform of the active bin:** Monitors the best grasp for the current active bin.

#. **Monitor whether the active bin is reached:** Sets the ``active_bin.{is_grasp_reached,is_attached}``
   flags based on the proximity between the end-effector and desired grasp transform, and whether
   the suction gripper is "closed".

#. **Monitor diagnostics:** Prints some information about the logical state at a readable
   (throttled) rate.
