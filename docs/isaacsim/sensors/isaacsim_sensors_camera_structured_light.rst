..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaacsim_sensors_camera_structured_light:

========================
Structured Light Cameras
========================

|isaac-sim_short| models structured light cameras through the ``isaacsim.sensors.experimental.rtx.StructuredLightCamera`` class. Structured light imaging works by projecting a known pattern onto a scene
and capturing the deformation of that pattern from a camera offset from the projector. Cycling through a sequence of patterns and reconstructing the deformation between projector and camera frames allows
fine-grained depth recovery. Real structured light rigs commonly use phase-shifting sinusoids, gray-code stripes, or De Bruijn patterns; the per-pattern exposure is typically on the order of microseconds to
milliseconds, which keeps the captured scene effectively static across the pattern sequence.

Overview
========

``StructuredLightCamera`` is a subclass of ``isaacsim.sensors.experimental.rtx.RtxCamera``. In addition to the underlying USD ``Camera`` prim, it creates a parent ``Xform`` (default ``{path}/projectors``) populated with one
``UsdLux.RectLight`` per projector pattern. Each ``RectLight`` has the ``ShapingAPI`` schema applied, the projector pattern as its ``inputs:texture:file``, the projector direction texture as its
``projector:directionTexture:file``, ``isProjector=True``, and ``visibleInPrimaryRay=False``. At any given simulation time exactly one ``RectLight`` is visible.

Pattern selection is **simulation-time-driven**:

* The constructor accepts a ``projector_timestamps`` list of rational tuples ``(numerator, denominator)``, one per pattern. Each tuple is the simulation time (in seconds) at which that pattern becomes active.
  The first entry must represent :math:`t = 0` (typically ``(0, 1)``; any ``(0, k)`` is accepted), and the list must be strictly increasing. Rational tuples avoid the floating-point precision issues that
  arise when timestamps span sub-millisecond resolution. If ``projector_timestamps`` is omitted, the schedule defaults to ``[(i, 30) for i in range(N)]`` (a 30 Hz uniform cadence).
* On every Kit app-update tick, an observer reads the current timeline value, computes ``current_time mod cycle_period``, and selects the pattern whose timestamp is the largest one less than or equal to the
  resulting phase. The cycle period defaults to ``timestamps[-1] + (timestamps[1] - timestamps[0])`` for :math:`N \geq 2` patterns, or ``Fraction(1, 30)`` for :math:`N = 1`. It can be overridden via
  ``projector_cycle_period``.

Because pattern intervals are typically much smaller than a single physics step, the class emits a one-time warning at the first observed simulation ``dt`` larger than the minimum interval between consecutive
patterns (including the wrap-around from the last pattern back to the first), and a per-tick warning whenever a single tick advances the active pattern by more than one index.

Data acquisition
================

``StructuredLightCamera`` is an authoring class — it creates and manages USD prims but does not retrieve image data on its own. To capture frames, wrap an instance in
``isaacsim.sensors.experimental.rtx.CameraSensor``:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera_structured_light/script_editor.py
   :language: python

The ``CameraSensor`` owns a Replicator render product against the same Camera prim, and there are two complementary ways to get image data out of it:

* **Manual annotator pull** — construct the sensor with the desired annotators (``annotators=["rgb"]`` above) and call ``sensor.get_data("rgb")`` from your own loop. The snippet above uses this pattern.
* **Replicator writer** — leave ``annotators=[]`` and call ``sensor.attach_writer("BasicWriter", output_dir=..., rgb=True)`` (or any other Replicator writer). Each ``rep.orchestrator.step`` then automatically
  dispatches a write to disk without any custom plumbing in your loop. See the :ref:`isaacsim_sensors_camera_structured_light_standalone` section for an end-to-end example of this pattern.

.. _isaacsim_sensors_camera_structured_light_standalone:

Standalone Python
=================

The standalone example at ``standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_structured_light.py`` demonstrates capturing a 10-pattern sequence using the Replicator Orchestrator and a
``BasicWriter``. The example:

* Loads the bundled structured-light patterns and projector direction texture from the extension's ``tests/data/structured_light_camera/`` directory.
* Builds a 1000-unit white PBR cube as an enclosure, with the camera and coincident projector at the origin.
* Drives ``rep.orchestrator.step(rt_subframes=32, delta_time=<interval>)`` once per pattern, where ``<interval>`` is the difference between consecutive timestamps. Because ``timestamps[0]`` is always zero,
  the first step's ``delta_time`` is also zero, so the orchestrator captures pattern 0 at :math:`t = 0` before advancing.
* Attaches a ``BasicWriter`` to the sensor so each step writes one ``rgb_NNNN.png`` to the example's output directory.

.. note::

   This example demonstrates the API plumbing — pattern cycling, RectLight cluster authoring, calibrated camera intrinsics, and Orchestrator capture. The camera and projector share an origin and so it
   does **not** model a real depth-recovery rig (which would have a non-zero baseline between camera and projector). For a depth-recovery workflow, position the projector with ``projector_position`` /
   ``projector_orientation`` offset from the camera and adjust the captured-pattern triangulation accordingly.

Run the example:

.. code-block:: bash

   ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_structured_light.py

After the script completes, the output directory ``_example_output_isaacsim.sensors.experimental.rtx/camera_structured_light/`` contains 10 RGB frames named ``rgb_0000.png`` through ``rgb_0009.png``, plus a
``metadata.txt`` file recording the writer name, version, and Replicator global seed.

.. tab-set::

   .. tab-item:: Pattern 0

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0000.png
         :alt: Structured light capture pattern 0
         :align: center
         :width: 80%

   .. tab-item:: Pattern 1

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0001.png
         :alt: Structured light capture pattern 1
         :align: center
         :width: 80%

   .. tab-item:: Pattern 2

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0002.png
         :alt: Structured light capture pattern 2
         :align: center
         :width: 80%

   .. tab-item:: Pattern 3

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0003.png
         :alt: Structured light capture pattern 3
         :align: center
         :width: 80%

   .. tab-item:: Pattern 4

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0004.png
         :alt: Structured light capture pattern 4
         :align: center
         :width: 80%

   .. tab-item:: Pattern 5

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0005.png
         :alt: Structured light capture pattern 5
         :align: center
         :width: 80%

   .. tab-item:: Pattern 6

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0006.png
         :alt: Structured light capture pattern 6
         :align: center
         :width: 80%

   .. tab-item:: Pattern 7

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0007.png
         :alt: Structured light capture pattern 7
         :align: center
         :width: 80%

   .. tab-item:: Pattern 8

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0008.png
         :alt: Structured light capture pattern 8
         :align: center
         :width: 80%

   .. tab-item:: Pattern 9

      .. image:: /images/isim_6.0_full_ext-isaacsim.sensors.experimental.rtx-1.1.2_structured_light_rgb_0009.png
         :alt: Structured light capture pattern 9
         :align: center
         :width: 80%

.. note::

   Your output images may differ from those shown above due to variance in the renderer across different hardware and driver configurations.