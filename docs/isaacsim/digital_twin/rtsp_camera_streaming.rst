..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_rtsp_camera_streaming:

===============================
Live Camera Streaming over RTSP
===============================

|isaac-sim| can publish a live video feed of a camera in the scene over the
Real Time Streaming Protocol (RTSP). Frames captured from a render product are
encoded with NVIDIA's hardware video encoder (NVENC) and pushed to an in-process
RTSP server, which any standard client (VLC, ``ffplay``, GStreamer, OpenCV) can
connect to. This is the recommended path for piping simulated camera output
into perception stacks, recording rigs, broadcast pipelines, or downstream
analytics services that already speak RTSP.

The streaming pipeline ships in the ``isaacsim.streaming.rtsp`` extension and is
enabled by default in the full Isaac Sim experience. It exposes two
entry points: an |omnigraph_short| node for declarative scene-graph
authoring, and a Replicator writer for fully programmatic setups.


.. _isaac_sim_rtsp_prerequisites:

Prerequisites
=============

Ensure you have the following:

* An NVIDIA GPU with NVENC support (required for H.264 encoding).
* The ``isaacsim.streaming.rtsp`` extension. It is bundled with the
  ``isaacsim.exp.full`` experience and loads automatically. To enable it
  manually in a custom experience, open **Window > Extensions** and toggle
  **RTSP Streaming OmniGraph Nodes** on.


.. _isaac_sim_rtsp_streaming_a_camera:

Streaming a Camera
==================

The ``isaacsim.streaming.rtsp.RTSPCameraHelper`` |omnigraph_short| node
publishes a camera's render product over RTSP. A complete pipeline consists
of this node and two supporting nodes wired in a single execution chain:

* ``OnPlaybackTick`` --- runs the graph once per timeline frame while
  playback is running.
* ``IsaacCreateRenderProduct`` --- creates (or reuses) a render product
  for the target camera at the requested resolution and emits its USD
  path on ``renderProductPath``.
* ``RTSPCameraHelper`` --- attaches the streaming writer to that render
  product and brings up the RTSP server on the configured port and mount
  path.

Building the Graph in the Editor
--------------------------------

The recommended way to author the pipeline is the |omnigraph_short| editor.
To build the graph:

1. Open **Window > Visual Scripting > Action Graph** and click **New Action
   Graph**.
2. Add the three nodes listed above. To find them, search for ``RTSP``,
   ``Isaac Create Render Product``, and ``On Playback Tick``.
3. Connect ``OnPlaybackTick.tick`` to ``IsaacCreateRenderProduct.execIn``,
   then ``IsaacCreateRenderProduct.execOut`` to ``RTSPCameraHelper.execIn``.
4. Connect ``IsaacCreateRenderProduct.renderProductPath`` to
   ``RTSPCameraHelper.renderProductPath`` so the helper attaches to the
   render product the previous node created.
5. On the ``IsaacCreateRenderProduct`` node, set **cameraPrim** to the
   camera you want to stream.
6. On the ``RTSPCameraHelper`` node, set **port** (default ``8554``) and
   **mountPath** (default ``/stream``).
7. Press **Play** in the timeline. The RTSP server starts lazily on the
   first rendered frame and the stream becomes available at
   ``rtsp://localhost:8554/<mountPath>``. The server shuts down cleanly when
   you press **Stop**.

Refer to :ref:`isaac_sim_rtsp_streaming_parameters` for the full set of node
inputs. The screencast below shows the full sequence end-to-end:

.. image:: /images/isim_6.0_streaming_rtsp_gui_create_action_graph.gif
    :alt: Animated walkthrough showing how to create an action graph in the OmniGraph editor with OnPlaybackTick, IsaacCreateRenderProduct, and RTSPCameraHelper nodes wired together to stream a camera over RTSP.
    :align: center
    :width: 100%

Building the Graph from a Script
--------------------------------

