..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _ira_custom_writer_example:

===========================================
Example: RTSP Streaming with CustomWriter
===========================================

This walkthrough demonstrates how to use the :ref:`CustomWriter <ira_configuration_file>` to stream live RTSP video from IRA cameras. The ``RTSPStreamWriter`` provided by the ``isaacsim.streaming.rtsp`` extension serves as the target writer.

``RTSPStreamWriter`` streams LdrColor frames over RTSP and supports two encoding modes: 

- hardware-accelerated H.264 (default)
- raw CUDA

Because it is designed with a **one-to-one mapping** between writer instances and cameras, each camera requires its own ``CustomWriter`` entry with a unique port.

Prerequisites
=============

-  Isaac Sim is installed and can launch successfully.
-  The ``isaacsim.replicator.agent.core`` and ``isaacsim.replicator.agent.ui`` extensions are enabled (:ref:`Enable extensions <actor_sim_enable_extensions>`).
-  An RTSP client is available for playback (for example, `VLC <https://www.videolan.org/>`_, ``ffplay``, or a GStreamer pipeline).

Step 1: Enable the RTSP Streaming Extension
============================================

``RTSPStreamWriter`` is provided by the ``isaacsim.streaming.rtsp`` extension. If the extension is not already active, enable it before proceeding:

1.  Open **Window > Extensions** to launch the Extension Manager.
2.  Search for ``isaacsim.streaming.rtsp``.
3.  If the extension is not enabled, click the toggle to enable it. Check the **autoload** checkbox if you want it to load automatically on future launches.

After enabled, ``RTSPStreamWriter`` registers itself in ``omni.replicator.core.WriterRegistry`` and becomes available to the CustomWriter selection dialog.

Step 2: Add a CustomWriter and Select the Writer
==================================================

1.  Open the Actor SDG panel (**Tools > Action and Event Data Generation > Actor SDG**).
2.  Scroll to the **Replicator** section and click **Add Writer**.
3.  Select **CustomWriter** from the writer type list and click **Next**.
4.  In the **Configure CustomWriter** dialog, open the **Writer Name** dropdown and look for ``RTSPStreamWriter``.

    -   If ``RTSPStreamWriter`` appears in the list, select it and proceed to step 5.
    -   If it does not appear, follow step 3 below to register it manually.

Step 3: Manual Registration 
=========================================

If ``RTSPStreamWriter`` is not listed in the **Writer Name** dropdown, the extension may not have been enabled or its self-registration may not have run yet. You can register the writer class manually:

1.  In the **Class Path** field, enter:

    .. code-block:: text

        isaacsim.streaming.rtsp.impl.rtsp_writer.RTSPStreamWriter

2.  Click **Register**. The system imports the class, validates that it is a subclass of ``omni.replicator.core.Writer``, and registers it in the ``WriterRegistry``.
3.  The **Writer Name** dropdown refreshes and ``RTSPStreamWriter`` appears. Select it.
4.  Click **OK** to confirm.

Step 4: Configure the Sensor Prim List
========================================

``RTSPStreamWriter`` is designed with a **one-to-one** mapping: each writer instance streams from exactly one camera. You must specify the target camera by adding it to the **Sensor Prim List** within the CustomWriter panel:

1.  In the CustomWriter parameters panel, click **Add Parameter** and select ``sensor_prim_list``.
2.  Add the prim path of the camera you want to stream (for example, ``/World/Cameras/Camera_01``).

.. note::
    If ``sensor_prim_list`` is left empty, the writer attempts to attach to all cameras under the sensor root, which is not supported by ``RTSPStreamWriter``. Always specify exactly one camera per CustomWriter instance.

Step 5: Set the Port and Mount Path
=====================================

Each RTSP stream requires a unique network port. When streaming from multiple cameras, assign a different ``port`` value to each CustomWriter instance to avoid conflicts.

1.  Click **Add Parameter** and select ``port``. Set a port number (default is ``8554``). Valid range is 1--65535.
2.  Click **Add Parameter** and select ``mountPath``. Enter a descriptive mount path that starts with ``/`` (for example, ``/camera_01``). This makes it easier to identify each stream when monitoring.

The resulting RTSP URL for this stream is:

.. code-block:: text

    rtsp://localhost:<port><mountPath>

For example, with ``port: 8554`` and ``mountPath: /camera_01``, the stream URL is ``rtsp://localhost:8554/camera_01``.

Step 6: Optional Encoding Settings
====================================

``RTSPStreamWriter`` supports two encoding modes controlled by the ``encoding`` parameter:

-   ``"h264"`` (default): Pre-encoded H.264 with per-frame SEI metadata injection. This is the recommended mode for most use cases.
-   ``"raw"``: Uncompressed CUDA RGBA buffer path. The RTSP backend handles encoding internally.

When using ``"h264"`` encoding, you can also configure ``width`` and ``height`` (default 1920x1080) to set the RTSP server resolution.

Multi-camera YAML Example
===========================

The following config streams from two cameras on separate ports:

.. code-block:: yaml

    replicator:
      writers:
        CustomWriter:
          writer_name: "RTSPStreamWriter"
          writer_class_path: "isaacsim.streaming.rtsp.impl.rtsp_writer.RTSPStreamWriter"
          sensor_prim_list:
            - "/World/Cameras/Camera_01"
          port: 8554
          mountPath: "/camera_01"
          encoding: "h264"
        CustomWriter_1:
          writer_name: "RTSPStreamWriter"
          writer_class_path: "isaacsim.streaming.rtsp.impl.rtsp_writer.RTSPStreamWriter"
          sensor_prim_list:
            - "/World/Cameras/Camera_02"
          port: 8555
          mountPath: "/camera_02"
          encoding: "h264"

.. tip::
    If the ``isaacsim.streaming.rtsp`` extension is enabled and ``RTSPStreamWriter`` is already registered, ``writer_class_path`` can be omitted. It is included here for robustness so the config works even when the extension has not been loaded yet.

Verify the Stream
==================

After clicking **Start Data Generation**, open an RTSP client and connect to the stream URL. For example, with ``ffplay``:

.. code-block:: bash

    ffplay rtsp://localhost:8554/camera_01

You should recieve live rendered frames from the corresponding camera. Repeat for each port and mount-path pair to verify all streams.
