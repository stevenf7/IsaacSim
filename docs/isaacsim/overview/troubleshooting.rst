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

If you observe publish rates that differ from the target simulation frame rate, try:

1. Running |isaac-sim_short| with factory settings to clear any persistent simulation frame rate settings:

   .. code-block:: bash

       ./isaac-sim.sh --reset-user

2. Check your computer's CPU usage to identify bottlenecks. If Isaac Sim is exhibiting incredibly high usage, try running with *Fabric* enabled.

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