The same pipeline can be authored programmatically using
:py:class:`omni.graph.core.Controller`. This is useful for headless setups,
batch jobs, and tests. The snippet below builds the equivalent graph against
a camera at ``/Camera`` and configures the stream at
``rtsp://localhost:8554/stream``. Press **Play** or start Replicator capture
to produce frames and start the RTSP server.

.. literalinclude:: ../snippets/digital_twin/rtsp_camera_streaming/stream_camera.py
    :language: python

Connecting a Client
-------------------

Any standard RTSP client (such as VLC, ``ffplay``, or GStreamer) can
subscribe to the stream at ``rtsp://<host>:<port><mountPath>``.

When connecting from another machine, replace ``localhost`` with the
simulator host's IP and make sure the port is reachable through any
firewalls.


.. _isaac_sim_rtsp_streaming_parameters:

Stream Parameters
=================

The ``RTSPCameraHelper`` node exposes the following inputs:

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Input
     - Default
     - Description
   * - ``renderProductPath``
     - ---
     - Path of the render product whose ``LdrColor`` Arbitrary Output Variable
       (AOV) is streamed. Wire it
       to the ``renderProductPath`` output of ``IsaacCreateRenderProduct`` or
       set it to a pre-authored render product prim.
   * - ``port``
     - ``8554``
     - TCP port the RTSP server listens on. Must be in ``1``--``65535``. Each
       simultaneous stream needs a unique port.
   * - ``mountPath``
     - ``/stream``
     - Path appended to the server URL (for example ``/front``, ``/cam_1``).
       Must start with ``/``.
   * - ``useRawEncoding``
     - ``false``
     - When ``false``, frames are pre-encoded as H.264 in the render pipeline
       (NVENC) and Supplemental Enhancement Information (SEI) metadata is
       injected per frame. When ``true``, raw RGBA
       CUDA buffers are streamed and the RTSP server encodes them. Refer to
       :ref:`isaac_sim_rtsp_encoding_modes`.
   * - ``enabled``
     - ``true``
     - Toggle the stream at runtime. Setting it to ``false`` after attachment
       tears down the server and releases the port.


.. _isaac_sim_rtsp_encoding_modes:

Encoding Modes
==============

The writer supports two encoding paths, controlled by ``useRawEncoding``:

H.264 (Default, Recommended)
----------------------------

The render pipeline produces H.264-encoded bytes directly using NVENC and
hands them to the RTSP server already compressed. This mode:

* Minimizes copies (no CPU readback, no double-encode).
* Supports per-frame SEI metadata. Refer to :ref:`isaac_sim_rtsp_frame_metadata`.
* Sends the simulation timestamp with each streamed frame so downstream
  consumers can align frames to the sim time.

Use this mode unless you have a specific reason to bypass NVENC.

Raw
---

The writer streams uncompressed RGBA CUDA buffers and lets the RTSP server
encode them internally.

The render product's resolution is read from the CUDA buffer shape on the
first frame. SEI metadata injection is **not** supported in raw mode.


.. _isaac_sim_rtsp_streaming_multi_camera:

Streaming Multiple Cameras
==========================

To publish several cameras simultaneously, instantiate one ``RTSPCameraHelper``
per camera and give each helper a unique ``port``. The ``mountPath`` can be
shared across streams, but using a descriptive mount path per camera (such as
``/front`` and ``/rear``) makes the URLs self-documenting:

.. literalinclude:: ../snippets/digital_twin/rtsp_camera_streaming/stream_multiple_cameras.py
    :language: python

The two streams above are addressable as ``rtsp://localhost:8554/front`` and
``rtsp://localhost:8555/rear``. Each helper owns its own RTSP server, so a
client connecting to one stream does not affect the other.


.. _isaac_sim_rtsp_frame_metadata:

Frame Metadata
==============

