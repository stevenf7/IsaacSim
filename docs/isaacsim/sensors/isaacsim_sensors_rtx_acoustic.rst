..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_rtx_acoustic:

=====================
RTX Acoustic Sensor
=====================


RTX Acoustic sensors simulate ultrasonic wave propagation at render time on the GPU with RTX hardware.
Their results are written to the ``GenericModelOutput`` AOV, similar to RTX Lidar and Radar sensors.

.. _isaacsim_sensors_rtx_acoustic_how_they_work:

Overview
--------

RTX Acoustic sensors are rendered using ``OmniAcoustic`` prims, with the ``OmniSensorGenericAcousticWpmAPI``
schema applied. After attaching a render product to the ``OmniAcoustic`` prim, and setting the
``GenericModelOutput`` AOV on the render product, the RTXSensor renderer writes acoustic simulation
results to the AOV.

Unlike Lidar and Radar sensors, acoustic sensors do not produce a 3D point cloud. Instead, they produce
**signal ways** — amplitude samples for each transmitter–receiver pair on each channel. The
``GenericModelOutput`` element fields have the following meaning for acoustic sensors:

.. csv-table::
    :header: "Field", "Meaning"
    :widths: 15, 85

    "``x``", "Transmitter sensor mount ID"
    "``y``", "Receiver sensor mount ID"
    "``z``", "Channel ID"
    "``scalar``", "Amplitude sample value"

Sensor Mounts and Receiver Groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Acoustic sensors use **multi-apply schemas** to define sensor mounts and receiver groups:

- **Sensor mounts** (``OmniSensorWpmAcousticSensorMountAPI``) define the physical positions and
  orientations of transducers (transmitters and receivers). Each mount is an instance with a unique
  name (for example, ``m001``, ``m002``).

- **Receiver groups** (``OmniSensorWpmAcousticRxGroupAPI``) define logical groupings of receivers
  by specifying which mount indices belong to the group. Each group is an instance with a unique
  name (for example, ``g001``).

These schemas are applied automatically when the corresponding attribute prefixes are provided
in the ``attributes`` dictionary.

How to Create an RTX Acoustic Sensor
-------------------------------------

The ``isaacsim.sensors.experimental.rtx`` extension provides the ``Acoustic`` class for creating RTX
Acoustic sensors.

Create an RTX Acoustic Sensor Using the ``Acoustic`` Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``Acoustic`` class creates or wraps an ``OmniAcoustic`` prim with the appropriate schemas applied.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_acoustic/create_an_rtx_acoustic.py
    :language: python

The snippet above creates an ``OmniAcoustic`` prim at ``/World/acoustic`` with:

- A center frequency of 40,000 Hz (ultrasonic)
- Two sensor mounts at positions ``(0, 0, 0)`` and ``(0.1, 0, 0)``
- A receiver group combining both mounts

Tick Rate
^^^^^^^^^

The ``tick_rate`` parameter (Hz) controls how frequently the sensor renders. A value of ``0``
(the default) enables autotrigger mode, where the sensor renders every simulation frame. Setting a
nonzero value causes the sensor to render at the specified frequency independently of the simulation
step rate. This maps to the ``omni:sensor:tickRate`` prim attribute.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_acoustic/set_acoustic_tick_rate.py
    :language: python

Auxiliary Output Level
^^^^^^^^^^^^^^^^^^^^^^

In previous releases, users set ``auxOutputType`` as a prim attribute directly on acoustic prims.
With the experimental API in 6.0, use the ``aux_output_level`` constructor parameter instead. This
controls what auxiliary data appears in ``GenericModelOutput`` frames.

Valid values for Acoustic: ``"NONE"`` (default), ``"BASIC"``.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_acoustic/set_acoustic_aux_output_level.py
    :language: python

See :ref:`rtx_sensor_annotator_descriptions` for details on what fields are available at each level.

How to Collect Data from an RTX Acoustic Sensor
-------------------------------------------------

Use the ``AcousticSensor`` runtime class to attach annotators and retrieve data:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_acoustic/collect_data_with_acoustic_sensor.py
    :language: python

Refer to :ref:`rtx_sensor_reading_gmo_buffer` for more details on the ``GenericModelOutput`` buffer.

Standalone Examples
-------------------

**Basic Creation**

.. code-block:: bash

    # Create an acoustic sensor with two mounts and a receiver group
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_acoustic_basic.py

**Data Inspection**

.. code-block:: bash

    # Inspect acoustic GenericModelOutput data and signal ways
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/inspect_acoustic_gmo.py

.. note::

    Refer to the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.
