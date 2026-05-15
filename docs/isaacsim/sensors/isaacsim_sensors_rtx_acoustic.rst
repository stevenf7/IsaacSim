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

For complete documentation on all acoustic schema attributes and the underlying Wave Propagation Model (WPM),
see the `Omniverse Acoustic Extension documentation <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.acoustic/3.0.0/acoustic_extension.html>`_.

.. note::
   Earlier releases referred to this sensor as the "Ultrasonic" sensor (or "USS"). The Omniverse plugin
   has been renamed to "Acoustic"; if you previously used ``omni.kit.commands.execute("IsaacSensorCreateRtxUltrasonic", ...)``
   in ``isaacsim.sensors.rtx``, see :ref:`isaacsim_sensors_rtx_migration` for the migration to
   ``Acoustic`` / ``AcousticSensor``.

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
Acoustic sensors. An equivalent menu entry is also registered by the ``isaacsim.sensors.rtx.ui``
extension for UI-driven creation.

Create an RTX Acoustic Sensor From the Create Menu
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a generic RTX Acoustic sensor from the |isaac-sim_short| UI:

* **Main menu**: *Create > Sensors > RTX Acoustic > NVIDIA > Generic RTX Acoustic*
* **Viewport context menu** (right-click in the viewport): *Create > Isaac > Sensors > RTX Acoustic > NVIDIA > Generic RTX Acoustic*

Both entries create an ``OmniAcoustic`` prim with the ``OmniSensorGenericAcousticWpmAPI`` schema applied,
at the next available path. If a prim is selected at creation time, the new sensor is parented under
the selected prim; otherwise it is created at the stage root.

The menu entry creates a bare prim with no sensor mounts or receiver groups configured. To author the
multi-apply schemas (``OmniSensorWpmAcousticSensorMountAPI``, ``OmniSensorWpmAcousticRxGroupAPI``)
and tune attributes such as ``omni:sensor:WpmAcoustic:centerFrequency``, either edit the prim in the
property panel after creation, or use the ``Acoustic`` class for programmatic setup as shown below.

The RTX Acoustic submenu also auto-populates additional vendor entries from the
``SUPPORTED_ACOUSTIC_CONFIGS`` dict in ``isaacsim.sensors.experimental.rtx``, so OEM acoustic asset
USDs registered there appear in the menu automatically.

Create an RTX Acoustic Sensor Using the ``Acoustic`` Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``Acoustic`` class creates or wraps an ``OmniAcoustic`` prim with the appropriate schemas applied.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_acoustic/create_an_rtx_acoustic.py
    :language: python

The snippet above creates an ``OmniAcoustic`` prim at ``/World/acoustic`` with:

- A center frequency of 40,000 Hz (ultrasonic)
- Two sensor mounts at positions ``(0, 0, 0)`` and ``(0.1, 0, 0)``
- A receiver group combining both mounts

.. note::

   ``Acoustic.create()`` accepts ``config`` (from
   ``isaacsim.sensors.experimental.rtx.SUPPORTED_ACOUSTIC_CONFIGS``) or ``usd_path`` (mutually
   exclusive), plus ``attributes`` for prim-attribute overrides — including the multi-apply
   ``OmniSensorWpmAcousticSensorMountAPI`` / ``OmniSensorWpmAcousticRxGroupAPI`` /
   ``OmniSensorWpmAcousticFiringSeqAPI`` schema attributes — and the plural transform arrays
   (``positions=[[...]]`` / ``translations=[[...]]`` / ``orientations=[[...]]`` / ``scales=[[...]]``;
   ``N=1``). Additional USD schemas via ``schemas=[...]`` are accepted by the ``Acoustic(...)``
   constructor — pass them through ``Acoustic(...)`` directly if you need them, since
   ``Acoustic.create()`` does not currently forward ``schemas``.

Tick Rate
^^^^^^^^^

.. warning::

    In Isaac Sim 6.0 GA, RTX Acoustic autotriggers regardless of ``omni:sensor:tickRate`` attribute. This will be corrected in a future release.

The ``tick_rate`` parameter (Hz) controls how frequently the sensor renders. A value of ``0``
(the default) enables autotrigger mode, where the sensor renders every simulation frame. This maps to the ``omni:sensor:tickRate`` prim attribute.

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
