..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_troubleshooting:


=======================
Troubleshooting
=======================

This page serves as a central hub for troubleshooting information across Isaac Sim components. For detailed troubleshooting guidance on specific components, follow the links below.

Isaac Sim Issues
====================

Isaac Lab
^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   ../isaac_lab_tutorials/troubleshooting

ROS 2 Troubleshooting
^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   ../ros2_tutorials/troubleshooting

Replicator
^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   ../replicator_tutorials/troubleshooting

Robot Setup
^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   ../robot_setup/troubleshooting

Digital Twin
^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   ../digital_twin/troubleshooting

Common Issues
=============

Installation Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

Linux Driver Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~


* See :doc:`Linux Troubleshooting<dev-guide:linux-troubleshooting>` to resolve driver installation issues on Linux.
* We recommend installing the **Latest Production Branch Version drivers** from the `Unix Driver Archive`_ using the :code:`.run` installer on Linux, if you are on a new GPU or experiencing issues with current drivers.
* NVIDIA driver version **535.216.01** or later is recommended when upgrading to **Ubuntu 22.04.5 kernel 6.8.0-48-generic** or later.

.. _Unix Driver Archive: https://www.nvidia.com/Download/Find.aspx?lang=en-us

Performance Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

Tracy Profiler
~~~~~~~~~~~~~~~~

For performance troubleshooting, you can use the Tracy profiler to gauge the performance of various components of the application.
See :ref:`isaac_sim_app_profiling_performance` for details on using Tracy for performance profiling.

Simulation Frame Rates
~~~~~~~~~~~~~~~~~~~~~~

If you observe publish rates that differ from the target simulation frame rate, first confirm you set the rate coherently using the ``SimulationManager.setup_simulation`` + ``RenderingManager.set_dt`` pair documented at :ref:`isaac_sim_app_tutorial_ros2_publish_rate_set_simulation_frame_rates`. Setting only one of the three rate clocks (loop rate, timeline ``timeCodesPerSecond``, physics ``timeStepsPerSecond``) produces non-obvious slow-motion or fast-forward behavior - see :ref:`isaac_sim_sensors_multitick_clock_relationships`.

If the rate is set coherently and the issue persists, try:

1. Running |isaac-sim_short| with factory settings to clear any persistent simulation frame rate settings:

   .. code-block:: bash

       ./isaac-sim.sh --reset-user

2. Check your computer's CPU usage to identify bottlenecks. If Isaac Sim is exhibiting incredibly high usage, try running with *Fabric* enabled.

.. _isaac_sim_troubleshooting_animation_playback_slow:

Choppy or Slow Animation Playback (Fixed Time Stepping)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If USD scenes containing keyframe animations play back smoothly in USD Composer (or in Isaac Sim 4.5) but appear slow, choppy, or lag wall-clock when played in Isaac Sim 5.0 or later, the cause is **Fixed Time Stepping**.

The full Isaac Sim experience enables Fixed Time Stepping by default (in ``isaacsim.exp.full.kit``) so that ``SimulationApp`` and other scripted workflows step the timeline deterministically. Under Fixed Time Stepping, the timeline advances by a fixed ``dt`` per loop tick rather than by wall-clock time, so if the renderer cannot sustain the target rate (typically 60 Hz on heavy scenes), simulated time — including animation playback — falls behind real time. This behavior is documented for ``/app/player/useFixedTimeStepping`` in the ``omni.timeline`` Kit reference, which recommends **Variable** stepping for animation-only scenarios.

For interactive GUI animation playback on heavy scenes, launch with the following overrides to opt the experience into Variable stepping:

.. code-block:: bash

    ./isaac-sim.sh \
        --/app/player/useFixedTimeStepping=false \
        --/app/runLoops/main/manualModeEnabled=false \
        --/exts/isaacsim.core.throttling/enable_manualmode=false

All three flags are required: the first two switch the timeline and main loop out of fixed/manual stepping at startup, and the third prevents the ``isaacsim.core.throttling`` extension from re-enabling manual mode on every Play (see ``_on_play`` in ``source/extensions/isaacsim.core.throttling/isaacsim/core/throttling/extension.py``). Disabling these defaults gives up determinism for scripted simulation runs, so use them for animation review / authoring workflows rather than for ``SimulationApp`` jobs that rely on a fixed per-step ``dt``.

The Isaac Sim Base experience (``isaacsim.exp.base.kit``) already sets ``player.useFixedTimeStepping = false`` for the same reason, which is why scenes played from Base or from USD Composer do not exhibit this lag.

If you are authoring the scene rather than just reviewing it, prefer one of the alternatives described in :ref:`isaac_sim_animated_usd_fixed_step_alternatives` over relying on the GUI launch-flag workaround — those keep determinism for ``SimulationApp`` and remain correct under any time-stepping mode.

Reducing Log Output
~~~~~~~~~~~~~~~~~~~~

There can be many warnings and other messages when running |isaac-sim_short|. You can reduce log output using command line arguments:

.. code-block:: bash

    --/log/level=error --/log/fileLogLevel=error --/log/outputStreamLevel=error

UI Issues
^^^^^^^^^^^^

When the frame rate is low, the UI response may be sluggish. This can be resolved using "Ctrl + click" instead of the standard "click" to select objects.


Windows-Specific Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

Thread Cleanup
~~~~~~~~~~~~~~

When running standalone examples in Windows, threads may not be properly cleaned up when the application is closed. This can usually be ignored because the application will still successfully close. As a workaround, add multiple ``standalone_app.update()`` calls before calling ``standalone_app.close()``.

File Path Length
~~~~~~~~~~~~~~~~

The ``omni.kit.telemetry`` extension startup error with code ``(error = 206)`` on Windows is caused by a file path exceeding the length limit. Verify that the file path of ``omni.telemetry.transmitter.exe`` does not exceed 260 characters.

GPU Overclocking
~~~~~~~~~~~~~~~~

If you encounter the error message ``Windows fatal exception: int divide by zero`` once the app is started, it could be due to GPU overclocking software such as MSI Afterburner. Try disabling such software to resolve the issue.

Python Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

Python errors related to ``tkinter`` indicate the user is attempting to use ``tkinter`` with the Python distribution shipped with |isaac-sim_short|. This is not supported.

Additional Resources
====================

For a comprehensive list of known issues and their workarounds, see :ref:`isaac_sim_known_issues`. 