In H.264 mode, each frame carries a Supplemental Enhancement Information
(SEI) Network Abstraction Layer (NAL) unit with a JSON payload. The payload uses the fixed UUID
``aa71e48f-0711-5d80-a247-cd31ca6fa49c``, derived from
``isaacsim.streaming.rtsp.sei_metadata``, so consumers can identify and filter
the metadata stream. The schema is:

.. code-block:: json

    {
        "publish_sim_time_ns": 1500000000,
        "timestamp_iso8601": "2026-01-01T12:00:01.500Z",
        "timestamp": 1767268801500000000,
        "frame_num": 42
    }

* ``publish_sim_time_ns`` --- simulation time at frame capture, in
  nanoseconds. Reset to zero when the timeline stops and restarts.
* ``timestamp_iso8601`` --- wall-clock timestamp anchored to the moment the
  RTSP server started, advanced by ``publish_sim_time_ns``. Useful for
  correlating with logs and other wall-clock-stamped streams.
* ``timestamp`` --- the same instant as ``timestamp_iso8601``, expressed as
  nanoseconds since the Unix epoch.
* ``frame_num`` --- monotonically increasing frame counter, starting at ``1``
  and reset on detach.

Downstream tools that parse SEI NAL units (for example a custom
``rtspsrc`` callback in GStreamer, or NVIDIA DeepStream's metadata API) can
recover the payload by matching the UUID and decoding the JSON bytes.


.. _isaac_sim_rtsp_attach_writer_directly:

Attaching the Writer Directly
=============================

For workflows that already drive Replicator from Python and don't need the
|omnigraph_short| layer (custom SDG scripts, batch jobs, headless services),
``isaacsim.streaming.rtsp.RTSPStreamWriter`` can be attached to a
render product directly. The writer is registered with Replicator's
``WriterRegistry`` on extension startup and accepts ``port``, ``mountPath``,
``encoding``, ``width``, and ``height`` parameters. Author the SRTX
``LdrColor`` ``RenderVar`` on the render product first via
``isaacsim.streaming.rtsp.impl.render_var_utils.ensure_render_var_on_product``,
then attach the writer:

.. literalinclude:: ../snippets/digital_twin/rtsp_camera_streaming/attach_writer_programmatically.py
    :language: python

After attaching the writer, start Replicator capture or play the timeline to
produce frames. The RTSP server starts when the writer receives the first
frame.

.. _isaac_sim_rtsp_server_lifecycle:

Server Lifecycle
================

The RTSP server starts the first time the writer receives a frame and stops
when the writer detaches. ``RTSPCameraHelper`` ties this lifecycle to the
timeline:

* **Play** --- the action graph runs, the writer attaches to the render
  product, and the server starts on the first frame.
* **Stop** --- the writer detaches, the server is torn down, and the port
  is released.
* **Setting** ``enabled`` **to** ``false`` --- same effect as **Stop** for
  that helper.

If the RTSP server encounters an unrecoverable error during streaming (for
example a connection failure or NVENC error), the writer logs the error,
shuts down its server, and silently skips subsequent frames until the
timeline restarts. This prevents a broken stream from spamming the log or
blocking the simulation loop.


.. _isaac_sim_rtsp_troubleshooting:

Troubleshooting
===============

The stream URL refuses connections
    The RTSP server starts only after the first rendered frame. Press
    **Play** and confirm the timeline is advancing. If the writer logged a
    setup error (for example "render product has no resolution attribute"),
    the server never started. Check the carb log for details.

Port already in use
    Another process (or another ``RTSPCameraHelper`` in the same scene) is
    already bound to the port. Pick a unique port per helper and verify that
    nothing else is listening with ``ss -ltnp | grep 8554``.

Stream stops mid-run and never recovers
    The writer enters a "failed" state on the first encoder or transport
    error, drops further frames silently, and waits for the timeline to
    restart. Stop and restart the timeline (or toggle ``enabled``) to retry it.

SEI metadata is missing
    SEI metadata is only injected in H.264 mode. Set ``useRawEncoding`` to
    ``false`` (the default).
